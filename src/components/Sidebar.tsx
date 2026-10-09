import React from 'react';
import { useFinance } from '../context/FinanceContext';
import { TabKey } from '../types/finance';
import {
  LayoutDashboard,
  LineChart,
  ShieldAlert,
  Sparkles,
  Zap,
  BarChart3,
  PieChart,
  TableProperties,
  PlusCircle,
  Tags,
  CreditCard as CreditCardIcon,
  Bot,
  Brain,
  Database,
  TrendingUp,
  X
} from 'lucide-react';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const { activeTab, setActiveTab, transactions } = useFinance();

  const navGroups: {
    title: string;
    items: { key: TabKey; label: string; icon: React.FC<{ className?: string }>; badge?: string }[];
  }[] = [
    {
      title: 'VISÃO GERAL & AUDITORIA',
      items: [
        { key: 'dashboard', label: 'Dashboard Geral', icon: LayoutDashboard },
        { key: 'auditoria', label: 'Auditoria Avançada', icon: ShieldAlert },
        { key: 'lancamentos', label: 'Lançamentos', icon: TableProperties, badge: `${transactions.length}` },
        { key: 'cadastro', label: 'Novo Cadastro', icon: PlusCircle }
      ]
    },
    {
      title: 'QUANTITATIVO & ESTATÍSTICA',
      items: [
        { key: 'ia_analysis', label: 'IA Analysis', icon: Brain, badge: 'OLS' },
        { key: 'norm_dist', label: 'Distribuição Normal', icon: LineChart },
        { key: 'adv_kpis_2', label: 'Advanced KPIs 2', icon: Zap },
        { key: 'adv_analytics', label: 'Advanced Analytics', icon: Sparkles },
        { key: 'statistics', label: 'Econometria & Estatística', icon: BarChart3 },
        { key: 'graphics', label: 'Gráficos Sofisticados', icon: PieChart }
      ]
    },
    {
      title: 'GESTÃO & CONFIGURAÇÃO',
      items: [
        { key: 'cartoes', label: 'Cartões de Crédito', icon: CreditCardIcon },
        { key: 'cadastro_cat_contas', label: 'Categorias & Contas', icon: Tags },
        { key: 'ai_assistant', label: 'IA & Gemini Assistant', icon: Bot },
        { key: 'backup', label: 'Backup & Segurança', icon: Database }
      ]
    }
  ];

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 w-72 bg-slate-900/95 border-r border-slate-800 flex flex-col transition-transform duration-300 ease-in-out lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand Header */}
        <div className="p-5 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-500/20">
              <TrendingUp className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-base text-white tracking-tight flex items-center gap-1.5">
                Fluxo 106 <span className="text-xs px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-mono font-medium">PRO</span>
              </h1>
              <p className="text-xs text-slate-400 font-medium">Gestão Financeira & Quant</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="lg:hidden p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation list */}
        <div className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
          {navGroups.map((group, idx) => (
            <div key={idx}>
              <h3 className="px-3 mb-2 text-[11px] font-semibold tracking-wider text-slate-400 uppercase">
                {group.title}
              </h3>
              <div className="space-y-1">
                {group.items.map(item => {
                  const Icon = item.icon;
                  const isActive = activeTab === item.key;
                  return (
                    <button
                      key={item.key}
                      onClick={() => {
                        setActiveTab(item.key);
                        onClose();
                      }}
                      className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                        isActive
                          ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 shadow-sm'
                          : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                      }`}
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-emerald-400' : 'text-slate-400'}`} />
                        <span className="truncate">{item.label}</span>
                      </div>
                      {item.badge && (
                        <span
                          className={`text-xs px-2 py-0.5 rounded-full font-mono ${
                            isActive
                              ? 'bg-emerald-500/30 text-emerald-300'
                              : 'bg-slate-800 text-slate-400'
                          }`}
                        >
                          {item.badge}
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        {/* Footer status */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/50">
          <div className="bg-slate-950/60 rounded-xl p-3 border border-slate-800/80">
            <div className="flex items-center justify-between text-xs text-slate-400">
              <span>Status Base:</span>
              <span className="flex items-center gap-1.5 text-emerald-400 font-medium">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                Operacional
              </span>
            </div>
            <div className="mt-2 text-[11px] text-slate-400">
              Finance 106 Engine • v2.4.0
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};
