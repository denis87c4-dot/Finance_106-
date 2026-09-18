import pandas as pd
import streamlit as st

# Configuração da página
st.set_page_config(page_title="Fluxo Básico", page_icon="💰", layout="wide")

# ==================== NAVEGAÇÃO LATERAL ====================
# Alterado a ordem e os nomes das abas conforme solicitado
aba = st.sidebar.radio(
    "Navegação", ["Dashboard", "Cadastro", "Cadastro de Categorias e Contas"]
)

# ==================== ESTADOS DA SESSÃO ====================
# Base de dados em memória para Lançamentos
if "lancamentos" not in st.session_state:
  st.session_state.lancamentos = pd.DataFrame(
      columns=[
          "Tipo",
          "Conta",
          "Conta Destino",
          "Categoria",
          "Descrição",
          "Valor",
          "Data",
          "Parcelas",
          "Modo Valor",
      ]
  )

# Base em memória para Categorias
if "categorias" not in st.session_state:
  st.session_state.categorias = [
      "Alimentação",
      "Transporte",
      "Moradia",
      "Salário",
      "Lazer",
  ]

# Base em memória para Contas
if "contas" not in st.session_state:
  st.session_state.contas = [
      "Conta Corrente",
      "Carteira",
      "Cartão de Crédito",
      "Poupança",
  ]


# ==================== DASHBOARD ====================
if aba == "Dashboard":
  st.title("📊 Dashboard Financeiro")
  if not st.session_state.lancamentos.empty:
    st.dataframe(st.session_state.lancamentos, use_container_width=True)

    df_rec = st.session_state.lancamentos[
        st.session_state.lancamentos["Tipo"] == "Receita"
    ]
    df_desp = st.session_state.lancamentos[
        st.session_state.lancamentos["Tipo"] == "Despesa"
    ]

    col1, col2 = st.columns(2)
    with col1:
      st.metric("Total Receitas", f"R$ {df_rec['Valor'].sum():,.2f}")
    with col2:
      st.metric("Total Despesas", f"R$ {df_desp['Valor'].sum():,.2f}")
  else:
    st.info("Nenhum lançamento registrado ainda.")


# ==================== CADASTRO (ANTIGA TELA DE LANÇAMENTOS) ====================
elif aba == "Cadastro":
  st.title("💵 Registrar Lançamento")

  tipo = st.selectbox(
      "Tipo de Lançamento", ["Receita", "Despesa", "Transferência"]
  )

  st.markdown("---")

  col_origem, col_dest = st.columns(2)

  with col_origem:
    conta_opcoes = st.session_state.contas + ["+ Adicionar nova conta"]
    conta_escolha = st.selectbox("Conta Principal / Origem", conta_opcoes)

    if conta_escolha == "+ Adicionar nova conta":
      nova_conta_input = st.text_input(
          "Digite o nome da nova conta", key="input_nova_conta"
      )
      if nova_conta_input and nova_conta_input not in st.session_state.contas:
        st.session_state.contas.append(nova_conta_input)
        conta = nova_conta_input
      else:
        conta = ""
    else:
      conta = conta_escolha

  conta_destino = "-"
  if tipo == "Transferência":
    with col_dest:
      conta_dest_opcoes = st.session_state.contas + [
          "+ Adicionar nova conta"
      ]
      conta_dest_escolha = st.selectbox(
          "Conta de Destino", conta_dest_opcoes, key="select_conta_dest"
      )

      if conta_dest_escolha == "+ Adicionar nova conta":
        nova_dest_input = st.text_input(
            "Digite o nome da conta de destino", key="input_nova_dest"
        )
        if nova_dest_input and nova_dest_input not in st.session_state.contas:
          st.session_state.contas.append(nova_dest_input)
          conta_destino = nova_dest_input
        else:
          conta_destino = ""
      else:
        conta_destino = conta_dest_escolha

  if tipo != "Transferência":
    cat_opcoes = st.session_state.categorias + ["+ Adicionar nova categoria"]
    cat_escolha = st.selectbox("Categoria", cat_opcoes)
    if cat_escolha == "+ Adicionar nova categoria":
      nova_cat_input = st.text_input(
          "Digite o nome da nova categoria", key="input_nova_cat"
      )
      if nova_cat_input and nova_cat_input not in st.session_state.categorias:
        st.session_state.categorias.append(nova_cat_input)
        categoria = nova_cat_input
      else:
        categoria = ""
    else:
      categoria = cat_escolha
  else:
    categoria = "Transferência"

  st.markdown("---")

  descricao = st.text_input(
      "Descrição", placeholder="Ex: Supermercado, Aluguel, Salário..."
  )

  col_val1, col_val2 = st.columns(2)
  with col_val1:
    valor = st.number_input(
        "Valor Total (R$)", min_value=0.0, step=10.0, format="%.2f"
    )
  with col_val2:
    data = st.date_input("Data do Lançamento / 1ª Parcela")

  parcelas = 1
  modo_valor = "Integral"

  if tipo in ["Despesa", "Receita"]:
    with st.expander("⚙️ Opções Avançadas / Parcelamento", expanded=False):
      col_p1, col_p2 = st.columns(2)
      with col_p1:
        parcelas = st.number_input(
            "Número de Parcelas", min_value=1, max_value=120, value=1, step=1
        )
      if parcelas > 1:
        with col_p2:
          modo_valor = st.radio(
              "Modo de cálculo do valor",
              [
                  "Dividir (Total ÷ Parcelas)",
                  "Replicar (Valor integral por parcela)",
              ],
          )

        valor_parcela_calc = (
            valor / parcelas if "Dividir" in modo_valor else valor
        )
        st.info(
            f"ℹ️ Serão geradas **{parcelas} parcelas** mensais. Valor por"
            f" parcela: **R$ {valor_parcela_calc:,.2f}**"
        )

  st.markdown("")

  if st.button(
      "💾 Salvar Lançamento", type="primary", use_container_width=True
  ):
    erros = []
    if not descricao:
      erros.append("A descrição não pode estar vazia.")
    if valor <= 0:
      erros.append("O valor deve ser maior que zero.")
    if not conta:
      erros.append("Selecione uma conta principal válida.")
    if tipo == "Transferência" and conta == conta_destino:
      erros.append(
          "A conta de origem e destino não podem ser iguais em uma"
          " transferência."
      )

    if erros:
      for erro in erros:
        st.error(erro)
    else:
      novos_registros = []

      for i in range(parcelas):
        data_parcela = pd.to_datetime(data) + pd.DateOffset(months=i)

        if parcelas > 1 and "Dividir" in modo_valor:
          valor_final = valor / parcelas
        else:
          valor_final = valor

        desc_formatada = (
            f"{descricao} ({i+1}/{parcelas})" if parcelas > 1 else descricao
        )
        parcela_str = f"{i+1}/{parcelas}" if parcelas > 1 else "Única"

        novos_registros.append([
            tipo,
            conta,
            conta_destino,
            categoria,
            desc_formatada,
            valor_final,
            data_parcela.date(),
            parcela_str,
            modo_valor,
        ])

      df_novos = pd.DataFrame(
          novos_registros,
          columns=[
              "Tipo",
              "Conta",
              "Conta Destino",
              "Categoria",
              "Descrição",
              "Valor",
              "Data",
              "Parcelas",
              "Modo Valor",
          ],
      )

      st.session_state.lancamentos = pd.concat(
          [st.session_state.lancamentos, df_novos], ignore_index=True
      )
      st.success(
          f"Lançamento(s) salvo(s) com sucesso! ({parcelas} registro(s)"
          " gerado(s))"
      )


# ==================== CADASTRO DE CATEGORIAS E CONTAS ====================
elif aba == "Cadastro de Categorias e Contas":
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
