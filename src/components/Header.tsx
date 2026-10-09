import React from 'react';
import { useFinance } from '../context/FinanceContext';
import { Menu, PlusCircle, RotateCcw, Wallet, ArrowDownRight, ArrowUpRight } from 'lucide-react';

interface HeaderProps {
  onToggleSidebar: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onToggleSidebar }) => {
  const { transactions, setActiveTab, resetToSample } = useFinance();

  const totalReceitas = transactions
    .filter(t => t.tipo === 'Receita')
    .reduce((acc, t) => acc + t.valor, 0);

  const totalDespesas = transactions
    .filter(t => t.tipo === 'Despesa')
    .reduce((acc, t) => acc + t.valor, 0);

  const saldoLiquido = totalReceitas - totalDespesas;

  const formatBRL = (val: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(val);
  };

  return (
    <header className="sticky top-0 z-30 bg-slate-900/80 backdrop-blur-md border-b border-slate-800 px-4 lg:px-8 py-3.5 flex items-center justify-between gap-4">
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleSidebar}
          className="lg:hidden p-2 text-slate-300 hover:text-white rounded-lg hover:bg-slate-800 border border-slate-700/60"
          aria-label="Abrir Menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="hidden sm:flex items-center gap-2 text-sm text-slate-400">
          <span className="font-semibold text-slate-200">Fluxo Financeiro Profissional</span>
          <span>•</span>
          <span className="text-emerald-400 font-medium">Análise Quantitativa Ativa</span>
        </div>
      </div>

      {/* Mini Snapshot KPIs in header */}
      <div className="flex items-center gap-3 md:gap-5">
        <div className="hidden md:flex items-center gap-4 text-xs bg-slate-950/70 border border-slate-800/80 px-3 py-1.5 rounded-xl">
          <div className="flex items-center gap-1.5 text-emerald-400">
            <ArrowUpRight className="w-3.5 h-3.5" />
            <span className="text-slate-400">Rec:</span>
            <span className="font-semibold">{formatBRL(totalReceitas)}</span>
          </div>
          <div className="w-px h-3 bg-slate-800" />
          <div className="flex items-center gap-1.5 text-rose-400">
            <ArrowDownRight className="w-3.5 h-3.5" />
            <span className="text-slate-400">Desp:</span>
            <span className="font-semibold">{formatBRL(totalDespesas)}</span>
          </div>
          <div className="w-px h-3 bg-slate-800" />
          <div className="flex items-center gap-1.5">
            <Wallet className="w-3.5 h-3.5 text-sky-400" />
            <span className="text-slate-400">Saldo:</span>
            <span className={`font-semibold ${saldoLiquido >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
              {formatBRL(saldoLiquido)}
            </span>
          </div>
        </div>

        <button
          onClick={() => setActiveTab('cadastro')}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs sm:text-sm font-semibold transition-all shadow-md shadow-emerald-600/20 active:scale-95"
        >
          <PlusCircle className="w-4 h-4" />
          <span>Novo Lançamento</span>
        </button>

        <button
          onClick={() => {
            if (confirm('Deseja recarregar a base de demonstração do Fluxo 106?')) {
              resetToSample();
            }
          }}
          title="Restaurar dados padrão de demonstração"
          className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-xl border border-slate-800 transition-colors"
        >
          <RotateCcw className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};
