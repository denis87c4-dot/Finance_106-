import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Fluxo Básico", page_icon="💰", layout="wide")

# Navegação lateral
aba = st.sidebar.radio("Navegação", ["Dashboard", "Cadastro", "Lançamentos"])

# Base de dados em memória para Lançamentos
if "lancamentos" not in st.session_state:
    st.session_state.lancamentos = pd.DataFrame(columns=[
        "Tipo", "Conta", "Conta Destino", "Categoria", "Descrição", "Valor", "Data", "Parcelas", "Modo Valor"
    ])

# Base em memória para Categorias
if "categorias" not in st.session_state:
    st.session_state.categorias = ["Alimentação", "Transporte", "Moradia", "Salário", "Lazer"]

# Base em memória para Contas (Accounts)
if "contas" not in st.session_state:
    st.session_state.contas = ["Conta Corrente", "Carteira", "Cartão de Crédito", "Poupança"]

# ==================== DASHBOARD ====================
if aba == "Dashboard":
    st.title("📊 Dashboard Financeiro")
    if not st.session_state.lancamentos.empty:
        st.dataframe(st.session_state.lancamentos, use_container_width=True)
        
        df_rec = st.session_state.lancamentos[st.session_state.lancamentos['Tipo'] == 'Receita']
        df_desp = st.session_state.lancamentos[st.session_state.lancamentos['Tipo'] == 'Despesa']
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Receitas", f"R$ {df_rec['Valor'].sum():,.2f}")
        with col2:
            st.metric("Total Despesas", f"R$ {df_desp['Valor'].sum():,.2f}")
    else:
        st.info("Nenhum lançamento registrado ainda.")

# ==================== CADASTRO ====================
elif aba == "Cadastro":
    st.title("📝 Cadastro Geral")
    
    tab_cat, tab_acc = st.tabs(["Categorias", "Contas (Accounts)"])
    
    with tab_cat:
        st.subheader("Gerenciar Categorias")
        nova_cat = st.text_input("Nova Categoria", key="input_nova_cat")
        if st.button("Adicionar Categoria"):
            if nova_cat and nova_cat not in st.session_state.categorias:
                st.session_state.categorias.append(nova_cat)
                st.success(f"Categoria '{nova_cat}' adicionada com sucesso!")
                st.rerun()
            else:
                st.warning("Insira uma categoria válida ou que já exista.")
        st.write("Categorias atuais:", st.session_state.categorias)

    with tab_acc:
        st.subheader("Gerenciar Contas")
        nova_conta = st.text_input("Nova Conta (Account)", key="input_nova_acc")
        if st.button("Adicionar Conta"):
            if nova_conta and nova_conta not in st.session_state.contas:
                st.session_state.contas.append(nova_conta)
                st.success(f"Conta '{nova_conta}' adicionada com sucesso!")
                st.rerun()
            else:
                st.warning("Insira uma conta válida ou que já exista.")
        st.write("Contas atuais:", st.session_state.contas)

# ==================== LANÇAMENTOS ====================
elif aba == "Lançamentos":
    st.title("💵 Registrar Lançamento")
    
    tipo = st.selectbox("Tipo de Lançamento", ["Receita", "Despesa", "Transferência"])
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        conta = st.selectbox("Conta (Account)", st.session_state.contas)

    conta_destino = "-"
    if tipo == "Transferência":
        with col_c2:
            conta_destino = st.selectbox("Conta de Destino", st.session_state.contas)

    # Categoria com opção de adicionar na mesma hora
    cat_lista = ["+ Adicionar nova categoria..."] + st.session_state.categorias
    cat_escolha = st.selectbox("Categoria", cat_lista)
    
    categoria = cat_escolha
    if cat_escolha == "+ Adicionar nova categoria...":
        categoria_nova = st.text_input("Digite o nome da nova categoria:")
        if categoria_nova:
            categoria = categoria_nova

    descricao = st.text_input("Descrição")
    valor = st.number_input("Valor (R$)", min_value=0.0, step=10.0)
    data = st.date_input("Data Inicial")
    
    # Linha do Parcelamento
    st.markdown("---")
    st.subheader("Parcelamento")
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        parcelas = st.number_input("Número de Parcelas", min_value=1, max_value=120, value=1, step=1)
    
    modo_valor = "Integral"
    if parcelas > 1:
        with col_p2:
            modo_valor = st.radio(
                "Como tratar o valor nas parcelas?", 
                ["Dividir valor total pelas parcelas", "Replicar valor integral em cada parcela"]
            )

    st.markdown("---")
    if st.button("Salvar Lançamento", type="primary"):
        # Salva automaticamente a nova categoria na session_state se foi criada agora
        if cat_escolha == "+ Adicionar nova categoria..." and categoria and categoria not in st.session_state.categorias:
            st.session_state.categorias.append(categoria)

        valor_final = valor / parcelas if (parcelas > 1 and "Dividir" in modo_valor) else valor

        novo = pd.DataFrame([[
            tipo, conta, conta_destino, 
            categoria, descricao, valor_final, data, parcelas, modo_valor
        ]], columns=["Tipo", "Conta", "Conta Destino", "Categoria", "Descrição", "Valor", "Data", "Parcelas", "Modo Valor"])
        
        st.session_state.lancamentos = pd.concat([st.session_state.lancamentos, novo], ignore_index=True)
        st.success("Lançamento salvo com sucesso!")
