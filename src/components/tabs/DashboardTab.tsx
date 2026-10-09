import React, { useState, useMemo } from 'react';
import { useFinance } from '../../context/FinanceContext';
import {
  TrendingUp,
  TrendingDown,
  Wallet,
  PiggyBank,
  Receipt,
  Calendar,
  Filter,
  BarChart2,
  PieChart as PieIcon
} from 'lucide-react';

export const DashboardTab: React.FC = () => {
  const { transactions } = useFinance();

  // Filters
  const [selectedMonth, setSelectedMonth] = useState<string>('2026-10');
  const [budgetType, setBudgetType] = useState<'Despesa' | 'Receita'>('Despesa');
  const [timeGrouping, setTimeGrouping] = useState<'Mensal' | 'Trimestral' | 'Anual'>('Mensal');

  const formatBRL = (val: number) =>
    new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);

  // Available months
  const availableMonths = useMemo(() => {
    const months = new Set<string>();
    transactions.forEach(t => {
      if (t.data) months.add(t.data.substring(0, 7));
    });
    const arr = Array.from(months).sort().reverse();
    return arr.length > 0 ? arr : ['2026-10'];
  }, [transactions]);

  // Overall Totals
  const { totalReceitas, totalDespesas, saldo, savingRate, ticketMedio } = useMemo(() => {
    const rec = transactions
      .filter(t => t.tipo === 'Receita')
      .reduce((acc, t) => acc + t.valor, 0);
    const desp = transactions
      .filter(t => t.tipo === 'Despesa')
      .reduce((acc, t) => acc + t.valor, 0);
    const s = rec - desp;
    const rate = rec > 0 ? (s / rec) * 100 : 0;
    const count = transactions.length;
    const tm = count > 0 ? (rec + desp) / count : 0;
    return {
      totalReceitas: rec,
      totalDespesas: desp,
      saldo: s,
      savingRate: rate,
      ticketMedio: tm
    };
  }, [transactions]);

  // Budget vs Efetivado calculation for the selected month
  const budgetTable = useMemo(() => {
    const monthTx = transactions.filter(
      t => t.data.startsWith(selectedMonth) && t.tipo === budgetType
    );

    const categoriesMap = new Map<string, { budget: number; efetivado: number }>();

    monthTx.forEach(t => {
      const current = categoriesMap.get(t.categoria) || { budget: 0, efetivado: 0 };
      if (t.status === 'Orçado') {
        current.budget += t.valor;
      } else {
        current.efetivado += t.valor;
      }
      categoriesMap.set(t.categoria, current);
    });

    const rows = Array.from(categoriesMap.entries()).map(([categoria, vals]) => {
      const diferenca =
        budgetType === 'Despesa'
          ? vals.budget - vals.efetivado
          : vals.efetivado - vals.budget;
      const pctUtilizado =
        vals.budget > 0 ? (vals.efetivado / vals.budget) * 100 : vals.efetivado > 0 ? 100 : 0;
      return {
        categoria,
        budget: vals.budget,
        efetivado: vals.efetivado,
        diferenca,
        pctUtilizado
      };
    });

    return rows.sort((a, b) => b.efetivado - a.efetivado);
  }, [transactions, selectedMonth, budgetType]);

  // Grouped temporal data (by month)
  const monthlyData = useMemo(() => {
    const map = new Map<string, { receitas: number; despesas: number }>();
    transactions.forEach(t => {
      const key = t.data.substring(0, 7);
      const cur = map.get(key) || { receitas: 0, despesas: 0 };
      if (t.tipo === 'Receita') cur.receitas += t.valor;
      if (t.tipo === 'Despesa') cur.despesas += t.valor;
      map.set(key, cur);
    });
    return Array.from(map.entries())
      .sort((a, b) => a[0].localeCompare(b[0]))
      .map(([periodo, vals]) => ({
        periodo,
        ...vals,
        saldo: vals.receitas - vals.despesas
      }));
  }, [transactions]);

  // Category breakdown (Despesas)
  const categoryExpenses = useMemo(() => {
    const map = new Map<string, number>();
    let total = 0;
    transactions
      .filter(t => t.tipo === 'Despesa')
      .forEach(t => {
        map.set(t.categoria, (map.get(t.categoria) || 0) + t.valor);
        total += t.valor;
      });

    return Array.from(map.entries())
      .map(([categoria, valor]) => ({
        categoria,
        valor,
        pct: total > 0 ? (valor / total) * 100 : 0
      }))
      .sort((a, b) => b.valor - a.valor);
  }, [transactions]);

  const maxExpense = Math.max(...monthlyData.map(m => Math.max(m.receitas, m.despesas)), 1);

  return (
    <div className="space-y-6">
      {/* Title & Introduction */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <span>📊 Dashboard Financeiro Executivo</span>
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Controle de fluxo de caixa, orçamento por categoria e tendências históricas.
          </p>
        </div>
      </div>

      {/* Top 5 KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Receitas */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4.5 hover:border-emerald-500/40 transition-all shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Receitas Totais</span>
            <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="text-xl lg:text-2xl font-bold text-white tracking-tight">
            {formatBRL(totalReceitas)}
          </div>
          <div className="text-xs text-emerald-400 mt-2 font-medium flex items-center gap-1">
            <span>Entradas registradas</span>
          </div>
        </div>

        {/* Despesas */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4.5 hover:border-rose-500/40 transition-all shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Despesas Totais</span>
            <div className="p-2 rounded-xl bg-rose-500/10 text-rose-400">
              <TrendingDown className="w-4 h-4" />
            </div>
          </div>
          <div className="text-xl lg:text-2xl font-bold text-white tracking-tight">
            {formatBRL(totalDespesas)}
          </div>
          <div className="text-xs text-rose-400 mt-2 font-medium flex items-center gap-1">
            <span>Saídas consolidadas</span>
          </div>
        </div>

        {/* Saldo Líquido */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4.5 hover:border-sky-500/40 transition-all shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Saldo Líquido</span>
            <div className="p-2 rounded-xl bg-sky-500/10 text-sky-400">
              <Wallet className="w-4 h-4" />
            </div>
          </div>
          <div className={`text-xl lg:text-2xl font-bold tracking-tight ${saldo >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
            {formatBRL(saldo)}
          </div>
          <div className="text-xs text-slate-400 mt-2 font-medium">
            Resultado acumulado
          </div>
        </div>

        {/* Taxa de Poupança */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4.5 hover:border-amber-500/40 transition-all shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Taxa de Poupança</span>
            <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400">
              <PiggyBank className="w-4 h-4" />
            </div>
          </div>
          <div className="text-xl lg:text-2xl font-bold text-white tracking-tight">
            {savingRate.toFixed(1)}%
          </div>
          <div className="text-xs text-slate-400 mt-2 font-medium">
            {savingRate >= 20 ? 'Meta saudável atingida' : 'Abaixo da meta recomendada (20%)'}
          </div>
        </div>

        {/* Ticket Médio */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4.5 hover:border-purple-500/40 transition-all shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Ticket Médio</span>
            <div className="p-2 rounded-xl bg-purple-500/10 text-purple-400">
              <Receipt className="w-4 h-4" />
            </div>
          </div>
          <div className="text-xl lg:text-2xl font-bold text-white tracking-tight">
            {formatBRL(ticketMedio)}
          </div>
          <div className="text-xs text-slate-400 mt-2 font-medium">
            Por operação transacionada
          </div>
        </div>
      </div>

      {/* Orçamento: Budget vs Efetivado */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
          <div>
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <span>🎯 Controle Orçamentário: Budget vs. Efetivado</span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Comparativo de metas orçadas e gastos efetivados por categoria.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2 bg-slate-950/70 border border-slate-800 rounded-xl px-3 py-1.5 text-xs">
              <Calendar className="w-3.5 h-3.5 text-slate-400" />
              <select
                value={selectedMonth}
                onChange={e => setSelectedMonth(e.target.value)}
                className="bg-transparent text-white focus:outline-none cursor-pointer"
              >
                {availableMonths.map(m => (
                  <option key={m} value={m} className="bg-slate-900 text-white">
                    {m}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center rounded-xl bg-slate-950/70 border border-slate-800 p-1 text-xs">
              <button
                onClick={() => setBudgetType('Despesa')}
                className={`px-3 py-1 rounded-lg font-medium transition-all ${
                  budgetType === 'Despesa'
                    ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                Despesas
              </button>
              <button
                onClick={() => setBudgetType('Receita')}
                className={`px-3 py-1 rounded-lg font-medium transition-all ${
                  budgetType === 'Receita'
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                Receitas
              </button>
            </div>
          </div>
        </div>

        {budgetTable.length === 0 ? (
          <div className="text-center py-12 text-slate-400 text-sm">
            Nenhum lançamento encontrado para o período selecionado ({selectedMonth}).
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 text-xs font-semibold uppercase tracking-wider">
                  <th className="pb-3 px-3">Categoria</th>
                  <th className="pb-3 px-3">Budget (Orçado)</th>
                  <th className="pb-3 px-3">Efetivado</th>
                  <th className="pb-3 px-3">Diferença (Saldo)</th>
                  <th className="pb-3 px-3 w-48">% Utilizado</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-medium">
                {budgetTable.map((row, idx) => {
                  const isOverBudget = budgetType === 'Despesa' && row.pctUtilizado > 100;
                  return (
                    <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-3 px-3 text-white font-semibold">{row.categoria}</td>
                      <td className="py-3 px-3 text-slate-300 font-mono">{formatBRL(row.budget)}</td>
                      <td className="py-3 px-3 text-white font-mono">{formatBRL(row.efetivado)}</td>
                      <td className={`py-3 px-3 font-mono ${row.diferenca >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {formatBRL(row.diferenca)}
                      </td>
                      <td className="py-3 px-3">
                        <div className="flex items-center gap-3">
                          <div className="flex-1 bg-slate-800 h-2 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full transition-all ${
                                isOverBudget
                                  ? 'bg-rose-500'
                                  : row.pctUtilizado > 80
                                  ? 'bg-amber-500'
                                  : 'bg-emerald-500'
                              }`}
                              style={{ width: `${Math.min(row.pctUtilizado, 100)}%` }}
                            />
                          </div>
                          <span
                            className={`text-xs font-mono w-14 text-right ${
                              isOverBudget ? 'text-rose-400 font-bold' : 'text-slate-400'
                            }`}
                          >
                            {row.pctUtilizado.toFixed(1)}%
                          </span>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Visual Charts: Evolução Mensal & Distribuição de Despesas */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Monthly evolution */}
        <div className="lg:col-span-2 bg-slate-900/80 border border-slate-800 rounded-2xl p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <BarChart2 className="w-4 h-4 text-emerald-400" />
                <span>Evolução Mensal (Receitas vs. Despesas)</span>
              </h3>
              <p className="text-xs text-slate-400">Comparativo histórico por competência</p>
            </div>
            <div className="flex items-center gap-4 text-xs">
              <span className="flex items-center gap-1.5 text-slate-300">
                <span className="w-3 h-3 rounded bg-emerald-500"></span> Receitas
              </span>
              <span className="flex items-center gap-1.5 text-slate-300">
                <span className="w-3 h-3 rounded bg-rose-500"></span> Despesas
              </span>
            </div>
          </div>

          <div className="space-y-4 pt-2">
            {monthlyData.map((item, idx) => {
              const recWidth = (item.receitas / maxExpense) * 100;
              const despWidth = (item.despesas / maxExpense) * 100;
              return (
                <div key={idx} className="space-y-1.5 bg-slate-950/40 p-3 rounded-xl border border-slate-800/60">
                  <div className="flex items-center justify-between text-xs font-semibold">
                    <span className="text-slate-300 font-mono">{item.periodo}</span>
                    <span className={`font-mono ${item.saldo >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                      Saldo: {formatBRL(item.saldo)}
                    </span>
                  </div>

                  <div className="space-y-1">
                    {/* Receita bar */}
                    <div className="flex items-center gap-3 text-xs">
                      <span className="w-16 text-slate-400 shrink-0">Receita:</span>
                      <div className="flex-1 bg-slate-800/80 h-3 rounded-full overflow-hidden">
                        <div
                          className="bg-emerald-500 h-full rounded-full transition-all"
                          style={{ width: `${Math.max(recWidth, 2)}%` }}
                        />
                      </div>
                      <span className="font-mono text-slate-300 w-24 text-right">
                        {formatBRL(item.receitas)}
                      </span>
                    </div>

                    {/* Despesa bar */}
                    <div className="flex items-center gap-3 text-xs">
                      <span className="w-16 text-slate-400 shrink-0">Despesa:</span>
                      <div className="flex-1 bg-slate-800/80 h-3 rounded-full overflow-hidden">
                        <div
                          className="bg-rose-500 h-full rounded-full transition-all"
                          style={{ width: `${Math.max(despWidth, 2)}%` }}
                        />
                      </div>
                      <span className="font-mono text-slate-300 w-24 text-right">
                        {formatBRL(item.despesas)}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Category Share */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6">
          <div className="mb-6">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <PieIcon className="w-4 h-4 text-sky-400" />
              <span>Distribuição de Gastos</span>
            </h3>
            <p className="text-xs text-slate-400">Participação por categoria</p>
          </div>

          <div className="space-y-3">
            {categoryExpenses.slice(0, 7).map((cat, idx) => (
              <div key={idx} className="space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-300 font-medium truncate">{cat.categoria}</span>
                  <span className="font-mono text-slate-400">{cat.pct.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-emerald-500 to-teal-400 h-full rounded-full"
                    style={{ width: `${cat.pct}%` }}
                  />
                </div>
                <div className="text-[11px] text-slate-400 text-right font-mono">
                  {formatBRL(cat.valor)}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
