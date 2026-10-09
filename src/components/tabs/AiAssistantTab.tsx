import React, { useState, useMemo } from 'react';
import { useFinance } from '../../context/FinanceContext';
import { Bot, Sparkles, Send, Lightbulb, TrendingUp, AlertTriangle } from 'lucide-react';

export const AiAssistantTab: React.FC = () => {
  const { transactions } = useFinance();

  const [activeSubTab, setActiveSubTab] = useState<'relatorio' | 'chat'>('relatorio');
  const [inputQuestion, setInputQuestion] = useState('');
  const [messages, setMessages] = useState<
    { role: 'user' | 'assistant'; text: string; time: string }[]
  >([
    {
      role: 'assistant',
      text: 'Olá! Sou o Assistente Financeiro Inteligente do Fluxo 106. Analisei seus lançamentos em tempo real. Como posso auxiliar seu planejamento orçamentário hoje?',
      time: 'Agora'
    }
  ]);

  const formatBRL = (val: number) =>
    new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);

  // Diagnostic calculations
  const diagnostic = useMemo(() => {
    const rec = transactions.filter(t => t.tipo === 'Receita').reduce((a, b) => a + b.valor, 0);
    const desp = transactions.filter(t => t.tipo === 'Despesa').reduce((a, b) => a + b.valor, 0);
    const saldo = rec - desp;

    const catSums = new Map<string, number>();
    transactions
      .filter(t => t.tipo === 'Despesa')
      .forEach(t => {
        catSums.set(t.categoria, (catSums.get(t.categoria) || 0) + t.valor);
      });

    const sortedCats = Array.from(catSums.entries()).sort((a, b) => b[1] - a[1]);
    const maiorCat = sortedCats.length > 0 ? sortedCats[0][0] : 'Nenhum';
    const maiorVal = sortedCats.length > 0 ? sortedCats[0][1] : 0;
    const pctMaior = desp > 0 ? (maiorVal / desp) * 100 : 0;

    const proj12m = saldo * 1.08;

    return { rec, desp, saldo, maiorCat, maiorVal, pctMaior, proj12m };
  }, [transactions]);

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputQuestion.trim()) return;

    const q = inputQuestion.trim();
    const userMsg = { role: 'user' as const, text: q, time: 'Agora' };

    let reply = '';
    const qLower = q.toLowerCase();

    if (qLower.includes('saldo') || qLower.includes('total') || qLower.includes('quanto')) {
      reply = `Seu saldo líquido consolidado atual é de **${formatBRL(diagnostic.saldo)}**, composto por **${formatBRL(diagnostic.rec)}** em receitas e **${formatBRL(diagnostic.desp)}** em despesas.`;
    } else if (qLower.includes('maior') || qLower.includes('gasto') || qLower.includes('ralo')) {
      reply = `O seu maior centro de despesas é a categoria **${diagnostic.maiorCat}**, que soma **${formatBRL(diagnostic.maiorVal)}** (${diagnostic.pctMaior.toFixed(1)}% de todas as despesas). Recomendo fixar uma meta orçamentária para ela na aba Dashboard.`;
    } else if (qLower.includes('dica') || qLower.includes('economizar') || qLower.includes('conselho')) {
      reply = `Com base no seu perfil:\n1. A categoria **${diagnostic.maiorCat}** consome ${diagnostic.pctMaior.toFixed(1)}% do seu orçamento.\n2. Fixar uma meta de teto com corte de 10% nessa categoria liberaria cerca de **${formatBRL(diagnostic.maiorVal * 0.1)}** mensais diretamente para a sua reserva de emergência ou investimentos.`;
    } else if (qLower.includes('projeção') || qLower.includes('futuro') || qLower.includes('ano')) {
      reply = `Mantendo a taxa de poupança atual com reinvestimento em Selic/CDI, sua projeção de patrimônio líquido acumulado aponta para **${formatBRL(diagnostic.proj12m)}** ao final do próximo ciclo anual.`;
    } else {
      reply = `Analisando seu fluxo: você possui uma margem operacional positiva com receitas de **${formatBRL(diagnostic.rec)}** superando as saídas de **${formatBRL(diagnostic.desp)}**. Seu principal ralo é **${diagnostic.maiorCat}**. Continue alimentando os lançamentos para apurar o VaR e desvios de cauda!`;
    }

    setMessages(prev => [...prev, userMsg, { role: 'assistant', text: reply, time: 'Agora' }]);
    setInputQuestion('');
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <span>🤖 Central de Inteligência Artificial & Assistente Financeiro</span>
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          Diagnósticos preditivos heurísticos e consultoria orçamentária conectada aos seus dados financeiros reais.
        </p>
      </div>

      {/* Tabs Switcher */}
      <div className="flex border-b border-slate-800 gap-4 text-sm font-semibold">
        <button
          onClick={() => setActiveSubTab('relatorio')}
          className={`pb-3 transition-colors flex items-center gap-2 ${
            activeSubTab === 'relatorio'
              ? 'text-emerald-400 border-b-2 border-emerald-400'
              : 'text-slate-400 hover:text-white'
          }`}
        >
          <Sparkles className="w-4 h-4" />
          <span>Relatório Preditivo Avançado</span>
        </button>
        <button
          onClick={() => setActiveSubTab('chat')}
          className={`pb-3 transition-colors flex items-center gap-2 ${
            activeSubTab === 'chat'
              ? 'text-emerald-400 border-b-2 border-emerald-400'
              : 'text-slate-400 hover:text-white'
          }`}
        >
          <Bot className="w-4 h-4" />
          <span>Chat com Assistente Financeiro</span>
        </button>
      </div>

      {activeSubTab === 'relatorio' ? (
        <div className="space-y-6">
          {/* 3 Metric Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5">
              <div className="text-xs font-semibold uppercase text-slate-400">Saldo Consolidado Global</div>
              <div className="text-2xl font-bold text-emerald-400 font-mono mt-1">
                {formatBRL(diagnostic.saldo)}
              </div>
              <div className="text-xs text-slate-400 mt-1">Receitas totais menos despesas</div>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5">
              <div className="text-xs font-semibold uppercase text-slate-400">Principal Ralo de Gastos</div>
              <div className="text-2xl font-bold text-rose-400 font-mono mt-1">
                {diagnostic.maiorCat}
              </div>
              <div className="text-xs text-rose-400/80 mt-1 font-mono">
                {formatBRL(diagnostic.maiorVal)}
              </div>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5">
              <div className="text-xs font-semibold uppercase text-slate-400">Concentração na Maior Categoria</div>
              <div className="text-2xl font-bold text-amber-400 font-mono mt-1">
                {diagnostic.pctMaior.toFixed(1)}%
              </div>
              <div className="text-xs text-slate-400 mt-1">Do total de saídas registradas</div>
            </div>
          </div>

          {/* Insights Box */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Lightbulb className="w-5 h-5 text-amber-400" />
              <span>Insights & Revelações de Comportamento de Consumo</span>
            </h3>

            <div className="space-y-3 text-sm text-slate-300">
              <div className="flex items-start gap-3 p-3 bg-slate-950/60 rounded-xl border border-slate-800/60">
                <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
                <div>
                  <strong className="text-white">Alocação de Recursos:</strong> A categoria{' '}
                  <span className="text-amber-400 font-semibold">{diagnostic.maiorCat}</span> absorve sozinha{' '}
                  <span className="font-mono font-bold text-white">{diagnostic.pctMaior.toFixed(1)}%</span> de
                  todo o seu capital de saída.
                </div>
              </div>

              <div className="flex items-start gap-3 p-3 bg-slate-950/60 rounded-xl border border-slate-800/60">
                <TrendingUp className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
                <div>
                  <strong className="text-white">Projeção de Trajetória Futura (12M):</strong> Mantendo a
                  taxa de poupança atual com reinvestimento do excedente, a tendência estimada para o próximo
                  ciclo anual aponta para um fluxo patrimonial líquido de aproximadamente{' '}
                  <span className="text-emerald-400 font-bold font-mono">
                    {formatBRL(diagnostic.proj12m)}
                  </span>
                  .
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* Chat SubTab */
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 flex flex-col h-[520px]">
          {/* Chat Messages */}
          <div className="flex-1 overflow-y-auto space-y-4 pr-2">
            {messages.map((m, idx) => (
              <div
                key={idx}
                className={`flex gap-3 text-xs sm:text-sm ${
                  m.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                {m.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0">
                    <Bot className="w-4 h-4" />
                  </div>
                )}
                <div
                  className={`p-3.5 rounded-2xl max-w-lg leading-relaxed ${
                    m.role === 'user'
                      ? 'bg-emerald-600 text-white rounded-tr-none'
                      : 'bg-slate-950 border border-slate-800 text-slate-200 rounded-tl-none'
                  }`}
                >
                  <p className="whitespace-pre-line">{m.text}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Prompt suggestions */}
          <div className="flex flex-wrap gap-2 pt-3 pb-2 text-[11px] text-slate-400">
            <button
              type="button"
              onClick={() => setInputQuestion('Qual é o meu maior ralo de gastos?')}
              className="px-2.5 py-1 bg-slate-950 hover:bg-slate-800 rounded-lg border border-slate-800 transition-colors"
            >
              "Qual o maior ralo de gastos?"
            </button>
            <button
              type="button"
              onClick={() => setInputQuestion('Como economizar e otimizar meu saldo?')}
              className="px-2.5 py-1 bg-slate-950 hover:bg-slate-800 rounded-lg border border-slate-800 transition-colors"
            >
              "Como economizar mais?"
            </button>
            <button
              type="button"
              onClick={() => setInputQuestion('Qual a projeção do meu patrimônio em 1 ano?')}
              className="px-2.5 py-1 bg-slate-950 hover:bg-slate-800 rounded-lg border border-slate-800 transition-colors"
            >
              "Projeção em 1 ano?"
            </button>
          </div>

          {/* Input Form */}
          <form onSubmit={handleSendMessage} className="flex gap-2 pt-2 border-t border-slate-800">
            <input
              type="text"
              placeholder="Digite sua dúvida financeira sobre seus dados..."
              value={inputQuestion}
              onChange={e => setInputQuestion(e.target.value)}
              className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs sm:text-sm text-white focus:outline-none focus:border-emerald-500"
            />
            <button
              type="submit"
              className="px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs sm:text-sm font-semibold flex items-center gap-1.5 transition-all shadow-md shadow-emerald-600/20"
            >
              <Send className="w-4 h-4" />
              <span>Enviar</span>
            </button>
          </form>
        </div>
      )}
    </div>
  );
};
