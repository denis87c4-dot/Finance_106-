import React, { useRef, useState } from 'react';
import { useFinance } from '../../context/FinanceContext';
import { Download, Upload, RotateCcw, Trash2, CheckCircle2, Database, Shield } from 'lucide-react';

export const BackupSecurityTab: React.FC = () => {
  const {
    transactions,
    categories,
    accounts,
    cards,
    importData,
    resetToSample,
    clearAll
  } = useFinance();

  const fileInputRef = useRef<HTMLInputElement>(null);
  const [feedback, setFeedback] = useState<string | null>(null);

  const downloadJSON = () => {
    const data = {
      lancamentos: transactions,
      categorias: categories,
      contas: accounts,
      cartoes: cards,
      versao: '2.4.0',
      exportadoEm: new Date().toISOString()
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `backup_financeiro_${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
    setFeedback('Backup JSON gerado e baixado com sucesso!');
  };

  const downloadCSV = () => {
    const headers = ['id', 'tipo', 'conta', 'contaDestino', 'categoria', 'descricao', 'valor', 'data', 'dataPagamento', 'parcelas', 'status', 'cenario'];
    const rows = transactions.map(t => [
      t.id,
      t.tipo,
      t.conta,
      t.contaDestino || '',
      t.categoria,
      `"${t.descricao.replace(/"/g, '""')}"`,
      t.valor,
      t.data,
      t.dataPagamento || t.data,
      t.parcelas,
      t.status,
      t.cenario
    ]);
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.href = encodedUri;
    link.download = `lancamentos_${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
    setFeedback('Lançamentos exportados em CSV com sucesso!');
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = event => {
      try {
        const text = event.target?.result as string;
        if (file.name.endsWith('.json')) {
          const parsed = JSON.parse(text);
          importData(parsed);
          setFeedback('Backup JSON importado e restaurado com sucesso!');
        } else if (file.name.endsWith('.csv')) {
          const lines = text.split('\n').filter(l => l.trim().length > 0);
          if (lines.length > 1) {
            const importedList: any[] = [];
            for (let i = 1; i < lines.length; i++) {
              const cols = lines[i].split(',');
              if (cols.length >= 6) {
                importedList.push({
                  tipo: cols[1]?.trim() || 'Despesa',
                  conta: cols[2]?.trim() || 'Conta Corrente',
                  categoria: cols[4]?.trim() || 'Outros',
                  descricao: cols[5]?.replace(/"/g, '').trim() || 'Importado',
                  valor: Math.abs(parseFloat(cols[6]) || 0),
                  data: cols[7]?.trim() || new Date().toISOString().slice(0, 10),
                  parcelas: cols[8]?.trim() || '1/1',
                  status: (cols[9]?.trim() || 'Efetivado') as any,
                  cenario: (cols[10]?.trim() || 'Efetivado') as any
                });
              }
            }
            importData({ lancamentos: importedList });
            setFeedback(`${importedList.length} lançamentos importados do arquivo CSV com sucesso!`);
          }
        }
      } catch (err: any) {
        alert('Erro ao processar arquivo: ' + err.message);
      }
    };
    reader.readAsText(file);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <span>🛡️ Central de Backup, Segurança & Persistência</span>
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          Gerencie cópias de segurança em formatos JSON e CSV, restauração de demonstrativos e sincronização local.
        </p>
      </div>

      {feedback && (
        <div className="p-4 bg-emerald-500/15 border border-emerald-500/30 rounded-2xl flex items-center gap-2 text-emerald-400 text-sm">
          <CheckCircle2 className="w-5 h-5 shrink-0" />
          <span>{feedback}</span>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Exportar */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center gap-2">
            <Download className="w-5 h-5 text-emerald-400" />
            <h3 className="text-base font-bold text-white">Exportação de Dados</h3>
          </div>
          <p className="text-xs text-slate-400">
            Gere uma cópia exata de todos os lançamentos, categorias, contas e cartões de crédito configurados.
          </p>

          <div className="space-y-3 pt-2">
            <button
              onClick={downloadJSON}
              className="w-full flex items-center justify-between p-3.5 bg-slate-950 border border-slate-800 hover:border-emerald-500/40 rounded-xl text-xs font-semibold text-white transition-all shadow-sm"
            >
              <div className="flex items-center gap-3">
                <Database className="w-4 h-4 text-emerald-400" />
                <span>Baixar Backup Completo (.json)</span>
              </div>
              <span className="text-emerald-400 font-mono">JSON</span>
            </button>

            <button
              onClick={downloadCSV}
              className="w-full flex items-center justify-between p-3.5 bg-slate-950 border border-slate-800 hover:border-emerald-500/40 rounded-xl text-xs font-semibold text-white transition-all shadow-sm"
            >
              <div className="flex items-center gap-3">
                <Download className="w-4 h-4 text-sky-400" />
                <span>Baixar Apenas Lançamentos (.csv)</span>
              </div>
              <span className="text-sky-400 font-mono">CSV</span>
            </button>
          </div>
        </div>

        {/* Importar */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center gap-2">
            <Upload className="w-5 h-5 text-sky-400" />
            <h3 className="text-base font-bold text-white">Importação Multi-formato</h3>
          </div>
          <p className="text-xs text-slate-400">
            Restaure um arquivo JSON ou anexe novos lançamentos através de uma planilha CSV.
          </p>

          <input
            type="file"
            ref={fileInputRef}
            accept=".json,.csv"
            onChange={handleFileUpload}
            className="hidden"
          />

          <div className="pt-2">
            <button
              onClick={() => fileInputRef.current?.click()}
              className="w-full flex items-center justify-center gap-2 p-3.5 bg-sky-600 hover:bg-sky-500 text-white rounded-xl text-xs font-semibold transition-all shadow-md shadow-sky-600/20"
            >
              <Upload className="w-4 h-4" />
              <span>Selecionar Arquivo (JSON ou CSV)</span>
            </button>
          </div>
        </div>
      </div>

      {/* Database Reset & Demo restore */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6">
        <h3 className="text-base font-bold text-white mb-2 flex items-center gap-2">
          <Shield className="w-5 h-5 text-amber-400" />
          <span>Gestão de Ciclo de Vida da Base de Dados</span>
        </h3>
        <p className="text-xs text-slate-400 mb-6">
          Restaure os dados de demonstração iniciais ou limpe todos os registros para começar do zero.
        </p>

        <div className="flex flex-wrap items-center gap-4">
          <button
            onClick={() => {
              if (confirm('Restaurar dados completos de demonstração do Fluxo 106?')) {
                resetToSample();
                setFeedback('Dados de demonstração restaurados com sucesso!');
              }
            }}
            className="flex items-center gap-2 px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-semibold border border-slate-700 transition-all"
          >
            <RotateCcw className="w-4 h-4 text-emerald-400" />
            <span>Restaurar Base Demonstrativa Padrão</span>
          </button>

          <button
            onClick={() => {
              if (confirm('Atenção: Deseja apagar TODOS os lançamentos da base de dados? Esta ação é irreversível.')) {
                clearAll();
                setFeedback('Base de lançamentos limpa com sucesso.');
              }
            }}
            className="flex items-center gap-2 px-4 py-2.5 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 rounded-xl text-xs font-semibold border border-rose-500/30 transition-all"
          >
            <Trash2 className="w-4 h-4" />
            <span>Zerar Todos os Lançamentos</span>
          </button>
        </div>
      </div>
    </div>
  );
};
