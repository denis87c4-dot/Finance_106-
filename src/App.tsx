import React, { useState } from 'react';
import { FinanceProvider, useFinance } from './context/FinanceContext';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { DashboardTab } from './components/tabs/DashboardTab';
import { NormalDistTab } from './components/tabs/NormalDistTab';
import { AdvancedKpis2Tab } from './components/tabs/AdvancedKpis2Tab';
import { AdvancedAnalyticsTab } from './components/tabs/AdvancedAnalyticsTab';
import { AuditTab } from './components/tabs/AuditTab';
import { StatisticsTab } from './components/tabs/StatisticsTab';
import { GraphicsTab } from './components/tabs/GraphicsTab';
import { TransactionsTab } from './components/tabs/TransactionsTab';
import { NewTransactionTab } from './components/tabs/NewTransactionTab';
import { CategoriesAccountsTab } from './components/tabs/CategoriesAccountsTab';
import { CreditCardsTab } from './components/tabs/CreditCardsTab';
import { AiAssistantTab } from './components/tabs/AiAssistantTab';
import { IaAnalysisTab } from './components/tabs/IaAnalysisTab';
import { BackupSecurityTab } from './components/tabs/BackupSecurityTab';

const MainContent: React.FC = () => {
  const { activeTab } = useFinance();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const renderActiveTab = () => {
    switch (activeTab) {
      case 'dashboard':
        return <DashboardTab />;
      case 'norm_dist':
        return <NormalDistTab />;
      case 'adv_kpis_2':
        return <AdvancedKpis2Tab />;
      case 'adv_analytics':
        return <AdvancedAnalyticsTab />;
      case 'auditoria':
        return <AuditTab />;
      case 'statistics':
        return <StatisticsTab />;
      case 'ia_analysis':
        return <IaAnalysisTab />;
      case 'graphics':
      case 'financial_analysis':
        return <GraphicsTab />;
      case 'lancamentos':
        return <TransactionsTab />;
      case 'cadastro':
        return <NewTransactionTab />;
      case 'cadastro_cat_contas':
        return <CategoriesAccountsTab />;
      case 'cartoes':
        return <CreditCardsTab />;
      case 'ai_assistant':
        return <AiAssistantTab />;
      case 'backup':
        return <BackupSecurityTab />;
      default:
        return <DashboardTab />;
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex">
      {/* Sidebar Navigation */}
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Main Container */}
      <div className="flex-1 lg:pl-72 flex flex-col min-w-0">
        <Header onToggleSidebar={() => setSidebarOpen(prev => !prev)} />
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          {renderActiveTab()}
        </main>
      </div>
    </div>
  );
};

export default function App() {
  return (
    <FinanceProvider>
      <MainContent />
    </FinanceProvider>
  );
}
