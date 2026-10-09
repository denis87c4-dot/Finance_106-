import React, { createContext, useContext, useState, useEffect } from 'react';
import { Transaction, CreditCard, TabKey } from '../types/finance';
import {
  INITIAL_CATEGORIES,
  INITIAL_ACCOUNTS,
  INITIAL_CARDS,
  INITIAL_TRANSACTIONS
} from '../utils/sampleData';

interface FinanceContextType {
  transactions: Transaction[];
  categories: string[];
  accounts: string[];
  cards: CreditCard[];
  activeTab: TabKey;
  setActiveTab: (tab: TabKey) => void;
  addTransaction: (tx: Omit<Transaction, 'id'>) => void;
  updateTransaction: (id: string, tx: Partial<Transaction>) => void;
  deleteTransaction: (id: string) => void;
  deleteMultipleTransactions: (ids: string[]) => void;
  addCategory: (name: string) => void;
  removeCategory: (name: string) => void;
  addAccount: (name: string) => void;
  removeAccount: (name: string) => void;
  addCard: (card: CreditCard) => void;
  removeCard: (name: string) => void;
  resetToSample: () => void;
  clearAll: () => void;
  importData: (imported: {
    lancamentos?: any[];
    categories?: string[];
    categorias?: string[];
    accounts?: string[];
    contas?: string[];
    cards?: CreditCard[];
    cartoes?: CreditCard[];
  }) => void;
}

const FinanceContext = createContext<FinanceContextType | undefined>(undefined);

const STORAGE_KEY_TX = 'finance106_transactions_v1';
const STORAGE_KEY_CAT = 'finance106_categories_v1';
const STORAGE_KEY_ACC = 'finance106_accounts_v1';
const STORAGE_KEY_CARDS = 'finance106_cards_v1';

export const FinanceProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [activeTab, setActiveTab] = useState<TabKey>('dashboard');

  const [transactions, setTransactions] = useState<Transaction[]>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY_TX);
      if (saved) return JSON.parse(saved);
    } catch (e) {
      console.error(e);
    }
    return INITIAL_TRANSACTIONS;
  });

  const [categories, setCategories] = useState<string[]>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY_CAT);
      if (saved) return JSON.parse(saved);
    } catch (e) {
      console.error(e);
    }
    return INITIAL_CATEGORIES;
  });

  const [accounts, setAccounts] = useState<string[]>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY_ACC);
      if (saved) return JSON.parse(saved);
    } catch (e) {
      console.error(e);
    }
    return INITIAL_ACCOUNTS;
  });

  const [cards, setCards] = useState<CreditCard[]>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY_CARDS);
      if (saved) return JSON.parse(saved);
    } catch (e) {
      console.error(e);
    }
    return INITIAL_CARDS;
  });

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY_TX, JSON.stringify(transactions));
    } catch (e) {
      console.error(e);
    }
  }, [transactions]);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY_CAT, JSON.stringify(categories));
    } catch (e) {
      console.error(e);
    }
  }, [categories]);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY_ACC, JSON.stringify(accounts));
    } catch (e) {
      console.error(e);
    }
  }, [accounts]);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY_CARDS, JSON.stringify(cards));
    } catch (e) {
      console.error(e);
    }
  }, [cards]);

  const addTransaction = (tx: Omit<Transaction, 'id'>) => {
    const newTx: Transaction = {
      ...tx,
      id: 'tx-' + Date.now() + '-' + Math.random().toString(36).substring(2, 6)
    };
    setTransactions(prev => [newTx, ...prev]);
  };

  const updateTransaction = (id: string, updated: Partial<Transaction>) => {
    setTransactions(prev =>
      prev.map(item => (item.id === id ? { ...item, ...updated } : item))
    );
  };

  const deleteTransaction = (id: string) => {
    setTransactions(prev => prev.filter(item => item.id !== id));
  };

  const deleteMultipleTransactions = (ids: string[]) => {
    const idSet = new Set(ids);
    setTransactions(prev => prev.filter(item => !idSet.has(item.id)));
  };

  const addCategory = (name: string) => {
    const clean = name.trim();
    if (clean && !categories.includes(clean)) {
      setCategories(prev => [...prev, clean]);
    }
  };

  const removeCategory = (name: string) => {
    setCategories(prev => prev.filter(c => c !== name));
  };

  const addAccount = (name: string) => {
    const clean = name.trim();
    if (clean && !accounts.includes(clean)) {
      setAccounts(prev => [...prev, clean]);
    }
  };

  const removeAccount = (name: string) => {
    setAccounts(prev => prev.filter(a => a !== name));
  };

  const addCard = (card: CreditCard) => {
    setCards(prev => [...prev.filter(c => c.nome !== card.nome), card]);
    if (!accounts.includes(card.nome)) {
      setAccounts(prev => [...prev, card.nome]);
    }
  };

  const removeCard = (name: string) => {
    setCards(prev => prev.filter(c => c.nome !== name));
  };

  const resetToSample = () => {
    setTransactions(INITIAL_TRANSACTIONS);
    setCategories(INITIAL_CATEGORIES);
    setAccounts(INITIAL_ACCOUNTS);
    setCards(INITIAL_CARDS);
  };

  const clearAll = () => {
    setTransactions([]);
  };

  const importData = (imported: any) => {
    if (imported.lancamentos && Array.isArray(imported.lancamentos)) {
      const formatted: Transaction[] = imported.lancamentos.map((l: any, idx: number) => ({
        id: l.id || `imp-${Date.now()}-${idx}`,
        tipo: l.Tipo || l.tipo || 'Despesa',
        conta: l.Conta || l.conta || 'Conta Corrente',
        contaDestino: l['Conta Destino'] || l.contaDestino || '',
        categoria: l.Categoria || l.categoria || 'Outros',
        descricao: l.Descrição || l.descricao || 'Sem descrição',
        valor: Math.abs(Number(l.Valor || l.valor || 0)),
        data: (l.Data || l.data || new Date().toISOString().split('T')[0]).substring(0, 10),
        parcelas: l.Parcelas || l.parcelas || '1/1',
        modoValor: l['Modo Valor'] || l.modoValor || 'À vista',
        status: (l.Status || l.status || 'Efetivado') as any,
        cenario: (l.Cenario || l.cenario || 'Efetivado') as any
      }));
      setTransactions(formatted);
    }
    if (imported.categorias || imported.categories) {
      setCategories(imported.categorias || imported.categories);
    }
    if (imported.contas || imported.accounts) {
      setAccounts(imported.contas || imported.accounts);
    }
    if (imported.cartoes || imported.cards) {
      setCards(imported.cartoes || imported.cards);
    }
  };

  return (
    <FinanceContext.Provider
      value={{
        transactions,
        categories,
        accounts,
        cards,
        activeTab,
        setActiveTab,
        addTransaction,
        updateTransaction,
        deleteTransaction,
        deleteMultipleTransactions,
        addCategory,
        removeCategory,
        addAccount,
        removeAccount,
        addCard,
        removeCard,
        resetToSample,
        clearAll,
        importData
      }}
    >
      {children}
    </FinanceContext.Provider>
  );
};

export const useFinance = () => {
  const context = useContext(FinanceContext);
  if (!context) {
    throw new Error('useFinance must be used within FinanceProvider');
  }
  return context;
};
