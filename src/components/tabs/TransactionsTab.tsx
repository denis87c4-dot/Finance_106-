import React, { useState, useMemo } from 'react';
import { useFinance } from '../../context/FinanceContext';
import { Transaction } from '../../types/finance';
import { DatePickerWithInput } from '../common/DatePickerWithInput';
import {
  Search,
  Filter,
  Trash2,
  Edit2,
  Download,
  PlusCircle,
  CheckCircle,
  Clock,
  ArrowRight,
  AlertTriangle,
  RotateCcw,
  CheckSquare,
  Square,
  X
} from 'lucide-react';

export const TransactionsTab: React.FC = () => {
  const {
    transactions,
    categories,
    accounts,
    deleteTransaction,
    deleteMultipleTransactions,
    clearAll,
    resetToSample,
    updateTransaction,
    setActiveTab
  } = useFinance();

  const [search, setSearch] = useState('');
  const [filterType, setFilterType] = useState<string>('Todos');
  const [filterCategory, setFilterCategory] = useState<string>('Todas');
  const [filterAccount, setFilterAccount] = useState<string>('Todas');
  const [filterStatus, setFilterStatus] = useState<string>('Todos');

  // Seleção múltipla por checkbox
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  // Modais de exclusão e edição
  const [editingTx, setEditingTx] = useState<Transaction | null>(null);
  const [deleteModal, setDeleteModal] = useState<{
    isOpen: boolean;
    type: 'single' | 'selected' | 'filtered' | 'all';
    targetId?: string;
    targetDesc?: string;
    count?: number;
  } | null>(null);

  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const formatBRL = (val: number) =>
    new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage(null);
    }, 4000);
  };

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

  // Selecionar todos os visíveis
  const allFilteredSelected = filtered.length > 0 && filtered.every(t => selectedIds.includes(t.id));

  const toggleSelectAllFiltered = () => {
    if (allFilteredSelected) {
      setSelectedIds([]);
    } else {
      setSelectedIds(filtered.map(t => t.id));
    }
  };

  const toggleSelectOne = (id: string) => {
    setSelectedIds(prev =>
      prev.includes(id) ? prev.filter(item => item !== id) : [...prev, id]
    );
  };

  // Execução de Exclusão Confirmada
  const handleConfirmDelete = () => {
    if (!deleteModal) return;

    if (deleteModal.type === 'single' && deleteModal.targetId) {
      deleteTransaction(deleteModal.targetId);
      setSelectedIds(prev => prev.filter(id => id !== deleteModal.targetId));
      showToast('Lançamento excluído com sucesso.');
    } else if (deleteModal.type === 'selected') {
      deleteMultipleTransactions(selectedIds);
      const count = selectedIds.length;
      setSelectedIds([]);
      showToast(`${count} lançamentos selecionados foram excluídos com sucesso.`);
    } else if (deleteModal.type === 'filtered') {
      const idsToDelete = filtered.map(t => t.id);
      deleteMultipleTransactions(idsToDelete);
      setSelectedIds([]);
      showToast(`${idsToDelete.length} lançamentos filtrados foram excluídos com sucesso.`);
    } else if (deleteModal.type === 'all') {
      clearAll();
      setSelectedIds([]);
      showToast('Todos os lançamentos da base de dados foram excluídos com sucesso.');
    }

    setDeleteModal(null);
  };

  const exportCSV = () => {
    const headers = ['ID', 'Tipo', 'Conta', 'Conta Destino', 'Categoria', 'Descrição', 'Valor', 'Data Compra', 'Data Pagamento', 'Parcelas', 'Status', 'Cenario'];
    const rows = filtered.map(t => [
      t.id,
      t.tipo,
      t.conta,
      t.contaDestino || '',
      t.categoria,
      `"${t.descricao.replace(/"/g, '""')}"`,
      t.valor,
      t.data,
      t.dataPagamento || t.data,
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
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed top-5 right-5 z-50 p-4 bg-emerald-600 text-white rounded-2xl shadow-2xl flex items-center gap-3 text-sm font-semibold animate-in fade-in slide-in-from-top-4">
          <CheckCircle className="w-5 h-5 shrink-0" />
          <span>{toastMessage}</span>
          <button onClick={() => setToastMessage(null)} className="ml-2 hover:opacity-80">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Header & Ações Globais */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <span>📋 Central Inteligente de Lançamentos</span>
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Consulte, filtre por múltiplos parâmetros, edite, exclua individualmente ou limpe todos os registros de uma só vez.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={exportCSV}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-semibold border border-slate-700 transition-all"
          >
            <Download className="w-4 h-4" />
            <span>Exportar CSV</span>
          </button>

          <button
            onClick={() => setActiveTab('cadastro')}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-semibold transition-all shadow-md shadow-emerald-600/20"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Novo Lançamento</span>
          </button>

          {/* Botão de Excluir Todos de uma Vez */}
          {transactions.length > 0 && (
            <button
              onClick={() =>
                setDeleteModal({
                  isOpen: true,
                  type: 'all',
                  count: transactions.length
                })
              }
              className="flex items-center gap-1.5 px-3.5 py-2 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 hover:text-rose-300 rounded-xl text-xs font-semibold border border-rose-500/30 transition-all shadow-sm"
              title="Apagar todos os lançamentos cadastrados"
            >
              <Trash2 className="w-4 h-4" />
              <span>Excluir Todos ({transactions.length})</span>
            </button>
          )}
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

      {/* Barra de Filtros e Busca */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
          {/* Busca por texto */}
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

          {/* Tipo */}
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

          {/* Categoria */}
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

        {/* Barra de Ações Rápidas de Exclusão Filtrada */}
        {filtered.length > 0 && (
          <div className="flex flex-wrap items-center justify-between pt-2 border-t border-slate-800/60 text-xs gap-3">
            <span className="text-slate-400">
              Mostrando <strong className="text-white">{filtered.length}</strong> de{' '}
              {transactions.length} registros totais
            </span>

            <div className="flex items-center gap-3">
              <button
                onClick={() =>
                  setDeleteModal({
                    isOpen: true,
                    type: 'filtered',
                    count: filtered.length
                  })
                }
                className="flex items-center gap-1.5 text-rose-400 hover:text-rose-300 font-semibold"
                title="Excluir apenas os que aparecem no filtro atual"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>Excluir Todos os Filtrados ({filtered.length})</span>
              </button>
            </div>
          </div>
        )}
      </div>

      {/* ==================== BARRA FLUTUANTE DE SELEÇÃO MÚLTIPLA ==================== */}
      {selectedIds.length > 0 && (
        <div className="p-3.5 bg-indigo-950/80 border border-indigo-500/40 rounded-2xl flex flex-wrap items-center justify-between gap-3 text-xs shadow-xl animate-in fade-in">
          <div className="flex items-center gap-2 text-indigo-200">
            <span className="font-bold bg-indigo-500/30 text-indigo-300 px-2.5 py-1 rounded-xl font-mono">
              {selectedIds.length} selecionados
            </span>
            <span>Marque ou desmarque itens específicos para aplicar ações em lote.</span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setSelectedIds([])}
              className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl font-semibold transition-colors"
            >
              Desmarcar Todos
            </button>
            <button
              onClick={() =>
                setDeleteModal({
                  isOpen: true,
                  type: 'selected',
                  count: selectedIds.length
                })
              }
              className="px-3.5 py-1.5 bg-rose-600 hover:bg-rose-500 text-white rounded-xl font-semibold flex items-center gap-1.5 shadow-md shadow-rose-600/20 transition-all"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Excluir Selecionados ({selectedIds.length})</span>
            </button>
          </div>
        </div>
      )}

      {/* Tabela de Lançamentos */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden shadow-sm">
        {filtered.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-sm space-y-3">
            <p>Nenhum lançamento cadastrado ou correspondente aos filtros.</p>
            {transactions.length === 0 && (
              <button
                onClick={() => resetToSample()}
                className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600/20 border border-emerald-500/30 text-emerald-400 rounded-xl text-xs font-semibold hover:bg-emerald-600/30"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Restaurar Base Demonstrativa</span>
              </button>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 uppercase font-semibold">
                  {/* Checkbox Selecionar Todos */}
                  <th className="py-3 px-3 w-10 text-center">
                    <button
                      type="button"
                      onClick={toggleSelectAllFiltered}
                      className="p-1 hover:text-white"
                      title={allFilteredSelected ? 'Desmarcar todos' : 'Selecionar todos os visíveis'}
                    >
                      {allFilteredSelected ? (
                        <CheckSquare className="w-4 h-4 text-emerald-400" />
                      ) : (
                        <Square className="w-4 h-4 text-slate-500" />
                      )}
                    </button>
                  </th>
                  <th className="py-3 px-3">Data</th>
                  <th className="py-3 px-4">Descrição</th>
                  <th className="py-3 px-4">Categoria</th>
                  <th className="py-3 px-4">Conta</th>
                  <th className="py-3 px-4">Tipo</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Valor</th>
                  <th className="py-3 px-4 text-center w-28">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-medium">
                {filtered.map(t => {
                  const isChecked = selectedIds.includes(t.id);
                  return (
                    <tr
                      key={t.id}
                      className={`transition-colors ${
                        isChecked ? 'bg-indigo-500/10' : 'hover:bg-slate-800/40'
                      }`}
                    >
                      {/* Checkbox individual */}
                      <td className="py-3 px-3 text-center">
                        <button
                          type="button"
                          onClick={() => toggleSelectOne(t.id)}
                          className="p-1 text-slate-400 hover:text-white"
                        >
                          {isChecked ? (
                            <CheckSquare className="w-4 h-4 text-emerald-400" />
                          ) : (
                            <Square className="w-4 h-4 text-slate-600" />
                          )}
                        </button>
                      </td>
                      <td className="py-3 px-3 font-mono">
                        <div className="text-slate-300 font-semibold">{t.data}</div>
                        {t.dataPagamento && t.dataPagamento !== t.data && (
                          <div className="text-[10px] text-emerald-400 font-medium">
                            Fatura: {t.dataPagamento}
                          </div>
                        )}
                      </td>
                      <td className="py-3 px-4 text-white font-semibold">
                        <div>{t.descricao}</div>
                        {t.parcelas && t.parcelas !== '1/1' && (
                          <span className="text-[10px] text-indigo-400 font-mono font-medium">
                            Parcela {t.parcelas}
                          </span>
                        )}
                      </td>
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
                            title="Editar lançamento"
                          >
                            <Edit2 className="w-3.5 h-3.5" />
                          </button>
                          {/* Excluir UM lançamento individual */}
                          <button
                            onClick={() =>
                              setDeleteModal({
                                isOpen: true,
                                type: 'single',
                                targetId: t.id,
                                targetDesc: t.descricao
                              })
                            }
                            className="p-1.5 text-rose-400 hover:text-rose-300 rounded-lg hover:bg-rose-500/10 transition-colors"
                            title="Excluir este lançamento"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
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

      {/* ==================== MODAL DE CONFIRMAÇÃO DE EXCLUSÃO ==================== */}
      {deleteModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl max-w-md w-full p-6 shadow-2xl space-y-4 animate-in fade-in zoom-in-95">
            <div className="flex items-center gap-3 text-rose-400">
              <div className="p-3 rounded-2xl bg-rose-500/10 border border-rose-500/20">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">
                  {deleteModal.type === 'single'
                    ? 'Excluir Lançamento'
                    : deleteModal.type === 'all'
                    ? 'Excluir TODOS os Lançamentos'
                    : deleteModal.type === 'selected'
                    ? 'Excluir Lançamentos Selecionados'
                    : 'Excluir Lançamentos Filtrados'}
                </h3>
                <p className="text-xs text-slate-400">Esta operação removerá os registros selecionados.</p>
              </div>
            </div>

            <div className="p-3.5 bg-slate-950/70 border border-slate-800 rounded-2xl text-xs text-slate-300">
              {deleteModal.type === 'single' && (
                <p>
                  Deseja realmente excluir o lançamento{' '}
                  <strong className="text-white font-semibold">"{deleteModal.targetDesc}"</strong>?
                </p>
              )}
              {deleteModal.type === 'all' && (
                <p>
                  Atenção: Você está prestes a apagar <strong className="text-rose-400 font-bold">{deleteModal.count}</strong> lançamentos (toda a base de dados). Todos os históricos financeiros serão zerados.
                </p>
              )}
              {deleteModal.type === 'selected' && (
                <p>
                  Deseja excluir os <strong className="text-rose-400 font-bold">{deleteModal.count}</strong> lançamentos marcados com checkbox?
                </p>
              )}
              {deleteModal.type === 'filtered' && (
                <p>
                  Deseja excluir todos os <strong className="text-rose-400 font-bold">{deleteModal.count}</strong> lançamentos correspondentes aos filtros atuais?
                </p>
              )}
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setDeleteModal(null)}
                className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold transition-colors"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={handleConfirmDelete}
                className="px-4 py-2.5 bg-rose-600 hover:bg-rose-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-rose-600/25 transition-all"
              >
                Confirmar e Excluir
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ==================== MODAL DE EDIÇÃO DE LANÇAMENTO ==================== */}
      {editingTx && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <h3 className="text-lg font-bold text-white">Editar Lançamento</h3>

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

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <DatePickerWithInput
                  value={editingTx.data}
                  onChange={val => setEditingTx({ ...editingTx, data: val })}
                  label="Data da Compra"
                  helperText="Digite ou selecione no calendário"
                />

                <DatePickerWithInput
                  value={editingTx.dataPagamento || editingTx.data}
                  onChange={val => setEditingTx({ ...editingTx, dataPagamento: val })}
                  label="Data de Pagamento / Fatura"
                  helperText="Digite ou selecione no calendário"
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

            <div className="flex items-center justify-end gap-3 pt-2">
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
                  showToast('Lançamento atualizado com sucesso.');
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
