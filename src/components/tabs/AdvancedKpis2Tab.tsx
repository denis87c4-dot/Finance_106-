import React, { useState, useMemo } from 'react';
import { useFinance } from '../../context/FinanceContext';
import {
  mean,
  median,
  standardDeviation,
  percentile,
  skewness
} from '../../utils/mathStats';
import { Zap, ShieldAlert, Activity, BarChart3, Filter } from 'lucide-react';

export const AdvancedKpis2Tab: React.FC = () => {
  const { transactions, categories, accounts } = useFinance();

  const [selectedType, setSelectedType] = useState<string>('Todos');
  const [selectedCat, setSelectedCat] = useState<string>('Todas');
  const [selectedAccount, setSelectedAccount] = useState<string>('Todas');

  const formatBRL = (val: number) =>
    new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);

  // Filtered dataset
  const filteredTx = useMemo(() => {
    return transactions.filter(t => {
      if (selectedType !== 'Todos' && t.tipo !== selectedType) return false;
      if (selectedCat !== 'Todas' && t.categoria !== selectedCat) return false;
      if (selectedAccount !== 'Todas' && t.conta !== selectedAccount) return false;
      return true;
    });
  }, [transactions, selectedType, selectedCat, selectedAccount]);

  // Calculations for 20 KPIs
  const kpis = useMemo(() => {
    const vals = filteredTx.map(t => (t.tipo === 'Despesa' ? -t.valor : t.valor));
    const absVals = filteredTx.map(t => t.valor);

    const rec = filteredTx.filter(t => t.tipo === 'Receita').reduce((a, b) => a + b.valor, 0);
    const desp = filteredTx.filter(t => t.tipo === 'Despesa').reduce((a, b) => a + b.valor, 0);

    const n = vals.length;
    const avg = mean(vals);
    const med = median(vals);
    const std = standardDeviation(vals, avg);
    const variance = Math.pow(std, 2);

    // 1. VaR Histórico (95%)
    const varHist = n > 1 ? percentile(vals, 5) : vals[0] || 0;

    // 2. Expected Shortfall (CVaR)
    const tailVals = vals.filter(v => v <= varHist);
    const cvar = tailVals.length > 0 ? mean(tailVals) : varHist;

    // 3. ICD (Índice de Cobertura de Despesas)
    const icd = desp > 0 ? rec / desp : rec > 0 ? 99 : 0;

    // 4. Volatilidade de Burn Rate
    const burnVol = std / (Math.abs(avg) + 1e-9);

    // 5. Share Top 10% Cauda
    const p90Abs = n > 1 ? percentile(absVals, 90) : 0;
    const top10Sum = absVals.filter(v => v >= p90Abs).reduce((a, b) => a + b, 0);
    const grossTotal = absVals.reduce((a, b) => a + b, 0);
    const top10Share = grossTotal > 0 ? (top10Sum / grossTotal) * 100 : 0;

    // 6. Fator de Resiliência (Median / Mean)
    const resilience = med / (avg + 1e-9);

    // 7. Coeficiente Risco-Impacto
    const skew = skewness(vals);
    const riskImpact = skew * std;

    // 8. Estabilidade de Frequência Temporal
    const uniqueDays = new Set(filteredTx.map(t => t.data)).size;
    const dates = filteredTx.map(t => new Date(t.data).getTime()).filter(t => !isNaN(t));
    let freqStability = 100;
    if (dates.length > 1) {
      const minD = Math.min(...dates);
      const maxD = Math.max(...dates);
      const spanDays = Math.max(1, Math.round((maxD - minD) / (1000 * 60 * 60 * 24)) + 1);
      freqStability = (uniqueDays / spanDays) * 100;
    }

    // 9. Amplitude Relativa (IQR)
    const q75 = percentile(absVals, 75);
    const q25 = percentile(absVals, 25);
    const iqr = q75 - q25;
    const relIqr = (iqr / (Math.abs(avg) + 1e-9)) * 100;

    // 10. Razão de Cauda (Tail Ratio P95 / P05)
    const p95 = percentile(absVals, 95);
    const p05 = percentile(absVals, 5);
    const tailRatio = p95 / (p05 + 1e-9);

    // 11. Dispersão Exponencial (Var / Mean)
    const dispExp = variance / (Math.abs(avg) + 1e-9);

    // 12. Elasticidade por Categoria
    const catSums = new Map<string, number>();
    filteredTx.forEach(t => {
      catSums.set(t.categoria, (catSums.get(t.categoria) || 0) + t.valor);
    });
    const catVals = Array.from(catSums.values());
    const catStd = catVals.length > 1 ? standardDeviation(catVals) : 0;
    const catElasticity = catStd / (Math.abs(avg) + 1e-9);

    // 13. Eficiência de Fluxo Líquido
    const netSum = vals.reduce((a, b) => a + b, 0);
    const netEfficiency = grossTotal > 0 ? (netSum / grossTotal) * 100 : 0;

    // 14. Inércia de Transação (Lag-1)
    let autocorr = 0;
    if (vals.length > 2) {
      let num = 0;
      let den = 0;
      for (let i = 0; i < vals.length - 1; i++) {
        num += (vals[i] - avg) * (vals[i + 1] - avg);
        den += Math.pow(vals[i] - avg, 2);
      }
      autocorr = den > 0 ? num / den : 0;
    }

    // 15. Z-Score Máximo (Outlier severity)
    let maxZ = 0;
    if (std > 0) {
      maxZ = Math.max(...vals.map(v => Math.abs((v - avg) / std)));
    }

    // 16. Concentração de Contas (HHI)
    const accountSums = new Map<string, number>();
    filteredTx.forEach(t => {
      accountSums.set(t.conta, (accountSums.get(t.conta) || 0) + t.valor);
    });
    let hhi = 0;
    accountSums.forEach(val => {
      const share = grossTotal > 0 ? val / grossTotal : 0;
      hhi += Math.pow(share, 2) * 100;
    });

    // 17. Fator de Assimetria de Fluxo
    const flowSkew = (rec / (desp + 1e-9)) * (1 + Math.abs(skew));

    // 18. Média Geométrica Positiva
    const posVals = absVals.filter(v => v > 0);
    let geomMean = 0;
    if (posVals.length > 0) {
      const logSum = posVals.reduce((acc, v) => acc + Math.log(v), 0);
      geomMean = Math.exp(logSum / posVals.length);
    }

    // 19. Volatilidade Ponderada por Volume (VWCV)
    const vwcv = avg !== 0 ? (std * grossTotal) / (Math.pow(avg, 2) + 1e-9) : 0;

    // 20. Indicador de Estresse Sintético
    const synthStress = (Math.abs(varHist) * (1 + burnVol)) / (icd + 0.1);

    return {
      varHist,
      cvar,
      icd,
      burnVol,
      top10Share,
      resilience,
      riskImpact,
      freqStability,
      relIqr,
      tailRatio,
      dispExp,
      catElasticity,
      netEfficiency,
      autocorr,
      maxZ,
      hhi,
      flowSkew,
      geomMean,
      vwcv,
      synthStress
    };
  }, [filteredTx]);

  return (
    <div className="space-y-6">
      {/* Title */}
      <div>
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <span>⚡ Advanced KPIs 2: Econometric & Quantitative Synthesis</span>
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          Painel executivo com 20 KPIs estatístico-financeiros inéditos, volatilidade de cauda, HHI e estresse sintético.
        </p>
      </div>

      {/* Filter Bar */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex flex-wrap items-center gap-4 text-xs">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-emerald-400" />
          <span className="font-semibold text-slate-300">Filtros:</span>
        </div>

        <div>
          <select
            value={selectedType}
            onChange={e => setSelectedType(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-white"
          >
            <option value="Todos">Todos os Tipos</option>
            <option value="Receita">Receitas</option>
            <option value="Despesa">Despesas</option>
          </select>
        </div>

        <div>
          <select
            value={selectedCat}
            onChange={e => setSelectedCat(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-white"
          >
            <option value="Todas">Todas as Categorias</option>
            {categories.map(c => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>

        <div>
          <select
            value={selectedAccount}
            onChange={e => setSelectedAccount(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-white"
          >
            <option value="Todas">Todas as Contas</option>
            {accounts.map(a => (
              <option key={a} value={a}>
                {a}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Bloco 1: Gestão de Risco e Cauda */}
      <div className="space-y-3">
        <h3 className="text-sm font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-2">
          <ShieldAlert className="w-4 h-4" />
          <span>Bloco 1: Gestão de Risco e Cauda Estatística</span>
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-3.5">
            <div className="text-[11px] text-slate-400 uppercase font-semibold">1. VaR Histórico (95%)</div>
            <div className="text-lg font-bold text-white font-mono mt-1">{formatBRL(kpis.varHist)}</div>
            <div className="text-[10px] text-slate-400 mt-1">Pior impacto em 95% dos casos</div>
          </div>
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-3.5">
            <div className="text-[11px] text-slate-400 uppercase font-semibold">2. Expected Shortfall (CVaR)</div>
            <div className="text-lg font-bold text-rose-400 font-mono mt-1">{formatBRL(kpis.cvar)}</div>
            <div className="text-[10px] text-slate-400 mt-1">Média dos 5% piores cenários</div>
          </div>
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-3.5">
            <div className="text-[11px] text-slate-400 uppercase font-semibold">3. Índice Cobertura (ICD)</div>
            <div className="text-lg font-bold text-emerald-400 font-mono mt-1">{kpis.icd.toFixed(2)}x</div>
            <div className="text-[10px] text-slate-400 mt-1">Razão receitas / despesas</div>
          </div>
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-3.5">
            <div className="text-[11px] text-slate-400 uppercase font-semibold">4. Volatilidade Burn Rate</div>
            <div className="text-lg font-bold text-sky-400 font-mono mt-1">{kpis.burnVol.toFixed(2)}</div>
            <div className="text-[10px] text-slate-400 mt-1">Desvio padrão vs média</div>
          </div>
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-3.5">
            <div className="text-[11px] text-slate-400 uppercase font-semibold">5. Share Top 10% Cauda</div>
            <div className="text-lg font-bold text-amber-400 font-mono mt-1">{kpis.top10Share.toFixed(1)}%</div>
            <div className="text-[10px] text-slate-400 mt-1">Concentração dos maiores gastos</div>
          </div>
        </div>
      </div>

      {/* Bloco 2: Estrutura, Resiliência e Dinâmica de Fluxo */}
      <div className="space-y-3">
        <h3 className="text-sm font-bold uppercase tracking-wider text-sky-400 flex items-center gap-2">
          <Activity className="w-4 h-4" />
          <span>Bloco 2: Estrutura, Resiliência e Dinâmica de Fluxo</span>
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-3.5">
            <div className="text-[11px] text-slate-400 uppercase font-semibold">6. Fator de Resiliência</div>
            <div className="text-lg font-bold text-white font-mono mt-1">{kpis.resilience.toFixed(2)}</div>
            <div className="text-[10px] text-slate-400 mt-1">Razão Mediana / Média</div>
          </div>
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-3.5">
            <div className="text-[11px] text-slate-400 uppercase font-semibold">7. Coef. Risco-Impacto</div>
            <div className="text-lg font-bold text-white font-mono mt-1">{kpis.riskImpact.toFixed(2)}</div>
            <div className="text-[10px] text-slate-400 mt-1">Assimetria × Volatilidade</div>
          </div>
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-3.5">
            <div className="text-[11px] text-slate-400 uppercase font-semibold">8. Estabilidade Freq.</div>
            <div className="text-lg font-bold text-emerald-400 font-mono mt-1">{kpis.freqStability.toFixed(1)}%</div>
            <div className="text-[10px] text-slate-400 mt-1">% dias movimentados</div>
          </div>
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-3.5">
            <div className="text-[11px] text-slate-400 uppercase font-semibold">9. Amplitude Relativa (IQR)</div>
            <div className="text-lg font-bold text-white font-mono mt-1">{kpis.relIqr.toFixed(1)}%</div>
            <div className="text-[10px] text-slate-400 mt-1">IQR normalizado pela média</div>
          </div>
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-3.5">
            <div className="text-[11px] text-slate-400 uppercase font-semibold">10. Razão de Cauda (Tail)</div>
            <div className="text-lg font-bold text-white font-mono mt-1">{kpis.tailRatio.toFixed(2)}</div>
            <div className="text-[10px] text-slate-400 mt-1">P95 / P05 absolutos</div>
          </div>
        </div>
      </div>

      {/* Bloco 3: Dispersão, Inércia e Concentração Sistêmica */}
      <div className="space-y-3">
        <h3 className="text-sm font-bold uppercase tracking-wider text-amber-400 flex items-center gap-2">
          <Zap className="w-4 h-4" />
          <span>Bloco 3: Dispersão, Inércia e Concentração Sistêmica</span>
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-3.5">
            <div className="text-[11px] text-slate-400 uppercase font-semibold">11. Dispersão Exponencial</div>
            <div className="text-lg font-bold text-white font-mono mt-1">{kpis.dispExp.toFixed(2)}</div>
            <div className="text-[10px] text-slate-400 mt-1">Variância / Média absoluta</div>
          </div>
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-3.5">
            <div className="text-[11px] text-slate-400 uppercase font-semibold">12. Elasticidade Categoria</div>
            <div className="text-lg font-bold text-white font-mono mt-1">{kpis.catElasticity.toFixed(2)}</div>
            <div className="text-[10px] text-slate-400 mt-1">Desvio padrão inter-categorias</div>
          </div>
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-3.5">
            <div className="text-[11px] text-slate-400 uppercase font-semibold">13. Eficiência Fluxo Líquido</div>
            <div className="text-lg font-bold text-emerald-400 font-mono mt-1">{kpis.netEfficiency.toFixed(1)}%</div>
            <div className="text-[10px] text-slate-400 mt-1">Saldo líquido / Volume bruto</div>
          </div>
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-3.5">
            <div className="text-[11px] text-slate-400 uppercase font-semibold">14. Inércia Transação (Lag-1)</div>
            <div className="text-lg font-bold text-white font-mono mt-1">{kpis.autocorr.toFixed(2)}</div>
            <div className="text-[10px] text-slate-400 mt-1">Autocorrelação temporal</div>
          </div>
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-3.5">
            <div className="text-[11px] text-slate-400 uppercase font-semibold">15. Z-Score Máximo (Outlier)</div>
            <div className="text-lg font-bold text-rose-400 font-mono mt-1">{kpis.maxZ.toFixed(2)}σ</div>
            <div className="text-[10px] text-slate-400 mt-1">Severidade do maior desvio</div>
          </div>
        </div>
      </div>

      {/* Bloco 4: Concentração, Geometria e Estresse de Caixa */}
      <div className="space-y-3">
        <h3 className="text-sm font-bold uppercase tracking-wider text-purple-400 flex items-center gap-2">
          <BarChart3 className="w-4 h-4" />
          <span>Bloco 4: Concentração, Geometria e Estresse de Caixa</span>
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-3.5">
            <div className="text-[11px] text-slate-400 uppercase font-semibold">16. Concentração HHI Contas</div>
            <div className="text-lg font-bold text-purple-400 font-mono mt-1">{kpis.hhi.toFixed(1)}%</div>
            <div className="text-[10px] text-slate-400 mt-1">Índice Herfindahl-Hirschman</div>
          </div>
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-3.5">
            <div className="text-[11px] text-slate-400 uppercase font-semibold">17. Fator Assimetria Fluxo</div>
            <div className="text-lg font-bold text-white font-mono mt-1">{kpis.flowSkew.toFixed(2)}</div>
            <div className="text-[10px] text-slate-400 mt-1">Razão com peso assimétrico</div>
          </div>
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-3.5">
            <div className="text-[11px] text-slate-400 uppercase font-semibold">18. Média Geométrica (+)</div>
            <div className="text-lg font-bold text-white font-mono mt-1">{formatBRL(kpis.geomMean)}</div>
            <div className="text-[10px] text-slate-400 mt-1">Média geométrica dos valores</div>
          </div>
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-3.5">
            <div className="text-[11px] text-slate-400 uppercase font-semibold">19. Volatilidade VWCV</div>
            <div className="text-lg font-bold text-white font-mono mt-1">{kpis.vwcv.toFixed(2)}</div>
            <div className="text-[10px] text-slate-400 mt-1">Ponderada pelo volume total</div>
          </div>
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-3.5">
            <div className="text-[11px] text-slate-400 uppercase font-semibold">20. Estresse Sintético</div>
            <div className="text-lg font-bold text-rose-400 font-mono mt-1">{kpis.synthStress.toFixed(2)}</div>
            <div className="text-[10px] text-slate-400 mt-1">Risco combinado de liquidez</div>
          </div>
        </div>
      </div>
    </div>
  );
};
