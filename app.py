import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Fluxo Básico", page_icon="💰", layout="wide")

# Navegação lateral
aba = st.sidebar.radio("Navegação", ["Dashboard", "Cadastro", "Lançamentos"])

# Base de dados em memória
if "lancamentos" not in st.session_state:
    st.session_state.lancamentos = pd.DataFrame(columns=["Tipo", "Descrição", "Valor", "Data"])

# ==================== DASHBOARD ====================
if aba == "Dashboard":
    st.title("📊 Dashboard Financeiro")
    if not st.session_state.lancamentos.empty:
        st.dataframe(st.session_state.lancamentos)
        st.metric("Total Receitas", f"R$ {st.session_state.lancamentos[st.session_state.lancamentos['Tipo']=='Receita']['Valor'].sum():,.2f}")
        st.metric("Total Despesas", f"R$ {st.session_state.lancamentos[st.session_state.lancamentos['Tipo']=='Despesa']['Valor'].sum():,.2f}")
    else:
        st.info("Nenhum lançamento registrado ainda.")

# ==================== CADASTRO ====================
elif aba == "Cadastro":
    st.title("📝 Cadastro de Categorias")
    nova_cat = st.text_input("Digite uma nova categoria")
    if st.button("Adicionar Categoria"):
        st.success(f"Categoria '{nova_cat}' adicionada!")

# ==================== LANÇAMENTOS ====================
elif aba == "Lançamentos":
    st.title("💵 Registrar Lançamento")
    tipo = st.selectbox("Tipo", ["Receita", "Despesa"])
    descricao = st.text_input("Descrição")
    valor = st.number_input("Valor (R$)", min_value=0.0, step=10.0)
    data = st.date_input("Data")
    
    if st.button("Salvar Lançamento"):
        novo = pd.DataFrame([[tipo, descricao, valor, data]], columns=["Tipo", "Descrição", "Valor", "Data"])
        st.session_state.lancamentos = pd.concat([st.session_state.lancamentos, novo], ignore_index=True)
        st.success("Lançamento salvo com sucesso!")
