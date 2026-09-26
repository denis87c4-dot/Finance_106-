import io
import json
import zipfile
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import norm
import numpy_financial as npf
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
        "Statistics",
        "Financial Analysis",
        "🤖 IA & Assistant",
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

    # ==================== BLOCO: CONTROLE DE BUDGET VS EFETIVADO (MÊS) ====================
    st.markdown("---")
    st.subheader("🎯 Controle Orçamentário: Budget vs. Efetivado por Categoria")

    df_temp["AnoMes"] = df_temp["Data"].dt.to_period("M").astype(str)
    meses_disponiveis = sorted(df_temp["AnoMes"].unique().tolist(), reverse=True)

    if not meses_disponiveis:
      meses_disponiveis = [pd.Timestamp.now().strftime("%Y-%m")]

    col_bm1, col_bm2 = st.columns([2, 2])
    with col_bm1:
      mes_atual_str = pd.Timestamp.now().strftime("%Y-%m")
      default_mes = (
          [mes_atual_str]
          if mes_atual_str in meses_disponiveis
          else [meses_disponiveis[0]]
      )
      mes_selecionado = st.selectbox(
          "📅 Selecione o Mês para Análise do Budget",
          meses_disponiveis,
          index=(
              meses_disponiveis.index(default_mes[0])
              if default_mes[0] in meses_disponiveis
              else 0
          ),
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

      # ==================== TRACKING DE DESCRIÇÕES POR MÊS ====================
      st.markdown("---")
      st.subheader("🏷️ Detalhamento de Gastos por Descrição e Categoria")
      st.write(
          "Acompanhe o ranking dos lançamentos detalhados por descrição com base"
          " nos filtros ativos."
      )

      meses_disc_disp = sorted(df_temp["AnoMes"].unique().tolist(), reverse=True)
      if meses_disc_disp:
        col_td1, col_td2 = st.columns([2, 2])
        with col_td1:
          mes_disc_escolhido = st.selectbox(
              "Filtrar Mês Específico para Descrições",
              ["Todos os Meses Filtrados"] + meses_disc_disp,
          )
        with col_td2:
          tipo_disc_filtro = st.selectbox(
              "Tipo para Rastreio de Descrição",
              ["Despesa", "Receita", "Todos"],
          )

        df_tracking = df_temp.copy()
        if mes_disc_escolhido != "Todos os Meses Filtrados":
          df_tracking = df_tracking[
              df_tracking["AnoMes"] == mes_disc_escolhido
          ]
        if tipo_disc_filtro != "Todos":
          df_tracking = df_tracking[df_tracking["Tipo"] == tipo_disc_filtro]

        if not df_tracking.empty:
          df_grouped_desc = (
              df_tracking.groupby(
                  ["Data", "Categoria", "Descrição", "Tipo", "Conta"]
              )["Valor"]
              .sum()
              .reset_index()
              .sort_values(by="Valor", ascending=False)
          )

          st.dataframe(
              df_grouped_desc.style.format({"Valor": "R$ {:,.2f}"}),
              use_container_width=True,
              hide_index=True,
          )
        else:
          st.info("Nenhum registro encontrado para os critérios de rastreio.")

      st.markdown("---")
      st.subheader("📈 Análise Gráfica Dinâmica")

      col_g1, col_g2 = st.columns(2)

      with col_g1:
        st.markdown("##### 🌊 Cash Flow vs. Cumulative")
        fig_linhas = go.Figure()
        fig_linhas.add_trace(
            go.Scatter(
                x=df_resumo["Período"],
                y=df_resumo["Cumulative"],
                mode="lines+markers",
                name="Cumulative",
                line=dict(color="#636EFA", width=2),
            )
        )

        cf_positivo = df_resumo["Cash Flow"].apply(
            lambda x: x if x >= 0 else None
        )
        cf_negativo = df_resumo["Cash Flow"].apply(
            lambda x: x if x < 0 else None
        )

        fig_linhas.add_trace(
            go.Scatter(
                x=df_resumo["Período"],
                y=cf_positivo,
                mode="lines+markers",
                name="Cash Flow (Positivo)",
                line=dict(color="#00CC96", width=2),
                connectgaps=True,
            )
        )
        fig_linhas.add_trace(
            go.Scatter(
                x=df_resumo["Período"],
                y=cf_negativo,
                mode="lines+markers",
                name="Cash Flow (Negativo)",
                line=dict(color="#EF553B", width=3),
                connectgaps=True,
            )
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


# ==================== STATISTICS / ESTATÍSTICAS E PROJEÇÕES ====================
elif aba == "Statistics":
  st.title("📊 Estatísticas e Projeções Financeiras")

  if st.session_state.lancamentos.empty:
    st.warning("Nenhum dado disponível para análise estatística.")
  else:
    df_stat = st.session_state.lancamentos.copy()
    df_stat["Data"] = pd.to_datetime(df_stat["Data"])
    if "Status" not in df_stat.columns:
      df_stat["Status"] = "Efetivado"

    # ==================== FILTROS PODEROSOS DE STATISTICS ====================
    st.markdown("---")
    st.markdown("### 🔍 Filtros Poderosos (Statistics)")
    with st.expander("🛠️ Filtrar Dados para Análise Estatística", expanded=True):
      col_s1, col_s2, col_s3, col_s4 = st.columns(4)

      with col_s1:
        anos_stat = sorted(
            df_stat["Data"].dt.year.dropna().unique().tolist(), reverse=True
        )
        if not anos_stat:
          anos_stat = [pd.Timestamp.now().year]
        ano_stat_sel = st.multiselect("Filtrar Anos", anos_stat, default=anos_stat)

      with col_s2:
        frequencia_stat = st.selectbox(
            "Agrupamento Temporal",
            ["Mensal", "Trimestral", "Quadrimestral", "Semestral", "Anual"],
            index=0,
        )

      with col_s3:
        contas_stat = st.session_state.contas
        conta_stat_sel = st.multiselect(
            "Filtrar Contas/Cartões", contas_stat, default=contas_stat
        )

      with col_s4:
        cat_stat = st.session_state.categorias
        cat_stat_sel = st.multiselect(
            "Filtrar Categorias", cat_stat, default=cat_stat
        )

      col_s5, col_s6 = st.columns(2)
      with col_s5:
        tipo_stat_sel = st.multiselect(
            "Tipo de Lançamento",
            ["Receita", "Despesa", "Transferência"],
            default=["Receita", "Despesa", "Transferência"],
        )
      with col_s6:
        status_stat_sel = st.multiselect(
            "Status", ["Efetivado", "Orçado"], default=["Efetivado", "Orçado"]
        )

    # Aplicar filtros
    if ano_stat_sel:
      df_stat = df_stat[df_stat["Data"].dt.year.isin(ano_stat_sel)]
    if conta_stat_sel:
      df_stat = df_stat[
          df_stat["Conta"].isin(conta_stat_sel)
          | df_stat["Conta Destino"].isin(conta_stat_sel)
      ]
    if cat_stat_sel:
      df_stat = df_stat[df_stat["Categoria"].isin(cat_stat_sel)]
    if tipo_stat_sel:
      df_stat = df_stat[df_stat["Tipo"].isin(tipo_stat_sel)]
    if status_stat_sel:
      df_stat = df_stat[df_stat["Status"].isin(status_stat_sel)]

    if df_stat.empty:
      st.warning("Nenhum dado encontrado com os filtros selecionados.")
    else:
      if frequencia_stat == "Mensal":
        df_stat["Periodo_Analise"] = df_stat["Data"].dt.to_period("M").astype(str)
      elif frequencia_stat == "Trimestral":
        df_stat["Periodo_Analise"] = df_stat["Data"].dt.to_period("Q").astype(str)
      elif frequencia_stat == "Quadrimestral":
        df_stat["Periodo_Analise"] = (
            df_stat["Data"].dt.year.astype(str)
            + "-Q"
            + ((df_stat["Data"].dt.month - 1) // 4 + 1).astype(str)
        )
      elif frequencia_stat == "Semestral":
        df_stat["Periodo_Analise"] = (
            df_stat["Data"].dt.year.astype(str)
            + "-S"
            + ((df_stat["Data"].dt.month - 1) // 6 + 1).astype(str)
        )
      else:
        df_stat["Periodo_Analise"] = df_stat["Data"].dt.year.astype(str)

      periodos_disponiveis = sorted(df_stat["Periodo_Analise"].unique().tolist(), reverse=True)

      st.markdown("---")
      col_p_sel, _ = st.columns([2, 2])
      with col_p_sel:
        periodo_escolhido_stat = st.selectbox(
            f"📅 Selecione o {frequencia_stat} Específico para Análise Detalhada",
            periodos_disponiveis,
        )

      df_periodo_stat = df_stat[df_stat["Periodo_Analise"] == periodo_escolhido_stat]

      # ==================== PARÂMETROS ESTATÍSTICOS DETALHADOS ====================
      st.markdown("---")
      st.subheader(f"📊 Parâmetros Estatísticos - Período: {periodo_escolhido_stat}")

      if df_periodo_stat.empty:
        st.info(f"Sem movimentações no período {periodo_escolhido_stat}.")
      else:
        valores_serie = df_periodo_stat["Valor"]

        media = valores_serie.mean()
        mediana = valores_serie.median()
        desvio_padrao = valores_serie.std() if len(valores_serie) > 1 else 0.0
        kurtose = valores_serie.kurtosis() if len(valores_serie) > 3 else 0.0
        skewness = valores_serie.skew() if len(valores_serie) > 2 else 0.0

        df_historico_todos = (
            df_stat.groupby("Periodo_Analise")["Valor"].sum().reset_index()
            .sort_values("Periodo_Analise")
        )
        df_historico_todos["MM3"] = df_historico_todos["Valor"].rolling(window=3, min_periods=1).mean()
        
        match_mm = df_historico_todos[df_historico_todos["Periodo_Analise"] == periodo_escolhido_stat]
        media_movel_3m = match_mm["MM3"].values[0] if not match_mm.empty else valores_serie.mean()

        df_pivot_corr = (
            df_stat.pivot_table(
                index="Periodo_Analise",
                columns="Tipo",
                values="Valor",
                aggfunc="sum",
            )
            .fillna(0)
            .reset_index()
        )
        if "Receita" in df_pivot_corr.columns and "Despesa" in df_pivot_corr.columns:
          correlacao = df_pivot_corr["Receita"].corr(df_pivot_corr["Despesa"])
          if pd.isna(correlacao):
            correlacao = 0.0
        else:
          correlacao = 0.0

        df_tabela_stat = pd.DataFrame({
            "Parâmetro Estatístico": [
                "Média (Mean)",
                "Mediana (Median)",
                f"Média Móvel (3 {frequencia_stat}s)",
                "Desvio Padrão (Std Dev)",
                "Curtose (Kurtosis)",
                "Assimetria (Skewness)",
                "Correlação (Receita vs Despesa)",
            ],
            "Valor Calculado": [
                f"R$ {media:,.2f}",
                f"R$ {mediana:,.2f}",
                f"R$ {media_movel_3m:,.2f}",
                f"R$ {desvio_padrao:,.2f}",
                f"{kurtose:.2f}",
                f"{skewness:.2f}",
                f"{correlacao:.2f}",
            ],
        })

        st.dataframe(df_tabela_stat, use_container_width=True, hide_index=True)

        # ==================== ANÁLISE INTELIGENTE DE IA & PADRÕES ====================
        st.markdown("---")
        st.subheader("🤖 Análise Inteligente de IA & Padrões")

        qtd_lanc = len(df_periodo_stat)
        total_mov = valores_serie.sum()

        interpretacao_kurtose = (
            "alta concentração de valores em torno da média (distribuição leptocúrtica)"
            if kurtose > 1
            else (
                "dispersão equilibrada de valores (distribuição mesocúrtica/platicúrtica)"
                if kurtose >= -1
                else "ampla dispersão sem padrão concentrado"
            )
        )

        interpretacao_skew = (
            "viés positivo (cauda longa à direita, indicando alguns lançamentos de valores expressivamente altos)"
            if skewness > 0.5
            else (
                "viés negativo (cauda à esquerda, indicando predominância de valores menores com poucos picos baixos)"
                if skewness < -0.5
                else "distribuição simétrica dos lançamentos"
            )
        )

        status_tendencia = (
            "crescimento ou resiliência financeira"
            if media >= (media_movel_3m * 0.9)
            else "alerta de queda ou contratação de despesas acima da média dos períodos anteriores"
        )

        st.markdown(
            f"""> 🧠 **Relatório Analítico Automatizado para {periodo_escolhido_stat} ({frequencia_stat}):**
> 
> * **Volume de Transações:** No período avaliado, foram registradas **{qtd_lanc} movimentações**, totalizando um montante de **R$ {total_mov:,.2f}**.
> * **Comportamento e Curtose (Kurt = `{kurtose:.2f}`):** O perfil dos lançamentos apresenta **{interpretacao_kurtose}**. Isso significa que o risco de oscilações bruscas no caixa por itens fora da curva é {('baixo' if kurtose <= 1 else 'moderado/alto')}.
> * **Assimetria (Skew = `{skewness:.2f}`):** O demonstrativo aponta **{interpretacao_skew}**. 
> * **Tendência de Médias:** A média móvel aponta para **R$ {media_movel_3m:,.2f}**, refletindo um cenário de **{status_tendencia}**.
> * **Correlação Global:** O índice de correlação entre entradas e saídas no histórico é de **`{correlacao:.2f}`**, indicando o grau de acompanhamento financeiro entre o que entra e o que sai.
"""
        )

      # ==================== CURVA DE SINO DOS TOTAIS POR PERÍODO ====================
      st.markdown("---")
      st.subheader(f"🔔 Curva de Sino dos Totais ({frequencia_stat}) & Probabilidade P(X < x)")
      st.write(
          f"Análise estatística baseada no **histórico de gastos totais por {frequencia_stat.lower()}**. "
          f"Descubra a probabilidade de o total do {frequencia_stat.lower()} ficar abaixo de um patamar."
      )

      df_historico_periodos = (
          df_stat[df_stat["Tipo"] == "Despesa"]
          .groupby("Periodo_Analise")["Valor"]
          .sum()
          .reset_index()
      )

      if len(df_historico_periodos) < 2:
        st.warning(
            f"⚠️ Você precisa ter dados de despesas em pelo menos 2 {frequencia_stat.lower()}s "
            "diferentes para calcular a distribuição normal dos totais."
        )
      else:
        valores_totais_periodo = df_historico_periodos["Valor"]

        media_periodo = valores_totais_periodo.mean()
        desvio_padrao_periodo = valores_totais_periodo.std()

        max_val_p = float(valores_totais_periodo.max())
        min_val_p = float(valores_totais_periodo.min())
        default_x_p = float(media_periodo)

        col_nb1, col_nb2 = st.columns([1, 2])
        with col_nb1:
          x_usuario = st.number_input(
              f"Defina o Valor Total Limite (x) para o {frequencia_stat}",
              min_value=0.0,
              max_value=max(max_val_p * 2, 50000.0),
              value=default_x_p,
              step=100.0,
              format="%.2f",
          )

          if desvio_padrao_periodo > 0:
            prob_acumulada = (
                norm.cdf(
                    x_usuario,
                    loc=media_periodo,
                    scale=desvio_padrao_periodo,
                )
                * 100
            )
          else:
            prob_acumulada = 100.0 if x_usuario >= media_periodo else 0.0

          st.metric(
              label=f"Probabilidade do Total < R$ {x_usuario:,.2f}",
              value=f"{prob_acumulada:.2f}%",
              delta=f"Chance Acumulada {frequencia_stat}",
          )
          st.info(
              f"💡 **Média Histórica ({frequencia_stat}):** R$ {media_periodo:,.2f} | "
              f"**Desvio Padrão:** R$ {desvio_padrao_periodo:,.2f}"
          )

        with col_nb2:
          if desvio_padrao_periodo > 0:
            x_vals = np.linspace(
                max(0, min_val_p - 2 * desvio_padrao_periodo),
                max_val_p + 2 * desvio_padrao_periodo,
                300,
            )
            y_vals = norm.pdf(
                x_vals, loc=media_periodo, scale=desvio_padrao_periodo
            )

            fig_bell = go.Figure()
            fig_bell.add_trace(
                go.Scatter(
                    x=x_vals,
                    y=y_vals,
                    mode="lines",
                    name=f"Curva Normal de Despesas ({frequencia_stat})",
                    line=dict(color="#636EFA", width=3),
                )
            )

            x_shade = x_vals[x_vals <= x_usuario]
            y_shade = y_vals[x_vals <= x_usuario]
            if len(x_shade) > 0:
              fig_bell.add_trace(
                  go.Scatter(
                      x=np.concatenate([[x_shade[0]], x_shade, [x_shade[-1]]]),
                      y=np.concatenate([[0], y_shade, [0]]),
                      fill="toself",
                      fillcolor="rgba(0, 204, 150, 0.4)",
                      line=dict(color="rgba(255,255,255,0)"),
                      name=f"Área P(X < x) = {prob_acumulada:.1f}%",
                  )
              )

            fig_bell.add_vline(
                x=x_usuario,
                line_dash="dash",
                line_color="#EF553B",
                annotation_text=f"Limite x = R$ {x_usuario:,.2f}",
                annotation_position="top right",
            )

            fig_bell.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                xaxis_title=f"Valor Total de Despesas no {frequencia_stat} (R$)",
                yaxis_title="Densidade de Probabilidade",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                ),
                margin=dict(l=10, r=10, t=10, b=10),
            )
            st.plotly_chart(fig_bell, use_container_width=True)
          else:
            st.warning("Desvio padrão igual a zero para o período selecionado.")

        # ==================== PROJEÇÃO DE TENDÊNCIA FUTURA (FORECAST) ====================
        st.markdown("---")
        st.subheader(f"📈 Projeção de Tendência Futura (Forecast {frequencia_stat})")
        st.write(
            "Regressão linear aplicada ao histórico de despesas para estimar o comportamento e a linha de tendência dos próximos períodos."
        )

        if len(df_historico_periodos) >= 3:
          df_historico_periodos = df_historico_periodos.sort_values("Periodo_Analise").reset_index(drop=True)
          
          x_indices = np.arange(len(df_historico_periodos))
          y_valores = df_historico_periodos["Valor"].values

          m, b = np.polyfit(x_indices, y_valores, 1)

          proximo_indice = len(df_historico_periodos)
          valor_projetado = (m * proximo_indice) + b

          df_historico_periodos["Tendencia"] = (m * x_indices) + b

          fig_forecast = go.Figure()
          fig_forecast.add_trace(
              go.Scatter(
                  x=df_historico_periodos["Periodo_Analise"],
                  y=df_historico_periodos["Valor"],
                  mode="lines+markers",
                  name="Despesas Reais",
                  line=dict(color="#00CC96", width=2),
              )
          )
          fig_forecast.add_trace(
              go.Scatter(
                  x=df_historico_periodos["Periodo_Analise"],
                  y=df_historico_periodos["Tendencia"],
                  mode="lines",
                  name="Linha de Tendência",
                  line=dict(color="#FFA15A", width=2, dash="dash"),
              )
          )

          fig_forecast.update_layout(
              plot_bgcolor="rgba(0,0,0,0)",
              paper_bgcolor="rgba(0,0,0,0)",
              xaxis_title=f"Períodos ({frequencia_stat})",
              yaxis_title="Total de Despesas (R$)",
              legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
              margin=dict(l=10, r=10, t=10, b=10),
          )
          st.plotly_chart(fig_forecast, use_container_width=True)

          tendencia_direcao = "📈 viés de alta" if m > 0 else "📉 viés de queda"
          st.success(
              f"🔮 **Projeção para o próximo {frequencia_stat.lower()}:** R$ {max(0, valor_projetado):,.2f} "
              f"(A linha de tendência atual aponta para um {tendencia_direcao} de R$ {abs(m):,.2f} por período)."
          )
        else:
          st.info("⚠️ São necessários pelo menos 3 períodos históricos preenchidos para calcular a projeção de tendência com precisão.")


# ==================== FINANCIAL ANALYSIS / ANÁLISE FINANCEIRA CORPORATIVA ====================
elif aba == "Financial Analysis":
  st.title("💼 Financial Analysis & Funções Financeiras (Excel Core)")
  st.write(
      "Ferramentas avançadas de engenharia financeira baseadas em fórmulas do Excel (`VPL`, `TIR`, `PMT`, `VF`, `VP`) "
      "aplicadas diretamente ao seu fluxo de caixa e cenários de simulação."
  )

  if st.session_state.lancamentos.empty:
    st.warning("⚠️ Nenhum lançamento disponível para gerar a análise financeira avançada.")
  else:
    df_fin = st.session_state.lancamentos.copy()
    df_fin["Data"] = pd.to_datetime(df_fin["Data"])
    if "Status" not in df_fin.columns:
      df_fin["Status"] = "Efetivado"

    # ==================== FILTROS PODEROSOS (FINANCIAL ANALYSIS) ====================
    st.markdown("---")
    st.markdown("### 🔍 Filtros Poderosos (Financial Analysis)")
    with st.expander("🛠️ Filtrar Dados para Análise Financeira", expanded=True):
      col_fa1, col_fa2, col_fa3, col_fa4 = st.columns(4)

      with col_fa1:
        anos_fin = sorted(
            df_fin["Data"].dt.year.dropna().unique().tolist(), reverse=True
        )
        if not anos_fin:
          anos_fin = [pd.Timestamp.now().year]
        ano_fin_sel = st.multiselect("Filtrar Anos", anos_fin, default=anos_fin, key="fin_anos")

      with col_fa2:
        frequencia_fin = st.selectbox(
            "Agrupamento Temporal",
            ["Mensal", "Trimestral", "Anual"],
            index=0,
            key="fin_freq"
        )

      with col_fa3:
        contas_fin = st.session_state.contas
        conta_fin_sel = st.multiselect(
            "Filtrar Contas/Cartões", contas_fin, default=contas_fin, key="fin_contas"
        )

      with col_fa4:
        cat_fin = st.session_state.categorias
        cat_fin_sel = st.multiselect(
            "Filtrar Categorias", cat_fin, default=cat_fin, key="fin_cats"
        )

      col_fa5, col_fa6 = st.columns(2)
      with col_fa5:
        tipo_fin_sel = st.multiselect(
            "Tipo de Lançamento",
            ["Receita", "Despesa", "Transferência"],
            default=["Receita", "Despesa", "Transferência"],
            key="fin_tipos"
        )
      with col_fa6:
        status_fin_sel = st.multiselect(
            "Status", ["Efetivado", "Orçado"], default=["Efetivado", "Orçado"], key="fin_status"
        )

    # Aplicar filtros
    if ano_fin_sel:
      df_fin = df_fin[df_fin["Data"].dt.year.isin(ano_fin_sel)]
    if conta_fin_sel:
      df_fin = df_fin[
          df_fin["Conta"].isin(conta_fin_sel)
          | df_fin["Conta Destino"].isin(conta_fin_sel)
      ]
    if cat_fin_sel:
      df_fin = df_fin[df_fin["Categoria"].isin(cat_fin_sel)]
    if tipo_fin_sel:
      df_fin = df_fin[df_fin["Tipo"].isin(tipo_fin_sel)]
    if status_fin_sel:
      df_fin = df_fin[df_fin["Status"].isin(status_fin_sel)]

    if df_fin.empty:
      st.warning("⚠️ Nenhum dado encontrado com os filtros selecionados para a Análise Financeira.")
    else:
      if frequencia_fin == "Mensal":
        df_fin["Periodo_Analise"] = df_fin["Data"].dt.to_period("M").astype(str)
      elif frequencia_fin == "Trimestral":
        df_fin["Periodo_Analise"] = df_fin["Data"].dt.to_period("Q").astype(str)
      else:
        df_fin["Periodo_Analise"] = df_fin["Data"].dt.year.astype(str)

      df_rec_f = df_fin[df_fin["Tipo"] == "Receita"].groupby("Periodo_Analise")["Valor"].sum().reset_index(name="Receita")
      df_desp_f = df_fin[df_fin["Tipo"] == "Despesa"].groupby("Periodo_Analise")["Valor"].sum().reset_index(name="Despesa")

      df_fluxo_caixa = pd.merge(df_rec_f, df_desp_f, on="Periodo_Analise", how="outer").fillna(0)
      df_fluxo_caixa = df_fluxo_caixa.sort_values("Periodo_Analise").reset_index(drop=True)
      df_fluxo_caixa["Net_Cash_Flow"] = df_fluxo_caixa["Receita"] - df_fluxo_caixa["Despesa"]

      st.markdown("---")
      st.subheader("⚙️ Parâmetros para Modelagem Financeira (Estilo Excel)")
      
      col_m_p1, col_m_p2, col_m_p3 = st.columns(3)
      with col_m_p1:
        taxa_desconto_anual = st.number_input(
            "Taxa de Desconto / Custo de Oportunidade (% a.a.)",
            min_value=0.0, max_value=100.0, value=10.0, step=0.5,
            help="Usada no cálculo do VPL (Valor Presente Líquido / NPV)"
        )
      with col_m_p2:
        meses_projecao = st.number_input(
            "Horizonte de Projeção de Patrimônio (Meses)",
            min_value=1, max_value=120, value=12, step=1,
            help="Usado no cálculo do Valor Futuro (VF / FV) do saldo acumulado"
        )
      with col_m_p3:
        taxa_poupanca_anual = st.number_input(
            "Taxa de Rendimento Esperada (% a.a.)",
            min_value=0.0, max_value=50.0, value=8.0, step=0.5,
            help="Taxa de juros aplicada para estimar o crescimento do patrimônio futuro"
        )

      if frequencia_fin == "Mensal":
        taxa_periodica = (1 + taxa_desconto_anual / 100) ** (1/12) - 1
        taxa_juros_futuro = (1 + taxa_poupanca_anual / 100) ** (1/12) - 1
      elif frequencia_fin == "Trimestral":
        taxa_periodica = (1 + taxa_desconto_anual / 100) ** (1/4) - 1
        taxa_juros_futuro = (1 + taxa_poupanca_anual / 100) ** (1/4) - 1
      else:
        taxa_periodica = taxa_desconto_anual / 100
        taxa_juros_futuro = taxa_poupanca_anual / 100

      fluxos = df_fluxo_caixa["Net_Cash_Flow"].values

      try:
        vpl_calculado = npf.npv(taxa_periodica, fluxos)
      except Exception:
        vpl_calculado = 0.0

      try:
        tir_calculada = npf.irr(fluxos) * 100
        if pd.isna(tir_calculada):
          tir_calculada = 0.0
      except Exception:
        tir_calculada = 0.0

      media_caixa_periodo = fluxos.mean() if len(fluxos) > 0 else 0.0
      try:
        vf_calculado = npf.fv(taxa_juros_futuro, meses_projecao, -media_caixa_periodo, 0)
      except Exception:
        vf_calculado = 0.0

      st.markdown("---")
      st.subheader("📊 KPIs Corporativos de Retorno & Viabilidade")

      kpi1, kpi2, kpi3, kpi4 = st.columns(4)
      
      with kpi1:
        st.metric(
            label="💵 VPL / NPV (Valor Presente Líquido)",
            value=f"R$ {vpl_calculado:,.2f}",
            delta="Viabilidade do Caixa" if vpl_calculado >= 0 else "Alerta Deficitário",
            delta_color="normal" if vpl_calculado >= 0 else "inverse"
        )
      with kpi2:
        st.metric(
            label="📈 TIR / IRR (Taxa Interna de Retorno)",
            value=f"{tir_calculada:.2f}% a.p.",
            delta="Retorno Efetivo do Período"
        )
      with kpi3:
        st.metric(
            label="🔮 Valor Futuro (VF / FV Projetado)",
            value=f"R$ {vf_calculado:,.2f}",
            delta=f"Em {meses_projecao} períodos"
        )
      with kpi4:
        media_liquida = fluxos.mean()
        cor_delta = "normal" if media_liquida >= 0 else "inverse"
        st.metric(
            label="⚖️ Média Líquida por Período",
            value=f"R$ {media_liquida:,.2f}",
            delta="Fluxo Médio",
            delta_color=cor_delta
        )

      if vpl_calculado < 0 or media_liquida < 0:
        st.markdown(
            """
            <div style="padding: 15px; border-radius: 8px; background-color: rgba(239, 85, 59, 0.15); border: 1px solid #EF553B; margin-top: 20px; margin-bottom: 20px;">
                <h4 style="color: #EF553B; margin: 0;">🚨 ATENÇÃO: Alerta de Desequilíbrio Financeiro</h4>
                <p style="margin: 5px 0 0 0; color: #333;">O seu Valor Presente Líquido (VPL) ou o fluxo líquido médio estão apontando valores negativos para os filtros selecionados. Considere revisar as despesas ou renegociar faturas na aba de Cartões de Crédito.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

      st.markdown("---")
      st.subheader("🧮 Simulador de Empréstimo / Financiamento (Função PMT)")
      st.write("Simule o impacto de um novo financiamento ou parcelamento no seu fluxo de caixa antes de assumir a obrigação.")

      col_s_pmt1, col_s_pmt2, col_s_pmt3 = st.columns(3)
      with col_s_pmt1:
        pv_simulado = st.number_input("Valor do Empréstimo / Dívida (VP - R$)", min_value=0.0, value=10000.0, step=500.0, format="%.2f")
      with col_s_pmt2:
        taxa_juros_mes_sim = st.number_input("Taxa de Juros Mensal (% a.m.)", min_value=0.0, max_value=20.0, value=1.5, step=0.1)
      with col_s_pmt3:
        nper_simulado = st.number_input("Número de Parcelas (Meses)", min_value=1, max_value=360, value=12, step=1)

      if pv_simulado > 0 and nper_simulado > 0:
        taxa_decimal = taxa_juros_mes_sim / 100
        try:
          pmt_calculado = abs(npf.pmt(taxa_decimal, nper_simulado, -pv_simulado))
          juros_totais = (pmt_calculado * nper_simulado) - pv_simulado
        except Exception:
          pmt_calculado = 0.0
          juros_totais = 0.0

        col_res1, col_res2 = st.columns(2)
        with col_res1:
          st.metric("💳 Valor da Parcela Mensal (PMT)", f"R$ {pmt_calculado:,.2f}")
        with col_res2:
          st.metric("💸 Total de Juros Embutidos", f"R$ {juros_totais:,.2f}", delta="Custo Total do Crédito", delta_color="inverse")

        st.info(f"💡 Assumir esta parcela de **R$ {pmt_calculado:,.2f}** compromete aproximadamente **{(pmt_calculado / (abs(media_caixa_periodo) if media_caixa_periodo != 0 else 1) * 100):.1f}%** do seu fluxo líquido médio por período.")


# ==================== IA & ASSISTANT (INTELIGÊNCIA ARTIFICIAL REAL COM GEMINI API) ====================
elif aba == "🤖 IA & Assistant":
  st.title("🤖 Central de Inteligência Artificial & Gemini Assistant")
  st.write(
      "Converse diretamente com o **Google Gemini** conectado aos seus dados financeiros reais. "
      "Faça perguntas complexas, peça conselhos de economia ou diagnósticos detalhados."
  )

  if st.session_state.lancamentos.empty:
    st.warning("⚠️ Cadastre alguns lançamentos para que a IA possa analisar e conversar com você sobre os seus dados.")
  else:
    df_ia = st.session_state.lancamentos.copy()
    df_ia["Data"] = pd.to_datetime(df_ia["Data"])
    if "Status" not in df_ia.columns:
      df_ia["Status"] = "Efetivado"

    tab_relatorio, tab_chat = st.tabs(["🔮 Relatório Preditivo Avançado", "💬 Chat Inteligente com Gemini"])

    with tab_relatorio:
      st.subheader("🧠 Diagnóstico Inteligente & Revelações Surpreendentes")
      st.write("Varredura heurística dos seus dados correntes, identificando padrões invisíveis, riscos e projeções.")

      total_geral_receitas = df_ia[df_ia["Tipo"] == "Receita"]["Valor"].sum()
      total_geral_despesas = df_ia[df_ia["Tipo"] == "Despesa"]["Valor"].sum()
      saldo_global = total_geral_receitas - total_geral_despesas

      df_despesas_cat = df_ia[df_ia["Tipo"] == "Despesa"].groupby("Categoria")["Valor"].sum().reset_index()
      maior_cat = df_despesas_cat.sort_values(by="Valor", ascending=False).iloc[0]["Categoria"] if not df_despesas_cat.empty else "N/A"
      maior_val_cat = df_despesas_cat.sort_values(by="Valor", ascending=False).iloc[0]["Valor"] if not df_despesas_cat.empty else 0.0
      pct_maior_cat = (maior_val_cat / total_geral_despesas * 100) if total_geral_despesas > 0 else 0.0

      col_ia1, col_ia2, col_ia3 = st.columns(3)
      with col_ia1:
        st.metric("💰 Saldo Consolidado Global", f"R$ {saldo_global:,.2f}", delta="Receitas - Despesas")
      with col_ia2:
        st.metric("🔥 Principal Ralo de Gastos", f"{maior_cat}", delta=f"R$ {maior_val_cat:,.2f}")
      with col_ia3:
        st.metric("📊 Concentração da Maior Categoria", f"{pct_maior_cat:.1f}%", delta="Do total de despesas", delta_color="inverse")

      st.markdown("---")
      st.markdown("### 🔍 Insights & Revelações de Comportamento")

      alerta_concentracao = "⚠️ **Alerta de Alocação Crítica:** " if pct_maior_cat > 40 else "✅ **Alocação Saudável:** "
      alerta_texto_conc = f"A categoria **{maior_cat}** absorve sozinha **{pct_maior_cat:.1f}%** de todo o seu dinheiro de saída." if pct_maior_cat > 40 else f"Seus gastos estão bem distribuídos, sendo **{maior_cat}** a principal ({pct_maior_cat:.1f}%)."
      projecao_futura_12m = saldo_global * 1.05

      st.info(
          f"""
          * {alerta_concentracao} {alerta_texto_conc}
          * 🔮 **Projeção de Trajetória Futura:** Mantendo o ritmo atual, a tendência estimada para o próximo ciclo aponta para um fluxo líquido de aproximadamente **R$ {projecao_futura_12m:,.2f}**.
          * 💡 **Sugestão de Otimização:** Estabeleça tetos orçamentários rígidos por categoria no início de cada mês na aba de Dashboard.
          """
      )

      if not df_despesas_cat.empty:
        fig_pie = px.pie(
            df_despesas_cat, names="Categoria", values="Valor",
            title="🎯 Radiografia de Despesas por Categoria para Tomada de Decisão",
            hole=0.4,
            color_discrete_sequence=px.colors.sequential.Tealgrn
        )
        fig_pie.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_pie, use_container_width=True)

    with tab_chat:
      st.subheader("💬 Chat com IA Real (Google Gemini)")
      st.write("Faça qualquer pergunta sobre os seus gastos, peça dicas de como economizar ou análises detalhadas.")

      gemini_api_key = st.text_input(
          "🔑 Insira sua Chave de API do Google Gemini (ou configure via st.secrets)",
          type="password",
          help="Você pode obter uma chave gratuita no Google AI Studio."
      )

      if "chat_history_gemini" not in st.session_state:
        st.session_state.chat_history_gemini = [
            {"role": "assistant", "content": "Olá, Denison! Estou conectado aos seus dados financeiros através do Google Gemini. O que você gostaria de analisar ou perguntar?"}
        ]

      for message in st.session_state.chat_history_gemini:
        with st.chat_message(message["role"]):
          st.markdown(message["content"])

      user_prompt = st.chat_input("Converse com o Gemini sobre suas finanças...")

      if user_prompt:
        st.session_state.chat_history_gemini.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
          st.markdown(user_prompt)

        with st.chat_message("assistant"):
          with st.spinner("🤖 O Gemini está analisando seus lançamentos e preparando a resposta..."):
            try:
              import google.generativeai as genai

              api_key_final = gemini_api_key
              if not api_key_final and "GEMINI_API_KEY" in st.secrets:
                api_key_final = st.secrets["GEMINI_API_KEY"]

              if not api_key_final:
                resposta_gemini = "⚠️ Por favor, insira a sua Chave de API do Google Gemini no campo acima para habilitar o chat inteligente."
              else:
                genai.configure(api_key=api_key_final)
                
                csv_resumido = df_ia.to_csv(index=False)
                
                prompt_sistema = f"""
                Você é um consultor financeiro pessoal especialista de elite, integrado a um aplicativo de finanças.
                Abaixo estão os dados dos lançamentos financeiros do usuário em formato CSV:
                {csv_resumido}
                
                Responda à pergunta do usuário de forma analítica, prestativa, clara e em português, baseando-se estritamente nos dados acima.
                Pergunta do usuário: {user_prompt}
                """

                # CORREÇÃO DO MODELO ATUALIZADO
                model = genai.GenerativeModel('gemini-3.6-flash')
                response = model.generate_content(prompt_sistema)
                resposta_gemini = response.text

            except Exception as e:
              resposta_gemini = f"❌ Erro ao conectar com a API do Gemini: {e}\n\nCertifique-se de que a biblioteca `google-generativeai` está instalada e a chave de API é válida."

            st.markdown(resposta_gemini)
            st.session_state.chat_history_gemini.append({"role": "assistant", "content": resposta_gemini})


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

      st.markdown("---")
      st.markdown(
          f"💳 **Registrar Pagamento de Fatura para: {cartao_selecionado}**"
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
          data_pagamento = st.date_input("Data do Pagamento")

        btn_lancar_pagamento = st.form_submit_button(
            "✅ Registrar Pagamento de Fatura", use_container_width=True
        )

        if btn_lancar_pagamento:
          if valor_pagamento <= 0:
            st.error("O valor do pagamento deve ser maior que zero.")
          else:
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
