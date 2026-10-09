import React, { useState, useMemo } from 'react';
import { useFinance } from '../../context/FinanceContext';
import { Transaction } from '../../types/finance';
import {
  Search,
  Filter,
  Trash2,
  Edit2,
  Download,
  PlusCircle,
  CheckCircle,
  Clock,
  ArrowRight
} from 'lucide-react';

export const TransactionsTab: React.FC = () => {
  const {
    transactions,
    categories,
    accounts,
    deleteTransaction,
    deleteMultipleTransactions,
    updateTransaction,
    setActiveTab
  } = useFinance();

  const [search, setSearch] = useState('');
  const [filterType, setFilterType] = useState<string>('Todos');
  const [filterCategory, setFilterCategory] = useState<string>('Todas');
  const [filterAccount, setFilterAccount] = useState<string>('Todas');
  const [filterStatus, setFilterStatus] = useState<string>('Todos');

  // Editing modal state
  const [editingTx, setEditingTx] = useState<Transaction | null>(null);

  const formatBRL = (val: number) =>
    new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);

  const filtered = useMemo(() => {
    return transactions.filter(t => {
      if (filterType !== 'Todos' && t.tipo !== filterType) return false;
      if (filterCategory !== 'Todas' && t.categoria !== filterCategory) return false;
      if (filterAccount !== 'Todas' && t.conta !== filterAccount) return false;
      if (filterStatus !== 'Todos' && t.status !== filterStatus) return false;
      if (search.trim()) {
        const query = search.toLowerCase();
        const matchDesc = t.descricao.toLowerCase().includes(query);
        const matchCat = t.categoria.toLowerCase().includes(query);
        const matchAcc = t.conta.toLowerCase().includes(query);
        if (!matchDesc && !matchCat && !matchAcc) return false;
      }
      return true;
    });
  }, [transactions, filterType, filterCategory, filterAccount, filterStatus, search]);

  const totalSoma = filtered.reduce((acc, t) => acc + (t.tipo === 'Receita' ? t.valor : -t.valor), 0);
  const mediaVal = filtered.length > 0 ? filtered.reduce((acc, t) => acc + t.valor, 0) / filtered.length : 0;

  const exportCSV = () => {
    const headers = ['ID', 'Tipo', 'Conta', 'Conta Destino', 'Categoria', 'Descrição', 'Valor', 'Data', 'Parcelas', 'Status', 'Cenario'];
    const rows = filtered.map(t => [
      t.id,
      t.tipo,
      t.conta,
      t.contaDestino || '',
      t.categoria,
      `"${t.descricao.replace(/"/g, '""')}"`,
      t.valor,
      t.data,
      t.parcelas,
      t.status,
      t.cenario
    ]);
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `lancamentos_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-6">
      {/* Title & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <span>📋 Central Inteligente de Lançamentos</span>
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Consulte, filtre por múltiplos parâmetros, edite ou exclua registros com agilidade.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={exportCSV}
            className="flex items-center gap-1.5 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-semibold border border-slate-700 transition-all"
          >
            <Download className="w-4 h-4" />
            <span>Exportar CSV</span>
          </button>
          <button
            onClick={() => setActiveTab('cadastro')}
            className="flex items-center gap-1.5 px-3 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-semibold transition-all shadow-md shadow-emerald-600/20"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Novo Lançamento</span>
          </button>
        </div>
      </div>

      {/* KPI mini-cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4">
          <div className="text-xs uppercase text-slate-400 font-semibold">Registros Encontrados</div>
          <div className="text-2xl font-bold text-white font-mono mt-1">{filtered.length} itens</div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4">
          <div className="text-xs uppercase text-slate-400 font-semibold">Saldo dos Filtrados</div>
          <div className={`text-2xl font-bold font-mono mt-1 ${totalSoma >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
            {formatBRL(totalSoma)}
          </div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4">
          <div className="text-xs uppercase text-slate-400 font-semibold">Ticket Médio Absoluto</div>
          <div className="text-2xl font-bold text-sky-400 font-mono mt-1">{formatBRL(mediaVal)}</div>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
          {/* Search Input */}
          <div className="md:col-span-2 relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              placeholder="Buscar por descrição, conta ou categoria..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
            />
          </div>

          {/* Type */}
          <div>
            <select
              value={filterType}
              onChange={e => setFilterType(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
            >
              <option value="Todos">Tipo: Todos</option>
              <option value="Receita">Receita</option>
              <option value="Despesa">Despesa</option>
              <option value="Transferência">Transferência</option>
            </select>
          </div>

          {/* Category */}
          <div>
            <select
              value={filterCategory}
              onChange={e => setFilterCategory(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
            >
              <option value="Todas">Categoria: Todas</option>
              {categories.map(c => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>

          {/* Status */}
          <div>
            <select
              value={filterStatus}
              onChange={e => setFilterStatus(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
            >
              <option value="Todos">Status: Todos</option>
              <option value="Efetivado">Efetivado</option>
              <option value="Orçado">Orçado</option>
            </select>
          </div>
        </div>

        {/* Bulk Action */}
        {filtered.length > 0 && (
          <div className="flex items-center justify-between pt-2 border-t border-slate-800/60 text-xs">
            <span className="text-slate-400">
              Mostrando <strong className="text-white">{filtered.length}</strong> de{' '}
              {transactions.length} registros totais
            </span>
            <button
              onClick={() => {
                if (confirm(`Tem certeza que deseja excluir todos os ${filtered.length} lançamentos filtrados?`)) {
                  deleteMultipleTransactions(filtered.map(t => t.id));
                }
              }}
              className="flex items-center gap-1.5 text-rose-400 hover:text-rose-300 font-semibold"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Excluir Filtrados</span>
            </button>
          </div>
        )}
      </div>

      {/* Transaction List Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden shadow-sm">
        {filtered.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-sm">
            Nenhum lançamento corresponde aos filtros especificados.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 uppercase font-semibold">
                  <th className="py-3 px-4">Data</th>
                  <th className="py-3 px-4">Descrição</th>
                  <th className="py-3 px-4">Categoria</th>
                  <th className="py-3 px-4">Conta</th>
                  <th className="py-3 px-4">Tipo</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Valor</th>
                  <th className="py-3 px-4 text-center">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-medium">
                {filtered.map(t => (
                  <tr key={t.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4 text-slate-400 font-mono">{t.data}</td>
                    <td className="py-3 px-4 text-white font-semibold">{t.descricao}</td>
                    <td className="py-3 px-4 text-slate-300">{t.categoria}</td>
                    <td className="py-3 px-4 text-slate-400">
                      {t.conta}
                      {t.contaDestino && (
                        <span className="text-slate-500 inline-flex items-center gap-1 ml-1">
                          <ArrowRight className="w-3 h-3 inline" /> {t.contaDestino}
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                          t.tipo === 'Receita'
                            ? 'bg-emerald-500/20 text-emerald-400'
                            : t.tipo === 'Despesa'
                            ? 'bg-rose-500/20 text-rose-400'
                            : 'bg-sky-500/20 text-sky-400'
                        }`}
                      >
                        {t.tipo}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold ${
                          t.status === 'Efetivado'
                            ? 'bg-emerald-500/10 text-emerald-400'
                            : 'bg-amber-500/20 text-amber-400'
                        }`}
                      >
                        {t.status === 'Efetivado' ? (
                          <CheckCircle className="w-3 h-3" />
                        ) : (
                          <Clock className="w-3 h-3" />
                        )}
                        {t.status}
                      </span>
                    </td>
                    <td
                      className={`py-3 px-4 text-right font-mono font-bold ${
                        t.tipo === 'Receita'
                          ? 'text-emerald-400'
                          : t.tipo === 'Despesa'
                          ? 'text-rose-400'
                          : 'text-sky-400'
                      }`}
                    >
                      {t.tipo === 'Despesa' ? '-' : '+'} {formatBRL(t.valor)}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <div className="flex items-center justify-center gap-2">
                        <button
                          onClick={() => setEditingTx(t)}
                          className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
                          title="Editar"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => {
                            if (confirm(`Excluir "${t.descricao}"?`)) {
                              deleteTransaction(t.id);
                            }
                          }}
                          className="p-1.5 text-rose-400 hover:text-rose-300 rounded-lg hover:bg-rose-500/10 transition-colors"
                          title="Excluir"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Edit Modal */}
      {editingTx && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl">
            <h3 className="text-lg font-bold text-white mb-4">Editar Lançamento</h3>

            <div className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Descrição</label>
                <input
                  type="text"
                  value={editingTx.descricao}
                  onChange={e => setEditingTx({ ...editingTx, descricao: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Tipo</label>
                  <select
                    value={editingTx.tipo}
                    onChange={e => setEditingTx({ ...editingTx, tipo: e.target.value as any })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white"
                  >
                    <option value="Receita">Receita</option>
                    <option value="Despesa">Despesa</option>
                    <option value="Transferência">Transferência</option>
                  </select>
                </div>

                <div>
                  <label className="block text-slate-400 mb-1">Valor (R$)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={editingTx.valor}
                    onChange={e =>
                      setEditingTx({ ...editingTx, valor: parseFloat(e.target.value) || 0 })
                    }
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white font-mono"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Conta</label>
                  <select
                    value={editingTx.conta}
                    onChange={e => setEditingTx({ ...editingTx, conta: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white"
                  >
                    {accounts.map(a => (
                      <option key={a} value={a}>
                        {a}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-slate-400 mb-1">Categoria</label>
                  <select
                    value={editingTx.categoria}
                    onChange={e => setEditingTx({ ...editingTx, categoria: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white"
                  >
                    {categories.map(c => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Data</label>
                  <input
                    type="date"
                    value={editingTx.data}
                    onChange={e => setEditingTx({ ...editingTx, data: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white font-mono"
                  />
                </div>

                <div>
                  <label className="block text-slate-400 mb-1">Status</label>
                  <select
                    value={editingTx.status}
                    onChange={e => setEditingTx({ ...editingTx, status: e.target.value as any })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white"
                  >
                    <option value="Efetivado">Efetivado</option>
                    <option value="Orçado">Orçado</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 mt-6">
              <button
                onClick={() => setEditingTx(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold"
              >
                Cancelar
              </button>
              <button
                onClick={() => {
                  updateTransaction(editingTx.id, editingTx);
                  setEditingTx(null);
                }}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-semibold shadow-md shadow-emerald-600/20"
              >
                Salvar Alterações
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
