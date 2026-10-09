import React, { useState } from 'react';
import { useFinance } from '../../context/FinanceContext';
import { Tags, Wallet, Plus, Trash2 } from 'lucide-react';

export const CategoriesAccountsTab: React.FC = () => {
  const { categories, accounts, addCategory, removeCategory, addAccount, removeAccount, transactions } =
    useFinance();

  const [newCat, setNewCat] = useState('');
  const [newAcc, setNewAcc] = useState('');

  const handleAddCat = (e: React.FormEvent) => {
    e.preventDefault();
    if (newCat.trim()) {
      addCategory(newCat.trim());
      setNewCat('');
    }
  };

  const handleAddAcc = (e: React.FormEvent) => {
    e.preventDefault();
    if (newAcc.trim()) {
      addAccount(newAcc.trim());
      setNewAcc('');
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <span>🏷️ Cadastro de Categorias & Contas Bancárias</span>
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          Gerencie a taxonomia de classificação financeira e as contas de custódia e carteiras.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Categorias */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center gap-2">
            <Tags className="w-5 h-5 text-emerald-400" />
            <h3 className="text-base font-bold text-white">Categorias de Lançamento</h3>
          </div>

          <form onSubmit={handleAddCat} className="flex gap-2">
            <input
              type="text"
              placeholder="Nova categoria (ex: Assinaturas)..."
              value={newCat}
              onChange={e => setNewCat(e.target.value)}
              className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
            />
            <button
              type="submit"
              className="px-3 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-semibold flex items-center gap-1 shadow-md shadow-emerald-600/20"
            >
              <Plus className="w-4 h-4" />
              <span>Adicionar</span>
            </button>
          </form>

          <div className="divide-y divide-slate-800/60 max-h-96 overflow-y-auto pr-1">
            {categories.map(cat => {
              const txCount = transactions.filter(t => t.categoria === cat).length;
              return (
                <div key={cat} className="py-2.5 flex items-center justify-between text-xs">
                  <div>
                    <span className="text-white font-medium">{cat}</span>
                    <span className="text-[11px] text-slate-400 ml-2">({txCount} lançamentos)</span>
                  </div>
                  <button
                    onClick={() => {
                      if (confirm(`Remover categoria "${cat}"?`)) {
                        removeCategory(cat);
                      }
                    }}
                    className="p-1 text-slate-400 hover:text-rose-400 transition-colors"
                    title="Remover"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              );
            })}
          </div>
        </div>

        {/* Contas Bancárias */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center gap-2">
            <Wallet className="w-5 h-5 text-sky-400" />
            <h3 className="text-base font-bold text-white">Contas & Carteiras</h3>
          </div>

          <form onSubmit={handleAddAcc} className="flex gap-2">
            <input
              type="text"
              placeholder="Nova conta (ex: Banco do Brasil)..."
              value={newAcc}
              onChange={e => setNewAcc(e.target.value)}
              className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
            />
            <button
              type="submit"
              className="px-3 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-xl text-xs font-semibold flex items-center gap-1 shadow-md shadow-sky-600/20"
            >
              <Plus className="w-4 h-4" />
              <span>Adicionar</span>
            </button>
          </form>

          <div className="divide-y divide-slate-800/60 max-h-96 overflow-y-auto pr-1">
            {accounts.map(acc => {
              const txCount = transactions.filter(t => t.conta === acc).length;
              return (
                <div key={acc} className="py-2.5 flex items-center justify-between text-xs">
                  <div>
                    <span className="text-white font-medium">{acc}</span>
                    <span className="text-[11px] text-slate-400 ml-2">({txCount} lançamentos)</span>
                  </div>
                  <button
                    onClick={() => {
                      if (confirm(`Remover conta "${acc}"?`)) {
                        removeAccount(acc);
                      }
                    }}
                    className="p-1 text-slate-400 hover:text-rose-400 transition-colors"
                    title="Remover"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
