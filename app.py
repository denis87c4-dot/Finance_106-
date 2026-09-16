
import streamlit as st
import pandas as pd
import os
import io
import zipfile
from datetime import datetime

# ==================== CONFIGURAÇÃO DA PÁGINA ====================
st.set_page_config(page_title="Finance_106", page_icon="💳", layout="wide")
st.title("💳 Finance_106 - Gestão Financeira Limpa e Eficiente")

# ==================== PERSISTÊNCIA DE DADOS (CSV) ====================
ARQUIVO_LANCAMENTOS = "lancamentos.csv"
ARQUIVO_CARTOES = "cartoes.csv"
ARQUIVO_CATEGORIAS = "categorias.csv"

colunas_lancamentos = [
    "Tipo", "Status", "Descricao", "Categoria", "Conta", "ContaDestino", 
    "Valor", "Data", "Parcela", "RegraParcelamento", "FormaPagamento", "Observacoes"
]

# Inicialização de Estados e Arquivos
if os.path.exists(ARQUIVO_LANCAMENTOS):
    st.session_state.lancamentos = pd.read_csv(ARQUIVO_LANCAMENTOS)
else:
    st.session_state.lancamentos = pd.DataFrame(columns=colunas_lancamentos)

if os.path.exists(ARQUIVO_CATEGORIAS):
    df_cat = pd.read_csv(ARQUIVO_CATEGORIAS)
    st.session_state.categorias = df_cat["Categoria"].tolist()
else:
    st.session_state.categorias = ["Alimentação", "Transporte", "Moradia", "Lazer", "Transferência", "Outros"]

if os.path.exists(ARQUIVO_CARTOES):
    st.session_state.cartoes = pd.read_csv(ARQUIVO_CARTOES)
else:
    st.session_state.cartoes = pd.DataFrame(columns=["Nome", "Fechamento", "Limite", "Vencimento"])

# ==================== FUNÇÕES DE BACKUP ====================
def salvar_backup(mostrar_aviso=True):
    st.session_state.lancamentos.to_csv(ARQUIVO_LANCAMENTOS, index=False)
    st.session_state.cartoes.to_csv(ARQUIVO_CARTOES, index=False)
    pd.DataFrame({"Categoria": st.session_state.categorias}).to_csv(ARQUIVO_CATEGORIAS, index=False)
    if mostrar_aviso:
        st.success("💾 Backup realizado com sucesso!")

def salvar_backup_automatico():
    try:
        salvar_backup(mostrar_aviso=False)
    except:
        pass

salvar_backup_automatico()

# ==================== FUNÇÕES DE FORMATAÇÃO E ESTILO ====================
def formatar_moeda_br(val):
    if pd.isna(val):
        return "R$ 0,00"
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def colorir_negativos(val):
    if isinstance(val, str) and "R$" in val:
        try:
            limpo = val.replace("R$", "").replace(".", "").replace(",", ".").replace("%", "").strip()
            val_num = float(limpo)
            if val_num < 0:
                return 'color: #ff4b4b; font-weight: bold;'
        except:
            pass
    elif isinstance(val, (int, float)) and val < 0:
        return 'color: #ff4b4b; font-weight: bold;'
    return ''

def aplicar_estilo_tabela(df_styled, subset=None):
    try:
        if hasattr(df_styled, "map"):
            return df_styled.map(colorir_negativos, subset=subset)
        else:
            return df_styled.applymap(colorir_negativos, subset=subset)
    except Exception:
        return df_styled

# ==================== NAVEGAÇÃO LIMPA ====================
aba = st.sidebar.radio("Navegação", ["Lançamentos", "Cadastro", "Financial Summary", "Cartões", "Backup"])

# ==================== 1. LANÇAMENTOS ====================
if aba == "Lançamentos":
    st.subheader("📒 Registro de Lançamentos")
    df_exibicao = st.session_state.lancamentos.copy()
    
    if not df_exibicao.empty and "Valor" in df_exibicao.columns:
        df_exibicao["Valor"] = pd.to_numeric(df_exibicao["Valor"], errors="coerce").fillna(0.0)
        df_estilizado = aplicar_estilo_tabela(df_exibicao.style.format(formatar_moeda_br, subset=["Valor"]), subset=["Valor"])
        st.dataframe(df_estilizado, use_container_width=True)
    else:
        st.info("Nenhum lançamento cadastrado.")

# ==================== 2. CADASTRO ====================
elif aba == "Cadastro":
    st.subheader("📝 Novo Lançamento")
    with st.form("form_lancamento", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            tipo = st.selectbox("Tipo", ["Receita", "Despesa", "Transferência"])
            status = st.selectbox("Status", ["Efetivado", "Budget"])
            descricao = st.text_input("Descrição *")
            categoria = st.selectbox("Categoria", st.session_state.categorias)
            conta = st.text_input("Conta / Cartão de Origem", value="Conta Principal")
        with col2:
            conta_destino = st.text_input("Conta Destino (Apenas Transferências)", value="")
            valor = st.number_input("Valor (R$) *", min_value=0.0, step=0.01)
            data = st.date_input("Data *", value=datetime.today())
            num_parcelas = st.number_input("Número de Parcelas", min_value=1, step=1, value=1)
            forma_pagamento = st.selectbox("Forma de Pagamento", ["Pix", "Cartão de Crédito", "Conta Corrente", "Dinheiro", "Outros"])

        observacoes = st.text_area("Observações (opcional)")
        submit = st.form_submit_button("Salvar Lançamento")

        if submit:
            if not descricao.strip() or valor <= 0:
                st.error("⚠️ Preencha a descrição e um valor maior que zero.")
            else:
                registros = []
                for i in range(num_parcelas):
                    valor_parcela = valor / num_parcelas
                    data_parcela = pd.to_datetime(data) + pd.DateOffset(months=i)
                    desc_parcela = f"{descricao} ({i+1}/{num_parcelas})" if num_parcelas > 1 else descricao
                    
                    registros.append([
                        str(tipo), str(status), str(desc_parcela), str(categoria), str(conta), str(conta_destino),
                        float(valor_parcela), data_parcela.strftime("%Y-%m-%d"), str(f"{i+1}/{num_parcelas}"), 
                        "Parcelado", str(forma_pagamento), str(observacoes)
                    ])

                novo_df = pd.DataFrame(registros, columns=colunas_lancamentos)
                st.session_state.lancamentos = pd.concat([st.session_state.lancamentos, novo_df], ignore_index=True)
                salvar_backup(mostrar_aviso=False)
                st.success(f"✅ {num_parcelas} lançamento(s) cadastrado(s) com sucesso!")

# ==================== 3. FINANCIAL SUMMARY ====================
elif aba == "Financial Summary":
    st.subheader("📊 Financial Summary")
    st.markdown("Consolidated view of **Income**, **Expenses**, **Cash Flow**, and **Cumulative Balance**.")

    df = st.session_state.lancamentos
    if not df.empty:
        df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0.0)
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
        df["AnoMes"] = df["Data"].dt.to_period("M").astype(str)

        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            status_sel = st.selectbox("Filter by Status", ["All", "Efetivado", "Budget"])
        with col_f2:
            start_date = st.date_input("Start Date", df["Data"].min().date() if not df["Data"].isna().all() else datetime.today().date())
        with col_f3:
            end_date = st.date_input("End Date", df["Data"].max().date() if not df["Data"].isna().all() else datetime.today().date())

        df_filtrado = df[(df["Data"].dt.date >= start_date) & (df["Data"].dt.date <= end_date)]
        if status_sel != "All":
            df_filtrado = df_filtrado[df_filtrado["Status"] == status_sel]

        df_filtrado["Income"] = df_filtrado.apply(lambda r: r["Valor"] if r["Tipo"] == "Receita" else 0.0, axis=1)
        df_filtrado["Expense"] = df_filtrado.apply(lambda r: r["Valor"] if r["Tipo"] == "Despesa" else 0.0, axis=1)

        pivot = df_filtrado.pivot_table(
            index="AnoMes",
            values=["Income", "Expense"],
            aggfunc="sum",
            fill_value=0.0
        ).reset_index()

        pivot = pivot.sort_values("AnoMes").reset_index(drop=True)
        
        # Lógica rigorosa: Income - Expense
        pivot["Cash Flow"] = pivot["Income"] - pivot["Expense"]
        pivot["Cumulative"] = pivot["Cash Flow"].cumsum()
        pivot["Month"] = pd.PeriodIndex(pivot["AnoMes"], freq="M").strftime("%m/%Y")

        pivot_exibicao = pivot[["Month", "Income", "Expense", "Cash Flow", "Cumulative"]].copy()
        
        # Formatação individual para string de moeda
        for col in ["Income", "Expense", "Cash Flow", "Cumulative"]:
            pivot_exibicao[col] = pivot_exibicao[col].apply(formatar_moeda_br)

        # Aplicação perfeita do estilo de vermelhos em negativos nas colunas de resultado
        pivot_estilizado = aplicar_estilo_tabela(
            pivot_exibicao.set_index("Month").style, 
            subset=["Cash Flow", "Cumulative"]
        )

        st.dataframe(pivot_estilizado, use_container_width=True)
    else:
        st.info("Nenhum dado disponível para o resumo financeiro.")

# ==================== 4. CARTÕES ====================
elif aba == "Cartões":
    st.subheader("💳 Gerenciamento de Cartões / Contas")
    with st.form("form_cartao", clear_on_submit=True):
        nome = st.text_input("Nome do Cartão/Banco")
        limite = st.number_input("Limite (R$)", min_value=0.0, value=1000.0)
        fechamento = st.number_input("Dia de Fechamento", min_value=1, max_value=31, value=10)
        vencimento = st.number_input("Dia de Vencimento", min_value=1, max_value=31, value=17)
        btn_cartao = st.form_submit_button("Salvar Cartão")
        
        if btn_cartao and nome.strip():
            novo_c = pd.DataFrame([{"Nome": nome, "Fechamento": fechamento, "Limite": limite, "Vencimento": vencimento}])
            st.session_state.cartoes = pd.concat([st.session_state.cartoes, novo_c], ignore_index=True)
            salvar_backup(mostrar_aviso=False)
            st.success("✅ Cartão salvo com sucesso!")

    if not st.session_state.cartoes.empty:
        st.dataframe(st.session_state.cartoes, use_container_width=True)

# ==================== 5. BACKUP ====================
elif aba == "Backup":
    st.subheader("🔐 Central de Backup & Segurança")
    if st.button("💾 Salvar Backup Local"):
        salvar_backup(mostrar_aviso=True)

    arquivos = [ARQUIVO_LANCAMENTOS, ARQUIVO_CARTOES, ARQUIVO_CATEGORIAS]
    existentes = [f for f in arquivos if os.path.exists(f)]
    if existentes:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for arq in existentes:
                zf.write(arq)
        zip_buffer.seek(0)
        st.download_button(
            label="📥 Baixar Backup Completo (.zip)",
            data=zip_buffer,
            file_name=f"backup_finance_106_{datetime.today().strftime('%Y-%m-%d')}.zip",
            mime="application/zip"
        )

    arquivo_upload = st.file_uploader("📤 Restaurar Backup (ZIP)", type="zip")
    if arquivo_upload is not None:
        try:
            with zipfile.ZipFile(arquivo_upload, "r") as zf:
                zf.extractall(".")
            st.success("✅ Dados restaurados com sucesso! Recarregue a página.")
        except Exception as e:
            st.error(f"❌ Erro ao restaurar: {e}")
