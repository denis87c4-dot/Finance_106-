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
            
            lista_cat_opcao = st.session_state.categorias + ["+ Adicionar nova categoria..."]
            cat_escolhida = st.selectbox("Categoria", lista_cat_opcao)

            contas_base = ["Conta Principal", "Nubank", "Carteira"]
            if not st.session_state.cartoes.empty:
                for c_nome in st.session_state.cartoes["Nome"].tolist():
                    if c_nome not in contas_base:
                        contas_base.append(c_nome)
            
            conta_opcao = st.selectbox("Conta / Cartão de Origem", contas_base + ["+ Adicionar nova conta..."])

        with col2:
            conta_destino = st.text_input("Conta Destino (Apenas Transferências)", value="")
            valor = st.number_input("Valor (R$) *", min_value=0.0, step=0.01)
            data = st.date_input("Data *", value=datetime.today())
            num_parcelas = st.number_input("Número de Parcelas", min_value=1, step=1, value=1)
            forma_pagamento = st.selectbox("Forma de Pagamento", ["Pix", "Cartão de Crédito", "Conta Corrente", "Dinheiro", "Outros"])

        observacoes = st.text_area("Observações (opcional)")
        submit = st.form_submit_button("Salvar Lançamento")

    # CAMPOS DINÂMICOS FORA DO FORM
    nova_cat_digitada = ""
    if cat_escolhida == "+ Adicionar nova categoria...":
        nova_cat_digitada = st.text_input("Digite o nome da nova categoria:")

    nova_conta_digitada = ""
    if conta_opcao == "+ Adicionar nova conta...":
        nova_conta_digitada = st.text_input("Digite o nome da nova Conta/Banco:")

    if submit:
        categoria_final = cat_escolhida
        if cat_escolhida == "+ Adicionar nova categoria...":
            if nova_cat_digitada.strip() != "":
                categoria_final = nova_cat_digitada.strip()
                if categoria_final not in st.session_state.categorias:
                    st.session_state.categorias.append(categoria_final)
            else:
                st.error("⚠️ Digite o nome da nova categoria.")

        conta_final = conta_opcao
        if conta_opcao == "+ Adicionar nova conta...":
            if nova_conta_digitada.strip() != "":
                conta_final = nova_conta_digitada.strip()
            else:
                st.error("⚠️ Digite o nome da nova conta.")

        if not descricao.strip() or valor <= 0:
            st.error("⚠️ Preencha a descrição e um valor maior que zero.")
        else:
            registros = []
            for i in range(num_parcelas):
                valor_parcela = valor / num_parcelas
                data_parcela = pd.to_datetime(data) + pd.DateOffset(months=i)
                desc_parcela = f"{descricao} ({i+1}/{num_parcelas})" if num_parcelas > 1 else descricao
                
                registros.append([
                    str(tipo), str(status), str(desc_parcela), str(categoria_final), str(conta_final), str(conta_destino),
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
    # (mantém igual ao seu código original)

# ==================== 4. CARTÕES ====================
elif aba == "Cartões":
    st.subheader("💳 Gerenciamento de Cartões / Contas")
