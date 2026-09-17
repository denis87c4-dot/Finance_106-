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

# Base em memória para Categorias (com algumas iniciais)
if "categorias" not in st.session_state:
    st.session_state.categorias = ["Alimentação", "Transporte", "Moradia", "Salário", "Lazer"]

# Base em memória para Contas (Accounts) (com algumas iniciais)
if "contas" not in st.session_state:
    st.session_state.contas = ["Conta Corrente", "Carteira", "Cartão de Crédito", "Poupança"]

# ==================== DASHBOARD ====================
if aba == "Dashboard":
    st.title("📊 Dashboard Financeiro")
    if not st.session_state.lancamentos.empty:
        st.dataframe(st.session_state.lancamentos, use_container_width=True)
        
        # Filtros simples para métricas (excluindo transferências do cálculo de receita/despesa líquida se preferir)
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
        nova_cat = st.text_input("Nova Categoria")
        if st.button("Adicionar Categoria"):
            if nova_cat and nova_cat not in st.session_state.categorias:
                st.session_state.categorias.append(nova_cat)
                st.success(f"Categoria '{nova_cat}' adicionada com sucesso!")
            else:
                st.warning("Insira uma categoria válida ou que não exista.")
        
        st.write("Categorias atuais:", st.session_state.categorias)

    with tab_acc:
        st.subheader("Gerenciar Contas")
        nova_conta = st.text_input("Nova Conta (Account)")
        if st.button("Adicionar Conta"):
            if nova_conta and nova_conta not in st.session_state.contas:
                st.session_state.contas.append(nova_conta)
                st.success(f"Conta '{nova_conta}' adicionada com sucesso!")
            else:
                st.warning("Insira uma conta válida ou que não exista.")
        
        st.write("Contas atuais:", st.session_state.contas)

# ==================== LANÇAMENTOS ====================
elif aba == "Lançamentos":
    st.title("💵 Registrar Lançamento")
    
    tipo = st.selectbox("Tipo de Lançamento", ["Receita", "Despesa", "Transferência"])
    
    # Seleção de Contas com opção de criar nova rapidamente
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        conta_opcoes = st.session_state.contas + ["+ Adicionar nova conta"]
        conta_escolha = st.selectbox("Conta", conta_opcoes)
        if conta_escolha == "+ Adicionar nova conta":
            nova_conta_input = st.text_input("Nome da nova conta")
            if nova_conta_input and nova_conta_input not in st.session_state.contas:
                st.session_state.contas.append(nova_conta_input)
                conta = nova_conta_input
            else:
                conta = conta_escolha
        else:
            conta = conta_escolha

    # Conta de destino caso seja Transferência
    conta_destino = ""
    if tipo == "Transferência":
        with col_c2:
            conta_dest_opcoes = st.session_state.contas + ["+ Adicionar nova conta"]
            conta_dest_escolha = st.selectbox("Conta de Destino", conta_dest_opcoes)
            if conta_dest_escolha == "+ Adicionar nova conta":
                nova_dest_input = st.text_input("Nome da conta de destino")
                if nova_dest_input and nova_dest_input not in st.session_state.contas:
                    st.session_state.contas.append(nova_dest_input)
                    conta_destino = nova_dest_input
                else:
                    conta_destino = conta_dest_escolha
            else:
                conta_destino = conta_dest_escolha

    # Seleção de Categoria com opção de criar nova rapidamente
    cat_opcoes = st.session_state.categorias + ["+ Adicionar nova categoria"]
    cat_escolha = st.selectbox("Categoria", cat_opcoes)
    if cat_escolha == "+ Adicionar nova categoria":
        nova_cat_input = st.text_input("Nome da nova categoria")
        if nova_cat_input and nova_cat_input not in st.session_state.categorias:
            st.session_state.categorias.append(nova_cat_input)
            categoria = nova_cat_input
        else:
            categoria = cat_escolha
    else:
        categoria = cat_escolha

    descricao = st.text_input("Descrição")
    valor = st.number_input("Valor Total (R$)", min_value=0.0, step=10.0)
    data = st.date_input("Data Inicial")
    
    # Parcelamento
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        parcelas = st.number_input("Número de Parcelas", min_value=1, max_value=120, value=1, step=1)
    
    modo_valor = "Integral"
    if parcelas > 1:
        with col_p2:
            modo_valor = st.radio("Como tratar o valor nas parcelas?", ["Dividir (Valor total dividido pelas parcelas)", "Replicar (Valor integral em cada parcela)"])

    if st.button("Salvar Lançamento"):
        if parcelas > 1:
            valor_final = valor / parcelas if "Dividir" in modo_valor else valor
            # Aqui você poderia gerar um loop para criar linhas múltiplas se desejar expandir datas futuras. 
            # Por simplicidade de salvamento inicial, salvamos o registro indicando as regras:
        else:
            valor_final = valor

        novo = pd.DataFrame([[
            tipo, conta, conta_destino if tipo == "Transferência" else "-", 
            categoria, descricao, valor_final, data, parcelas, modo_valor
        ]], columns=["Tipo", "Conta", "Conta Destino", "Categoria", "Descrição", "Valor", "Data", "Parcelas", "Modo Valor"])
        
        st.session_state.lancamentos = pd.concat([st.session_state.lancamentos, novo], ignore_index=True)
        st.success("Lançamento salvo com sucesso!")
