import React, { useMemo } from 'react';
import { useFinance } from '../../context/FinanceContext';
import {
  mean,
  median,
  standardDeviation,
  percentile,
  giniIndex,
  shannonEntropy,
  linearRegression
} from '../../utils/mathStats';
import { BarChart3, TrendingUp, Activity, PieChart } from 'lucide-react';

export const StatisticsTab: React.FC = () => {
  const { transactions } = useFinance();

  const formatBRL = (val: number) =>
    new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);

  const stats = useMemo(() => {
    const despesas = transactions.filter(t => t.tipo === 'Despesa').map(t => t.valor);
    const receitas = transactions.filter(t => t.tipo === 'Receita').map(t => t.valor);

    const totRec = receitas.reduce((a, b) => a + b, 0);
    const totDesp = despesas.reduce((a, b) => a + b, 0);

    const n = despesas.length;
    const avgDesp = mean(despesas);
    const stdDesp = standardDeviation(despesas, avgDesp);

    // 1. Média Geométrica
    const posDesp = despesas.filter(d => d > 0);
    let geomMean = 0;
    if (posDesp.length > 0) {
      geomMean = Math.exp(posDesp.reduce((acc, v) => acc + Math.log(v), 0) / posDesp.length);
    }

    // 2. Média Harmônica
    let harmMean = 0;
    if (posDesp.length > 0) {
      const sumInv = posDesp.reduce((acc, v) => acc + 1 / v, 0);
      harmMean = posDesp.length / (sumInv || 1);
    }

    // 3. Média Aparada (10%)
    let trimmedMean = avgDesp;
    if (despesas.length > 5) {
      const sorted = [...despesas].sort((a, b) => a - b);
      const cut = Math.floor(0.1 * sorted.length);
      const sliced = sorted.slice(cut, sorted.length - cut);
      trimmedMean = mean(sliced);
    }

    // 4. Dispersão IQR
    const q75 = percentile(despesas, 75);
    const q25 = percentile(despesas, 25);
    const iqr = q75 - q25;

    // 5. Semi-Desvio Padrão
    const negDiffs = despesas.filter(d => d < avgDesp).map(d => Math.pow(d - avgDesp, 2));
    const semiStd = negDiffs.length > 0 ? Math.sqrt(mean(negDiffs)) : 0;

    // 6. CV
    const cv = avgDesp > 0 ? (stdDesp / avgDesp) * 100 : 0;

    // 7. Sharpe Pessoal (Média / Desvio Padrão)
    const sharpe = stdDesp > 0 ? avgDesp / stdDesp : 0;

    // 8. Sortino (Média / Semi-Desvio Padrão)
    const sortino = semiStd > 0 ? avgDesp / semiStd : 0;

    // 9. VaR 95%
    const var95 = percentile(despesas, 95);

    // 10. CVaR 95%
    const cvarList = despesas.filter(d => d >= var95);
    const cvar95 = cvarList.length > 0 ? mean(cvarList) : var95;

    // 11. Gini
    const gini = giniIndex(despesas);

    // 12. Shannon
    const catList = transactions.map(t => t.categoria);
    const entropy = shannonEntropy(catList);

    // 13. Z-Score Solvência
    const zScore = stdDesp > 0 ? avgDesp / stdDesp : 0;

    // 14. Taxa de Poupança Efetiva
    const savingRate = totRec > 0 ? ((totRec - totDesp) / totRec) * 100 : 0;

    // 15. Margem Operacional
    const netMargin = totRec > 0 ? ((totRec - totDesp) / totRec) * 100 : 0;

    // 16. Cobertura de Caixa
    const cashCoverage = totDesp > 0 ? totRec / totDesp : 0;

    return {
      geomMean,
      harmMean,
      trimmedMean,
      iqr,
      semiStd,
      cv,
      sharpe,
      sortino,
      var95,
      cvar95,
      gini,
      entropy,
      zScore,
      savingRate,
      netMargin,
      cashCoverage
    };
  }, [transactions]);

  // Bollinger Bands & Daily series
  const dailySeries = useMemo(() => {
    const map = new Map<string, number>();
    transactions
      .filter(t => t.tipo === 'Despesa')
      .forEach(t => {
        map.set(t.data, (map.get(t.data) || 0) + t.valor);
      });

    const dates = Array.from(map.keys()).sort();
    const rows = dates.map(d => ({ data: d, valor: map.get(d) || 0 }));

    // Moving average & bands
    const m = mean(rows.map(r => r.valor));
    const s = standardDeviation(rows.map(r => r.valor), m);

    // OLS regression
    const xVals = rows.map((_, i) => i);
    const yVals = rows.map(r => r.valor);
    const reg = linearRegression(xVals, yVals);

    return rows.map((r, i) => ({
      ...r,
      ma: m,
      upper: m + 2 * s,
      lower: Math.max(0, m - 2 * s),
      ols: reg.intercept + reg.slope * i
    }));
  }, [transactions]);

  // ABC Pareto by Category
  const paretoData = useMemo(() => {
    const map = new Map<string, number>();
    let total = 0;
    transactions
      .filter(t => t.tipo === 'Despesa')
      .forEach(t => {
        map.set(t.categoria, (map.get(t.categoria) || 0) + t.valor);
        total += t.valor;
      });

    const sorted = Array.from(map.entries())
      .map(([categoria, valor]) => ({ categoria, valor }))
      .sort((a, b) => b.valor - a.valor);

    let cum = 0;
    return sorted.map(item => {
      cum += item.valor;
      return {
        ...item,
        cumPct: total > 0 ? (cum / total) * 100 : 0
      };
    });
  }, [transactions]);

  // Drawdown calculation
  const drawdownData = useMemo(() => {
    const map = new Map<string, number>();
    transactions.forEach(t => {
      const delta = t.tipo === 'Receita' ? t.valor : -t.valor;
      map.set(t.data, (map.get(t.data) || 0) + delta);
    });

    const dates = Array.from(map.keys()).sort();
    let accumulated = 0;
    let peak = 0;

    return dates.map(d => {
      accumulated += map.get(d) || 0;
      if (accumulated > peak) peak = accumulated;
      const dd = accumulated - peak;
      return { data: d, accumulated, peak, drawdown: dd };
    });
  }, [transactions]);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <span>📈 Indicadores Econométricos & Quantitativos (Statistic 2)</span>
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          Painel avançado de métricas estatísticas de volatilidade, Sharpe, Sortino, Bandas de Bollinger e Análise de Drawdown.
        </p>
      </div>

      {/* 16 Quantitative Metrics Matrix */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Col 1 */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 space-y-3">
          <div>
            <div className="text-[11px] text-slate-400 uppercase font-semibold">1. Média Geométrica</div>
            <div className="text-lg font-bold text-white font-mono">{formatBRL(stats.geomMean)}</div>
          </div>
          <div>
            <div className="text-[11px] text-slate-400 uppercase font-semibold">2. Média Harmônica</div>
            <div className="text-lg font-bold text-white font-mono">{formatBRL(stats.harmMean)}</div>
          </div>
          <div>
            <div className="text-[11px] text-slate-400 uppercase font-semibold">3. Média Aparada (10%)</div>
            <div className="text-lg font-bold text-white font-mono">{formatBRL(stats.trimmedMean)}</div>
          </div>
          <div>
            <div className="text-[11px] text-slate-400 uppercase font-semibold">4. Dispersão IQR</div>
            <div className="text-lg font-bold text-emerald-400 font-mono">{formatBRL(stats.iqr)}</div>
          </div>
        </div>

        {/* Col 2 */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 space-y-3">
          <div>
            <div className="text-[11px] text-slate-400 uppercase font-semibold">5. Semi-Desvio Padrão</div>
            <div className="text-lg font-bold text-white font-mono">{formatBRL(stats.semiStd)}</div>
          </div>
          <div>
            <div className="text-[11px] text-slate-400 uppercase font-semibold">6. Coef. Variação (CV)</div>
            <div className="text-lg font-bold text-white font-mono">{stats.cv.toFixed(2)}%</div>
          </div>
          <div>
            <div className="text-[11px] text-slate-400 uppercase font-semibold">7. Sharpe Pessoal</div>
            <div className="text-lg font-bold text-emerald-400 font-mono">{stats.sharpe.toFixed(2)}</div>
          </div>
          <div>
            <div className="text-[11px] text-slate-400 uppercase font-semibold">8. Índice Sortino</div>
            <div className="text-lg font-bold text-emerald-400 font-mono">{stats.sortino.toFixed(2)}</div>
          </div>
        </div>

        {/* Col 3 */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 space-y-3">
          <div>
            <div className="text-[11px] text-slate-400 uppercase font-semibold">9. VaR (95%)</div>
            <div className="text-lg font-bold text-amber-400 font-mono">{formatBRL(stats.var95)}</div>
          </div>
          <div>
            <div className="text-[11px] text-slate-400 uppercase font-semibold">10. CVaR / Expected Shortfall</div>
            <div className="text-lg font-bold text-rose-400 font-mono">{formatBRL(stats.cvar95)}</div>
          </div>
          <div>
            <div className="text-[11px] text-slate-400 uppercase font-semibold">11. Coeficiente Gini</div>
            <div className="text-lg font-bold text-purple-400 font-mono">{stats.gini.toFixed(3)}</div>
          </div>
          <div>
            <div className="text-[11px] text-slate-400 uppercase font-semibold">12. Entropia Shannon</div>
            <div className="text-lg font-bold text-sky-400 font-mono">{stats.entropy.toFixed(2)} bits</div>
          </div>
        </div>

        {/* Col 4 */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 space-y-3">
          <div>
            <div className="text-[11px] text-slate-400 uppercase font-semibold">13. Z-Score Solvência</div>
            <div className="text-lg font-bold text-emerald-400 font-mono">{stats.zScore.toFixed(2)}</div>
          </div>
          <div>
            <div className="text-[11px] text-slate-400 uppercase font-semibold">14. Taxa de Poupança</div>
            <div className="text-lg font-bold text-emerald-400 font-mono">{stats.savingRate.toFixed(1)}%</div>
          </div>
          <div>
            <div className="text-[11px] text-slate-400 uppercase font-semibold">15. Margem Operacional</div>
            <div className="text-lg font-bold text-sky-400 font-mono">{stats.netMargin.toFixed(1)}%</div>
          </div>
          <div>
            <div className="text-[11px] text-slate-400 uppercase font-semibold">16. Cobertura de Caixa</div>
            <div className="text-lg font-bold text-emerald-400 font-mono">{stats.cashCoverage.toFixed(2)}x</div>
          </div>
        </div>
      </div>

      {/* Visual Analytics Panels */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Bandas de Bollinger & Regressão OLS */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6">
          <h3 className="text-base font-bold text-white mb-2 flex items-center gap-2">
            <Activity className="w-4 h-4 text-sky-400" />
            <span>Bandas de Bollinger & Tendência OLS (Despesas)</span>
          </h3>
          <p className="text-xs text-slate-400 mb-4">
            Média móvel com envelopes de volatilidade (+2σ / -2σ) e vetor de regressão linear.
          </p>

          <div className="space-y-3">
            {dailySeries.map((row, idx) => (
              <div key={idx} className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/60 text-xs">
                <div className="flex items-center justify-between font-mono mb-1">
                  <span className="text-slate-300 font-bold">{row.data}</span>
                  <span className="text-rose-400 font-bold">Gasto: {formatBRL(row.valor)}</span>
                </div>
                <div className="flex items-center justify-between text-[11px] text-slate-400 font-mono">
                  <span>Média: {formatBRL(row.ma)}</span>
                  <span>Banda Sup: {formatBRL(row.upper)}</span>
                  <span>Tendência OLS: {formatBRL(row.ols)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Análise ABC de Pareto */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6">
          <h3 className="text-base font-bold text-white mb-2 flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-emerald-400" />
            <span>Matriz ABC de Pareto por Categoria</span>
          </h3>
          <p className="text-xs text-slate-400 mb-4">
            Classificação 80/20 dos maiores centros de custo acumulados.
          </p>

          <div className="space-y-3">
            {paretoData.map((row, idx) => (
              <div key={idx} className="space-y-1">
                <div className="flex items-center justify-between text-xs font-medium">
                  <span className="text-white">{row.categoria}</span>
                  <span className="text-emerald-400 font-mono">{row.cumPct.toFixed(1)}% acum.</span>
                </div>
                <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-emerald-500 to-teal-400 h-full rounded-full"
                    style={{ width: `${row.cumPct}%` }}
                  />
                </div>
                <div className="text-[11px] text-slate-400 text-right font-mono">
                  {formatBRL(row.valor)}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
