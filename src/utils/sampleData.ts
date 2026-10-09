import { Transaction, CreditCard } from '../types/finance';

export const INITIAL_CATEGORIES = [
  'Alimentação',
  'Transporte',
  'Moradia',
  'Salário',
  'Lazer',
  'Investimentos',
  'Saúde',
  'Educação',
  'Serviços',
  'Fatura Cartão',
  'Outros'
];

export const INITIAL_ACCOUNTS = [
  'Conta Corrente',
  'Carteira',
  'Cartão de Crédito',
  'Poupança',
  'Investimentos XP',
  'Nubank',
  'Inter'
];

export const INITIAL_CARDS: CreditCard[] = [
  {
    nome: 'Nubank',
    limite: 5000.0,
    fechamento: 5,
    vencimento: 12
  },
  {
    nome: 'Inter',
    limite: 3000.0,
    fechamento: 10,
    vencimento: 17
  }
];

export const INITIAL_TRANSACTIONS: Transaction[] = [
  {
    id: 'tx-1',
    tipo: 'Receita',
    conta: 'Conta Corrente',
    categoria: 'Salário',
    descricao: 'Salário Mensal Corporativo',
    valor: 7500.0,
    data: '2026-09-05',
    parcelas: '1/1',
    modoValor: 'À vista',
    status: 'Efetivado',
    cenario: 'Efetivado'
  },
  {
    id: 'tx-2',
    tipo: 'Receita',
    conta: 'Inter',
    categoria: 'Investimentos',
    descricao: 'Dividendos FIIs & Ações',
    valor: 640.5,
    data: '2026-09-15',
    parcelas: '1/1',
    modoValor: 'À vista',
    status: 'Efetivado',
    cenario: 'Efetivado'
  },
  {
    id: 'tx-3',
    tipo: 'Receita',
    conta: 'Conta Corrente',
    categoria: 'Salário',
    descricao: 'Consultoria Financeira PJ Freelance',
    valor: 2200.0,
    data: '2026-09-20',
    parcelas: '1/1',
    modoValor: 'À vista',
    status: 'Efetivado',
    cenario: 'Efetivado'
  },
  {
    id: 'tx-4',
    tipo: 'Despesa',
    conta: 'Conta Corrente',
    categoria: 'Moradia',
    descricao: 'Aluguel & Condomínio',
    valor: 2400.0,
    data: '2026-09-08',
    parcelas: '1/1',
    modoValor: 'À vista',
    status: 'Efetivado',
    cenario: 'Efetivado'
  },
  {
    id: 'tx-5',
    tipo: 'Despesa',
    conta: 'Nubank',
    categoria: 'Alimentação',
    descricao: 'Supermercado Pão de Açúcar',
    valor: 680.4,
    data: '2026-09-10',
    parcelas: '1/1',
    modoValor: 'À vista',
    status: 'Efetivado',
    cenario: 'Efetivado'
  },
  {
    id: 'tx-6',
    tipo: 'Despesa',
    conta: 'Nubank',
    categoria: 'Transporte',
    descricao: 'Combustível Posto Shell',
    valor: 290.0,
    data: '2026-09-12',
    parcelas: '1/1',
    modoValor: 'À vista',
    status: 'Efetivado',
    cenario: 'Efetivado'
  },
  {
    id: 'tx-7',
    tipo: 'Despesa',
    conta: 'Nubank',
    categoria: 'Lazer',
    descricao: 'Jantar Restaurante Cantina',
    valor: 240.0,
    data: '2026-09-14',
    parcelas: '1/1',
    modoValor: 'À vista',
    status: 'Efetivado',
    cenario: 'Efetivado'
  },
  {
    id: 'tx-8',
    tipo: 'Despesa',
    conta: 'Conta Corrente',
    categoria: 'Serviços',
    descricao: 'Energia Elétrica Enel',
    valor: 185.3,
    data: '2026-09-18',
    parcelas: '1/1',
    modoValor: 'À vista',
    status: 'Efetivado',
    cenario: 'Efetivado'
  },
  {
    id: 'tx-9',
    tipo: 'Despesa',
    conta: 'Nubank',
    categoria: 'Saúde',
    descricao: 'Farmácia Droga Raia',
    valor: 145.8,
    data: '2026-09-22',
    parcelas: '1/1',
    modoValor: 'À vista',
    status: 'Efetivado',
    cenario: 'Efetivado'
  },
  {
    id: 'tx-10',
    tipo: 'Despesa',
    conta: 'Inter',
    categoria: 'Educação',
    descricao: 'Curso Especialização Finanças Quant',
    valor: 450.0,
    data: '2026-09-25',
    parcelas: '1/3',
    modoValor: 'A prazo',
    status: 'Efetivado',
    cenario: 'Efetivado'
  },
  {
    id: 'tx-11',
    tipo: 'Receita',
    conta: 'Conta Corrente',
    categoria: 'Salário',
    descricao: 'Salário Mensal Corporativo',
    valor: 7500.0,
    data: '2026-10-05',
    parcelas: '1/1',
    modoValor: 'À vista',
    status: 'Efetivado',
    cenario: 'Efetivado'
  },
  {
    id: 'tx-12',
    tipo: 'Receita',
    conta: 'Inter',
    categoria: 'Investimentos',
    descricao: 'Rendimentos Tesouro Direto Selic',
    valor: 710.2,
    data: '2026-10-06',
    parcelas: '1/1',
    modoValor: 'À vista',
    status: 'Efetivado',
    cenario: 'Efetivado'
  },
  {
    id: 'tx-13',
    tipo: 'Despesa',
    conta: 'Conta Corrente',
    categoria: 'Moradia',
    descricao: 'Aluguel & Condomínio',
    valor: 2400.0,
    data: '2026-10-07',
    parcelas: '1/1',
    modoValor: 'À vista',
    status: 'Efetivado',
    cenario: 'Efetivado'
  },
  {
    id: 'tx-14',
    tipo: 'Despesa',
    conta: 'Nubank',
    categoria: 'Alimentação',
    descricao: 'Compras Feira & Supermercado',
    valor: 520.6,
    data: '2026-10-08',
    parcelas: '1/1',
    modoValor: 'À vista',
    status: 'Efetivado',
    cenario: 'Efetivado'
  },
  {
    id: 'tx-15',
    tipo: 'Despesa',
    conta: 'Nubank',
    categoria: 'Transporte',
    descricao: 'Uber e Recarga Bilhete',
    valor: 175.0,
    data: '2026-10-08',
    parcelas: '1/1',
    modoValor: 'À vista',
    status: 'Efetivado',
    cenario: 'Efetivado'
  },
  {
    id: 'tx-16',
    tipo: 'Despesa',
    conta: 'Inter',
    categoria: 'Lazer',
    descricao: 'Ingressos Concerto Cultural',
    valor: 210.0,
    data: '2026-10-08',
    parcelas: '1/1',
    modoValor: 'À vista',
    status: 'Efetivado',
    cenario: 'Efetivado'
  },
  {
    id: 'tx-17',
    tipo: 'Despesa',
    conta: 'Conta Corrente',
    categoria: 'Alimentação',
    descricao: 'Previsão de Supermercado 2ª Quinzena',
    valor: 650.0,
    data: '2026-10-20',
    parcelas: '1/1',
    modoValor: 'À vista',
    status: 'Orçado',
    cenario: 'Budget'
  },
  {
    id: 'tx-18',
    tipo: 'Despesa',
    conta: 'Nubank',
    categoria: 'Transporte',
    descricao: 'Previsão de Abastecimento',
    valor: 280.0,
    data: '2026-10-24',
    parcelas: '1/1',
    modoValor: 'À vista',
    status: 'Orçado',
    cenario: 'Budget'
  },
  {
    id: 'tx-19',
    tipo: 'Receita',
    conta: 'Conta Corrente',
    categoria: 'Salário',
    descricao: 'Previsão Bônus Trimestral',
    valor: 3500.0,
    data: '2026-10-28',
    parcelas: '1/1',
    modoValor: 'À vista',
    status: 'Orçado',
    cenario: 'Budget'
  }
];
