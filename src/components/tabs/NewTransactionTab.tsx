import React, { useState, useEffect, useMemo } from 'react';
import { useFinance } from '../../context/FinanceContext';
import { TransactionType, TransactionStatus, TransactionScenario } from '../../types/finance';
import { calcularVencimentoFatura } from '../../utils/creditCardUtils';
import { DatePickerWithInput } from '../common/DatePickerWithInput';
import {
  PlusCircle,
  CheckCircle2,
  CreditCard as CreditCardIcon,
  Calendar,
  Layers,
  Sparkles,
  Info,
  RotateCcw,
  Clock,
  ArrowRight
} from 'lucide-react';

export const NewTransactionTab: React.FC = () => {
  const { categories, accounts, cards, addTransaction, setActiveTab } = useFinance();

  const [tipo, setTipo] = useState<TransactionType>('Despesa');
  const [conta, setConta] = useState<string>(accounts[0] || 'Conta Corrente');
  const [contaDestino, setContaDestino] = useState<string>(accounts[1] || 'Poupança');
  const [categoria, setCategoria] = useState<string>(categories[0] || 'Alimentação');
  const [descricao, setDescricao] = useState<string>('');
  const [valor, setValor] = useState<string>('');
  const [dataCompra, setDataCompra] = useState<string>(new Date().toISOString().slice(0, 10));
  const [dataPagamento, setDataPagamento] = useState<string>(new Date().toISOString().slice(0, 10));
  const [dataPagamentoManual, setDataPagamentoManual] = useState<boolean>(false);

  // Lançamentos Parcelados
  const [isParcelado, setIsParcelado] = useState<boolean>(false);
  const [numParcelas, setNumParcelas] = useState<number>(2);
  const [modoCalculoParcela, setModoCalculoParcela] = useState<'dividir' | 'replicar'>('dividir');

  const [status, setStatus] = useState<TransactionStatus>('Efetivado');
  const [cenario, setCenario] = useState<TransactionScenario>('Efetivado');
  const [submittedMessage, setSubmittedMessage] = useState<string | null>(null);

  const formatBRL = (val: number) =>
    new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);

  // Detecta se a conta selecionada é um cartão de crédito cadastrado
  const selectedCard = useMemo(() => {
    return cards.find(c => c.nome.toLowerCase() === conta.toLowerCase()) || null;
  }, [cards, conta]);

  // Cálculo automático da fatura do cartão com base no fechamento
  const calculoFatura = useMemo(() => {
    if (!selectedCard || !dataCompra) return null;
    return calcularVencimentoFatura(dataCompra, selectedCard.fechamento, selectedCard.vencimento, 0);
  }, [selectedCard, dataCompra]);

  // Atualiza automaticamente a Data de Pagamento quando a conta for cartão de crédito (se o usuário não tiver alterado manualmente)
  useEffect(() => {
    if (selectedCard && calculoFatura && !dataPagamentoManual) {
      setDataPagamento(calculoFatura.dataVencimento);
    } else if (!selectedCard && !dataPagamentoManual) {
      // Se não for cartão, a data de pagamento padrão é a data da compra
      setDataPagamento(dataCompra);
    }
  }, [selectedCard, calculoFatura, dataCompra, dataPagamentoManual]);

  // Recalcular data de pagamento com base no fechamento do cartão
  const handleRecalcularPeloCartao = () => {
    if (selectedCard && calculoFatura) {
      setDataPagamento(calculoFatura.dataVencimento);
      setDataPagamentoManual(false);
    }
  };

  // Cronograma detalhado de parcelas em tempo real
  const cronogramaParcelas = useMemo(() => {
    if (!isParcelado || numParcelas < 2) return [];
    const numValor = parseFloat(valor.replace(',', '.')) || 0;
    const valorParcela =
      modoCalculoParcela === 'dividir'
        ? (numValor > 0 ? numValor / numParcelas : 0)
        : numValor;

    return Array.from({ length: numParcelas }, (_, idx) => {
      let dataPgtoParcela = dataPagamento;
      let mesCiclo = '';
      let aposFechamento = false;

      if (selectedCard) {
        // Cada parcela subsequente avança um ciclo de fatura do cartão
        const info = calcularVencimentoFatura(
          dataCompra,
          selectedCard.fechamento,
          selectedCard.vencimento,
          idx
        );
        dataPgtoParcela = info.dataVencimento;
        mesCiclo = info.mesCiclo;
        aposFechamento = info.aposFechamento;
      } else {
        // Para contas normais, soma meses subsequentes
        const d = new Date(dataPagamento);
        d.setMonth(d.getMonth() + idx);
        dataPgtoParcela = d.toISOString().slice(0, 10);
      }

      return {
        numero: idx + 1,
        parcelaStr: `${idx + 1}/${numParcelas}`,
        valorParcela: Math.round(valorParcela * 100) / 100,
        dataCompra,
        dataPagamento: dataPgtoParcela,
        mesCiclo,
        aposFechamento
      };
    });
  }, [isParcelado, numParcelas, modoCalculoParcela, valor, dataCompra, dataPagamento, selectedCard]);

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

    if (isParcelado && numParcelas > 1) {
      const valorParcela =
        modoCalculoParcela === 'dividir' ? numValor / numParcelas : numValor;

      cronogramaParcelas.forEach((p, idx) => {
        addTransaction({
          tipo,
          conta,
          contaDestino: tipo === 'Transferência' ? contaDestino : undefined,
          categoria,
          descricao: `${descricao.trim()} (${p.parcelaStr})`,
          valor: Math.round(valorParcela * 100) / 100,
          data: dataCompra,
          dataPagamento: p.dataPagamento,
          parcelas: p.parcelaStr,
          modoValor: 'A prazo',
          status: idx === 0 ? status : 'Orçado',
          cenario
        });
      });

      const totalMsg =
        modoCalculoParcela === 'dividir'
          ? `dividida em ${numParcelas}x de ${formatBRL(valorParcela)}`
          : `com ${numParcelas}x parcelas replicadas de ${formatBRL(valorParcela)} (Total: ${formatBRL(valorParcela * numParcelas)})`;

      setSubmittedMessage(
        `Compra parcelada ${totalMsg} adicionada com sucesso! As parcelas foram agendadas conforme as faturas do cartão.`
      );
    } else {
      addTransaction({
        tipo,
        conta,
        contaDestino: tipo === 'Transferência' ? contaDestino : undefined,
        categoria,
        descricao: descricao.trim(),
        valor: numValor,
        data: dataCompra,
        dataPagamento: dataPagamento,
        parcelas: '1/1',
        modoValor: 'À vista',
        status,
        cenario
      });

      setSubmittedMessage('Lançamento adicionado com sucesso!');
    }

    setDescricao('');
    setValor('');
    setDataPagamentoManual(false);
    setTimeout(() => {
      setSubmittedMessage(null);
    }, 5000);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <span>➕ Novo Cadastro Financeiro</span>
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          Registre compras, receitas e transferências com gestão inteligente de parcelamento e fechamento de faturas de cartão.
        </p>
      </div>

      {submittedMessage && (
        <div className="p-4 bg-emerald-500/15 border border-emerald-500/30 rounded-2xl flex items-center justify-between text-emerald-400 text-sm animate-in fade-in">
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

      <form onSubmit={handleSubmit} className="bg-slate-900/90 border border-slate-800 rounded-3xl p-6 sm:p-7 shadow-xl space-y-6">
        {/* Tipo de Movimentação */}
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

        {/* Descrição e Valor */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs uppercase font-semibold text-slate-400 mb-1.5">
              Descrição do Lançamento
            </label>
            <input
              type="text"
              placeholder="Ex: Notebook Dell, Supermercado, Salário..."
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

        {/* Conta / Cartão e Categoria */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs uppercase font-semibold text-slate-400 mb-1.5 flex items-center justify-between">
              <span>{tipo === 'Transferência' ? 'Conta de Origem' : 'Conta / Cartão'}</span>
              {selectedCard && (
                <span className="text-[11px] text-emerald-400 font-mono font-medium flex items-center gap-1">
                  <CreditCardIcon className="w-3.5 h-3.5" />
                  Cartão Detectado
                </span>
              )}
            </label>
            <select
              value={conta}
              onChange={e => {
                setConta(e.target.value);
                setDataPagamentoManual(false);
              }}
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

        {/* ==================== CARTÃO DE CRÉDITO: PAINEL DE FECHAMENTO ==================== */}
        {selectedCard && calculoFatura && (
          <div className="p-4 bg-slate-950/80 border border-emerald-500/30 rounded-2xl space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
              <div className="flex items-center gap-2 font-bold text-white">
                <CreditCardIcon className="w-4 h-4 text-emerald-400" />
                <span>Regras de Fechamento do Cartão: {selectedCard.nome}</span>
              </div>
              <div className="flex items-center gap-3 text-slate-400 font-mono text-[11px]">
                <span>Fechamento: Dia <strong className="text-white">{selectedCard.fechamento}</strong></span>
                <span>•</span>
                <span>Vencimento: Dia <strong className="text-white">{selectedCard.vencimento}</strong></span>
              </div>
            </div>

            <div className="text-xs p-3 rounded-xl border flex items-start gap-2.5 leading-relaxed bg-slate-900/60 border-slate-800">
              {calculoFatura.aposFechamento ? (
                <>
                  <Sparkles className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                  <div className="text-slate-300">
                    <strong className="text-emerald-400">✨ Melhor Dia de Compra!</strong> Compra realizada após o fechamento da fatura (dia {selectedCard.fechamento}). O lançamento foi automaticamente atribuído para a fatura do ciclo seguinte, com vencimento em{' '}
                    <strong className="text-white font-mono">{calculoFatura.dataVencimento}</strong>.
                  </div>
                </>
              ) : (
                <>
                  <Info className="w-4 h-4 text-sky-400 shrink-0 mt-0.5" />
                  <div className="text-slate-300">
                    <strong className="text-sky-400">📅 Fatura do Ciclo Atual:</strong> Compra realizada antes do fechamento (dia {selectedCard.fechamento}). O vencimento desta fatura será em{' '}
                    <strong className="text-white font-mono">{calculoFatura.dataVencimento}</strong>.
                  </div>
                </>
              )}
            </div>
          </div>
        )}

        {/* ==================== DATAS: COMPRA E PAGAMENTO COM CALENDÁRIO & DIGITAÇÃO ==================== */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* Data da Compra */}
          <div>
            <DatePickerWithInput
              value={dataCompra}
              onChange={val => {
                setDataCompra(val);
                setDataPagamentoManual(false);
              }}
              label="Data da Compra / Competência"
              helperText="Digite (DD/MM/AAAA) ou selecione no calendário"
            />
          </div>

          {/* Data de Pagamento */}
          <div>
            <div className="relative">
              <DatePickerWithInput
                value={dataPagamento}
                onChange={val => {
                  setDataPagamento(val);
                  setDataPagamentoManual(true);
                }}
                label="Data de Pagamento / Vencimento"
                helperText={
                  selectedCard
                    ? 'Data em que a fatura do cartão vence e o valor é debitado'
                    : 'Data efetiva da liquidação financeira'
                }
                highlightDays={selectedCard ? [selectedCard.vencimento] : []}
                highlightLabel={
                  selectedCard ? `Dia ${selectedCard.vencimento} - Vencimento do ${selectedCard.nome}` : undefined
                }
              />

              {selectedCard && dataPagamentoManual && (
                <button
                  type="button"
                  onClick={handleRecalcularPeloCartao}
                  className="mt-1 text-[11px] text-emerald-400 hover:text-emerald-300 font-semibold flex items-center gap-1"
                >
                  <RotateCcw className="w-3 h-3" />
                  <span>Restaurar vencimento automático do cartão ({calculoFatura?.dataVencimento})</span>
                </button>
              )}
            </div>
          </div>
        </div>

        {/* ==================== OPÇÃO DE LANÇAMENTOS PARCELADOS ==================== */}
        <div className="p-5 bg-slate-950/70 border border-slate-800 rounded-2xl space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Layers className="w-5 h-5 text-indigo-400" />
              <div>
                <h3 className="text-sm font-bold text-white">Opção de Lançamento Parcelado</h3>
                <p className="text-xs text-slate-400">Divida a compra em parcelas mensais automáticas</p>
              </div>
            </div>

            {/* Toggle Switch */}
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={isParcelado}
                onChange={e => setIsParcelado(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-slate-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-600"></div>
            </label>
          </div>

          {isParcelado && (
            <div className="space-y-4 pt-3 border-t border-slate-800/80">
              {/* Modo de Cálculo: Dividir ou Replicar */}
              <div>
                <label className="block text-xs uppercase font-semibold text-slate-400 mb-2">
                  Forma de Cálculo das Parcelas
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                  <button
                    type="button"
                    onClick={() => setModoCalculoParcela('dividir')}
                    className={`p-3 rounded-xl border text-left transition-all ${
                      modoCalculoParcela === 'dividir'
                        ? 'bg-emerald-500/15 border-emerald-500/40 text-emerald-300 shadow-sm'
                        : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-white'
                    }`}
                  >
                    <div className="font-bold text-xs text-white flex items-center justify-between">
                      <span>➗ Dividir o Valor Total</span>
                      {modoCalculoParcela === 'dividir' && (
                        <span className="text-[10px] bg-emerald-500/20 text-emerald-300 px-1.5 py-0.5 rounded font-mono">
                          Ativo
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] text-slate-400 mt-1">
                      Divide o valor digitado igualmente entre as {numParcelas} parcelas ({formatBRL(parseFloat(valor.replace(',', '.')) > 0 ? parseFloat(valor.replace(',', '.')) / numParcelas : 0)} cada).
                    </p>
                  </button>

                  <button
                    type="button"
                    onClick={() => setModoCalculoParcela('replicar')}
                    className={`p-3 rounded-xl border text-left transition-all ${
                      modoCalculoParcela === 'replicar'
                        ? 'bg-indigo-500/15 border-indigo-500/40 text-indigo-300 shadow-sm'
                        : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-white'
                    }`}
                  >
                    <div className="font-bold text-xs text-white flex items-center justify-between">
                      <span>🔁 Replicar o Valor em Cada Parcela</span>
                      {modoCalculoParcela === 'replicar' && (
                        <span className="text-[10px] bg-indigo-500/20 text-indigo-300 px-1.5 py-0.5 rounded font-mono">
                          Ativo
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] text-slate-400 mt-1">
                      Repete o valor integral digitado ({formatBRL(parseFloat(valor.replace(',', '.')) || 0)}) em cada uma das {numParcelas} parcelas. Total acumulado: {formatBRL((parseFloat(valor.replace(',', '.')) || 0) * numParcelas)}.
                    </p>
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs uppercase font-semibold text-slate-400 mb-1.5">
                    Número de Parcelas
                  </label>
                  <select
                    value={numParcelas}
                    onChange={e => setNumParcelas(parseInt(e.target.value, 10))}
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                  >
                    {Array.from({ length: 35 }, (_, i) => i + 2).map(n => (
                      <option key={n} value={n}>
                        {n}x parcelas
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs uppercase font-semibold text-slate-400 mb-1.5 flex items-center justify-between">
                    <span>Valor por Parcela</span>
                    <span className="text-[10px] text-slate-400 font-mono">
                      {modoCalculoParcela === 'dividir' ? 'Total dividido' : 'Valor replicado'}
                    </span>
                  </label>
                  <div className="p-2.5 bg-slate-900 border border-slate-800 rounded-xl text-sm font-bold text-emerald-400 font-mono flex items-center justify-between">
                    <span>
                      {formatBRL(
                        parseFloat(valor.replace(',', '.')) > 0
                          ? modoCalculoParcela === 'dividir'
                            ? parseFloat(valor.replace(',', '.')) / numParcelas
                            : parseFloat(valor.replace(',', '.'))
                          : 0
                      )}
                      <span className="text-xs font-normal text-slate-400 ml-1">/ parcela</span>
                    </span>

                    {modoCalculoParcela === 'replicar' && parseFloat(valor.replace(',', '.')) > 0 && (
                      <span className="text-[11px] text-indigo-300 font-normal">
                        Total: {formatBRL(parseFloat(valor.replace(',', '.')) * numParcelas)}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Tabela de Previsão do Cronograma de Parcelas */}
              {cronogramaParcelas.length > 0 && (
                <div className="space-y-2">
                  <span className="text-xs font-semibold text-slate-400 uppercase block">
                    Cronograma de Parcelas & Vencimento das Faturas:
                  </span>
                  <div className="max-h-48 overflow-y-auto space-y-1.5 pr-1 text-xs">
                    {cronogramaParcelas.map(p => (
                      <div
                        key={p.numero}
                        className="flex items-center justify-between p-2.5 bg-slate-900/90 border border-slate-800/80 rounded-xl"
                      >
                        <div className="flex items-center gap-2">
                          <span className="px-2 py-0.5 rounded bg-slate-800 text-indigo-400 font-mono font-bold text-[11px]">
                            {p.parcelaStr}
                          </span>
                          <span className="text-slate-300">
                            Compra: <strong className="font-mono text-white">{p.dataCompra}</strong>
                          </span>
                          <ArrowRight className="w-3 h-3 text-slate-500" />
                          <span className="text-emerald-400">
                            Fatura / Pagamento: <strong className="font-mono text-white">{p.dataPagamento}</strong>
                          </span>
                        </div>
                        <div className="font-mono font-bold text-white">
                          {formatBRL(p.valorParcela)}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Status e Cenário */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs uppercase font-semibold text-slate-400 mb-1.5">
              Status Inicial
            </label>
            <select
              value={status}
              onChange={e => setStatus(e.target.value as any)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500"
            >
              <option value="Efetivado">Efetivado (Já Liquidado)</option>
              <option value="Orçado">Orçado / Previsto (A Pagar na Fatura)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs uppercase font-semibold text-slate-400 mb-1.5">
              Cenário de Planejamento
            </label>
            <select
              value={cenario}
              onChange={e => setCenario(e.target.value as any)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500"
            >
              <option value="Efetivado">Cenário Efetivado</option>
              <option value="Budget">Cenário Orçamentário (Budget)</option>
              <option value="Otimista">Cenário Otimista</option>
              <option value="Pessimista">Cenário Pessimista</option>
            </select>
          </div>
        </div>

        {/* Botão de Envio */}
        <div className="pt-2 flex justify-end">
          <button
            type="submit"
            className="flex items-center gap-2 px-7 py-3.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-sm font-semibold transition-all shadow-lg shadow-emerald-600/25 active:scale-95"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Salvar Lançamento</span>
          </button>
        </div>
      </form>
    </div>
  );
};
