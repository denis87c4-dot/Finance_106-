import React, { useMemo } from 'react';
import { useFinance } from '../../context/FinanceContext';
import {
  mean,
  median,
  standardDeviation,
  medianAbsoluteDeviation,
  percentile,
  skewness,
  kurtosis,
  shannonEntropy,
  giniIndex
} from '../../utils/mathStats';
import { Sparkles, BarChart2, PieChart } from 'lucide-react';

export const AdvancedAnalyticsTab: React.FC = () => {
  const { transactions } = useFinance();

  const formatBRL = (val: number) =>
    new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);

  const metrics = useMemo(() => {
    const vals = transactions.map(t => (t.tipo === 'Despesa' ? t.valor : t.valor));
    const categoriesList = transactions.map(t => t.categoria);

    const m = mean(vals);
    const s = standardDeviation(vals, m);
    const cv = m > 0 ? (s / m) * 100 : 0;
    const mad = medianAbsoluteDeviation(vals);
    const p95 = percentile(vals, 95);
    const entropy = shannonEntropy(categoriesList);
    const skew = skewness(vals);
    const kurt = kurtosis(vals);
    const gini = giniIndex(vals);
    const total = vals.reduce((a, b) => a + b, 0);

    return { cv, mad, p95, entropy, skew, kurt, gini, total };
  }, [transactions]);

  // Histogram calculation
  const histogramBuckets = useMemo(() => {
    const vals = transactions.map(t => t.valor);
    if (vals.length === 0) return [];
    const min = Math.min(...vals);
    const max = Math.max(...vals);
    const bucketsCount = 6;
    const step = (max - min) / bucketsCount || 1;

    const buckets = Array.from({ length: bucketsCount }, (_, i) => ({
      range: `${formatBRL(min + i * step)} - ${formatBRL(min + (i + 1) * step)}`,
      count: 0
    }));

    vals.forEach(v => {
      let bIdx = Math.floor((v - min) / step);
      if (bIdx >= bucketsCount) bIdx = bucketsCount - 1;
      buckets[bIdx].count++;
    });

    return buckets;
  }, [transactions]);

  const maxBucketCount = Math.max(...histogramBuckets.map(b => b.count), 1);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <span>🚀 Advanced Analytics & Statistical KPIs</span>
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          Estatística robusta, dispersão de cauda, entropia informacional de Shannon e coeficiente de concentração de Gini.
        </p>
      </div>

      {/* 8 Main Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4">
          <div className="text-xs font-semibold uppercase text-slate-400">Coef. de Variação (CV)</div>
          <div className="text-2xl font-bold text-white mt-1 font-mono">{metrics.cv.toFixed(2)}%</div>
          <div className="text-xs text-slate-400 mt-1">Volatilidade relativa (σ / μ)</div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4">
          <div className="text-xs font-semibold uppercase text-slate-400">Desvio Absoluto Mediano (MAD)</div>
          <div className="text-2xl font-bold text-emerald-400 mt-1 font-mono">{formatBRL(metrics.mad)}</div>
          <div className="text-xs text-slate-400 mt-1">Dispersão imune a outliers</div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4">
          <div className="text-xs font-semibold uppercase text-slate-400">Percentil P95 (Cauda)</div>
          <div className="text-2xl font-bold text-amber-400 mt-1 font-mono">{formatBRL(metrics.p95)}</div>
          <div className="text-xs text-slate-400 mt-1">Corte superior 95% do volume</div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4">
          <div className="text-xs font-semibold uppercase text-slate-400">Entropia de Shannon</div>
          <div className="text-2xl font-bold text-sky-400 mt-1 font-mono">{metrics.entropy.toFixed(2)} bits</div>
          <div className="text-xs text-slate-400 mt-1">Diversidade de categorias</div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4">
          <div className="text-xs font-semibold uppercase text-slate-400">Assimetria (Skewness)</div>
          <div className="text-2xl font-bold text-white mt-1 font-mono">{metrics.skew.toFixed(2)}</div>
          <div className="text-xs text-slate-400 mt-1">Viés da cauda da distribuição</div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4">
          <div className="text-xs font-semibold uppercase text-slate-400">Curtose (Kurtosis)</div>
          <div className="text-2xl font-bold text-white mt-1 font-mono">{metrics.kurt.toFixed(2)}</div>
          <div className="text-xs text-slate-400 mt-1">Propensão a choques extremos</div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4">
          <div className="text-xs font-semibold uppercase text-slate-400">Índice de Gini</div>
          <div className="text-2xl font-bold text-purple-400 mt-1 font-mono">{metrics.gini.toFixed(3)}</div>
          <div className="text-xs text-slate-400 mt-1">Concentração de valores (0 a 1)</div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4">
          <div className="text-xs font-semibold uppercase text-slate-400">Volume Total Transacionado</div>
          <div className="text-2xl font-bold text-white mt-1 font-mono">{formatBRL(metrics.total)}</div>
          <div className="text-xs text-slate-400 mt-1">Soma bruta de lançamentos</div>
        </div>
      </div>

      {/* Histograma de Frequência */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6">
        <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
          <BarChart2 className="w-4 h-4 text-emerald-400" />
          <span>Distribuição de Frequência (Histograma Empírico)</span>
        </h3>
        <div className="space-y-3">
          {histogramBuckets.map((bucket, idx) => (
            <div key={idx} className="space-y-1">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-slate-300">{bucket.range}</span>
                <span className="text-emerald-400 font-semibold">{bucket.count} transações</span>
              </div>
              <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden">
                <div
                  className="bg-emerald-500 h-full rounded-full transition-all"
                  style={{ width: `${(bucket.count / maxBucketCount) * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
