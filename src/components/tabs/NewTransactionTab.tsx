import React, { useState } from 'react';
import { useFinance } from '../../context/FinanceContext';
import { TransactionType, TransactionStatus, TransactionScenario } from '../../types/finance';
import { PlusCircle, CheckCircle2, ArrowRightLeft, CreditCard } from 'lucide-react';

export const NewTransactionTab: React.FC = () => {
  const { categories, accounts, cards, addTransaction, setActiveTab } = useFinance();

  const [tipo, setTipo] = useState<TransactionType>('Despesa');
  const [conta, setConta] = useState<string>(accounts[0] || 'Conta Corrente');
  const [contaDestino, setContaDestino] = useState<string>(accounts[1] || 'Poupança');
  const [categoria, setCategoria] = useState<string>(categories[0] || 'Alimentação');
  const [descricao, setDescricao] = useState<string>('');
  const [valor, setValor] = useState<string>('');
  const [data, setData] = useState<string>(new Date().toISOString().slice(0, 10));
  const [parcelasCount, setParcelasCount] = useState<number>(1);
  const [modoValor, setModoValor] = useState<string>('À vista');
  const [status, setStatus] = useState<TransactionStatus>('Efetivado');
  const [cenario, setCenario] = useState<TransactionScenario>('Efetivado');
  const [submittedMessage, setSubmittedMessage] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const numValor = parseFloat(valor.replace(',', '.'));
    if (isNaN(numValor) || numValor <= 0) {
      alert('Por favor, informe um valor numérico válido.');
      return;
    }
    if (!descricao.trim()) {
      alert('Por favor, informe uma descrição para o lançamento.');
      return;
    }

    if (parcelasCount > 1) {
      const valorParcela = numValor / parcelasCount;
      const baseDate = new Date(data);
      for (let i = 0; i < parcelasCount; i++) {
        const pDate = new Date(baseDate);
        pDate.setMonth(pDate.getMonth() + i);
        addTransaction({
          tipo,
          conta,
          contaDestino: tipo === 'Transferência' ? contaDestino : undefined,
          categoria,
          descricao: `${descricao} (${i + 1}/${parcelasCount})`,
          valor: Math.round(valorParcela * 100) / 100,
          data: pDate.toISOString().slice(0, 10),
          parcelas: `${i + 1}/${parcelasCount}`,
          modoValor: 'A prazo',
          status: i === 0 ? status : 'Orçado',
          cenario
        });
      }
    } else {
      addTransaction({
        tipo,
        conta,
        contaDestino: tipo === 'Transferência' ? contaDestino : undefined,
        categoria,
        descricao,
        valor: numValor,
        data,
        parcelas: '1/1',
        modoValor,
        status,
        cenario
      });
    }

    setSubmittedMessage('Lançamento adicionado com sucesso!');
    setDescricao('');
    setValor('');
    setTimeout(() => {
      setSubmittedMessage(null);
    }, 4000);
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <span>➕ Novo Cadastro Financeiro</span>
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          Registre despesas, receitas ou transferências entre contas e cartões com suporte a parcelamento inteligente.
        </p>
      </div>

      {submittedMessage && (
        <div className="p-4 bg-emerald-500/15 border border-emerald-500/30 rounded-2xl flex items-center justify-between text-emerald-400 text-sm">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 shrink-0" />
            <span>{submittedMessage}</span>
          </div>
          <button
            onClick={() => setActiveTab('lancamentos')}
            className="text-xs font-bold underline hover:text-emerald-300"
          >
            Ver em Lançamentos →
          </button>
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-5">
        {/* Type selector pill buttons */}
        <div>
          <label className="block text-xs uppercase font-semibold text-slate-400 mb-2">
            Tipo de Movimentação
          </label>
          <div className="grid grid-cols-3 gap-2">
            {(['Despesa', 'Receita', 'Transferência'] as TransactionType[]).map(t => (
              <button
                key={t}
                type="button"
                onClick={() => setTipo(t)}
                className={`py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all ${
                  tipo === t
                    ? t === 'Receita'
                      ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 shadow-sm'
                      : t === 'Despesa'
                      ? 'bg-rose-500/20 text-rose-400 border border-rose-500/40 shadow-sm'
                      : 'bg-sky-500/20 text-sky-400 border border-sky-500/40 shadow-sm'
                    : 'bg-slate-950/60 text-slate-400 hover:text-white border border-slate-800'
                }`}
              >
                {t}
              </button>
            ))}
          </div>
        </div>

        {/* Description & Value */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs uppercase font-semibold text-slate-400 mb-1.5">
              Descrição
            </label>
            <input
              type="text"
              placeholder="Ex: Supermercado Pão de Açúcar, Salário, etc."
              value={descricao}
              onChange={e => setDescricao(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
              required
            />
          </div>

          <div>
            <label className="block text-xs uppercase font-semibold text-slate-400 mb-1.5">
              Valor Total (R$)
            </label>
            <input
              type="number"
              step="0.01"
              placeholder="0,00"
              value={valor}
              onChange={e => setValor(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-white font-mono placeholder-slate-500 focus:outline-none focus:border-emerald-500"
              required
            />
          </div>
        </div>

        {/* Account and Destination (if Transferência) */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs uppercase font-semibold text-slate-400 mb-1.5">
              {tipo === 'Transferência' ? 'Conta de Origem' : 'Conta / Cartão'}
            </label>
            <select
              value={conta}
              onChange={e => setConta(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500"
            >
              {accounts.map(a => (
                <option key={a} value={a}>
                  {a}
                </option>
              ))}
            </select>
          </div>

          {tipo === 'Transferência' ? (
            <div>
              <label className="block text-xs uppercase font-semibold text-slate-400 mb-1.5">
                Conta de Destino
              </label>
              <select
                value={contaDestino}
                onChange={e => setContaDestino(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500"
              >
                {accounts.map(a => (
                  <option key={a} value={a}>
                    {a}
                  </option>
                ))}
              </select>
            </div>
          ) : (
            <div>
              <label className="block text-xs uppercase font-semibold text-slate-400 mb-1.5">
                Categoria
              </label>
              <select
                value={categoria}
                onChange={e => setCategoria(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500"
              >
                {categories.map(c => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        {/* Date & Installments */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs uppercase font-semibold text-slate-400 mb-1.5">
              Data de Competência
            </label>
            <input
              type="date"
              value={data}
              onChange={e => setData(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-white font-mono focus:outline-none focus:border-emerald-500"
              required
            />
          </div>

          <div>
            <label className="block text-xs uppercase font-semibold text-slate-400 mb-1.5">
              Parcelas
            </label>
            <select
              value={parcelasCount}
              onChange={e => setParcelasCount(parseInt(e.target.value, 10))}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500"
            >
              {Array.from({ length: 24 }, (_, i) => i + 1).map(num => (
                <option key={num} value={num}>
                  {num === 1 ? '1x (À vista)' : `${num}x`}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs uppercase font-semibold text-slate-400 mb-1.5">
              Status Inicial
            </label>
            <select
              value={status}
              onChange={e => setStatus(e.target.value as any)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500"
            >
              <option value="Efetivado">Efetivado (Liquidado)</option>
              <option value="Orçado">Orçado (Budget Previsto)</option>
            </select>
          </div>
        </div>

        {/* Submit button */}
        <div className="pt-2 flex justify-end">
          <button
            type="submit"
            className="flex items-center gap-2 px-6 py-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-sm font-semibold transition-all shadow-lg shadow-emerald-600/25 active:scale-95"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Salvar Lançamento</span>
          </button>
        </div>
      </form>
    </div>
  );
};
