export type TransactionType = 'Receita' | 'Despesa' | 'Transferência';
export type TransactionStatus = 'Efetivado' | 'Orçado';
export type TransactionScenario = 'Efetivado' | 'Budget' | 'Otimista' | 'Pessimista';

export interface Transaction {
  id: string;
  tipo: TransactionType;
  conta: string;
  contaDestino?: string;
  categoria: string;
  descricao: string;
  valor: number;
  data: string; // YYYY-MM-DD (Data da Compra / Competência)
  dataPagamento?: string; // YYYY-MM-DD (Data de Pagamento / Vencimento da Fatura)
  parcelas: string; // e.g. "1/1", "1/12"
  modoValor: string; // "À vista" | "A prazo"
  status: TransactionStatus;
  cenario: TransactionScenario;
}

export interface CreditCard {
  nome: string;
  limite: number;
  fechamento: number; // day of month (1-31)
  vencimento: number; // day of month (1-31)
}

export type TabKey =
  | 'dashboard'
  | 'norm_dist'
  | 'auditoria'
  | 'adv_analytics'
  | 'adv_kpis_2'
  | 'statistics'
  | 'graphics'
  | 'financial_analysis'
  | 'ia_analysis'
  | 'ai_assistant'
  | 'lancamentos'
  | 'cadastro'
  | 'cadastro_cat_contas'
  | 'cartoes'
  | 'backup';
