import React, { useState } from 'react';
import { useFinance } from '../../context/FinanceContext';
import { CreditCard as CreditCardType } from '../../types/finance';
import { CreditCard, Plus, Calendar, AlertCircle, Trash2 } from 'lucide-react';

export const CreditCardsTab: React.FC = () => {
  const { cards, addCard, removeCard, transactions } = useFinance();

  const [nome, setNome] = useState('');
  const [limite, setLimite] = useState('');
  const [fechamento, setFechamento] = useState('5');
  const [vencimento, setVencimento] = useState('12');

  const formatBRL = (val: number) =>
    new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);

  const handleAddCard = (e: React.FormEvent) => {
    e.preventDefault();
    const numLim = parseFloat(limite.replace(',', '.'));
    if (!nome.trim() || isNaN(numLim) || numLim <= 0) {
      alert('Informe o nome e um limite válido.');
      return;
    }
    addCard({
      nome: nome.trim(),
      limite: numLim,
      fechamento: parseInt(fechamento, 10),
      vencimento: parseInt(vencimento, 10)
    });
    setNome('');
    setLimite('');
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <span>💳 Gestão de Cartões de Crédito</span>
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          Acompanhe limites operacionais, datas de fechamento e vencimento de faturas com sincronização automática de fluxo orçado.
        </p>
      </div>

      {/* Cards List Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {cards.map(card => {
          // Calculate utilized balance for this card
          const cardExpenses = transactions
            .filter(t => t.conta === card.nome && t.tipo === 'Despesa')
            .reduce((acc, t) => acc + t.valor, 0);

          const pctUsed = Math.min(100, (cardExpenses / (card.limite || 1)) * 100);
          const available = Math.max(0, card.limite - cardExpenses);

          return (
            <div
              key={card.nome}
              className="bg-gradient-to-br from-slate-900 to-slate-950 border border-slate-800 rounded-3xl p-6 relative overflow-hidden shadow-xl"
            >
              {/* Background Glow */}
              <div className="absolute -right-8 -top-8 w-32 h-32 bg-emerald-500/10 rounded-full blur-2xl pointer-events-none" />

              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <CreditCard className="w-5 h-5 text-emerald-400" />
                  <span className="font-bold text-white text-base">{card.nome}</span>
                </div>
                <button
                  onClick={() => {
                    if (confirm(`Remover cartão ${card.nome}?`)) {
                      removeCard(card.nome);
                    }
                  }}
                  className="text-slate-400 hover:text-rose-400 transition-colors p-1"
                  title="Remover Cartão"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>

              {/* Limit numbers */}
              <div className="space-y-2 mb-5">
                <div className="flex items-baseline justify-between">
                  <span className="text-xs text-slate-400 uppercase font-semibold">Limite Total</span>
                  <span className="text-base font-bold text-white font-mono">{formatBRL(card.limite)}</span>
                </div>
                <div className="flex items-baseline justify-between text-xs">
                  <span className="text-slate-400">Gasto Atual:</span>
                  <span className="text-rose-400 font-mono font-semibold">{formatBRL(cardExpenses)}</span>
                </div>
                <div className="flex items-baseline justify-between text-xs">
                  <span className="text-slate-400">Disponível:</span>
                  <span className="text-emerald-400 font-mono font-semibold">{formatBRL(available)}</span>
                </div>

                {/* Progress bar */}
                <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden mt-3">
                  <div
                    className={`h-full rounded-full transition-all ${
                      pctUsed > 85 ? 'bg-rose-500' : pctUsed > 60 ? 'bg-amber-500' : 'bg-emerald-500'
                    }`}
                    style={{ width: `${pctUsed}%` }}
                  />
                </div>
                <div className="text-[11px] text-right text-slate-400 font-mono">
                  {pctUsed.toFixed(1)}% utilizado
                </div>
              </div>

              {/* Invoice dates */}
              <div className="grid grid-cols-2 gap-3 pt-3 border-t border-slate-800/80 text-xs text-slate-400">
                <div className="flex items-center gap-2 bg-slate-950/60 p-2.5 rounded-xl border border-slate-800/60">
                  <Calendar className="w-3.5 h-3.5 text-sky-400" />
                  <div>
                    <div className="text-[10px] uppercase font-semibold">Fechamento</div>
                    <div className="text-white font-bold font-mono">Dia {card.fechamento}</div>
                  </div>
                </div>

                <div className="flex items-center gap-2 bg-slate-950/60 p-2.5 rounded-xl border border-slate-800/60">
                  <Calendar className="w-3.5 h-3.5 text-amber-400" />
                  <div>
                    <div className="text-[10px] uppercase font-semibold">Vencimento</div>
                    <div className="text-white font-bold font-mono">Dia {card.vencimento}</div>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Add new card form */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 max-w-xl">
        <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
          <Plus className="w-4 h-4 text-emerald-400" />
          <span>Cadastrar Novo Cartão</span>
        </h3>

        <form onSubmit={handleAddCard} className="space-y-4 text-xs">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-slate-400 mb-1">Nome / Emissor</label>
              <input
                type="text"
                placeholder="Ex: C6 Bank, Itaú..."
                value={nome}
                onChange={e => setNome(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white"
                required
              />
            </div>

            <div>
              <label className="block text-slate-400 mb-1">Limite (R$)</label>
              <input
                type="number"
                step="100"
                placeholder="4000.00"
                value={limite}
                onChange={e => setLimite(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white font-mono"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-slate-400 mb-1">Dia de Fechamento</label>
              <select
                value={fechamento}
                onChange={e => setFechamento(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white"
              >
                {Array.from({ length: 31 }, (_, i) => i + 1).map(d => (
                  <option key={d} value={d}>
                    Dia {d}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-slate-400 mb-1">Dia de Vencimento</label>
              <select
                value={vencimento}
                onChange={e => setVencimento(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white"
              >
                {Array.from({ length: 31 }, (_, i) => i + 1).map(d => (
                  <option key={d} value={d}>
                    Dia {d}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="pt-2 flex justify-end">
            <button
              type="submit"
              className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl font-semibold shadow-md shadow-emerald-600/20"
            >
              Adicionar Cartão
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
