/**
 * Utilitários para cálculo de faturas, fechamento e vencimento de cartões de crédito.
 */

export interface CalculoFaturaResult {
  dataVencimento: string; // YYYY-MM-DD
  aposFechamento: boolean;
  mesCiclo: string; // YYYY-MM
  diasAteFechamento: number;
}

/**
 * Retorna o último dia de um determinado mês e ano.
 */
export function diasNoMes(ano: number, mes: number): number {
  return new Date(ano, mes, 0).getDate();
}

/**
 * Calcula a data de vencimento da fatura com base no dia de fechamento e dia de vencimento.
 * 
 * Regra:
 * - Se a compra for feita até o dia do fechamento: entra na fatura do ciclo atual.
 * - Se a compra for feita após o dia do fechamento: o fechamento já ocorreu (melhor dia de compra),
 *   portanto entra na fatura do ciclo seguinte (+1 mês).
 * - Se o dia de vencimento <= dia de fechamento: o vencimento ocorre no mês seguinte ao fechamento.
 * - Suporta offset para parcelas (0 para a 1ª parcela, 1 para a 2ª, etc.).
 */
export function calcularVencimentoFatura(
  dataCompraStr: string,
  fechamento: number,
  vencimento: number,
  parcelaOffset: number = 0
): CalculoFaturaResult {
  // Parsing seguro de data YYYY-MM-DD
  const partes = dataCompraStr.split('-');
  const anoCompra = parseInt(partes[0], 10);
  const mesCompra = parseInt(partes[1], 10); // 1-12
  const diaCompra = parseInt(partes[2], 10);

  const aposFechamento = diaCompra > fechamento;

  let mesesAdicionais = parcelaOffset;

  // Se comprou após o fechamento, joga para a fatura do mês seguinte
  if (aposFechamento) {
    mesesAdicionais += 1;
  }

  // Se o vencimento é menor ou igual ao fechamento (ex: fecha dia 25 e vence dia 5 do mês seguinte)
  if (vencimento <= fechamento) {
    mesesAdicionais += 1;
  }

  // Calcula ano e mês finais de vencimento
  let mesFinal = mesCompra + mesesAdicionais;
  let anoFinal = anoCompra;

  while (mesFinal > 12) {
    mesFinal -= 12;
    anoFinal += 1;
  }
  while (mesFinal < 1) {
    mesFinal += 12;
    anoFinal -= 1;
  }

  // Garante que o dia não passe do limite do mês final (ex: fevereiro)
  const maxDiasMesFinal = diasNoMes(anoFinal, mesFinal);
  const diaFinal = Math.min(vencimento, maxDiasMesFinal);

  const strAno = anoFinal.toString();
  const strMes = mesFinal.toString().padStart(2, '0');
  const strDia = diaFinal.toString().padStart(2, '0');

  const dataVencimento = `${strAno}-${strMes}-${strDia}`;
  const mesCiclo = `${strAno}-${strMes}`;

  const diasAteFechamento = fechamento - diaCompra;

  return {
    dataVencimento,
    aposFechamento,
    mesCiclo,
    diasAteFechamento
  };
}
