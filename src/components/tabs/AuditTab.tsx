import React, { useState, useMemo } from 'react';
import { useFinance } from '../../context/FinanceContext';
import { mean, standardDeviation } from '../../utils/mathStats';
import { ShieldAlert, AlertTriangle, CheckCircle, Search, Filter } from 'lucide-react';

export const AuditTab: React.FC = () => {
  const { transactions, categories, accounts } = useFinance();

  const [filterStatus, setFilterStatus] = useState<string>('Todos');
  const [filterType, setFilterType] = useState<string>('Todos');
  const [filterAccount, setFilterAccount] = useState<string>('Todas');

  const formatBRL = (val: number) =>
    new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);

  // Filtered transactions
  const filteredTx = useMemo(() => {
    return transactions.filter(t => {
      if (filterStatus !== 'Todos' && t.status !== filterStatus) return false;
      if (filterType !== 'Todos' && t.tipo !== filterType) return false;
      if (filterAccount !== 'Todas' && t.conta !== filterAccount) return false;
      return true;
    });
  }, [transactions, filterStatus, filterType, filterAccount]);

  const totalRegistros = filteredTx.length;
  const receitas = filteredTx.filter(t => t.tipo === 'Receita').reduce((a, b) => a + b.valor, 0);
  const despesas = filteredTx.filter(t => t.tipo === 'Despesa').reduce((a, b) => a + b.valor, 0);
  const saldoLiq = receitas - despesas;
  const ticketMedio = totalRegistros > 0 ? (receitas + despesas) / totalRegistros : 0;

  // Outlier detection (> mean + 2*std)
  const outliers = useMemo(() => {
    const vals = filteredTx.map(t => t.valor);
    if (vals.length < 2) return [];
    const m = mean(vals);
    const s = standardDeviation(vals, m);
    const limit = m + 2 * s;
    return filteredTx.filter(t => t.valor > limit);
  }, [filteredTx]);

  // Pending / budgeted items
  const pendingItems = useMemo(() => {
    return filteredTx.filter(t => t.status === 'Orçado');
  }, [filteredTx]);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <span>🔍 Auditoria e Conformidade Financeira</span>
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          Painel de controle analítico para verificação de consistência, detecção de anomalias estatísticas e validação de pendências.
        </p>
      </div>

      {/* Filter Bar */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex flex-wrap items-center gap-4 text-xs">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-emerald-400" />
          <span className="font-semibold text-slate-300">Filtros de Auditoria:</span>
        </div>

        <div>
          <select
            value={filterStatus}
            onChange={e => setFilterStatus(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-white"
          >
            <option value="Todos">Status: Todos</option>
            <option value="Efetivado">Efetivado</option>
            <option value="Orçado">Orçado / Pendente</option>
          </select>
        </div>

        <div>
          <select
            value={filterType}
            onChange={e => setFilterType(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-white"
          >
            <option value="Todos">Tipo: Todos</option>
            <option value="Receita">Receita</option>
            <option value="Despesa">Despesa</option>
          </select>
        </div>

        <div>
          <select
            value={filterAccount}
            onChange={e => setFilterAccount(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-white"
          >
            <option value="Todas">Conta: Todas</option>
            {accounts.map(a => (
              <option key={a} value={a}>
                {a}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Resumo Executivo Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4">
          <div className="text-xs font-semibold uppercase text-slate-400">Total Registros</div>
          <div className="text-2xl font-bold text-white mt-1 font-mono">{totalRegistros}</div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4">
          <div className="text-xs font-semibold uppercase text-emerald-400">Receitas Filtradas</div>
          <div className="text-xl font-bold text-emerald-400 mt-1 font-mono">{formatBRL(receitas)}</div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4">
          <div className="text-xs font-semibold uppercase text-rose-400">Despesas Filtradas</div>
          <div className="text-xl font-bold text-rose-400 mt-1 font-mono">{formatBRL(despesas)}</div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4">
          <div className="text-xs font-semibold uppercase text-sky-400">Saldo Líquido</div>
          <div className={`text-xl font-bold mt-1 font-mono ${saldoLiq >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
            {formatBRL(saldoLiq)}
          </div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4">
          <div className="text-xs font-semibold uppercase text-slate-400">Ticket Médio</div>
          <div className="text-xl font-bold text-white mt-1 font-mono">{formatBRL(ticketMedio)}</div>
        </div>
      </div>

      {/* Exception & Alerts Panels */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Outliers Box */}
        <div className="bg-slate-900/80 border border-amber-500/30 rounded-2xl p-5">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className="w-5 h-5 text-amber-400" />
            <h3 className="text-base font-bold text-white">
              Lançamentos Atípicos (Outliers &gt; μ + 2σ)
            </h3>
          </div>
          {outliers.length === 0 ? (
            <div className="flex items-center gap-2 text-emerald-400 text-sm py-4">
              <CheckCircle className="w-4 h-4" />
              <span>Nenhum valor discrepante detectado no filtro atual.</span>
            </div>
          ) : (
            <div className="space-y-2">
              <p className="text-xs text-amber-300 font-medium">
                Detectados {outliers.length} lançamentos acima de 2 desvios padrão da média:
              </p>
              <div className="max-h-48 overflow-y-auto space-y-2 pr-1">
                {outliers.map(item => (
                  <div
                    key={item.id}
                    className="flex items-center justify-between p-2.5 bg-slate-950/70 border border-amber-500/20 rounded-xl text-xs"
                  >
                    <div>
                      <div className="text-white font-medium">{item.descricao}</div>
                      <div className="text-slate-400 font-mono text-[11px]">
                        {item.data} • {item.categoria}
                      </div>
                    </div>
                    <div className="text-amber-400 font-bold font-mono">
                      {formatBRL(item.valor)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Status Critical Box */}
        <div className="bg-slate-900/80 border border-sky-500/30 rounded-2xl p-5">
          <div className="flex items-center gap-2 mb-3">
            <ShieldAlert className="w-5 h-5 text-sky-400" />
            <h3 className="text-base font-bold text-white">
              Pendências e Previsões (Orçado)
            </h3>
          </div>
          {pendingItems.length === 0 ? (
            <div className="flex items-center gap-2 text-emerald-400 text-sm py-4">
              <CheckCircle className="w-4 h-4" />
              <span>Todos os lançamentos do período estão 100% efetivados.</span>
            </div>
          ) : (
            <div className="space-y-2">
              <p className="text-xs text-sky-300 font-medium">
                {pendingItems.length} transações com status Orçado pendente de liquidação:
              </p>
              <div className="max-h-48 overflow-y-auto space-y-2 pr-1">
                {pendingItems.map(item => (
                  <div
                    key={item.id}
                    className="flex items-center justify-between p-2.5 bg-slate-950/70 border border-sky-500/20 rounded-xl text-xs"
                  >
                    <div>
                      <div className="text-white font-medium">{item.descricao}</div>
                      <div className="text-slate-400 font-mono text-[11px]">
                        Previsto: {item.data} • {item.categoria}
                      </div>
                    </div>
                    <div className="text-sky-400 font-bold font-mono">
                      {formatBRL(item.valor)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Base Consolidada Filtrada */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5">
        <h3 className="text-base font-bold text-white mb-3">📋 Base Consolidada de Auditoria</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 uppercase font-semibold">
                <th className="py-2.5 px-3">Data</th>
                <th className="py-2.5 px-3">Descrição</th>
                <th className="py-2.5 px-3">Categoria</th>
                <th className="py-2.5 px-3">Conta</th>
                <th className="py-2.5 px-3">Tipo</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3 text-right">Valor</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-medium">
              {filteredTx.map(t => (
                <tr key={t.id} className="hover:bg-slate-800/30">
                  <td className="py-2.5 px-3 text-slate-400 font-mono">{t.data}</td>
                  <td className="py-2.5 px-3 text-white font-semibold">{t.descricao}</td>
                  <td className="py-2.5 px-3 text-slate-300">{t.categoria}</td>
                  <td className="py-2.5 px-3 text-slate-400">{t.conta}</td>
                  <td className="py-2.5 px-3">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                        t.tipo === 'Receita'
                          ? 'bg-emerald-500/20 text-emerald-400'
                          : 'bg-rose-500/20 text-rose-400'
                      }`}
                    >
                      {t.tipo}
                    </span>
                  </td>
                  <td className="py-2.5 px-3">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                        t.status === 'Efetivado'
                          ? 'bg-slate-800 text-slate-300'
                          : 'bg-amber-500/20 text-amber-400'
                      }`}
                    >
                      {t.status}
                    </span>
                  </td>
                  <td
                    className={`py-2.5 px-3 text-right font-mono font-bold ${
                      t.tipo === 'Receita' ? 'text-emerald-400' : 'text-rose-400'
                    }`}
                  >
                    {formatBRL(t.valor)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
