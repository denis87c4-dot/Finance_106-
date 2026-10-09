import React, { useState, useMemo } from 'react';
import { useFinance } from '../../context/FinanceContext';
import {
  mean,
  median,
  standardDeviation,
  percentile,
  medianAbsoluteDeviation,
  skewness,
  kurtosis,
  shannonEntropy,
  giniIndex,
  advancedLinearRegression,
  AdvancedRegressionResult
} from '../../utils/mathStats';
import {
  Brain,
  TrendingUp,
  TrendingDown,
  Activity,
  Filter,
  SlidersHorizontal,
  Sparkles,
  BarChart2,
  Calendar,
  AlertTriangle,
  CheckCircle2,
  ArrowRight,
  Info,
  ShieldAlert,
  Compass,
  Cpu
} from 'lucide-react';

export const IaAnalysisTab: React.FC = () => {
  const { transactions, categories, accounts } = useFinance();

  // ==================== FILTROS PODEROSOS ====================
  const [presetTemporal, setPresetTemporal] = useState<string>('Todo o histórico');
  const [customStartDate, setCustomStartDate] = useState<string>('2026-01-01');
  const [customEndDate, setCustomEndDate] = useState<string>('2026-12-31');

  const [selectedGrouping, setSelectedGrouping] = useState<'Diário' | 'Semanal' | 'Mensal'>('Mensal');
  const [targetMetric, setTargetMetric] = useState<'Fluxo Líquido' | 'Despesas' | 'Receitas' | 'Saldo Acumulado'>('Fluxo Líquido');

  const [filterType, setFilterType] = useState<string>('Todos');
  const [selectedCats, setSelectedCats] = useState<string[]>([]);
  const [selectedAccs, setSelectedAccs] = useState<string[]>([]);
  const [filterStatus, setFilterStatus] = useState<string>('Todos');
  const [minValue, setMinValue] = useState<string>('');
  const [maxValue, setMaxValue] = useState<string>('');

  const formatBRL = (val: number) =>
    new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);

  // Filter application
  const filteredTransactions = useMemo(() => {
    const today = new Date();

    return transactions.filter(t => {
      const txDate = new Date(t.data);

      // Preset Temporal
      if (presetTemporal === 'Últimos 30 dias') {
        const d30 = new Date();
        d30.setDate(today.getDate() - 30);
        if (txDate < d30 || txDate > today) return false;
      } else if (presetTemporal === 'Últimos 90 dias') {
        const d90 = new Date();
        d90.setDate(today.getDate() - 90);
        if (txDate < d90 || txDate > today) return false;
      } else if (presetTemporal === 'Ano corrente') {
        const startYear = new Date(today.getFullYear(), 0, 1);
        const endYear = new Date(today.getFullYear(), 11, 31);
        if (txDate < startYear || txDate > endYear) return false;
      } else if (presetTemporal === 'Personalizado') {
        if (t.data < customStartDate || t.data > customEndDate) return false;
      }

      // Tipo
      if (filterType !== 'Todos' && t.tipo !== filterType) return false;

      // Categorias
      if (selectedCats.length > 0 && !selectedCats.includes(t.categoria)) return false;

      // Contas
      if (selectedAccs.length > 0 && !selectedAccs.includes(t.conta)) return false;

      // Status
      if (filterStatus !== 'Todos' && t.status !== filterStatus) return false;

      // Min / Max
      const minNum = parseFloat(minValue);
      if (!isNaN(minNum) && t.valor < minNum) return false;

      const maxNum = parseFloat(maxValue);
      if (!isNaN(maxNum) && t.valor > maxNum) return false;

      return true;
    });
  }, [
    transactions,
    presetTemporal,
    customStartDate,
    customEndDate,
    filterType,
    selectedCats,
    selectedAccs,
    filterStatus,
    minValue,
    maxValue
  ]);

  // Aggregate time series for regression and statistical analysis
  const aggregatedSeries = useMemo(() => {
    const map = new Map<string, { income: number; expense: number; count: number }>();

    filteredTransactions.forEach(t => {
      let key = t.data.substring(0, 7); // Mês YYYY-MM
      if (selectedGrouping === 'Diário') {
        key = t.data; // YYYY-MM-DD
      } else if (selectedGrouping === 'Semanal') {
        const d = new Date(t.data);
        const firstDayOfYear = new Date(d.getFullYear(), 0, 1);
        const pastDaysOfYear = (d.getTime() - firstDayOfYear.getTime()) / 86400000;
        const weekNum = Math.ceil((pastDaysOfYear + firstDayOfYear.getDay() + 1) / 7);
        key = `${d.getFullYear()}-S${weekNum.toString().padStart(2, '0')}`;
      }

      const cur = map.get(key) || { income: 0, expense: 0, count: 0 };
      if (t.tipo === 'Receita') cur.income += t.valor;
      if (t.tipo === 'Despesa') cur.expense += t.valor;
      cur.count += 1;
      map.set(key, cur);
    });

    const sortedKeys = Array.from(map.keys()).sort();
    let accumulated = 0;

    return sortedKeys.map((k, idx) => {
      const item = map.get(k)!;
      const net = item.income - item.expense;
      accumulated += net;

      let targetVal = net;
      if (targetMetric === 'Despesas') targetVal = item.expense;
      else if (targetMetric === 'Receitas') targetVal = item.income;
      else if (targetMetric === 'Saldo Acumulado') targetVal = accumulated;

      return {
        index: idx,
        periodo: k,
        income: item.income,
        expense: item.expense,
        net,
        accumulated,
        targetVal,
        count: item.count
      };
    });
  }, [filteredTransactions, selectedGrouping, targetMetric]);

  // ==================== ANÁLISE DE REGRESSÃO OLS ====================
  const regression: AdvancedRegressionResult = useMemo(() => {
    const xVals = aggregatedSeries.map(s => s.index);
    const yVals = aggregatedSeries.map(s => s.targetVal);
    return advancedLinearRegression(xVals, yVals);
  }, [aggregatedSeries]);

  // Projeção futura com base na reta da regressão para os próximos 3 períodos
  const futureProjections = useMemo(() => {
    const n = aggregatedSeries.length;
    if (n === 0) return [];
    const lastPeriod = aggregatedSeries[n - 1].periodo;

    return [1, 2, 3].map(step => {
      const nextX = n - 1 + step;
      const yHat = regression.intercept + regression.slope * nextX;
      return {
        step,
        label: `T+${step} (${lastPeriod} +${step})`,
        predictedValue: yHat,
        lowerBound: yHat - 1.96 * regression.stdError,
        upperBound: yHat + 1.96 * regression.stdError
      };
    });
  }, [aggregatedSeries, regression]);

  // ==================== DETALHAMENTO ESTATÍSTICO & FINANCEIRO ====================
  const statsAndFinancials = useMemo(() => {
    const vals = filteredTransactions.map(t => (t.tipo === 'Despesa' ? -t.valor : t.valor));
    const absVals = filteredTransactions.map(t => t.valor);
    const n = vals.length;

    const totalRec = filteredTransactions
      .filter(t => t.tipo === 'Receita')
      .reduce((a, b) => a + b.valor, 0);

    const totalDesp = filteredTransactions
      .filter(t => t.tipo === 'Despesa')
      .reduce((a, b) => a + b.valor, 0);

    const saldoLiq = totalRec - totalDesp;
    const grossVolume = absVals.reduce((a, b) => a + b, 0);

    const m = mean(absVals);
    const med = median(absVals);
    const s = standardDeviation(absVals, m);
    const cv = m > 0 ? (s / m) * 100 : 0;
    const mad = medianAbsoluteDeviation(absVals);

    const q75 = percentile(absVals, 75);
    const q25 = percentile(absVals, 25);
    const iqr = q75 - q25;

    const p95 = percentile(absVals, 95);
    const skew = skewness(vals);
    const kurt = kurtosis(vals);

    // Gini e Shannon
    const gini = giniIndex(absVals);
    const catEntropy = shannonEntropy(filteredTransactions.map(t => t.categoria));

    // VaR 95% e CVaR
    const var95 = n > 1 ? percentile(vals, 5) : vals[0] || 0;
    const tailVals = vals.filter(v => v <= var95);
    const cvar = tailVals.length > 0 ? mean(tailVals) : var95;

    // Métricas financeiras
    const margemOperacional = totalRec > 0 ? (saldoLiq / totalRec) * 100 : 0;
    const taxaPoupanca = totalRec > 0 ? Math.max(0, (saldoLiq / totalRec) * 100) : 0;
    const ticketMedio = n > 0 ? grossVolume / n : 0;

    // Runway em meses (baseado nas despesas do período)
    const distinctMonths = new Set(filteredTransactions.map(t => t.data.substring(0, 7))).size || 1;
    const burnRateMensal = totalDesp / distinctMonths;
    const runway = burnRateMensal > 0 ? Math.max(0, saldoLiq / burnRateMensal) : 12;

    return {
      n,
      totalRec,
      totalDesp,
      saldoLiq,
      grossVolume,
      m,
      med,
      s,
      cv,
      mad,
      iqr,
      p95,
      skew,
      kurt,
      gini,
      catEntropy,
      var95,
      cvar,
      margemOperacional,
      taxaPoupanca,
      ticketMedio,
      burnRateMensal,
      runway
    };
  }, [filteredTransactions]);

  // ==================== DIAGNÓSTICO HEURÍSTICO DE IA ====================
  const aiDiagnostics = useMemo(() => {
    const list: { type: 'alert' | 'success' | 'info'; title: string; desc: string }[] = [];

    // 1. Tendência OLS da métrica
    if (regression.rSquared >= 0.4) {
      if (regression.slope > 0) {
        list.push({
          type: 'success',
          title: `Trajetória Positiva em ${targetMetric}`,
          desc: `A regressão linear indica uma taxa de aceleração consistente de +${formatBRL(regression.slope)} por ${selectedGrouping.toLowerCase()}, com aderência explicativa R² de ${(regression.rSquared * 100).toFixed(1)}%.`
        });
      } else {
        list.push({
          type: 'alert',
          title: `Vetor de Redução em ${targetMetric}`,
          desc: `Identificada inclinação decrescente com declínio médio de -${formatBRL(Math.abs(regression.slope))} por ${selectedGrouping.toLowerCase()}. Recomenda-se calibrar os tetos de gasto.`
        });
      }
    } else {
      list.push({
        type: 'info',
        title: `Comportamento Disperso / Estocástico (R²: ${(regression.rSquared * 100).toFixed(1)}%)`,
        desc: `A série apresenta flutuações distribuídas sem dependência linear estrita, caracterizando estabilidade operacional ou sazonalidade equilibrada.`
      });
    }

    // 2. Margem e Poupança
    if (statsAndFinancials.margemOperacional >= 20) {
      list.push({
        type: 'success',
        title: 'Eficiência de Caixa Superior',
        desc: `Sua margem operacional está em ${statsAndFinancials.margemOperacional.toFixed(1)}%, indicando excelente poder de retenção de capital superavitário.`
      });
    } else if (statsAndFinancials.margemOperacional < 5) {
      list.push({
        type: 'alert',
        title: 'Atenção à Margem de Segurança',
        desc: `Margem operacional atual de ${statsAndFinancials.margemOperacional.toFixed(1)}% está próxima da paridade orçamentária. Qualquer desvio atípico pode gerar déficit temporário.`
      });
    }

    // 3. Risco de Cauda (VaR)
    if (Math.abs(statsAndFinancials.var95) > statsAndFinancials.m * 1.8) {
      list.push({
        type: 'alert',
        title: 'Exposição de Cauda Assimétrica (Outliers)',
        desc: `O VaR 95% (${formatBRL(statsAndFinancials.var95)}) aponta para risco de transações concentradas pontuais que podem desestabilizar o fluxo planejado.`
      });
    }

    return list;
  }, [regression, targetMetric, selectedGrouping, statsAndFinancials]);

  // SVG Scatter + Regression Graph
  const svgWidth = 840;
  const svgHeight = 320;
  const padding = { top: 30, right: 40, bottom: 45, left: 60 };

  const chartData = useMemo(() => {
    if (aggregatedSeries.length === 0) return null;
    const yVals = aggregatedSeries.map(s => s.targetVal);
    const futureY = futureProjections.map(f => f.predictedValue);
    const allY = [...yVals, ...futureY];

    const minY = Math.min(0, ...allY);
    const maxY = Math.max(10, ...allY);
    const totalPoints = aggregatedSeries.length + futureProjections.length;

    const scaleX = (xIndex: number) => {
      const span = Math.max(1, totalPoints - 1);
      return padding.left + (xIndex / span) * (svgWidth - padding.left - padding.right);
    };

    const scaleY = (val: number) => {
      const range = maxY - minY || 1;
      return svgHeight - padding.bottom - ((val - minY) / range) * (svgHeight - padding.top - padding.bottom);
    };

    // Actual line points
    const actualPoints = aggregatedSeries.map(s => ({
      x: scaleX(s.index),
      y: scaleY(s.targetVal),
      raw: s
    }));

    // Regression line endpoints
    const regStart = {
      x: scaleX(0),
      y: scaleY(regression.intercept)
    };
    const regEnd = {
      x: scaleX(totalPoints - 1),
      y: scaleY(regression.intercept + regression.slope * (totalPoints - 1))
    };

    // Future projection points
    const projPoints = futureProjections.map((f, i) => {
      const xIdx = aggregatedSeries.length + i;
      return {
        x: scaleX(xIdx),
        y: scaleY(f.predictedValue),
        label: f.label,
        val: f.predictedValue
      };
    });

    return { actualPoints, regStart, regEnd, projPoints, minY, maxY, scaleX, scaleY };
  }, [aggregatedSeries, futureProjections, regression]);

  return (
    <div className="space-y-6">
      {/* Title & Badge */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-purple-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <Brain className="w-5 h-5 text-white" />
            </div>
            <span>IA Analysis: Inteligência Analítica & Regressão</span>
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Motor de inteligência quantitativa multidimensional com regressão linear OLS, testes de significância estatística, projeções prospectivas e síntese preditiva.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-3 py-1 bg-indigo-500/15 border border-indigo-500/30 text-indigo-400 rounded-full text-xs font-mono font-semibold flex items-center gap-1.5">
            <Cpu className="w-3.5 h-3.5" />
            <span>Motor Quantitativo V3 Ativo</span>
          </span>
        </div>
      </div>

      {/* ==================== PAINEL DE FILTROS PODEROSOS ==================== */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-3xl p-5 sm:p-6 shadow-xl space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800/80">
          <div className="flex items-center gap-2 text-sm font-bold text-white">
            <SlidersHorizontal className="w-4 h-4 text-emerald-400" />
            <span>Filtros Poderosos de Análise</span>
          </div>
          <span className="text-xs text-slate-400">
            {filteredTransactions.length} de {transactions.length} transações selecionadas
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
          {/* Preset Temporal */}
          <div>
            <label className="block text-slate-400 font-semibold uppercase mb-1.5">
              Preset Temporal
            </label>
            <select
              value={presetTemporal}
              onChange={e => setPresetTemporal(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
            >
              <option value="Todo o histórico">Todo o Histórico</option>
              <option value="Últimos 30 dias">Últimos 30 dias</option>
              <option value="Últimos 90 dias">Últimos 90 dias</option>
              <option value="Ano corrente">Ano Corrente (2026)</option>
              <option value="Personalizado">Período Personalizado</option>
            </select>
          </div>

          {/* Agrupamento Temporal */}
          <div>
            <label className="block text-slate-400 font-semibold uppercase mb-1.5">
              Agrupamento para Séries / Regressão
            </label>
            <select
              value={selectedGrouping}
              onChange={e => setSelectedGrouping(e.target.value as any)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
            >
              <option value="Diário">Diário (Dia a Dia)</option>
              <option value="Semanal">Semanal (Semanas do Ano)</option>
              <option value="Mensal">Mensal (Mês a Mês)</option>
            </select>
          </div>

          {/* Métrica Alvo da Regressão */}
          <div>
            <label className="block text-indigo-400 font-semibold uppercase mb-1.5 flex items-center gap-1">
              <Compass className="w-3.5 h-3.5" />
              <span>Métrica Alvo (Eixo Y)</span>
            </label>
            <select
              value={targetMetric}
              onChange={e => setTargetMetric(e.target.value as any)}
              className="w-full bg-slate-950 border border-indigo-500/40 rounded-xl px-3 py-2 text-white font-semibold focus:outline-none focus:border-indigo-500"
            >
              <option value="Fluxo Líquido">Fluxo Líquido (Receita - Despesa)</option>
              <option value="Despesas">Despesas Totais</option>
              <option value="Receitas">Receitas Totais</option>
              <option value="Saldo Acumulado">Patrimônio / Saldo Acumulado</option>
            </select>
          </div>

          {/* Tipo de Lançamento */}
          <div>
            <label className="block text-slate-400 font-semibold uppercase mb-1.5">
              Tipo de Transação
            </label>
            <select
              value={filterType}
              onChange={e => setFilterType(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
            >
              <option value="Todos">Todos os Tipos</option>
              <option value="Receita">Apenas Receitas</option>
              <option value="Despesa">Apenas Despesas</option>
              <option value="Transferência">Apenas Transferências</option>
            </select>
          </div>
        </div>

        {/* Custom Date Range if active */}
        {presetTemporal === 'Personalizado' && (
          <div className="grid grid-cols-2 gap-4 text-xs pt-1">
            <div>
              <label className="block text-slate-400 mb-1">Data Início</label>
              <input
                type="date"
                value={customStartDate}
                onChange={e => setCustomStartDate(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white font-mono"
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1">Data Fim</label>
              <input
                type="date"
                value={customEndDate}
                onChange={e => setCustomEndDate(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white font-mono"
              />
            </div>
          </div>
        )}

        {/* Second Row of Filters: Categorias, Contas, Status, Faixa de Valor */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs pt-2 border-t border-slate-800/60">
          {/* Status */}
          <div>
            <label className="block text-slate-400 font-semibold uppercase mb-1.5">Status</label>
            <select
              value={filterStatus}
              onChange={e => setFilterStatus(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white"
            >
              <option value="Todos">Todos os Status</option>
              <option value="Efetivado">Liquidado / Efetivado</option>
              <option value="Orçado">Orçado / Previsto</option>
            </select>
          </div>

          {/* Valor Mínimo */}
          <div>
            <label className="block text-slate-400 font-semibold uppercase mb-1.5">Valor Mínimo (R$)</label>
            <input
              type="number"
              placeholder="Ex: 50"
              value={minValue}
              onChange={e => setMinValue(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white font-mono"
            />
          </div>

          {/* Valor Máximo */}
          <div>
            <label className="block text-slate-400 font-semibold uppercase mb-1.5">Valor Máximo (R$)</label>
            <input
              type="number"
              placeholder="Ex: 5000"
              value={maxValue}
              onChange={e => setMaxValue(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white font-mono"
            />
          </div>

          {/* Reset Filters */}
          <div className="flex items-end">
            <button
              onClick={() => {
                setPresetTemporal('Todo o histórico');
                setFilterType('Todos');
                setSelectedCats([]);
                setSelectedAccs([]);
                setFilterStatus('Todos');
                setMinValue('');
                setMaxValue('');
              }}
              className="w-full py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl font-semibold transition-colors"
            >
              Resetar Filtros
            </button>
          </div>
        </div>
      </div>

      {/* ==================== SÍNTESE DIAGNÓSTICA DE IA ==================== */}
      <div className="space-y-3">
        <h3 className="text-sm font-bold uppercase tracking-wider text-indigo-400 flex items-center gap-2">
          <Sparkles className="w-4 h-4" />
          <span>Diagnósticos Preditivos Gerados pela IA em Tempo Real</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {aiDiagnostics.map((diag, idx) => (
            <div
              key={idx}
              className={`p-4 rounded-2xl border transition-all ${
                diag.type === 'alert'
                  ? 'bg-rose-500/10 border-rose-500/30 text-rose-300'
                  : diag.type === 'success'
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                  : 'bg-indigo-500/10 border-indigo-500/30 text-indigo-300'
              }`}
            >
              <div className="flex items-center gap-2 mb-1.5 font-bold text-white text-sm">
                {diag.type === 'alert' && <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />}
                {diag.type === 'success' && <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />}
                {diag.type === 'info' && <Info className="w-4 h-4 text-indigo-400 shrink-0" />}
                <span>{diag.title}</span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">{diag.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* ==================== NÚCLEO DE REGRESSÃO LINEAR OLS ==================== */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-3xl p-6 shadow-xl space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="p-2 rounded-xl bg-purple-500/20 text-purple-400">
                <TrendingUp className="w-5 h-5" />
              </span>
              <h3 className="text-lg font-bold text-white">
                Análise de Regressão Linear & Modelagem Preditiva OLS
              </h3>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Ajuste por Mínimos Quadrados Ordinários ($Y = \beta_1 X + \beta_0$) para modelar a dinâmica de {targetMetric}.
            </p>
          </div>

          {/* Equation Badge */}
          <div className="bg-slate-950 border border-purple-500/40 px-4 py-2 rounded-2xl">
            <span className="text-[10px] text-slate-400 uppercase font-semibold block">Equação da Reta OLS</span>
            <span className="text-base font-extrabold text-purple-300 font-mono tracking-wide">
              {regression.equation}
            </span>
          </div>
        </div>

        {/* Regression Metrics Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <div className="bg-slate-950/70 p-3 rounded-2xl border border-slate-800">
            <span className="text-[10px] text-slate-400 uppercase font-semibold block">Coef. R² (Determinação)</span>
            <span className="text-lg font-bold text-white font-mono mt-0.5 block">
              {(regression.rSquared * 100).toFixed(1)}%
            </span>
            <span className="text-[10px] text-slate-500">Variância explicada</span>
          </div>

          <div className="bg-slate-950/70 p-3 rounded-2xl border border-slate-800">
            <span className="text-[10px] text-slate-400 uppercase font-semibold block">Pearson (r)</span>
            <span
              className={`text-lg font-bold font-mono mt-0.5 block ${
                regression.r >= 0 ? 'text-emerald-400' : 'text-rose-400'
              }`}
            >
              {regression.r.toFixed(3)}
            </span>
            <span className="text-[10px] text-slate-500">Correlação linear</span>
          </div>

          <div className="bg-slate-950/70 p-3 rounded-2xl border border-slate-800">
            <span className="text-[10px] text-slate-400 uppercase font-semibold block">Inclinação (β₁)</span>
            <span className="text-lg font-bold text-indigo-400 font-mono mt-0.5 block">
              {formatBRL(regression.slope)}
            </span>
            <span className="text-[10px] text-slate-500">Por {selectedGrouping.toLowerCase()}</span>
          </div>

          <div className="bg-slate-950/70 p-3 rounded-2xl border border-slate-800">
            <span className="text-[10px] text-slate-400 uppercase font-semibold block">Intercepto (β₀)</span>
            <span className="text-lg font-bold text-white font-mono mt-0.5 block">
              {formatBRL(regression.intercept)}
            </span>
            <span className="text-[10px] text-slate-500">Nível base inicial</span>
          </div>

          <div className="bg-slate-950/70 p-3 rounded-2xl border border-slate-800">
            <span className="text-[10px] text-slate-400 uppercase font-semibold block">Erro Padrão (Sₑ)</span>
            <span className="text-lg font-bold text-amber-400 font-mono mt-0.5 block">
              {formatBRL(regression.stdError)}
            </span>
            <span className="text-[10px] text-slate-500">Dispersão residual</span>
          </div>

          <div className="bg-slate-950/70 p-3 rounded-2xl border border-slate-800">
            <span className="text-[10px] text-slate-400 uppercase font-semibold block">Durbin-Watson (DW)</span>
            <span className="text-lg font-bold text-sky-400 font-mono mt-0.5 block">
              {regression.durbinWatson.toFixed(2)}
            </span>
            <span className="text-[10px] text-slate-500">Autocorrelação</span>
          </div>
        </div>

        {/* Interactive SVG Chart: Scatter Points + Regression Line + Projections */}
        <div className="bg-slate-950/90 border border-slate-800/80 rounded-2xl p-4 sm:p-5">
          <div className="flex flex-wrap items-center justify-between gap-3 text-xs mb-4">
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1.5 text-sky-400">
                <span className="w-2.5 h-2.5 rounded-full bg-sky-400"></span> Observações Reais
              </span>
              <span className="flex items-center gap-1.5 text-purple-400">
                <span className="w-4 h-0.5 bg-purple-400"></span> Linha de Regressão OLS
              </span>
              <span className="flex items-center gap-1.5 text-emerald-400">
                <span className="w-2.5 h-2.5 rounded-full border border-dashed border-emerald-400 bg-emerald-500/20"></span> Projeções Futuras (T+1 .. T+3)
              </span>
            </div>
            <span className="text-slate-400 font-mono text-[11px]">{regression.trendDescription}</span>
          </div>

          {chartData ? (
            <div className="w-full overflow-x-auto">
              <svg
                viewBox={`0 0 ${svgWidth} ${svgHeight}`}
                className="w-full h-auto min-w-[700px] text-slate-400"
              >
                {/* Horizontal Zero / Base Line */}
                <line
                  x1={padding.left}
                  y1={chartData.scaleY(0)}
                  x2={svgWidth - padding.right}
                  y2={chartData.scaleY(0)}
                  stroke="#334155"
                  strokeWidth="1"
                  strokeDasharray="2 2"
                />

                {/* Regression OLS line */}
                <line
                  x1={chartData.regStart.x}
                  y1={chartData.regStart.y}
                  x2={chartData.regEnd.x}
                  y2={chartData.regEnd.y}
                  stroke="#a855f7"
                  strokeWidth="2.5"
                />

                {/* Actual Observation Line */}
                <path
                  d={chartData.actualPoints.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ')}
                  fill="none"
                  stroke="#38bdf8"
                  strokeWidth="1.5"
                  opacity="0.5"
                />

                {/* Actual Observation Scatter Points */}
                {chartData.actualPoints.map((p, i) => (
                  <g key={i}>
                    <circle cx={p.x} cy={p.y} r="4.5" fill="#38bdf8" />
                    <text
                      x={p.x}
                      y={svgHeight - padding.bottom + 18}
                      textAnchor="middle"
                      fill="#94a3b8"
                      fontSize="9"
                      fontFamily="monospace"
                    >
                      {p.raw.periodo.slice(-5)}
                    </text>
                  </g>
                ))}

                {/* Projected Future Points */}
                {chartData.projPoints.map((fp, i) => (
                  <g key={`proj-${i}`}>
                    <circle
                      cx={fp.x}
                      cy={fp.y}
                      r="5.5"
                      fill="#10b981"
                      stroke="#ffffff"
                      strokeWidth="1.5"
                      strokeDasharray="2 2"
                    />
                    <text
                      x={fp.x}
                      y={fp.y - 10}
                      textAnchor="middle"
                      fill="#10b981"
                      fontSize="10"
                      fontWeight="bold"
                      fontFamily="monospace"
                    >
                      {formatBRL(fp.val)}
                    </text>
                    <text
                      x={fp.x}
                      y={svgHeight - padding.bottom + 18}
                      textAnchor="middle"
                      fill="#10b981"
                      fontSize="9"
                      fontWeight="bold"
                      fontFamily="monospace"
                    >
                      {`T+${i + 1}`}
                    </text>
                  </g>
                ))}

                {/* Y Axis Reference Labels */}
                <text
                  x={padding.left - 8}
                  y={chartData.scaleY(chartData.maxY) + 4}
                  textAnchor="end"
                  fill="#64748b"
                  fontSize="9"
                  fontFamily="monospace"
                >
                  {formatBRL(chartData.maxY)}
                </text>
                <text
                  x={padding.left - 8}
                  y={chartData.scaleY(chartData.minY) - 4}
                  textAnchor="end"
                  fill="#64748b"
                  fontSize="9"
                  fontFamily="monospace"
                >
                  {formatBRL(chartData.minY)}
                </text>
              </svg>
            </div>
          ) : (
            <div className="py-12 text-center text-slate-500 text-xs">
              Sem dados suficientes após filtragem para plotar a regressão linear.
            </div>
          )}
        </div>

        {/* Future Prediction Table */}
        <div className="space-y-2">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
            Previsões Lineares de Curto Prazo (Próximos Períodos)
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {futureProjections.map(proj => (
              <div key={proj.step} className="bg-slate-950/70 p-3.5 rounded-2xl border border-slate-800 text-xs">
                <div className="flex items-center justify-between text-slate-400 font-mono mb-1">
                  <span>Horizonte: {proj.label}</span>
                  <span className="text-emerald-400 font-bold">Projetado</span>
                </div>
                <div className="text-base font-extrabold text-white font-mono">
                  {formatBRL(proj.predictedValue)}
                </div>
                <div className="text-[10px] text-slate-500 font-mono mt-1">
                  Intervalo IC 95%: {formatBRL(proj.lowerBound)} a {formatBRL(proj.upperBound)}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ==================== DETALHAMENTO ESTATÍSTICO & FINANCEIRO COMPLETO ==================== */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Painel Estatístico */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-3xl p-6 shadow-xl space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400">
                <Activity className="w-5 h-5" />
              </span>
              <h3 className="text-base font-bold text-white">Detalhamento Estatístico Robusto</h3>
            </div>
            <span className="text-xs text-slate-400 font-mono">{statsAndFinancials.n} amostras</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
            <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/60">
              <span className="text-slate-400 text-[10px] uppercase font-semibold block">Média (μ)</span>
              <span className="text-sm font-bold text-white font-mono mt-0.5 block">
                {formatBRL(statsAndFinancials.m)}
              </span>
            </div>

            <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/60">
              <span className="text-slate-400 text-[10px] uppercase font-semibold block">Mediana</span>
              <span className="text-sm font-bold text-white font-mono mt-0.5 block">
                {formatBRL(statsAndFinancials.med)}
              </span>
            </div>

            <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/60">
              <span className="text-slate-400 text-[10px] uppercase font-semibold block">Desvio Padrão (σ)</span>
              <span className="text-sm font-bold text-white font-mono mt-0.5 block">
                {formatBRL(statsAndFinancials.s)}
              </span>
            </div>

            <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/60">
              <span className="text-slate-400 text-[10px] uppercase font-semibold block">Coef. Variação (CV)</span>
              <span className="text-sm font-bold text-sky-400 font-mono mt-0.5 block">
                {statsAndFinancials.cv.toFixed(1)}%
              </span>
            </div>

            <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/60">
              <span className="text-slate-400 text-[10px] uppercase font-semibold block">Dispersão MAD</span>
              <span className="text-sm font-bold text-emerald-400 font-mono mt-0.5 block">
                {formatBRL(statsAndFinancials.mad)}
              </span>
            </div>

            <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/60">
              <span className="text-slate-400 text-[10px] uppercase font-semibold block">Amplitude IQR</span>
              <span className="text-sm font-bold text-white font-mono mt-0.5 block">
                {formatBRL(statsAndFinancials.iqr)}
              </span>
            </div>

            <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/60">
              <span className="text-slate-400 text-[10px] uppercase font-semibold block">Assimetria (Skew)</span>
              <span className="text-sm font-bold text-white font-mono mt-0.5 block">
                {statsAndFinancials.skew.toFixed(2)}
              </span>
            </div>

            <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/60">
              <span className="text-slate-400 text-[10px] uppercase font-semibold block">Curtose</span>
              <span className="text-sm font-bold text-white font-mono mt-0.5 block">
                {statsAndFinancials.kurt.toFixed(2)}
              </span>
            </div>

            <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/60">
              <span className="text-slate-400 text-[10px] uppercase font-semibold block">Gini & Entropia</span>
              <span className="text-sm font-bold text-purple-400 font-mono mt-0.5 block">
                {statsAndFinancials.gini.toFixed(2)} / {statsAndFinancials.catEntropy.toFixed(1)}b
              </span>
            </div>
          </div>
        </div>

        {/* Painel Financeiro */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-3xl p-6 shadow-xl space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="p-2 rounded-xl bg-sky-500/10 text-sky-400">
                <BarChart2 className="w-5 h-5" />
              </span>
              <h3 className="text-base font-bold text-white">Detalhamento Financeiro & Solvência</h3>
            </div>
            <span className="text-xs text-emerald-400 font-semibold font-mono">
              Saldo: {formatBRL(statsAndFinancials.saldoLiq)}
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
            <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/60">
              <span className="text-slate-400 text-[10px] uppercase font-semibold block">Receitas Filtradas</span>
              <span className="text-sm font-bold text-emerald-400 font-mono mt-0.5 block">
                {formatBRL(statsAndFinancials.totalRec)}
              </span>
            </div>

            <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/60">
              <span className="text-slate-400 text-[10px] uppercase font-semibold block">Despesas Filtradas</span>
              <span className="text-sm font-bold text-rose-400 font-mono mt-0.5 block">
                {formatBRL(statsAndFinancials.totalDesp)}
              </span>
            </div>

            <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/60">
              <span className="text-slate-400 text-[10px] uppercase font-semibold block">Margem Operacional</span>
              <span className="text-sm font-bold text-sky-400 font-mono mt-0.5 block">
                {statsAndFinancials.margemOperacional.toFixed(1)}%
              </span>
            </div>

            <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/60">
              <span className="text-slate-400 text-[10px] uppercase font-semibold block">Taxa de Poupança</span>
              <span className="text-sm font-bold text-emerald-400 font-mono mt-0.5 block">
                {statsAndFinancials.taxaPoupanca.toFixed(1)}%
              </span>
            </div>

            <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/60">
              <span className="text-slate-400 text-[10px] uppercase font-semibold block">Burn Rate Médio / Mês</span>
              <span className="text-sm font-bold text-rose-400 font-mono mt-0.5 block">
                {formatBRL(statsAndFinancials.burnRateMensal)}
              </span>
            </div>

            <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/60">
              <span className="text-slate-400 text-[10px] uppercase font-semibold block">Runway de Sobrevivência</span>
              <span className="text-sm font-bold text-white font-mono mt-0.5 block">
                {statsAndFinancials.runway.toFixed(1)} meses
              </span>
            </div>

            <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/60">
              <span className="text-slate-400 text-[10px] uppercase font-semibold block">VaR Histórico 95%</span>
              <span className="text-sm font-bold text-amber-400 font-mono mt-0.5 block">
                {formatBRL(statsAndFinancials.var95)}
              </span>
            </div>

            <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/60">
              <span className="text-slate-400 text-[10px] uppercase font-semibold block">CVaR (Expected Shortfall)</span>
              <span className="text-sm font-bold text-rose-400 font-mono mt-0.5 block">
                {formatBRL(statsAndFinancials.cvar)}
              </span>
            </div>

            <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/60">
              <span className="text-slate-400 text-[10px] uppercase font-semibold block">Volume Bruto Total</span>
              <span className="text-sm font-bold text-white font-mono mt-0.5 block">
                {formatBRL(statsAndFinancials.grossVolume)}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
