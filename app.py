import io
import json
import zipfile
import pandas as pd
import plotly.express as px
import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="Fluxo Financeiro Profissional", page_icon="💰", layout="wide"
)

# ==================== NAVEGAÇÃO LATERAL ====================
aba = st.sidebar.radio(
    "Navegação",
    [
        "Dashboard",
        "Lançamentos",
        "Cadastro",
        "Cadastro de Categorias e Contas",
        "Cartões de Crédito",
        "Backup & Segurança",
    ],
)

# ==================== ESTADOS DA SESSÃO ====================
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
          "Status",
      ]
  )

# Garantir compatibilidade com bases antigas que não tinham a coluna Status
if (
    not st.session_state.lancamentos.empty
    and "Status" not in st.session_state.lancamentos.columns
):
  st.session_state.lancamentos["Status"] = "Efetivado"

if "categorias" not in st.session_state:
  st.session_state.categorias = [
      "Alimentação",
      "Transporte",
      "Moradia",
      "Salário",
      "Lazer",
  ]

if "contas" not in st.session_state:
  st.session_state.contas = [
      "Conta Corrente",
      "Carteira",
      "Cartão de Crédito",
      "Poupança",
  ]

if "cartoes" not in st.session_state:
  st.session_state.cartoes = [
      {
          "Nome": "Nubank",
          "Limite": 5000.0,
          "Fechamento": 5,
          "Vencimento": 12,
      },
      {
          "Nome": "Inter",
          "Limite": 3000.0,
          "Fechamento": 10,
          "Vencimento": 17,
      },
  ]


# ==================== DASHBOARD ====================
if aba == "Dashboard":
  st.title("📊 Dashboard Financeiro")

  if not st.session_state.lancamentos.empty:
    df_temp = st.session_state.lancamentos.copy()
    df_temp["Data"] = pd.to_datetime(df_temp["Data"])
    if "Status" not in df_temp.columns:
      df_temp["Status"] = "Efetivado"

    # ==================== NOVO BLOCO: CONTROLE DE BUDGET VS EFETIVADO (MÊS) ====================
    st.markdown("---")
    st.subheader("🎯 Controle Orçamentário: Budget vs. Efetivado por Categoria")

    df_temp["AnoMes"] = df_temp["Data"].dt.to_period("M").astype(str)
    # Ordenar meses do mais recente para o mais antigo (mês atual em evidência)
    meses_disponiveis = sorted(df_temp["AnoMes"].unique().tolist(), reverse=True)

    if not meses_disponiveis:
      meses_disponiveis = [pd.Timestamp.now().strftime("%Y-%m")]

    col_bm1, col_bm2 = st.columns([2, 2])
    with col_bm1:
      mes_atual_str = pd.Timestamp.now().strftime("%Y-%m")
      default_mes = (
          [mes_atual_str] if mes_atual_str in meses_disponiveis else [meses_disponiveis[0]]
      )
      mes_selecionado = st.selectbox(
          "📅 Selecione o Mês para Análise do Budget",
          meses_disponiveis,
          index=meses_disponiveis.index(default_mes[0]) if default_mes[0] in meses_disponiveis else 0,
      )

    with col_bm2:
      tipo_orcamento = st.selectbox(
          "Tipo de Lançamento para o Budget", ["Despesa", "Receita"]
      )

    df_mes = df_temp[
        (df_temp["AnoMes"] == mes_selecionado)
        & (df_temp["Tipo"] == tipo_orcamento)
    ]

    if df_mes.empty:
      st.info(f"Nenhum lançamento encontrado para o período {mes_selecionado}.")
    else:
      df_pivot = (
          df_mes.pivot_table(
              index="Categoria",
              columns="Status",
              values="Valor",
              aggfunc="sum",
          )
          .reset_index()
          .fillna(0.0)
      )

      if "Orçado" not in df_pivot.columns:
        df_pivot["Orçado"] = 0.0
      if "Efetivado" not in df_pivot.columns:
        df_pivot["Efetivado"] = 0.0

      df_budget_final = pd.DataFrame()
      df_budget_final["Categoria"] = df_pivot["Categoria"]
      df_budget_final["Budget"] = df_pivot["Orçado"]
      df_budget_final["Efetivado"] = df_pivot["Efetivado"]

      if tipo_orcamento == "Despesa":
        df_budget_final["Diferença (Saldo)"] = (
            df_budget_final["Budget"] - df_budget_final["Efetivado"]
        )
      else:
        df_budget_final["Diferença (Saldo)"] = (
            df_budget_final["Efetivado"] - df_budget_final["Budget"]
        )

      df_budget_final["% Utilizado"] = df_budget_final.apply(
          lambda row: (row["Efetivado"] / row["Budget"] * 100)
          if row["Budget"] > 0
          else 0.0,
          axis=1,
      )

      st.dataframe(
          df_budget_final.style.format(
              {
                  "Budget": "R$ {:,.2f}",
                  "Efetivado": "R$ {:,.2f}",
                  "Diferença (Saldo)": "R$ {:,.2f}",
                  "% Utilizado": "{:.1f}%",
              }
          ),
          use_container_width=True,
          hide_index=True,
      )
    # ==================== FIM DO BLOCO DE BUDGET ====================

    # ==================== FILTROS DINÂMICOS ====================
    st.markdown("---")
    st.markdown("### 🔍 Filtros Dinâmicos")
    with st.expander("🛠️ Personalizar Visualização do Dashboard", expanded=True):
      col_f1, col_f2, col_f3, col_f4 = st.columns(4)

      with col_f1:
        tipo_periodo = st.selectbox(
            "Agrupamento Temporal",
            ["Mensal", "Trimestral", "Quadrimestral", "Semestral", "Anual"],
        )

      with col_f2:
        # Anos ordenados do mais recente para o mais antigo (decrescente)
        anos_disponiveis = sorted(
            df_temp["Data"].dt.year.dropna().unique().tolist(), reverse=True
        )
        if not anos_disponiveis:
          anos_disponiveis = [pd.Timestamp.now().year]
        ano_selecionado = st.multiselect(
            "Filtrar Anos",
            anos_disponiveis,
            default=anos_disponiveis,
        )

      with col_f3:
        contas_disponiveis = st.session_state.contas
        conta_selecionada = st.multiselect(
            "Filtrar Contas/Cartões",
            contas_disponiveis,
            default=contas_disponiveis,
        )

      with col_f4:
        categorias_disponiveis = st.session_state.categorias
        categoria_selecionada = st.multiselect(
            "Filtrar Categorias",
            categorias_disponiveis,
            default=categorias_disponiveis,
        )

      col_f5, col_f6 = st.columns(2)
      with col_f5:
        filtro_tipo_lanc = st.multiselect(
            "Tipos de Lançamento",
            ["Receita", "Despesa", "Transferência"],
            default=["Receita", "Despesa", "Transferência"],
        )

      with col_f6:
        status_disponiveis = ["Efetivado", "Orçado"]
        status_selecionado = st.multiselect(
            "Status (Budget / Realizado)",
            status_disponiveis,
            default=status_disponiveis,
        )

    # Aplicar filtros no DataFrame
    if ano_selecionado:
      df_temp = df_temp[df_temp["Data"].dt.year.isin(ano_selecionado)]
    if conta_selecionada:
      df_temp = df_temp[
          df_temp["Conta"].isin(conta_selecionada)
          | df_temp["Conta Destino"].isin(conta_selecionada)
      ]
    if categoria_selecionada:
      df_temp = df_temp[df_temp["Categoria"].isin(categoria_selecionada)]
    if filtro_tipo_lanc:
      df_temp = df_temp[df_temp["Tipo"].isin(filtro_tipo_lanc)]
    if status_selecionado:
      df_temp = df_temp[df_temp["Status"].isin(status_selecionado)]

    if df_temp.empty:
      st.warning(
          "Nenhum lançamento encontrado com os filtros selecionados no momento."
      )
    else:
      if tipo_periodo == "Mensal":
        df_temp["Periodo"] = df_temp["Data"].dt.to_period("M").astype(str)
      elif tipo_periodo == "Trimestral":
        df_temp["Periodo"] = df_temp["Data"].dt.to_period("Q").astype(str)
      elif tipo_periodo == "Quadrimestral":
        df_temp["Periodo"] = (
            df_temp["Data"].dt.year.astype(str)
            + "-Q"
            + ((df_temp["Data"].dt.month - 1) // 4 + 1).astype(str)
        )
      elif tipo_periodo == "Semestral":
        df_temp["Periodo"] = (
            df_temp["Data"].dt.year.astype(str)
            + "-S"
            + ((df_temp["Data"].dt.month - 1) // 6 + 1).astype(str)
        )
      else:
        df_temp["Periodo"] = df_temp["Data"].dt.year.astype(str)

      df_rec_m = (
          df_temp[df_temp["Tipo"] == "Receita"]
          .groupby("Periodo")["Valor"]
          .sum()
          .reset_index(name="Income")
      )
      df_desp_m = (
          df_temp[df_temp["Tipo"] == "Despesa"]
          .groupby("Periodo")["Valor"]
          .sum()
          .reset_index(name="Expense")
      )

      df_resumo = pd.merge(
          df_rec_m, df_desp_m, on="Periodo", how="outer"
      ).fillna(0)
      df_resumo = df_resumo.sort_values("Periodo").reset_index(drop=True)

      df_resumo["Cash Flow"] = df_resumo["Income"] - df_resumo["Expense"]
      df_resumo["Cumulative"] = df_resumo["Cash Flow"].cumsum()

      df_resumo = df_resumo.rename(columns={"Periodo": "Período"})

      st.markdown("---")
      st.subheader(f"📅 Resumo Financeiro ({tipo_periodo})")

      def color_negative(val):
        if isinstance(val, (int, float)) and val < 0:
          return "color: #ff4b4b; font-weight: bold;"
        return ""

      df_styled = df_resumo.style.format(
          {
              "Income": "R$ {:,.2f}",
              "Expense": "R$ {:,.2f}",
              "Cash Flow": "R$ {:,.2f}",
              "Cumulative": "R$ {:,.2f}",
          }
      ).map(color_negative, subset=["Cash Flow", "Cumulative"])

      st.dataframe(df_styled, use_container_width=True)

      st.markdown("---")
      st.subheader("📈 Análise Gráfica Dinâmica")

      col_g1, col_g2 = st.columns(2)

      with col_g1:
        st.markdown("##### 🌊 Cash Flow vs. Cumulative")
        df_melt_linhas = df_resumo.melt(
            id_vars=["Período"],
            value_vars=["Cash Flow", "Cumulative"],
            var_name="Métrica",
            value_name="Valor",
        )

        fig_linhas = px.line(
            df_melt_linhas,
            x="Período",
            y="Valor",
            color="Métrica",
            markers=True,
            color_discrete_map={
                "Cash Flow": "#00CC96",
                "Cumulative": "#636EFA",
            },
        )
        fig_linhas.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis_title="",
            yaxis_title="R$ (Reais)",
            legend_title="",
            margin=dict(l=10, r=10, t=10, b=10),
        )
        st.plotly_chart(fig_linhas, use_container_width=True)

      with col_g2:
        st.markdown("##### 📊 Receitas (Income) vs. Despesas (Expense)")
        df_melt_barras = df_resumo.melt(
            id_vars=["Período"],
            value_vars=["Income", "Expense"],
            var_name="Tipo",
            value_name="Valor",
        )

        fig_barras = px.bar(
            df_melt_barras,
            x="Período",
            y="Valor",
            color="Tipo",
            barmode="group",
            color_discrete_map={"Income": "#00CC96", "Expense": "#EF553B"},
        )
        fig_barras.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis_title="",
            yaxis_title="R$ (Reais)",
            legend_title="",
            margin=dict(l=10, r=10, t=10, b=10),
        )
        st.plotly_chart(fig_barras, use_container_width=True)

      st.markdown("---")
      st.subheader("📋 Lançamentos Filtrados")
      st.dataframe(df_temp, use_container_width=True)

      df_rec_tot = df_temp[df_temp["Tipo"] == "Receita"]
      df_desp_tot = df_temp[df_temp["Tipo"] == "Despesa"]

      col1, col2 = st.columns(2)
      with col1:
        st.metric(
            "Total Receitas (Filtrado)", f"R$ {df_rec_tot['Valor'].sum():,.2f}"
        )
      with col2:
        st.metric(
            "Total Despesas (Filtrado)", f"R$ {df_desp_tot['Valor'].sum():,.2f}"
        )
  else:
    st.info("Nenhum lançamento registrado ainda.")


# ==================== LANÇAMENTOS (GERENCIAMENTO INTELIGENTE) ====================
elif aba == "Lançamentos":
  st.title("📋 Central Inteligente de Lançamentos")
  st.write(
      "Consulte, filtre, edite ou exclua seus lançamentos com agilidade e"
      " precisão."
  )

  if st.session_state.lancamentos.empty:
    st.info(
        "Nenhum lançamento cadastrado até o momento. Vá até a aba 'Cadastro'"
        " para adicionar registros."
    )
  else:
    df_lanc = st.session_state.lancamentos.copy()
    df_lanc["Data"] = pd.to_datetime(df_lanc["Data"]).dt.date
    if "Status" not in df_lanc.columns:
      df_lanc["Status"] = "Efetivado"

    with st.expander("🔍 Filtros Avançados e Busca Global", expanded=True):
      col_b1, col_b2 = st.columns([2, 1])
      with col_b1:
        busca_texto = st.text_input(
            "🔎 Busca Rápida (Descrição, Categoria ou Conta)",
            placeholder="Digite para filtrar instantaneamente...",
        )
      with col_b2:
        tipos_filtro = st.multiselect(
            "Filtrar por Tipo",
            ["Receita", "Despesa", "Transferência"],
            default=["Receita", "Despesa", "Transferência"],
        )

      col_f1, col_f2, col_f3 = st.columns(3)
      with col_f1:
        contas_disp = st.session_state.contas
        filtro_conta = st.multiselect(
            "Contas / Origem", contas_disp, default=[]
        )
      with col_f2:
        cat_disp = st.session_state.categorias + ["Transferência"]
        filtro_cat = st.multiselect("Categorias", cat_disp, default=[])
      with col_f3:
        status_disp = ["Efetivado", "Orçado"]
        filtro_status_lanc = st.multiselect(
            "Status", status_disp, default=status_disp
        )

      min_data = df_lanc["Data"].min()
      max_data = df_lanc["Data"].max()
      periodo_datas = st.date_input(
          "Intervalo de Datas",
          value=(min_data, max_data),
          min_value=min_data,
          max_value=max_data,
      )

    df_filtrado = df_lanc[
        df_lanc["Tipo"].isin(tipos_filtro)
        & df_lanc["Status"].isin(filtro_status_lanc)
    ]

    if busca_texto:
      termo = busca_texto.lower()
      df_filtrado = df_filtrado[
          df_filtrado["Descrição"].str.lower().str.contains(termo, na=False)
          | df_filtrado["Categoria"].str.lower().str.contains(termo, na=False)
          | df_filtrado["Conta"].str.lower().str.contains(termo, na=False)
      ]

    if filtro_conta:
      df_filtrado = df_filtrado[
          df_filtrado["Conta"].isin(filtro_conta)
          | df_filtrado["Conta Destino"].isin(filtro_conta)
      ]

    if filtro_cat:
      df_filtrado = df_filtrado[df_filtrado["Categoria"].isin(filtro_cat)]

    if isinstance(periodo_datas, tuple) and len(periodo_datas) == 2:
      data_inicio, data_fim = periodo_datas
      df_filtrado = df_filtrado[
          (df_filtrado["Data"] >= data_inicio)
          & (df_filtrado["Data"] <= data_fim)
      ]

    st.markdown("---")
    m1, m2, m3 = st.columns(3)
    total_filtrado_val = df_filtrado["Valor"].sum()
    qtd_registros = len(df_filtrado)

    m1.metric("📊 Registros Encontrados", f"{qtd_registros} itens")
    m2.metric("💰 Soma dos Valores Exibidos", f"R$ {total_filtrado_val:,.2f}")
    m3.metric(
        "📈 Média por Lançamento",
        (
            f"R$ {total_filtrado_val / qtd_registros:,.2f}"
            if qtd_registros > 0
            else "R$ 0,00"
        ),
    )
    st.markdown("---")

    st.subheader("📑 Registros Correspondentes")

    if df_filtrado.empty:
      st.warning(
          "Nenhum lançamento corresponde aos filtros aplicados na busca."
      )
    else:
      df_exibicao = df_filtrado.copy()
      df_exibicao.index.name = "ID_Original"
      df_exibicao = df_exibicao.reset_index()

      st.dataframe(
          df_exibicao,
          use_container_width=True,
          hide_index=True,
          column_config={
              "ID_Original": st.column_config.NumberColumn(
                  "ID", help="Identificador único do lançamento"
              ),
              "Valor": st.column_config.NumberColumn(
                  "Valor (R$)", format="R$ %.2f"
              ),
              "Data": st.column_config.DateColumn(
                  "Data", format="DD/MM/YYYY"
              ),
          },
      )

      st.markdown("### ⚡ Ações em Lançamentos")
      acao_escolhida = st.radio(
          "Selecione a Ação desejada",
          [
              "Nenhuma",
              "✏️ Editar Lançamento",
              "🗑️ Excluir Lançamento Específico",
              "⚠️ Excluir TODOS os Filtrados",
          ],
          horizontal=True,
      )

      if acao_escolhida == "✏️ Editar Lançamento":
        st.markdown("#### Editar Registro")
        indices_disponiveis = df_filtrado.index.tolist()
        id_para_editar = st.selectbox(
            "Selecione o ID do lançamento que deseja editar",
            indices_disponiveis,
            format_func=lambda x: f"ID {x} - [{st.session_state.lancamentos.loc[x, 'Tipo']}] {st.session_state.lancamentos.loc[x, 'Descrição']} (R$ {st.session_state.lancamentos.loc[x, 'Valor']:,.2f})",
        )

        if id_para_editar is not None:
          reg_atual = st.session_state.lancamentos.loc[id_para_editar]

          with st.form("form_edicao_lancamento"):
            col_e1, col_e2 = st.columns(2)
            with col_e1:
              novo_tipo = st.selectbox(
                  "Tipo",
                  ["Receita", "Despesa", "Transferência"],
                  index=["Receita", "Despesa", "Transferência"].index(
                      reg_atual["Tipo"]
                  ),
              )
              nova_conta = st.selectbox(
                  "Conta",
                  st.session_state.contas,
                  index=(
                      st.session_state.contas.index(reg_atual["Conta"])
                      if reg_atual["Conta"] in st.session_state.contas
                      else 0
                  ),
              )
              nova_categoria = st.selectbox(
                  "Categoria",
                  st.session_state.categorias,
                  index=(
                      st.session_state.categorias.index(reg_atual["Categoria"])
                      if reg_atual["Categoria"]
                      in st.session_state.categorias
                      else 0
                  ),
              )
            with col_e2:
              nova_desc = st.text_input(
                  "Descrição", value=reg_atual["Descrição"]
              )
              novo_valor = st.number_input(
                  "Valor (R$)",
                  min_value=0.0,
                  value=float(reg_atual["Valor"]),
                  step=10.0,
              )
              nova_data = st.date_input(
                  "Data", value=pd.to_datetime(reg_atual["Data"])
              )
              status_atual_reg = (
                  reg_atual["Status"]
                  if "Status" in reg_atual
                  else "Efetivado"
              )
              novo_status = st.selectbox(
                  "Status",
                  ["Efetivado", "Orçado"],
                  index=["Efetivado", "Orçado"].index(status_atual_reg),
              )

            btn_salvar_edicao = st.form_submit_button(
                "💾 Salvar Alterações", use_container_width=True
            )
            if btn_salvar_edicao:
              st.session_state.lancamentos.loc[id_para_editar, "Tipo"] = (
                  novo_tipo
              )
              st.session_state.lancamentos.loc[id_para_editar, "Conta"] = (
                  nova_conta
              )
              st.session_state.lancamentos.loc[
                  id_para_editar, "Categoria"
              ] = nova_categoria
              st.session_state.lancamentos.loc[id_para_editar, "Descrição"] = (
                  nova_desc
              )
              st.session_state.lancamentos.loc[id_para_editar, "Valor"] = (
                  novo_valor
              )
              st.session_state.lancamentos.loc[id_para_editar, "Data"] = (
                  nova_data
              )
              st.session_state.lancamentos.loc[id_para_editar, "Status"] = (
                  novo_status
              )
              st.success(f"Lançamento ID {id_para_editar} atualizado com sucesso!")
              st.rerun()

      elif acao_escolhida == "🗑️ Excluir Lançamento Específico":
        st.markdown("#### Excluir Registro Individual")
        indices_disponiveis = df_filtrado.index.tolist()
        id_para_excluir = st.selectbox(
            "Selecione o ID para excluir",
            indices_disponiveis,
            format_func=lambda x: f"ID {x} - [{st.session_state.lancamentos.loc[x, 'Tipo']}] {st.session_state.lancamentos.loc[x, 'Descrição']} (R$ {st.session_state.lancamentos.loc[x, 'Valor']:,.2f})",
            key="select_excluir_unico",
        )

        if st.button(
            "🗑️ Confirmar Exclusão deste Lançamento", type="primary"
        ):
          st.session_state.lancamentos = st.session_state.lancamentos.drop(
              id_para_excluir
          ).reset_index(drop=True)
          st.success(
              f"Lançamento ID {id_para_excluir} removido com sucesso!"
          )
          st.rerun()

      elif acao_escolhida == "⚠️ Excluir TODOS os Filtrados":
        st.warning(
            f"Atenção: Você está prestes a excluir todos os {len(df_filtrado)}"
            " registros exibidos no filtro atual."
        )
        confirmacao = st.text_input(
            "Digite 'EXCLUIR' para confirmar a operação em lote:"
        )
        if st.button(
            "🗑️ Executar Exclusão em Lote", type="primary", use_container_width=True
        ):
          if confirmacao == "EXCLUIR":
            indices_para_remover = df_filtrado.index.tolist()
            st.session_state.lancamentos = (
                st.session_state.lancamentos.drop(indices_para_remover)
                .reset_index(drop=True)
            )
            st.success(
                f"{len(indices_para_remover)} lançamentos foram excluídos com"
                " sucesso!"
            )
            st.rerun()
          else:
            st.error("Confirmação incorreta. Digite 'EXCLUIR' exatamente.")


# ==================== CADASTRO (LANÇAMENTOS) ====================
elif aba == "Cadastro":
  st.title("💵 Registrar Lançamento")

  col_tipo_cad, col_status_cad = st.columns(2)
  with col_tipo_cad:
    tipo = st.selectbox(
        "Tipo de Lançamento", ["Receita", "Despesa", "Transferência"]
    )
  with col_status_cad:
    status_lancamento = st.selectbox(
        "Status",
        ["Efetivado", "Orçado"],
        help=(
            "Use 'Orçado' para previsões/planejamento e 'Efetivado' para o que"
            " já aconteceu."
        ),
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
        valor_final = (
            (valor / parcelas)
            if (parcelas > 1 and "Dividir" in modo_valor)
            else valor
        )
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
            status_lancamento,
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
              "Status",
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


# ==================== CARTÕES DE CRÉDITO ====================
elif aba == "Cartões de Crédito":
  st.title("💳 Gestão de Cartões de Crédito")
  st.write(
      "Cadastre seus cartões, acompanhe limites e visualize faturas em"
      " aberto baseadas nos lançamentos vinculados."
  )

  tab_gerenciar, tab_faturas = st.tabs(
      ["📝 Cadastrar / Meus Cartões", "📊 Faturas & Limites"]
  )

  with tab_gerenciar:
    st.subheader("Cadastrar Novo Cartão")
    with st.form("form_cad_cartao"):
      col_c1, col_c2 = st.columns(2)
      with col_c1:
        nome_cartao = st.text_input(
            "Nome do Cartão", placeholder="Ex: Visa Platinum, Mastercard..."
        )
        limite_cartao = st.number_input(
            "Limite Total (R$)", min_value=0.0, step=100.0, format="%.2f"
        )
      with col_c2:
        dia_fechamento = st.number_input(
            "Dia de Fechamento da Fatura",
            min_value=1,
            max_value=31,
            value=1,
            step=1,
        )
        dia_vencimento = st.number_input(
            "Dia de Vencimento da Fatura",
            min_value=1,
            max_value=31,
            value=10,
            step=1,
        )

      submitted_cartao = st.form_submit_button(
          "💾 Salvar Cartão", use_container_width=True
      )
      if submitted_cartao:
        if not nome_cartao:
          st.error("O nome do cartão não pode estar vazio.")
        elif limite_cartao <= 0:
          st.error("O limite deve ser maior que zero.")
        else:
          nomes_existentes = [c["Nome"] for c in st.session_state.cartoes]
          if nome_cartao in nomes_existentes:
            st.warning("Já existe um cartão cadastrado com esse nome.")
          else:
            st.session_state.cartoes.append({
                "Nome": nome_cartao,
                "Limite": limite_cartao,
                "Fechamento": int(dia_fechamento),
                "Vencimento": int(dia_vencimento),
            })
            if nome_cartao not in st.session_state.contas:
              st.session_state.contas.append(nome_cartao)
            st.success(f"Cartão '{nome_cartao}' cadastrado com sucesso!")
            st.rerun()

    st.markdown("---")
    st.subheader("Cartões Cadastrados")
    if st.session_state.cartoes:
      df_cartoes = pd.DataFrame(st.session_state.cartoes)
      st.dataframe(df_cartoes, use_container_width=True)
    else:
      st.info("Nenhum cartão cadastrado.")

  with tab_faturas:
    st.subheader("Visão Geral de Faturas e Limites")

    if not st.session_state.cartoes:
      st.warning(
          "Cadastre pelo menos um cartão na aba anterior para ver as faturas."
      )
    else:
      nomes_cartoes = [c["Nome"] for c in st.session_state.cartoes]
      cartao_selecionado = st.selectbox(
          "Selecione o Cartão", nomes_cartoes, key="select_cartao_detalhe"
      )

      dados_cartao = next(
          c for c in st.session_state.cartoes if c["Nome"] == cartao_selecionado
      )
      limite_total = dados_cartao["Limite"]

      df_lanc = st.session_state.lancamentos
      if not df_lanc.empty:
        df_cartao_lanc = df_lanc[
            (df_lanc["Conta"] == cartao_selecionado)
            | (df_lanc["Conta Destino"] == cartao_selecionado)
        ]
      else:
        df_cartao_lanc = pd.DataFrame()

      if not df_cartao_lanc.empty:
        total_gasto = df_cartao_lanc[
            df_cartao_lanc["Tipo"] == "Despesa"
        ]["Valor"].sum()
        total_pago = df_cartao_lanc[
            df_cartao_lanc["Tipo"] == "Receita"
        ]["Valor"].sum()
        comprometido = total_gasto - total_pago
      else:
        comprometido = 0.0

      limite_disponivel = limite_total - comprometido

      col_m1, col_m2, col_m3 = st.columns(3)
      with col_m1:
        st.metric("Limite Total", f"R$ {limite_total:,.2f}")
      with col_m2:
        st.metric(
            "Fatura / Comprometido Atual",
            f"R$ {comprometido:,.2f}",
            delta=f"Vencimento dia {dados_cartao['Vencimento']}",
            delta_color="inverse",
        )
      with col_m3:
        st.metric(
            "Limite Disponível",
            f"R$ {limite_disponivel:,.2f}",
            delta=(
                "Saudável" if limite_disponivel >= 0 else "Limite Ultrapassado!"
            ),
        )

      # ==================== NOVA FERRAMENTA: LANÇAR PAGAMENTO DE FATURA (EX: DIA 26) ====================
      st.markdown("---")
      st.markdown(f"💳 **Registrar Pagamento de Fatura para: {cartao_selecionado}**")
      st.write(
          "Para abater o saldo devedor do cartão sem precisar cadastrar novas"
          " compras passadas, faça um registro de pagamento/transferência (ex:"
          " Conta Corrente ➔ Cartão)."
      )

      with st.form("form_pagamento_fatura"):
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
          conta_origem_pag = st.selectbox(
              "Conta de Origem do Dinheiro",
              [c for c in st.session_state.contas if c != cartao_selecionado],
          )
        with col_p2:
          valor_pagamento = st.number_input(
              "Valor do Pagamento (R$)", min_value=0.0, step=10.0, format="%.2f"
          )
        with col_p3:
          data_pagamento = st.date_input("Data do Pagamento (Ex: Dia 26)")

        btn_lancar_pagamento = st.form_submit_button(
            "✅ Registrar Pagamento de Fatura", use_container_width=True
        )

        if btn_lancar_pagamento:
          if valor_pagamento <= 0:
            st.error("O valor do pagamento deve ser maior que zero.")
          else:
            # Criamos um registro do tipo Transferência para pagar a fatura
            novo_pag_df = pd.DataFrame(
                [[
                    "Transferência",
                    conta_origem_pag,
                    cartao_selecionado,
                    "Pagamento de Fatura",
                    f"Pagamento Fatura {cartao_selecionado}",
                    valor_pagamento,
                    data_pagamento,
                    "Única",
                    "Integral",
                    "Efetivado",
                ]],
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
                    "Status",
                ],
            )
            st.session_state.lancamentos = pd.concat(
                [st.session_state.lancamentos, novo_pag_df], ignore_index=True
            )
            st.success(
                f"Pagamento de R$ {valor_pagamento:,.2f} registrado com sucesso!"
            )
            st.rerun()

      st.markdown("---")
      st.markdown(
          f"### Lançamentos Vinculados ao Cartão: **{cartao_selecionado}**"
      )
      if not df_cartao_lanc.empty:
        st.dataframe(df_cartao_lanc, use_container_width=True)
      else:
        st.info(
            f"Nenhum lançamento encontrado para o cartão"
            f" '{cartao_selecionado}'."
        )


# ==================== BACKUP & SEGURANÇA ====================
elif aba == "Backup & Segurança":
  st.title("🛡️ Central de Backup e Segurança")
  st.write(
      "Gerencie cópias de segurança dos seus dados financeiros com total"
      " flexibilidade."
  )

  tab_exp, tab_zip, tab_imp, tab_loc = st.tabs(
      [
          "📤 Exportar Dados",
          "📦 Backup ZIP",
          "📥 Importar Multi-formato",
          "💾 Persistência Local",
      ]
  )

  with tab_exp:
    st.subheader("Exportação Rápida")
    dados_dict = {
        "lancamentos": st.session_state.lancamentos.to_dict(orient="records"),
        "categorias": st.session_state.categorias,
        "contas": st.session_state.contas,
        "cartoes": st.session_state.cartoes,
    }
    json_str = json.dumps(dados_dict, ensure_ascii=False, indent=4, default=str)

    st.download_button(
        label="📥 Baixar Backup Completo (.json)",
        data=json_str,
        file_name="backup_financeiro.json",
        mime="application/json",
        use_container_width=True,
    )

    st.markdown("---")
    csv_data = st.session_state.lancamentos.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📊 Baixar Apenas Lançamentos (.csv)",
        data=csv_data,
        file_name="lancamentos.csv",
        mime="text/csv",
        use_container_width=True,
    )

  with tab_zip:
    st.subheader("Pacote de Segurança Compactado (.zip)")
    if st.button("📦 Gerar Arquivo ZIP de Backup", use_container_width=True):
      zip_buffer = io.BytesIO()
      with zipfile.ZipFile(
          zip_buffer, "w", zipfile.ZIP_DEFLATED
      ) as zip_file:
        zip_file.writestr(
            "lancamentos.csv",
            st.session_state.lancamentos.to_csv(index=False).encode("utf-8"),
        )
        meta_dict = {
            "categorias": st.session_state.categorias,
            "contas": st.session_state.contas,
            "cartoes": st.session_state.cartoes,
        }
        zip_file.writestr(
            "metadados.json",
            json.dumps(meta_dict, ensure_ascii=False, indent=4),
        )

      zip_buffer.seek(0)
      st.download_button(
          label="📦 Baixar Pacote ZIP Seguro",
          data=zip_buffer,
          file_name="backup_completo_seguro.zip",
          mime="application/zip",
          use_container_width=True,
      )
      st.success("Pacote ZIP gerado com sucesso!")

  with tab_imp:
    st.subheader("Importar Dados (ZIP, JSON, CSV ou Excel)")
    st.write(
        "Faça upload de arquivos de backup anteriores (incluindo o arquivo"
        " .zip) para restaurar o seu sistema."
    )

    arquivo_subido = st.file_uploader(
        "Escolha o arquivo de backup", type=["zip", "json", "csv", "xlsx", "xls"]
    )

    if arquivo_subido is not None:
      extensao = arquivo_subido.name.split(".")[-1].lower()

      try:
        if extensao == "zip":
          with zipfile.ZipFile(arquivo_subido, "r") as zip_ref:
            arquivos_no_zip = zip_ref.namelist()

            if "lancamentos.csv" in arquivos_no_zip:
              with zip_ref.open("lancamentos.csv") as f:
                st.session_state.lancamentos = pd.read_csv(f)
                if "Status" not in st.session_state.lancamentos.columns:
                  st.session_state.lancamentos["Status"] = "Efetivado"

            if "metadados.json" in arquivos_no_zip:
              with zip_ref.open("metadados.json") as f:
                meta_data = json.load(f)
                if "categorias" in meta_data:
                  st.session_state.categorias = meta_data["categorias"]
                if "contas" in meta_data:
                  st.session_state.contas = meta_data["contas"]
                if "cartoes" in meta_data:
                  st.session_state.cartoes = meta_data["cartoes"]

          st.success("Backup ZIP importado e restaurado com sucesso!")

        elif extensao == "json":
          conteudo = json.load(arquivo_subido)
          if "lancamentos" in conteudo:
            st.session_state.lancamentos = pd.DataFrame(
                conteudo["lancamentos"]
            )
            if "Status" not in st.session_state.lancamentos.columns:
              st.session_state.lancamentos["Status"] = "Efetivado"
          if "categorias" in conteudo:
            st.session_state.categorias = conteudo["categorias"]
          if "contas" in conteudo:
            st.session_state.contas = conteudo["contas"]
          if "cartoes" in conteudo:
            st.session_state.cartoes = conteudo["cartoes"]
          st.success("Backup JSON importado e restaurado com sucesso!")

        elif extensao == "csv":
          df_importado = pd.read_csv(arquivo_subido)
          if "Status" not in df_importado.columns:
            df_importado["Status"] = "Efetivado"
          st.session_state.lancamentos = pd.concat(
              [st.session_state.lancamentos, df_importado], ignore_index=True
          )
          st.success("Lançamentos do CSV adicionados com sucesso!")

        elif extensao in ["xlsx", "xls"]:
          df_importado = pd.read_excel(arquivo_subido)
          if "Status" not in df_importado.columns:
            df_importado["Status"] = "Efetivado"
          st.session_state.lancamentos = pd.concat(
              [st.session_state.lancamentos, df_importado], ignore_index=True
          )
          st.success("Lançamentos do Excel adicionados com sucesso!")

        st.rerun()
      except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")

  with tab_loc:
    st.subheader("Backup Automático no Servidor / Máquina Local")
    st.write(
        "Salva o estado atual diretamente em um arquivo fixo (`meu_banco.json`)"
        " na pasta do sistema."
    )

    col_l1, col_l2 = st.columns(2)

    with col_l1:
      if st.button("💾 Salvar no Disco Local", use_container_width=True):
        dados_locais = {
            "lancamentos": st.session_state.lancamentos.to_dict(
                orient="records"
            ),
            "categorias": st.session_state.categorias,
            "contas": st.session_state.contas,
            "cartoes": st.session_state.cartoes,
        }
        with open("meu_banco.json", "w", encoding="utf-8") as f:
          json.dump(dados_locais, f, ensure_ascii=False, indent=4, default=str)
        st.success("Dados salvos com sucesso no arquivo 'meu_banco.json'!")

    with col_l2:
      if st.button("📂 Carregar do Disco Local", use_container_width=True):
        try:
          with open("meu_banco.json", "r", encoding="utf-8") as f:
            dados_locais = json.load(f)
            st.session_state.lancamentos = pd.DataFrame(
                dados_locais["lancamentos"]
            )
            if "Status" not in st.session_state.lancamentos.columns:
              st.session_state.lancamentos["Status"] = "Efetivado"
            st.session_state.categorias = dados_locais["categorias"]
            st.session_state.contas = dados_locais["contas"]
            if "cartoes" in dados_locais:
              st.session_state.cartoes = dados_locais["cartoes"]
          st.success("Dados carregados com sucesso do disco local!")
          st.rerun()
        except FileNotFoundError:
          st.warning(
              "Nenhum arquivo 'meu_banco.json' encontrado. Salve primeiro!"
          )
        except Exception as e:
          st.error(f"Erro ao carregar: {e}")
