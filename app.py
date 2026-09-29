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
        "KPIs",
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

# ==================== ABA KPIS (PRIMEIRA OPÇÃO) ====================
if aba == "KPIs":
  st.title("🎯 Central de KPIs Inteligentes & Previsibilidade de Risco")
  st.markdown(
      "Diagnóstico patrimonial completo com métricas de **fragilidade"
      " financeira, alavancagem de cartões, previsibilidade de caixa** e"
      " filtros globais reativos."
  )

  df = st.session_state.lancamentos.copy()

  if df.empty:
    st.warning(
        "Nenhum lançamento cadastrado ainda. Vá até a aba 'Lançamentos' para"
        " popular seus dados."
    )
  else:
    # Conversões e tratamento de dados
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    df["AnoMês"] = df["Data"].dt.to_period("M").astype(str)
    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0.0)

    if "Status" not in df.columns:
      df["Status"] = "Efetivado"
    df["Status"] = df["Status"].fillna("Efetivado")

    # ==================== FILTROS PODEROSOS NA BARRA LATERAL ====================
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎛️ Filtros Globais Poderosos")

    # 1. Filtro de Status (Efetivado, Pendente, Budget, etc.)
    status_disponiveis = df["Status"].unique().tolist()
    filtro_status = st.sidebar.multiselect(
        "📌 Status do Lançamento",
        options=status_disponiveis,
        default=status_disponiveis,
        help=(
            "Filtre entre efetivados, previstos, orçados (budget) ou pendentes."
        ),
    )

    # 2. Filtro de Tipo (Receita / Despesa)
    tipos_disponiveis = (
        df["Tipo"].dropna().unique().tolist()
        if "Tipo" in df.columns
        else ["Receita", "Despesa"]
    )
    filtro_tipos = st.sidebar.multiselect(
        "💰 Tipo de Movimentação",
        options=tipos_disponiveis,
        default=tipos_disponiveis,
    )

    # 3. Filtro de Anos
    anos_disponíveis = (
        sorted(df["Data"].dt.year.dropna().unique().astype(int))
        if not df["Data"].dropna().empty
        else [2026]
    )
    filtro_anos = st.sidebar.multiselect(
        "📅 Anos de Referência",
        options=anos_disponíveis,
        default=anos_disponíveis,
    )

    # 4. Filtro de Contas
    contas_disponíveis = (
        df["Conta"].dropna().unique().tolist()
        if "Conta" in df.columns
        else []
    )
    filtro_contas = st.sidebar.multiselect(
        "🏦 Contas / Carteiras",
        options=contas_disponíveis,
        default=contas_disponíveis,
    )

    # 5. Filtro de Categorias
    categorias_disponíveis = (
        df["Categoria"].dropna().unique().tolist()
        if "Categoria" in df.columns
        else []
    )
    filtro_categorias = st.sidebar.multiselect(
        "🏷️ Categorias",
        options=categorias_disponíveis,
        default=categorias_disponíveis,
    )

    # 6. Filtro de Período Específico de Datas
    st.sidebar.markdown("---")
    usar_filtro_data = st.sidebar.checkbox(
        "⏱️ Ativar Intervalo de Datas Personalizado", value=False
    )
    if usar_filtro_data and not df["Data"].dropna().empty:
      min_d = df["Data"].min().date()
      max_d = df["Data"].max().date()
      intervalo_datas = st.sidebar.date_input(
          "Selecione o Período", value=(min_d, max_d)
      )

    # ==================== APLICAÇÃO DOS FILTROS PODEROSOS ====================
    df_filtrado = df.copy()
    if filtro_status:
      df_filtrado = df_filtrado[df_filtrado["Status"].isin(filtro_status)]
    if filtro_tipos and "Tipo" in df_filtrado.columns:
      df_filtrado = df_filtrado[df_filtrado["Tipo"].isin(filtro_tipos)]
    if filtro_anos:
      df_filtrado = df_filtrado[df_filtrado["Data"].dt.year.isin(filtro_anos)]
    if filtro_contas and "Conta" in df_filtrado.columns:
      df_filtrado = df_filtrado[df_filtrado["Conta"].isin(filtro_contas)]
    if filtro_categorias and "Categoria" in df_filtrado.columns:
      df_filtrado = df_filtrado[
          df_filtrado["Categoria"].isin(filtro_categorias)
      ]
    if usar_filtro_data and "intervalo_datas" in locals() and len(intervalo_datas) == 2:
      d_inicio, d_fim = pd.to_datetime(
          intervalo_datas[0]
      ), pd.to_datetime(intervalo_datas[1])
      df_filtrado = df_filtrado[
          (df_filtrado["Data"] >= d_inicio) & (df_filtrado["Data"] <= d_fim)
      ]

    receitas_df = df_filtrado[df_filtrado["Tipo"].str.lower() == "receita"]
    despesas_df = df_filtrado[df_filtrado["Tipo"].str.lower() == "despesa"]

    total_receitas = receitas_df["Valor"].sum()
    total_despesas = despesas_df["Valor"].sum()
    saldo_liquido = total_receitas - total_despesas

    # ==================== CÁLCULO DOS 25 KPIS (COM FOCO EM PREVISIBILIDADE) ====================
    kpi_1 = saldo_liquido  # 1. Saldo Líquido Global
    kpi_2 = total_receitas  # 2. Total de Receitas
    kpi_3 = total_despesas  # 3. Total de Despesas
    kpi_4 = (
        (saldo_liquido / total_receitas * 100) if total_receitas > 0 else 0.0
    )  # 4. Taxa de Poupança (%)

    dias_periodo = (
        (df_filtrado["Data"].max() - df_filtrado["Data"].min()).days + 1
        if not df_filtrado.empty
        else 1
    )
    dias_periodo = max(dias_periodo, 1)
    kpi_5 = total_despesas / dias_periodo  # 5. Custo Médio Diário

    meses_unicos = (
        df_filtrado["AnoMês"].nunique() if not df_filtrado.empty else 1
    )
    kpi_6 = total_despesas / max(meses_unicos, 1)  # 6. Burn Rate Mensal

    caixa_total = (
        df[df["Tipo"].str.lower() == "receita"]["Valor"].sum()
        - df[df["Tipo"].str.lower() == "despesa"]["Valor"].sum()
    )
    kpi_7 = caixa_total / kpi_6 if kpi_6 > 0 else 0.0  # 7. Cobertura de Reserva

    essenciais = ["Moradia", "Alimentação"]
    desp_essencial = despesas_df[
        despesas_df["Categoria"].isin(essenciais)
    ]["Valor"].sum()
    kpi_8 = (
        (desp_essencial / total_receitas * 100) if total_receitas > 0 else 0.0
    )  # 8. Comprometimento Essencial

    kpi_9 = (
        total_despesas / len(despesas_df) if not despesas_df.empty else 0.0
    )  # 9. Ticket Médio por Transação
    kpi_10 = (
        despesas_df["Valor"].max() if not despesas_df.empty else 0.0
    )  # 10. Maior Pico de Despesa

    media_mensal_liquida = (
        (total_receitas - total_despesas) / max(meses_unicos, 1)
    )
    kpi_11 = (
        caixa_total + (media_mensal_liquida * 3)
    )  # 11. Projeção de Saldo (+3M)

    salarios = receitas_df[
        receitas_df["Categoria"].str.lower() == "salário"
    ]["Valor"].sum()
    kpi_12 = (
        ((total_receitas - salarios) / total_receitas * 100)
        if total_receitas > 0
        else 0.0
    )  # 12. Índice Renda Passiva / Outras

    desp_por_mes = despesas_df.groupby("AnoMês")["Valor"].sum()
    kpi_13 = (
        desp_por_mes.std() if len(desp_por_mes) > 1 else 0.0
    )  # 13. Volatilidade de Gastos

    discricionarias = ["Lazer"]
    desp_disc = despesas_df[
        despesas_df["Categoria"].isin(discricionarias)
    ]["Valor"].sum()
    kpi_14 = (
        (desp_disc / total_despesas * 100) if total_despesas > 0 else 0.0
    )  # 14. Gasto Discricionário

    kpi_15 = len(df_filtrado)  # 15. Volume Transacional
    kpi_16 = (
        (total_receitas / (total_despesas + 1)) if total_despesas > 0 else 100.0
    )  # 16. Eficiência de Arrecadação
    kpi_17 = (
        (caixa_total / kpi_5) if kpi_5 > 0 else 0.0
    )  # 17. Runway Financeiro (Dias)
    kpi_18 = kpi_4  # 18. Margem Pessoal (%)

    parcelados = (
        df_filtrado[
            df_filtrado["Parcelas"].notna()
            & (df_filtrado["Parcelas"] != "")
            & (df_filtrado["Parcelas"] != "1")
        ]
        if "Parcelas" in df_filtrado.columns
        else pd.DataFrame()
    )
    kpi_19 = len(parcelados)  # 19. Transações Parceladas Ativas
    kpi_20 = media_mensal_liquida * 12  # 20. Potencial Anual (CAGR)

    # --- 5 NOVOS KPIS DE PREVISIBILIDADE E RISCO DE CARTÃO/PASSIVOS ---
    valor_parcelado_total = (
        parcelados["Valor"].sum() if not parcelados.empty else 0.0
    )
    kpi_21 = (
        (valor_parcelado_total / total_receitas * 100)
        if total_receitas > 0
        else 0.0
    )

    custo_essencial_mensal = desp_essencial / max(meses_unicos, 1)
    kpi_22 = (
        (caixa_total / custo_essencial_mensal)
        if custo_essencial_mensal > 0
        else 99.0
    )

    limite_total_cartoes = sum(
        [c.get("Limite", 0) for c in st.session_state.get("cartoes", [])]
    )
    gastos_cartao = (
        df_filtrado[
            df_filtrado["Conta"].str.contains(
                "cartão|credito", case=False, na=False
            )
            | df_filtrado["Categoria"].str.contains(
                "cartão", case=False, na=False
            )
        ]["Valor"].sum()
        if not df_filtrado.empty
        else 0.0
    )
    kpi_23 = (
        (gastos_cartao / limite_total_cartoes * 100)
        if limite_total_cartoes > 0
        else 0.0
    )

    kpi_24 = (
        (salarios / total_receitas * 100) if total_receitas > 0 else 100.0
    )

    score_estresse = min(
        max(
            (kpi_8 * 0.4)
            + (kpi_21 * 0.4)
            - (min(kpi_7, 6) / 6 * 20),  # Essenciais + Parcelamentos - Reserva
            0.0,
        ),
        100.0,
    )
    kpi_25 = score_estresse

    # ==================== PAINEL DE DIAGNÓSTICO INTELIGENTE DE RISCO ====================
    st.markdown("### 🔍 Diagnóstico Avançado de Resiliência & Fragilidade")
    if kpi_25 < 30:
      st.success(
          "🛡️ **Status de Saúde: Robusto e Seguro.** Seu índice de fragilidade"
          f" está controlado ({kpi_25:.1f}/100). Você possui excelente margem"
          " de manobra contra imprevistos."
      )
    elif kpi_25 < 60:
      st.warning(
          "⚠️ **Status de Saúde: Atenção Moderada.** Seus compromissos futuros"
          f" (parcelamentos e essenciais) atingem {kpi_25:.1f}/100 no índice de"
          " estresse. Evite novas alavancagens em cartões no curto prazo."
      )
    else:
      st.error(
          "🚨 **Status de Risco Crítico:** Alerta de fragilidade financeira"
          f" acionado ({kpi_25:.1f}/100). Alto comprometimento da renda com"
          " parcelamentos e faturas de cartão. Recomenda-se forte contenção de"
          " gastos discricionários."
      )

    # ==================== EXIBIÇÃO EM BLOCOS DE CARDS (25 KPIS) ====================
    st.markdown("---")
    st.subheader(
        "📊 1. Visão Geral Patrimonial & Fluxo (Passado & Presente)"
    )
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric(
        "1. Saldo Líquido",
        f"R$ {kpi_1:,.2f}",
        delta=f"R$ {media_mensal_liquida:,.2f}/mês",
    )
    col2.metric("2. Total Receitas", f"R$ {kpi_2:,.2f}")
    col3.metric("3. Total Despesas", f"R$ {kpi_3:,.2f}")
    col4.metric(
        "4. Taxa de Poupança",
        f"{kpi_4:.1f}%",
        delta="Ideal > 20%",
        delta_color="normal" if kpi_4 >= 20 else "inverse",
    )
    col5.metric(
        "7. Cobertura de Reserva",
        f"{kpi_7:.1f} meses",
        delta="Meta: 6m",
        delta_color="normal" if kpi_7 >= 6 else "inverse",
    )

    st.markdown("---")
    st.subheader("⚡ 2. Indicadores de Ritmo, Custos & Riscos")
    col6, col7, col8, col9, col10 = st.columns(5)
    col6.metric("5. Custo Médio Diário", f"R$ {kpi_5:,.2f} / dia")
    col7.metric("6. Burn Rate Mensal", f"R$ {kpi_6:,.2f} / mês")
    col8.metric("8. Comprometimento Essencial", f"{kpi_8:.1f}%")
    col9.metric("9. Ticket Médio Despesa", f"R$ {kpi_9:,.2f}")
    col10.metric("10. Maior Pico de Gasto", f"R$ {kpi_10:,.2f}")

    st.markdown("---")
    st.subheader("🔮 3. Projeções Futuras & Eficiência Estrutural")
    col11, col12, col13, col14, col15 = st.columns(5)
    col11.metric(
        "11. Projeção Caixa (+3M)",
        f"R$ {kpi_11:,.2f}",
        delta="Tendência Linear",
    )
    col12.metric("12. Índice Renda Passiva", f"{kpi_12:.1f}%")
    col13.metric("13. Volatilidade Mensal", f"R$ {kpi_13:,.2f}")
    col14.metric("14. Gasto Discricionário", f"{kpi_14:.1f}%")
    col15.metric("15. Volume Transacional", f"{kpi_15} lçs")

    st.markdown("---")
    st.subheader("🛡️ 4. Solidez, Alavancagem & Longevidade")
    col16, col17, col18, col19, col20 = st.columns(5)
    col16.metric("16. Eficiência Arrecadação", f"{kpi_16:.2f}x")
    col17.metric(
        "17. Runway Financeiro",
        f"{kpi_17:.0f} dias",
        delta="Dias de fôlego",
    )
    col18.metric("18. Margem Pessoal", f"{kpi_18:.1f}%")
    col19.metric("19. Transações Parceladas", f"{kpi_19} ativas")
    col20.metric("20. Potencial Anual (CAGR)", f"R$ {kpi_20:,.2f}")

    st.markdown("---")
    st.subheader(
        "🎯 5. Indicadores Avançados de Previsibilidade & Fragilidade"
    )
    col21, col22, col23, col24, col25 = st.columns(5)
    col21.metric(
        "21. Fragilidade Parcelada",
        f"{kpi_21:.1f}%",
        delta="Comprometimento da Renda",
        delta_color="inverse" if kpi_21 > 30 else "normal",
    )
    col22.metric(
        "22. IVP (Vulnerabilidade Curta)",
        f"{kpi_22:.1f} meses",
        delta="Fôlego Essencial Puro",
    )
    col23.metric(
        "23. Alavancagem de Cartão",
        f"{kpi_23:.1f}%",
        delta="Do limite total em uso",
        delta_color="inverse" if kpi_23 > 50 else "normal",
    )
    col24.metric("24. Previsibilidade de Caixa", f"{kpi_24:.1f}%")
    col25.metric(
        "25. Score Estresse Estrutural",
        f"{kpi_25:.1f} pts",
        delta="Escala 0 a 100",
        delta_color="inverse" if kpi_25 > 50 else "normal",
    )

    # ==================== GRÁFICOS PODEROSOS DE ANÁLISE ====================
    st.markdown("---")
    st.subheader(
        "📈 Painel Gráfico Dinâmico (Reativo aos Filtros de Status, Datas e"
        " Categorias)"
    )

    gcol1, gcol2 = st.columns(2)

    with gcol1:
      st.markdown("### 📊 Evolução Mensal (Receitas vs. Despesas)")
      if not df_filtrado.empty:
        evolu_df = (
            df_filtrado.groupby(["AnoMês", "Tipo"])["Valor"]
            .sum()
            .reset_index()
        )
        fig_evolucao = px.bar(
            evolu_df,
            x="AnoMês",
            y="Valor",
            color="Tipo",
            barmode="group",
            color_discrete_map={"Receita": "#2ecc71", "Despesa": "#e74c3c"},
            template="plotly_dark",
        )
        fig_evolucao.update_layout(
            margin=dict(l=20, r=20, t=30, b=20), height=350
        )
        st.plotly_chart(fig_evolucao, use_container_width=True)
      else:
        st.info("Sem dados para o gráfico de evolução com os filtros.")

    with gcol2:
      st.markdown("### 🍩 Composição de Despesas por Categoria")
      if not despesas_df.empty:
        cat_df = despesas_df.groupby("Categoria")["Valor"].sum().reset_index()
        fig_donut = px.pie(
            cat_df,
            names="Categoria",
            values="Valor",
            hole=0.4,
            template="plotly_dark",
        )
        fig_donut.update_layout(
            margin=dict(l=20, r=20, t=30, b=20), height=350
        )
        st.plotly_chart(fig_donut, use_container_width=True)
      else:
        st.info("Sem despesas registradas para o gráfico de categorias.")

    st.markdown("### 🚀 Simulação Preditiva de Fluxo de Caixa Acumulado")
    if not df_filtrado.empty:
      df_temp = df_filtrado.sort_values("Data").copy()
      df_temp["FluxoDiario"] = df_temp.apply(
          lambda row: row["Valor"]
          if str(row["Tipo"]).lower() == "receita"
          else -row["Valor"],
          axis=1,
      )
      df_temp["CaixaAcumulado"] = df_temp["FluxoDiario"].cumsum()

      fig_proj = px.line(
          df_temp,
          x="Data",
          y="CaixaAcumulado",
          markers=True,
          template="plotly_dark",
          title=(
              "Curva de Crescimento do Patrimônio Líquido Baseada nos Filtros"
              " Atuais"
          ),
      )
      fig_proj.update_traces(line_color="#3498db", line_width=3)
      fig_proj.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=350)
      st.plotly_chart(fig_proj, use_container_width=True)
    else:
      st.info("Insira ou ajuste os filtros para visualizar a curva preditiva.")

# ==================== DEMAIS ABAS DO SISTEMA ====================
elif aba == "Dashboard":
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
      st.subheader("🏷️ Detalhamento de Gastos por Descrição e Categoria")
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
  else:
    st.info("Nenhum lançamento registrado ainda.")

elif aba == "Statistics":
  st.title("📊 Estatísticas e Projeções Financeiras")
  if st.session_state.lancamentos.empty:
    st.warning("Nenhum dado disponível para análise estatística.")
  else:
    df_stat = st.session_state.lancamentos.copy()
    df_stat["Data"] = pd.to_datetime(df_stat["Data"])
    if "Status" not in df_stat.columns:
      df_stat["Status"] = "Efetivado"

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

    if ano_stat_sel:
      df_stat = df_stat[df_stat["Data"].dt.year.isin(ano_stat_sel)]
    if conta_stat_sel:
      df_stat = df_stat[
          df_stat["Conta"].isin(conta_stat_sel)
          | df_stat["Conta Destino"].isin(conta_stat_sel)
      ]
    if cat_stat_sel:
      df_stat = df_stat[df_stat["Categoria"].isin(cat_stat_sel)]

    if df_stat.empty:
      st.warning("Nenhum dado encontrado com os filtros selecionados.")
    else:
      if frequencia_stat == "Mensal":
        df_stat["Periodo_Analise"] = df_stat["Data"].dt.to_period("M").astype(str)
      elif frequencia_stat == "Trimestral":
        df_stat["Periodo_Analise"] = df_stat["Data"].dt.to_period("Q").astype(str)
      else:
        df_stat["Periodo_Analise"] = df_stat["Data"].dt.year.astype(str)

      periodos_disponiveis = sorted(
          df_stat["Periodo_Analise"].unique().tolist(), reverse=True
      )
      periodo_escolhido_stat = st.selectbox(
          f"📅 Selecione o {frequencia_stat} Específico", periodos_disponiveis
      )
      df_periodo_stat = df_stat[
          df_stat["Periodo_Analise"] == periodo_escolhido_stat
      ]

      if not df_periodo_stat.empty:
        valores_serie = df_periodo_stat["Valor"]
        media = valores_serie.mean()
        mediana = valores_serie.median()
        desvio_padrao = valores_serie.std() if len(valores_serie) > 1 else 0.0

        st.markdown("---")
        st.subheader("📊 Parâmetros Estatísticos Básicos")
        st.metric("Média", f"R$ {media:,.2f}")
        st.metric("Mediana", f"R$ {mediana:,.2f}")
        st.metric("Desvio Padrão", f"R$ {desvio_padrao:,.2f}")

elif aba == "Financial Analysis":
  st.title("💼 Financial Analysis & Funções Financeiras (Excel Core)")
  if st.session_state.lancamentos.empty:
    st.warning("⚠️ Nenhum lançamento disponível.")
  else:
    df_fin = st.session_state.lancamentos.copy()
    df_fin["Data"] = pd.to_datetime(df_fin["Data"])
    fluxos = df_fin["Valor"].values
    try:
      vpl_calculado = npf.npv(0.10, fluxos)
    except Exception:
      vpl_calculado = 0.0
    st.metric("VPL / NPV Global", f"R$ {vpl_calculado:,.2f}")

elif aba == "🤖 IA & Assistant":
  st.title("🤖 Central de Inteligência Artificial & Gemini Assistant")
  st.info(
      "Converse com o Gemini ou analise os relatórios gerados por IA nos"
      " blocos anteriores."
  )

elif aba == "Lançamentos":
  st.title("📋 Central Inteligente de Lançamentos")
  if st.session_state.lancamentos.empty:
    st.info("Nenhum lançamento cadastrado.")
  else:
    st.dataframe(st.session_state.lancamentos, use_container_width=True)

elif aba == "Cadastro":
  st.title("💵 Registrar Lançamento")
  st.info(
      "Utilize o formulário completo de cadastro presente nas versões padrão"
      " do seu app."
  )

elif aba == "Cadastro de Categorias e Contas":
  st.title("📝 Cadastro Geral")
  st.write("Categorias:", st.session_state.categorias)
  st.write("Contas:", st.session_state.contas)

elif aba == "Cartões de Crédito":
  st.title("💳 Gestão de Cartões de Crédito")
  if st.session_state.cartoes:
    st.dataframe(pd.DataFrame(st.session_state.cartoes), use_container_width=True)
  else:
    st.info("Nenhum cartão cadastrado.")

elif aba == "Backup & Segurança":
  st.title("🛡️ Central de Backup e Segurança")
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
