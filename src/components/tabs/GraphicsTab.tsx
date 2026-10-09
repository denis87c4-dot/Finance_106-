import React, { useMemo } from 'react';
import { useFinance } from '../../context/FinanceContext';
import { PieChart, TrendingUp, ShieldCheck, Clock, Layers } from 'lucide-react';

export const GraphicsTab: React.FC = () => {
  const { transactions } = useFinance();

  const formatBRL = (val: number) =>
    new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);

  // Financial Health Metrics
  const healthMetrics = useMemo(() => {
    const rec = transactions.filter(t => t.tipo === 'Receita').reduce((a, b) => a + b.valor, 0);
    const desp = transactions.filter(t => t.tipo === 'Despesa').reduce((a, b) => a + b.valor, 0);
    const net = rec - desp;
    const saveRate = rec > 0 ? (net / rec) * 100 : 0;
    const coverage = desp > 0 ? rec / desp : 1;

    // Monthly avg expenses
    const months = new Set(transactions.map(t => t.data.substring(0, 7))).size || 1;
    const avgMonthlyExpense = desp / months;
    const runway = avgMonthlyExpense > 0 ? Math.max(0, net / avgMonthlyExpense) : 12;

    // Health Score 0 to 100
    let score = 50;
    if (saveRate > 25) score += 25;
    else if (saveRate > 10) score += 15;
    else if (saveRate < 0) score -= 25;

    if (coverage > 1.3) score += 20;
    else if (coverage < 1.0) score -= 20;

    score = Math.min(100, Math.max(10, score));

    return {
      score,
      saveRate,
      coverage,
      avgMonthlyExpense,
      runway: runway.toFixed(1),
      net
    };
  }, [transactions]);

  // Cumulative wealth timeline
  const timelineData = useMemo(() => {
    const sorted = [...transactions].sort((a, b) => a.data.localeCompare(b.data));
    let cum = 0;
    return sorted.map(t => {
      cum += t.tipo === 'Receita' ? t.valor : -t.valor;
      return {
        data: t.data,
        descricao: t.descricao,
        delta: t.tipo === 'Receita' ? t.valor : -t.valor,
        acumulado: cum
      };
    });
  }, [transactions]);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <span>📊 Gráficos Sofisticados & Diagnóstico de Saúde Financeira</span>
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          Indicadores avançados de solvência, runway operacional em meses e curva patrimonial acumulada.
        </p>
      </div>

      {/* Financial Health Index */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase text-slate-400">Score de Saúde Financeira</span>
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
          </div>
          <div className="my-4">
            <div className="flex items-baseline gap-2">
              <span className="text-4xl font-extrabold text-white font-mono">{healthMetrics.score}</span>
              <span className="text-slate-400 text-sm font-semibold">/ 100</span>
            </div>
            <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden mt-3">
              <div
                className={`h-full rounded-full transition-all ${
                  healthMetrics.score > 70
                    ? 'bg-emerald-500'
                    : healthMetrics.score > 40
                    ? 'bg-amber-500'
                    : 'bg-rose-500'
                }`}
                style={{ width: `${healthMetrics.score}%` }}
              />
            </div>
          </div>
          <div className="text-xs text-slate-400 font-medium">
            {healthMetrics.score >= 70
              ? 'Excelente resiliência financeira e fluxo superavitário.'
              : 'Requer atenção na contenção de despesas fixas.'}
          </div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase text-slate-400">Runway Operacional</span>
            <Clock className="w-5 h-5 text-sky-400" />
          </div>
          <div className="my-4">
            <div className="flex items-baseline gap-2">
              <span className="text-4xl font-extrabold text-sky-400 font-mono">
                {healthMetrics.runway}
              </span>
              <span className="text-slate-400 text-sm font-semibold">meses</span>
            </div>
            <div className="text-xs text-slate-400 mt-2 font-mono">
              Gasto médio mensal: {formatBRL(healthMetrics.avgMonthlyExpense)}
            </div>
          </div>
          <div className="text-xs text-slate-400 font-medium">
            Capacidade de sustentar o padrão de vida sem novas receitas.
          </div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase text-slate-400">Cobertura de Caixa</span>
            <Layers className="w-5 h-5 text-purple-400" />
          </div>
          <div className="my-4">
            <div className="flex items-baseline gap-2">
              <span className="text-4xl font-extrabold text-purple-400 font-mono">
                {healthMetrics.coverage.toFixed(2)}x
              </span>
            </div>
            <div className="text-xs text-slate-400 mt-2">
              Taxa de Poupança Efetiva: <strong className="text-white font-mono">{healthMetrics.saveRate.toFixed(1)}%</strong>
            </div>
          </div>
          <div className="text-xs text-slate-400 font-medium">
            Multiplicador de segurança sobre as obrigações correntes.
          </div>
        </div>
      </div>

      {/* Cumulative Cash Flow Timeline */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6">
        <h3 className="text-base font-bold text-white mb-2 flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-emerald-400" />
          <span>Curva de Patrimônio & Saldo Líquido Acumulado</span>
        </h3>
        <p className="text-xs text-slate-400 mb-6">
          Evolução cronológica de cada operação e impacto na curva patrimonial.
        </p>

        <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
          {timelineData.map((item, idx) => (
            <div
              key={idx}
              className="flex items-center justify-between p-3 bg-slate-950/60 border border-slate-800/60 rounded-xl text-xs"
            >
              <div className="flex items-center gap-3">
                <span className="text-slate-400 font-mono text-[11px]">{item.data}</span>
                <span className="text-white font-medium">{item.descricao}</span>
              </div>
              <div className="flex items-center gap-6">
                <span
                  className={`font-mono font-semibold ${
                    item.delta >= 0 ? 'text-emerald-400' : 'text-rose-400'
                  }`}
                >
                  {item.delta >= 0 ? '+' : ''}
                  {formatBRL(item.delta)}
                </span>
                <div className="text-right w-28">
                  <span className="text-slate-400 text-[10px] block">Acumulado:</span>
                  <span className="text-sky-400 font-bold font-mono">{formatBRL(item.acumulado)}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
