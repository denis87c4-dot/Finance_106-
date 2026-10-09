import React, { useState, useMemo } from 'react';
import { useFinance } from '../../context/FinanceContext';
import { mean, standardDeviation, normalCdf, normalPdf } from '../../utils/mathStats';
import { LineChart, Sliders, Info, Table } from 'lucide-react';

export const NormalDistTab: React.FC = () => {
  const { transactions } = useFinance();

  const [variable, setVariable] = useState<'Income' | 'Expense' | 'Cash Flow' | 'Acumulado'>('Income');
  const [freq, setFreq] = useState<'Mês' | 'Trimestre' | 'Ano'>('Mês');
  const [useProjection, setUseProjection] = useState<boolean>(false);
  const [growthRate, setGrowthRate] = useState<number>(2.0); // %
  const [monthsProj, setMonthsProj] = useState<number>(6);
  const [cutoffInput, setCutoffInput] = useState<number | null>(null);

  const formatBRL = (val: number) =>
    new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);

  // Grouped temporal data
  const seriesData = useMemo(() => {
    const map = new Map<string, { income: number; expense: number }>();

    transactions.forEach(t => {
      let key = t.data.substring(0, 7); // Mês YYYY-MM
      if (freq === 'Trimestre') {
        const year = t.data.substring(0, 4);
        const monthNum = parseInt(t.data.substring(5, 7), 10);
        const q = Math.ceil(monthNum / 3);
        key = `${year}-Q${q}`;
      } else if (freq === 'Ano') {
        key = t.data.substring(0, 4);
      }

      const cur = map.get(key) || { income: 0, expense: 0 };
      if (t.tipo === 'Receita') cur.income += t.valor;
      if (t.tipo === 'Despesa') cur.expense += t.valor;
      map.set(key, cur);
    });

    let list = Array.from(map.entries())
      .sort((a, b) => a[0].localeCompare(b[0]))
      .map(([periodo, vals]) => ({
        periodo,
        income: vals.income,
        expense: vals.expense,
        cashFlow: vals.income - vals.expense,
        acumulado: 0
      }));

    if (useProjection && list.length > 0 && monthsProj > 0) {
      let lastInc = list[list.length - 1].income;
      let lastExp = list[list.length - 1].expense;
      for (let i = 1; i <= monthsProj; i++) {
        lastInc *= 1 + growthRate / 100;
        lastExp *= 1 + (growthRate * 0.5) / 100;
        list.push({
          periodo: `Proj +${i}`,
          income: lastInc,
          expense: lastExp,
          cashFlow: lastInc - lastExp,
          acumulado: 0
        });
      }
    }

    // Compute cumulative
    let cum = 0;
    list = list.map(item => {
      cum += item.cashFlow;
      return { ...item, acumulado: cum };
    });

    return list;
  }, [transactions, freq, useProjection, growthRate, monthsProj]);

  // Extract selected variable series
  const activeSeries = useMemo(() => {
    return seriesData.map(d => {
      if (variable === 'Income') return d.income;
      if (variable === 'Expense') return d.expense;
      if (variable === 'Cash Flow') return d.cashFlow;
      return d.acumulado;
    });
  }, [seriesData, variable]);

  const mu = useMemo(() => mean(activeSeries), [activeSeries]);
  const rawSigma = useMemo(() => standardDeviation(activeSeries, mu), [activeSeries, mu]);
  const sigma = rawSigma <= 0 ? 1 : rawSigma;

  // Cutoff value X
  const xValue = cutoffInput !== null ? cutoffInput : Math.round(mu * 100) / 100;

  const probMenor = normalCdf(xValue, mu, sigma) * 100;
  const probMaior = Math.max(0, 100 - probMenor);

  // Generate bell curve points
  const curvePoints = useMemo(() => {
    const minVal = mu - 3.5 * sigma;
    const maxVal = mu + 3.5 * sigma;
    const steps = 120;
    const stepSize = (maxVal - minVal) / steps;
    const pts: { x: number; y: number }[] = [];

    let maxY = 0;
    for (let i = 0; i <= steps; i++) {
      const curX = minVal + i * stepSize;
      const curY = normalPdf(curX, mu, sigma);
      if (curY > maxY) maxY = curY;
      pts.push({ x: curX, y: curY });
    }
    return { pts, minVal, maxVal, maxY };
  }, [mu, sigma]);

  // SVG dimensions
  const svgWidth = 800;
  const svgHeight = 280;
  const padding = { top: 20, right: 30, bottom: 40, left: 50 };

  const scaleX = (val: number) => {
    const range = curvePoints.maxVal - curvePoints.minVal || 1;
    return padding.left + ((val - curvePoints.minVal) / range) * (svgWidth - padding.left - padding.right);
  };

  const scaleY = (val: number) => {
    const maxY = curvePoints.maxY || 0.0001;
    return svgHeight - padding.bottom - (val / maxY) * (svgHeight - padding.top - padding.bottom);
  };

  const linePath = useMemo(() => {
    return curvePoints.pts
      .map((p, i) => `${i === 0 ? 'M' : 'L'} ${scaleX(p.x).toFixed(1)} ${scaleY(p.y).toFixed(1)}`)
      .join(' ');
  }, [curvePoints, scaleX, scaleY]);

  // Shaded area path for x <= xValue
  const shadedPath = useMemo(() => {
    const shadedPts = curvePoints.pts.filter(p => p.x <= xValue);
    if (shadedPts.length === 0) return '';
    const firstX = scaleX(shadedPts[0].x);
    const lastX = scaleX(xValue);
    const baseY = svgHeight - padding.bottom;

    const pointsStr = shadedPts
      .map(p => `L ${scaleX(p.x).toFixed(1)} ${scaleY(p.y).toFixed(1)}`)
      .join(' ');

    return `M ${firstX.toFixed(1)} ${baseY} ${pointsStr} L ${lastX.toFixed(1)} ${scaleY(normalPdf(xValue, mu, sigma)).toFixed(1)} L ${lastX.toFixed(1)} ${baseY} Z`;
  }, [curvePoints, xValue, mu, sigma, scaleX, scaleY]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <span>📊 Distribuição Normal & Probabilidades Financeiras</span>
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          Analise a probabilidade estatística de ocorrência de valores com base na curva Gaussiana teórica para Income, Expense, Cash Flow e Acumulado.
        </p>
      </div>

      {/* Control Panel / Filters */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 grid grid-cols-1 md:grid-cols-4 gap-4">
        <div>
          <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">
            Variável de Análise
          </label>
          <select
            value={variable}
            onChange={e => {
              setVariable(e.target.value as any);
              setCutoffInput(null);
            }}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
          >
            <option value="Income">Income (Receitas)</option>
            <option value="Expense">Expense (Despesas)</option>
            <option value="Cash Flow">Cash Flow (Fluxo Líquido)</option>
            <option value="Acumulado">Acumulado Patrimonial</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">
            Agregação Temporal
          </label>
          <select
            value={freq}
            onChange={e => setFreq(e.target.value as any)}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
          >
            <option value="Mês">Mensal</option>
            <option value="Trimestre">Trimestral</option>
            <option value="Ano">Anual</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">
            Corte X Interativo (R$)
          </label>
          <input
            type="number"
            step="100"
            value={xValue}
            onChange={e => setCutoffInput(parseFloat(e.target.value) || 0)}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white font-mono focus:outline-none focus:border-emerald-500"
          />
        </div>

        <div className="flex flex-col justify-end">
          <label className="flex items-center gap-2 cursor-pointer text-sm text-slate-300">
            <input
              type="checkbox"
              checked={useProjection}
              onChange={e => setUseProjection(e.target.checked)}
              className="rounded bg-slate-950 border-slate-800 text-emerald-500 focus:ring-emerald-500 w-4 h-4"
            />
            <span>Ativar Simulação de Projeção</span>
          </label>
          {useProjection && (
            <div className="flex items-center gap-2 mt-2 text-xs text-slate-400 font-mono">
              <span>+{growthRate}% a.m.</span>
              <span>•</span>
              <span>{monthsProj} períodos</span>
            </div>
          )}
        </div>
      </div>

      {/* KPI Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4">
          <div className="text-xs font-semibold uppercase text-slate-400">Média (μ)</div>
          <div className="text-xl font-bold text-white mt-1 font-mono">{formatBRL(mu)}</div>
          <div className="text-xs text-slate-400 mt-1">Ponto central da distribuição</div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4">
          <div className="text-xs font-semibold uppercase text-slate-400">Desvio Padrão (σ)</div>
          <div className="text-xl font-bold text-white mt-1 font-mono">{formatBRL(sigma)}</div>
          <div className="text-xs text-slate-400 mt-1">Dispersão e volatilidade</div>
        </div>

        <div className="bg-slate-900/80 border border-emerald-500/30 bg-emerald-500/5 rounded-2xl p-4">
          <div className="text-xs font-semibold uppercase text-emerald-400">
            P(X ≤ {formatBRL(xValue)})
          </div>
          <div className="text-2xl font-bold text-emerald-400 mt-1 font-mono">
            {probMenor.toFixed(2)}%
          </div>
          <div className="text-xs text-slate-400 mt-1">Probabilidade cumulativa (CDF)</div>
        </div>

        <div className="bg-slate-900/80 border border-rose-500/30 bg-rose-500/5 rounded-2xl p-4">
          <div className="text-xs font-semibold uppercase text-rose-400">
            P(X &gt; {formatBRL(xValue)})
          </div>
          <div className="text-2xl font-bold text-rose-400 mt-1 font-mono">
            {probMaior.toFixed(2)}%
          </div>
          <div className="text-xs text-slate-400 mt-1">Probabilidade de superação</div>
        </div>
      </div>

      {/* Bell Curve Visualization */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <LineChart className="w-4 h-4 text-emerald-400" />
              <span>Curva de Gauss Teórica Ajustada — {variable} ({freq})</span>
            </h3>
            <p className="text-xs text-slate-400">
              Área sombreada verde representa a probabilidade acumulada P(X ≤ {formatBRL(xValue)})
            </p>
          </div>
          <div className="flex items-center gap-4 text-xs font-medium">
            <span className="flex items-center gap-1.5 text-sky-400">
              <span className="w-3 h-1 bg-sky-400 inline-block"></span> Curva Teórica
            </span>
            <span className="flex items-center gap-1.5 text-emerald-400">
              <span className="w-3 h-3 bg-emerald-500/30 border border-emerald-500 inline-block rounded"></span> Área ≤ X
            </span>
            <span className="flex items-center gap-1.5 text-rose-400">
              <span className="w-3 h-1 border-t-2 border-dashed border-rose-400 inline-block"></span> Corte X
            </span>
          </div>
        </div>

        {/* SVG Bell Curve */}
        <div className="w-full overflow-x-auto">
          <svg
            viewBox={`0 0 ${svgWidth} ${svgHeight}`}
            className="w-full h-auto min-w-[600px] text-slate-400"
          >
            {/* Grid lines */}
            <line
              x1={padding.left}
              y1={svgHeight - padding.bottom}
              x2={svgWidth - padding.right}
              y2={svgHeight - padding.bottom}
              stroke="#334155"
              strokeWidth="1"
            />

            {/* Shaded Area */}
            {shadedPath && <path d={shadedPath} fill="rgba(16, 185, 129, 0.25)" />}

            {/* Bell Curve Line */}
            <path d={linePath} fill="none" stroke="#38bdf8" strokeWidth="3" />

            {/* Vertical Cutoff line at X */}
            <line
              x1={scaleX(xValue)}
              y1={padding.top}
              x2={scaleX(xValue)}
              y2={svgHeight - padding.bottom}
              stroke="#f43f5e"
              strokeWidth="2"
              strokeDasharray="4 4"
            />

            {/* Mean vertical line */}
            <line
              x1={scaleX(mu)}
              y1={padding.top + 20}
              x2={scaleX(mu)}
              y2={svgHeight - padding.bottom}
              stroke="#94a3b8"
              strokeWidth="1"
              strokeDasharray="2 2"
            />

            {/* Labels */}
            <text
              x={scaleX(xValue)}
              y={padding.top + 14}
              textAnchor="middle"
              fill="#f43f5e"
              fontSize="11"
              fontWeight="bold"
            >
              X = {formatBRL(xValue)}
            </text>

            <text
              x={scaleX(mu)}
              y={svgHeight - padding.bottom + 20}
              textAnchor="middle"
              fill="#94a3b8"
              fontSize="10"
              fontWeight="bold"
            >
              μ = {formatBRL(mu)}
            </text>

            <text
              x={scaleX(curvePoints.minVal)}
              y={svgHeight - padding.bottom + 20}
              textAnchor="start"
              fill="#64748b"
              fontSize="10"
            >
              {formatBRL(curvePoints.minVal)}
            </text>

            <text
              x={scaleX(curvePoints.maxVal)}
              y={svgHeight - padding.bottom + 20}
              textAnchor="end"
              fill="#64748b"
              fontSize="10"
            >
              {formatBRL(curvePoints.maxVal)}
            </text>
          </svg>
        </div>
      </div>

      {/* Aggregate Series Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5">
        <h3 className="text-base font-bold text-white mb-3 flex items-center gap-2">
          <Table className="w-4 h-4 text-slate-400" />
          <span>Série Temporal Consolidada & Projeções</span>
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400">
                <th className="py-2.5 px-3">Período</th>
                <th className="py-2.5 px-3">Income (Receitas)</th>
                <th className="py-2.5 px-3">Expense (Despesas)</th>
                <th className="py-2.5 px-3">Cash Flow (Líquido)</th>
                <th className="py-2.5 px-3">Acumulado</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {seriesData.map((row, idx) => (
                <tr key={idx} className="hover:bg-slate-800/30">
                  <td className="py-2 px-3 text-slate-300 font-semibold">{row.periodo}</td>
                  <td className="py-2 px-3 text-emerald-400">{formatBRL(row.income)}</td>
                  <td className="py-2 px-3 text-rose-400">{formatBRL(row.expense)}</td>
                  <td className={`py-2 px-3 font-semibold ${row.cashFlow >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {formatBRL(row.cashFlow)}
                  </td>
                  <td className="py-2 px-3 text-sky-400">{formatBRL(row.acumulado)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
