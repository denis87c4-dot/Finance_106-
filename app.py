import calendar
import io
import json
import zipfile
import numpy as np
import numpy_financial as npf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import norm
import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="Fluxo Financeiro Profissional", page_icon="💰", layout="wide"
)

# ==================== ESTADOS DA SESSÃO ====================
COLUNAS_LANC = [
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
    "Cenario",
]

if "lancamentos" not in st.session_state:
  st.session_state.lancamentos = pd.DataFrame(columns=COLUNAS_LANC)

if (
    not st.session_state.lancamentos.empty
    and "Status" not in st.session_state.lancamentos.columns
):
  st.session_state.lancamentos["Status"] = "Efetivado"

if (
    not st.session_state.lancamentos.empty
    and "Cenario" not in st.session_state.lancamentos.columns
):
  st.session_state.lancamentos["Cenario"] = "Efetivado"

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

# ==================== NAVEGAÇÃO LATERAL ====================
aba = st.sidebar.radio(
    "Navegação",
    [
        "🤖 IA Analysis",
        "🔔 Norm.Dist (Probabilidade)",
        "📈 Inteligência Preditiva & Regressão",
        "🔍 Auditoria Avançada",
        "🚀 Advanced Analytics & KPIs",
        "⚡ Advanced KPIs 2",
        "Sophisticated Graphics",
        "Graphics",
        "KPIs",
        "Dashboard",
        "Statistics",
        "Statistic2",
        "Financial Analysis",
        "🤖 IA & Assistant",
        "Lançamentos",
        "Cadastro",
        "Cadastro de Categorias e Contas",
        "Cartões de Crédito",
        "Backup & Segurança",
    ],
)

# ==================== PAINEL DE FILTROS PODEROSOS (GLOBAL) ====================
st.sidebar.markdown("---")
st.sidebar.subheader("🎛️ Filtros Poderosos Globais")

df_global = st.session_state.lancamentos.copy()

if not df_global.empty:
  df_global["Data"] = pd.to_datetime(df_global["Data"], errors="coerce")
  df_global["Valor"] = pd.to_numeric(df_global["Valor"], errors="coerce").fillna(
      0.0
  )

  # 1. Período
  min_date = (
      df_global["Data"].min().date()
      if not df_global["Data"].isna().all()
      else pd.Timestamp.today().date()
  )
  max_date = (
      df_global["Data"].max().date()
      if not df_global["Data"].isna().all()
      else pd.Timestamp.today().date()
  )
  filtro_periodo = st.sidebar.date_input(
      "Período de Análise",
      value=(min_date, max_date),
      min_value=min_date,
      max_value=max_date,
  )

  # 2. Extração de Meses Disponíveis para o Filtro Específico
  df_global["AnoMesStr"] = df_global["Data"].dt.to_period("M").astype(str)
  meses_disponiveis = sorted(df_global["AnoMesStr"].dropna().unique().tolist())

  sel_meses = st.sidebar.multiselect(
      "Filtrar por Meses Específicos (AAAA-MM)",
      options=meses_disponiveis,
      default=meses_disponiveis,
  )

  # 3. Opções dos Demais Filtros
  status_opc = (
      df_global["Status"].dropna().unique().tolist()
      if "Status" in df_global.columns
      else []
  )
  cenario_opc = (
      df_global["Cenario"].dropna().unique().tolist()
      if "Cenario" in df_global.columns
      else []
  )
  tipo_opc = df_global["Tipo"].dropna().unique().tolist()
  cat_opc = df_global["Categoria"].dropna().unique().tolist()
  conta_opc = (
      df_global["Conta"].dropna().unique().tolist()
      if "Conta" in df_global.columns
      else []
  )
  modo_opc = (
      df_global["Modo Valor"].dropna().unique().tolist()
      if "Modo Valor" in df_global.columns
      else []
  )

  # 4. Componentes Multiselect
  sel_status = st.sidebar.multiselect(
      "Filtrar por Status", options=status_opc, default=status_opc
  )
  sel_cenario = st.sidebar.multiselect(
      "Filtrar por Cenário (Orçado/Efetivado)",
      options=cenario_opc,
      default=cenario_opc,
  )
  sel_tipo = st.sidebar.multiselect(
      "Filtrar por Tipo", options=tipo_opc, default=tipo_opc
  )
  sel_cat = st.sidebar.multiselect(
      "Filtrar por Categoria", options=cat_opc, default=cat_opc
  )
  sel_conta = st.sidebar.multiselect(
      "Filtrar por Conta", options=conta_opc, default=conta_opc
  )
  sel_modo = st.sidebar.multiselect(
      "Filtrar por Modo Valor", options=modo_opc, default=modo_opc
  )

  # Aplicação da Máscara Global em todas as abas
  mask_global = pd.Series(True, index=df_global.index)
  if len(filtro_periodo) == 2:
    start_d, end_d = filtro_periodo
    mask_global &= df_global["Data"].dt.date.between(start_d, end_d)
  if sel_meses:
    mask_global &= df_global["AnoMesStr"].isin(sel_meses)
  if sel_status and "Status" in df_global.columns:
    mask_global &= df_global["Status"].isin(sel_status)
  if sel_cenario and "Cenario" in df_global.columns:
    mask_global &= df_global["Cenario"].isin(sel_cenario)
  if sel_tipo:
    mask_global &= df_global["Tipo"].isin(sel_tipo)
  if sel_cat:
    mask_global &= df_global["Categoria"].isin(sel_cat)
  if sel_conta and "Conta" in df_global.columns:
    mask_global &= df_global["Conta"].isin(sel_conta)
  if sel_modo and "Modo Valor" in df_global.columns:
    mask_global &= df_global["Modo Valor"].isin(sel_modo)

  df_filtrado_global = df_global.drop(columns=["AnoMesStr"]).copy()
  df_filtrado_global = df_filtrado_global[mask_global]
else:
  df_filtrado_global = pd.DataFrame(columns=COLUNAS_LANC)

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Configurações Preditivas")
horizonte_proj = st.sidebar.slider(
    "Horizonte de Projeção (Meses Futuros)", 1, 12, 3
)
janela_mm = st.sidebar.slider("Janela da Média Móvel (Meses)", 2, 6, 3)


# ==================== ABA: IA ANALYSIS ====================
if aba == "🤖 IA Analysis":
  st.title("🤖 IA Analysis & Dossiê Financeiro Inteligente")
  st.markdown(
      "Painel executivo gerado automaticamente considerando os **Filtros"
      " Poderosos** ativos (como período, meses específicos, categorias, contas"
      " e o comparativo **Orçado** vs **Efetivado**). Explore também o"
      " **Glossário Estatístico** integrado abaixo."
  )

  if df_filtrado_global.empty:
    st.info(
        "Nenhum lançamento encontrado com os filtros atuais para gerar o"
        " dossiê."
    )
  else:
    df_ia = df_filtrado_global.copy()

    # Cálculos dinâmicos baseados estritamente nos filtros aplicados
    tot_reg = len(df_ia)
    rec_val = df_ia.loc[
        df_ia["Tipo"].str.lower().str.contains("receita|income", na=False),
        "Valor",
    ].sum()
    esp_val = df_ia.loc[
        df_ia["Tipo"].str.lower().str.contains("despesa|expense", na=False),
        "Valor",
    ].sum()
    saldo_liq = rec_val - esp_val

    st.subheader("📌 Resumo Executivo & Diagnóstico Atual")

    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("Registros Filtrados", f"{tot_reg:,}")
    col_b.metric("Total Receitas", f"R$ {rec_val:,.2f}")
    col_c.metric("Total Despesas", f"R$ {esp_val:,.2f}")
    col_d.metric("Saldo Líquido", f"R$ {saldo_liq:,.2f}")

    st.markdown("---")
    st.markdown("### 📝 Dossiê Comportamental Automático")

    status_txt = (
        "Superávit (Saudável)"
        if saldo_liq >= 0
        else "Déficit (Atenção Necessária)"
    )
    taxa_ret = (
        (saldo_liq / rec_val * 100)
        if rec_val > 0
        else (0.0 if saldo_liq >= 0 else -100.0)
    )

    st.info(
        f"""
        * **Situação do Recorte Atual:** O cenário filtrado encontra-se em **{status_txt}**.
        * **Taxa de Retenção / Poupança:** Representa **{taxa_ret:.2f}%** do volume total de entradas capturado pelas suas regras de filtro.
        * **Interatividade de Filtros:** Todos os valores acima mudam instantaneamente conforme você altera as categorias, os meses específicos ou alterna entre cenários de **Budget (Orçado)** e **Efetivado** na barra lateral.
        """
    )

    st.markdown("---")
    st.subheader(
        "📖 Guia Explicativo: Significado dos Termos Estatísticos do Sistema"
    )

    with st.expander("📊 O que é Média ($\mu$) e Desvio Padrão ($\sigma$)?"):
      st.markdown(
          """
            * **Média ($\mu$):** É o valor central ou esperado de uma série (por exemplo, quanto você costuma gastar ou arrecadar mensalmente).
            * **Desvio Padrão ($\sigma$):** Mede a **volatilidade**. Se for alto, significa que os valores oscilam bruscamente de um mês para o outro; se for baixo, indica estabilidade e previsibilidade nas suas finanças.
            """
      )

    with st.expander(
        "🔔 O que é a Curva de Sino e Probabilidade Acumulada ($P(X < x)$)?"
    ):
      st.markdown(
          """
            * **Curva de Sino (Distribuição Normal):** Modelo estatístico que mapeia a probabilidade dos seus resultados financeiros mês a mês.
            * **Probabilidade Acumulada $P(X < x)$:** Informa a chance percentual de que o resultado de um determinado mês fique **abaixo** de um valor de referência $x$ que você definir na aba de probabilidade.
            """
      )

    with st.expander("📈 O que são as Regressões e a Média Móvel?"):
      st.markdown(
          """
            * **Regressão Linear / Exponencial / Logarítmica:** Ferramentas estatísticas que traçam tendências ao longo do tempo para prever se as finanças estão numa trajetória de alta ou baixa.
            * **Média Móvel:** Calcula a média de uma janela de meses consecutivos (ex: últimos 3 meses) para eliminar ruídos e mostrar a real tendência do seu fluxo de caixa.
            """
      )


# ==================== ABA: NORM.DIST (PROBABILIDADE) ====================
if aba == "🔔 Norm.Dist (Probabilidade)":
  st.title("🔔 Curva de Sino & Análise Probabilística (Norm.Dist)")
  # (Restante das abas...)


# ==================== NAVEGAÇÃO LATERAL ====================
aba = st.sidebar.radio(
    "Navegação",
    [
        "🔔 Norm.Dist (Probabilidade)",
        "📈 Inteligência Preditiva & Regressão",
        "🔍 Auditoria Avançada",
        "🚀 Advanced Analytics & KPIs",
        "⚡ Advanced KPIs 2",
        "Sophisticated Graphics",
        "Graphics",
        "KPIs",
        "Dashboard",
        "Statistics",
        "Statistic2",
        "Financial Analysis",
        "🤖 IA & Assistant",
        "Lançamentos",
        "Cadastro",
        "Cadastro de Categorias e Contas",
        "Cartões de Crédito",
        "Backup & Segurança",
    ],
)

# ==================== PAINEL DE FILTROS PODEROSOS (GLOBAL) ====================
st.sidebar.markdown("---")
st.sidebar.subheader("🎛️ Filtros Poderosos Globais")

df_global = st.session_state.lancamentos.copy()

if not df_global.empty:
  df_global["Data"] = pd.to_datetime(df_global["Data"], errors="coerce")
  df_global["Valor"] = pd.to_numeric(df_global["Valor"], errors="coerce").fillna(
      0.0
  )

  # 1. Período
  min_date = (
      df_global["Data"].min().date()
      if not df_global["Data"].isna().all()
      else pd.Timestamp.today().date()
  )
  max_date = (
      df_global["Data"].max().date()
      if not df_global["Data"].isna().all()
      else pd.Timestamp.today().date()
  )
  filtro_periodo = st.sidebar.date_input(
      "Período de Análise",
      value=(min_date, max_date),
      min_value=min_date,
      max_value=max_date,
  )

  # 2. Extração de Meses Disponíveis para o Filtro Específico
  df_global["AnoMesStr"] = df_global["Data"].dt.to_period("M").astype(str)
  meses_disponiveis = sorted(df_global["AnoMesStr"].dropna().unique().tolist())

  sel_meses = st.sidebar.multiselect(
      "Filtrar por Meses Específicos (AAAA-MM)",
      options=meses_disponiveis,
      default=meses_disponiveis,
  )

  # 3. Opções dos Demais Filtros
  status_opc = (
      df_global["Status"].dropna().unique().tolist()
      if "Status" in df_global.columns
      else []
  )
  cenario_opc = (
      df_global["Cenario"].dropna().unique().tolist()
      if "Cenario" in df_global.columns
      else []
  )
  tipo_opc = df_global["Tipo"].dropna().unique().tolist()
  cat_opc = df_global["Categoria"].dropna().unique().tolist()
  conta_opc = (
      df_global["Conta"].dropna().unique().tolist()
      if "Conta" in df_global.columns
      else []
  )
  modo_opc = (
      df_global["Modo Valor"].dropna().unique().tolist()
      if "Modo Valor" in df_global.columns
      else []
  )

  # 4. Componentes Multiselect
  sel_status = st.sidebar.multiselect(
      "Filtrar por Status", options=status_opc, default=status_opc
  )
  sel_cenario = st.sidebar.multiselect(
      "Filtrar por Cenário (Orçado/Efetivado)",
      options=cenario_opc,
      default=cenario_opc,
  )
  sel_tipo = st.sidebar.multiselect(
      "Filtrar por Tipo", options=tipo_opc, default=tipo_opc
  )
  sel_cat = st.sidebar.multiselect(
      "Filtrar por Categoria", options=cat_opc, default=cat_opc
  )
  sel_conta = st.sidebar.multiselect(
      "Filtrar por Conta", options=conta_opc, default=conta_opc
  )
  sel_modo = st.sidebar.multiselect(
      "Filtrar por Modo Valor", options=modo_opc, default=modo_opc
  )

  # Aplicação da Máscara Global em todas as abas
  mask_global = pd.Series(True, index=df_global.index)
  if len(filtro_periodo) == 2:
    start_d, end_d = filtro_periodo
    mask_global &= df_global["Data"].dt.date.between(start_d, end_d)
  if sel_meses:
    mask_global &= df_global["AnoMesStr"].isin(sel_meses)
  if sel_status and "Status" in df_global.columns:
    mask_global &= df_global["Status"].isin(sel_status)
  if sel_cenario and "Cenario" in df_global.columns:
    mask_global &= df_global["Cenario"].isin(sel_cenario)
  if sel_tipo:
    mask_global &= df_global["Tipo"].isin(sel_tipo)
  if sel_cat:
    mask_global &= df_global["Categoria"].isin(sel_cat)
  if sel_conta and "Conta" in df_global.columns:
    mask_global &= df_global["Conta"].isin(sel_conta)
  if sel_modo and "Modo Valor" in df_global.columns:
    mask_global &= df_global["Modo Valor"].isin(sel_modo)

  df_filtrado_global = df_global.drop(columns=["AnoMesStr"]).copy()
  df_filtrado_global = df_filtrado_global[mask_global]
else:
  df_filtrado_global = pd.DataFrame(columns=COLUNAS_LANC)

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Configurações Preditivas")
horizonte_proj = st.sidebar.slider(
    "Horizonte de Projeção (Meses Futuros)", 1, 12, 3
)
janela_mm = st.sidebar.slider("Janela da Média Móvel (Meses)", 2, 6, 3)


# ==================== ABA: NORM.DIST (PROBABILIDADE) ====================
if aba == "🔔 Norm.Dist (Probabilidade)":
  st.title("🔔 Curva de Sino & Análise Probabilística (Norm.Dist)")
  st.markdown(
      "Analise a distribuição estatística e calcule a probabilidade"
      " acumulada ($P(X < x)$) para **Income**, **Expense**, **Cash Flow** e"
      " **Acumulado**, considerando os filtros poderosos, incluindo a"
      " seleção específica de meses."
  )

  if df_filtrado_global.empty:
    st.info(
        "Nenhum lançamento encontrado com os filtros atuais para gerar a"
        " distribuição normal."
    )
  else:
    df_nd = df_filtrado_global.copy()
    df_nd["MesAno"] = df_nd["Data"].dt.to_period("M").dt.to_timestamp()

    df_mensal_nd = (
        df_nd.groupby(["MesAno", "Tipo"])["Valor"].sum().reset_index()
    )
    df_piv_nd = (
        df_mensal_nd.pivot(index="MesAno", columns="Tipo", values="Valor")
        .fillna(0.0)
        .sort_index()
    )

    cols_lower_nd = {c.lower(): c for c in df_piv_nd.columns}
    inc_c = next(
        (
            cols_lower_nd[c]
            for c in cols_lower_nd
            if "receita" in c or "income" in c or "entrada" in c
        ),
        None,
    )
    exp_c = next(
        (
            cols_lower_nd[c]
            for c in cols_lower_nd
            if "despesa" in c or "expense" in c or "saída" in c
        ),
        None,
    )

    df_serie = pd.DataFrame(index=df_piv_nd.index)
    df_serie["Income"] = df_piv_nd[inc_c] if inc_c else 0.0
    df_serie["Expense"] = df_piv_nd[exp_c] if exp_c else 0.0
    df_serie["Cash_Flow"] = df_serie["Income"] - df_serie["Expense"]
    df_serie["Acumulado"] = df_serie["Cash_Flow"].cumsum()

    col_sel1, col_sel2 = st.columns([2, 2])
    with col_sel1:
      metrica_escolhida = st.selectbox(
          "Escolha a Métrica para Análise Norm.Dist:",
          ["Cash_Flow", "Income", "Expense", "Acumulado"],
          format_func=lambda x: {
              "Cash_Flow": "Fluxo de Caixa (Cash Flow)",
              "Income": "Receitas (Income)",
              "Expense": "Despesas (Expense)",
              "Acumulado": "Saldo Acumulado",
          }[x],
      )

    serie_dados = df_serie[metrica_escolhida].dropna()

    if len(serie_dados) < 2:
      st.warning(
          "É necessário pelo menos 2 períodos (meses) selecionados para"
          " calcular a média e o desvio padrão da distribuição normal."
      )
    else:
      mu = serie_dados.mean()
      sigma = serie_dados.std()
      if sigma == 0:
        sigma = 1e-5

      with col_sel2:
        val_x = st.number_input(
            f"Valor de referência (x) para probabilidade em {metrica_escolhida}:",
            value=float(mu),
            step=float(max(abs(mu) * 0.05, 1.0)),
        )

      prob_menor = norm.cdf(val_x, loc=mu, scale=sigma) * 100
      prob_maior = (1 - norm.cdf(val_x, loc=mu, scale=sigma)) * 100

      st.markdown("### 📊 Indicadores Estatísticos da Curva")
      k1, k2, k3, k4, k5 = st.columns(5)
      k1.metric("Média ($\mu$)", f"R$ {mu:,.2f}")
      k2.metric("Desvio Padrão ($\sigma$)", f"R$ {sigma:,.2f}")
      k3.metric("Valor de Referência ($x$)", f"R$ {val_x:,.2f}")
      k4.metric("Probabilidade $P(X < x)$", f"{prob_menor:.2f}%")
      k5.metric("Probabilidade $P(X \ge x)$", f"{prob_maior:.2f}%")

      st.markdown("---")

      min_g = mu - 3.5 * sigma
      max_g = mu + 3.5 * sigma
      x_vals_sino = np.linspace(min_g, max_g, 300)
      y_vals_sino = norm.pdf(x_vals_sino, loc=mu, scale=sigma)

      fig_sino = go.Figure()
      fig_sino.add_trace(
          go.Scatter(
              x=x_vals_sino,
              y=y_vals_sino,
              mode="lines",
              name="Distribuição Normal",
              line=dict(color="#1f77b4", width=3),
          )
      )

      x_fill = x_vals_sino[x_vals_sino <= val_x]
      y_fill = y_vals_sino[x_vals_sino <= val_x]
      if len(x_fill) > 0:
        fig_sino.add_trace(
            go.Scatter(
                x=np.concatenate([[x_fill[0]], x_fill, [x_fill[-1]]]),
                y=np.concatenate([[0], y_fill, [0]]),
                fill="toself",
                fillcolor="rgba(31, 119, 180, 0.3)",
                line=dict(color="rgba(255,255,255,0)"),
                name=f"P(X < {val_x:,.2f}) = {prob_menor:.1f}%",
            )
        )

      fig_sino.add_trace(
          go.Scatter(
              x=[val_x, val_x],
              y=[0, norm.pdf(val_x, loc=mu, scale=sigma)],
              mode="lines",
              name=f"Valor x = {val_x:,.2f}",
              line=dict(color="red", width=2, dash="dash"),
          )
      )

      fig_sino.update_layout(
          title=f"Curva de Sino (Norm.Dist) para {metrica_escolhida}",
          xaxis_title="Valores",
          yaxis_title="Densidade de Probabilidade",
          template="plotly_white",
          hovermode="x unified",
      )

      st.plotly_chart(fig_sino, use_container_width=True)

      st.markdown("### 📋 Série Mensal Utilizada no Cálculo")
      st.dataframe(df_serie, use_container_width=True)


# ==================== ABA: INTELIGÊNCIA PREDITIVA & REGRESSÃO ====================
if aba == "📈 Inteligência Preditiva & Regressão":
  st.title("📈 Inteligência Preditiva & Modelagem Estatística")
  # (Restante das outras abas...)

  
# ==================== ABA: INTELIGÊNCIA PREDITIVA & REGRESSÃO ====================
if aba == "📈 Inteligência Preditiva & Regressão":
  st.title("📈 Inteligência Preditiva & Modelagem Estatística")
  # (Restante do código preditivo mantido igual...)

    
# ==================== ABA: AUDITORIA AVANÇADA ====================
if aba == "🔍 Auditoria Avançada":
  st.title("🔍 Auditoria e Conformidade Financeira")
  st.markdown(
      "Painel de controle analítico para verificação de consistência,"
      " rastreabilidade de lançamentos e detecção de anomalias."
  )

  df_audit = st.session_state.lancamentos.copy()

  if df_audit.empty:
    st.info(
        "Nenhum lançamento cadastrado ainda para auditoria. Utilize a aba"
        " 'Lançamentos' para popular a base de dados."
    )
  else:
    # Conversão segura de datas e valores (corrigido com 'coerce')
    df_audit["Data"] = pd.to_datetime(df_audit["Data"], errors="coerce")
    df_audit["Valor"] = pd.to_numeric(
        df_audit["Valor"], errors="coerce"
    ).fillna(0.0)

    st.sidebar.markdown("---")
    st.sidebar.subheader("🎛️ Filtros de Auditoria")

    # Filtro de Período
    min_date = (
        df_audit["Data"].min().date()
        if not df_audit["Data"].isna().all()
        else pd.Timestamp.today().date()
    )
    max_date = (
        df_audit["Data"].max().date()
        if not df_audit["Data"].isna().all()
        else pd.Timestamp.today().date()
    )

    filtro_periodo = st.sidebar.date_input(
        "Período de Análise",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    # Filtros Avançados
    status_opcoes = (
        df_audit["Status"].dropna().unique().tolist()
        if "Status" in df_audit.columns
        else []
    )
    cenario_opcoes = (
        df_audit["Cenario"].dropna().unique().tolist()
        if "Cenario" in df_audit.columns
        else []
    )
    tipo_opcoes = df_audit["Tipo"].dropna().unique().tolist()
    cat_opcoes = df_audit["Categoria"].dropna().unique().tolist()

    sel_status = st.sidebar.multiselect(
        "Filtrar por Status",
        options=status_opcoes,
        default=status_opcoes,
    )
    sel_cenario = st.sidebar.multiselect(
        "Filtrar por Cenário",
        options=cenario_opcoes,
        default=cenario_opcoes,
    )
    sel_tipo = st.sidebar.multiselect(
        "Filtrar por Tipo", options=tipo_opcoes, default=tipo_opcoes
    )
    sel_cat = st.sidebar.multiselect(
        "Filtrar por Categoria", options=cat_opcoes, default=cat_opcoes
    )

    # Aplicação dos Filtros
    mask = pd.Series(True, index=df_audit.index)
    if len(filtro_periodo) == 2:
      start_d, end_d = filtro_periodo
      mask &= df_audit["Data"].dt.date.between(start_d, end_d)

    if sel_status and "Status" in df_audit.columns:
      mask &= df_audit["Status"].isin(sel_status)
    if sel_cenario and "Cenario" in df_audit.columns:
      mask &= df_audit["Cenario"].isin(sel_cenario)
    if sel_tipo:
      mask &= df_audit["Tipo"].isin(sel_tipo)
    if sel_cat:
      mask &= df_audit["Categoria"].isin(sel_cat)

    df_filtrado = df_audit[mask]

    # --- CARDS DE RESUMO EXECUTIVO ---
    col1, col2, col3, col4, col5 = st.columns(5)

    total_registros = len(df_filtrado)
    receitas = df_filtrado.loc[
        df_filtrado["Tipo"].str.lower().str.contains("receita", na=False),
        "Valor",
    ].sum()
    despesas = df_filtrado.loc[
        df_filtrado["Tipo"].str.lower().str.contains("despesa", na=False),
        "Valor",
    ].sum()
    saldo_liq = receitas - despesas
    ticket_medio = df_filtrado["Valor"].mean() if total_registros > 0 else 0

    col1.metric("Total Registros", f"{total_registros:,}")
    col2.metric("Receitas Filtradas", f"R$ {receitas:,.2f}")
    col3.metric("Despesas Filtradas", f"R$ {despesas:,.2f}")
    col4.metric("Saldo Líquido", f"R$ {saldo_liq:,.2f}")
    col5.metric("Ticket Médio", f"R$ {ticket_medio:,.2f}")

    st.markdown("---")

    # --- SEÇÃO DE ANOMALIAS E ALERTAS ---
    st.subheader("🚨 Painel de Exceções & Alertas de Auditoria")

    c_alerta1, c_alerta2 = st.columns(2)

    with c_alerta1:
      st.markdown("##### ⚠️ Lançamentos com Valores Atípicos (Outliers)")
      if not df_filtrado.empty and df_filtrado["Valor"].std() > 0:
        media_val = df_filtrado["Valor"].mean()
        desvio_val = df_filtrado["Valor"].std()
        limite_outlier = media_val + (2 * desvio_val)
        outliers = df_filtrado[df_filtrado["Valor"] > limite_outlier]

        if not outliers.empty:
          st.warning(
              f"Encontrados {len(outliers)} lançamentos acima de 2 desvios"
              " padrão da média."
          )
          st.dataframe(
              outliers[["Data", "Descrição", "Categoria", "Valor"]],
              use_container_width=True,
          )
        else:
          st.success(
              "Nenhum valor discrepante detectado para o filtro atual."
          )
      else:
        st.info("Dados insuficientes para cálculo de desvio padrão.")

    with c_alerta2:
      st.markdown("##### ⏳ Pendências e Status Críticos")
      if "Status" in df_filtrado.columns:
        pendentes = df_filtrado[
            df_filtrado["Status"].str.lower().str.contains(
                "pendente|aberto", na=False
            )
        ]
        if not pendentes.empty:
          st.error(
              f"Atenção: Há {len(pendentes)} registros com status pendente no"
              " período."
          )
          st.dataframe(
              pendentes[["Data", "Descrição", "Status", "Valor"]],
              use_container_width=True,
          )
        else:
          st.success("Todos os lançamentos do período estão efetivados.")
      else:
        st.info("Coluna 'Status' não encontrada na base.")

    st.markdown("---")

    # --- ANÁLISE GRÁFICA DE CONFORMIDADE ---
    st.subheader("📊 Distribuição Analítica para Conferência")
    g_col1, g_col2 = st.columns(2)

    with g_col1:
      if not df_filtrado.empty:
        fig_cat = px.pie(
            df_filtrado,
            names="Categoria",
            values="Valor",
            title="Volume Financeiro por Categoria",
            hole=0.4,
        )
        st.plotly_chart(fig_cat, use_container_width=True)

    with g_col2:
      if not df_filtrado.empty and "Conta" in df_filtrado.columns:
        fig_conta = px.bar(
            df_filtrado.groupby("Conta")["Valor"]
            .sum()
            .reset_index(),
            x="Conta",
            y="Valor",
            title="Movimentação por Conta",
            text_auto=".2f",
            color="Conta",
        )
        st.plotly_chart(fig_conta, use_container_width=True)

    # --- TABELA DETALHADA DE AUDITORIA ---
    st.subheader("📋 Base Consolidada Filtrada")
    st.dataframe(df_filtrado, use_container_width=True)

# Demais abas do sistema continuam estruturadas abaixo no seu projeto original...


# ==================== ABA 2: ADVANCED KPIS 2 (STATISTICS + FINANCE) ====================
elif aba == "⚡ Advanced KPIs 2":
  st.title("⚡ Advanced KPIs 2: Statistics & Financial Synthesis — Fluxo 106")
  st.markdown(
      "Painel de nível executivo com **20 KPIs estatístico-financeiros"
      " inéditos**, filtros avançados independentes e visualizações gráficas"
      " dinâmicas."
  )

  df = st.session_state.lancamentos.copy()

  if df.empty:
    st.info(
        "📭 Nenhum lançamento cadastrado. Adicione transações na aba"
        " **Lançamentos** para popular o painel."
    )
  else:
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0.0)

    # Filtros Poderosos Deduzidos para a Aba 2
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔍 Filtros Poderosos (Advanced KPIs 2)")

    tipos_disp2 = df["Tipo"].dropna().unique().tolist()
    cats_disp2 = df["Categoria"].dropna().unique().tolist()
    contas_disp2 = df["Conta"].dropna().unique().tolist()
    cenarios_disp2 = (
        df["Cenario"].dropna().unique().tolist()
        if "Cenario" in df.columns
        else ["Efetivado"]
    )

    sel_t2 = st.sidebar.multiselect(
        "Tipo (KPIs 2)",
        options=tipos_disp2,
        default=tipos_disp2,
        key="f_tipo_2",
    )
    sel_c2 = st.sidebar.multiselect(
        "Categoria (KPIs 2)",
        options=cats_disp2,
        default=cats_disp2,
        key="f_cat_2",
    )
    sel_co2 = st.sidebar.multiselect(
        "Conta (KPIs 2)",
        options=contas_disp2,
        default=contas_disp2,
        key="f_conta_2",
    )
    sel_ce2 = st.sidebar.multiselect(
        "Cenário (KPIs 2)",
        options=cenarios_disp2,
        default=cenarios_disp2,
        key="f_cen_2",
    )

    df_f2 = df[
        df["Tipo"].isin(sel_t2)
        & df["Categoria"].isin(sel_c2)
        & df["Conta"].isin(sel_co2)
        & df["Cenario"].isin(sel_ce2)
    ]

    if df_f2.empty:
      st.warning("⚠️ Nenhum registro encontrado para os filtros aplicados.")
    else:
      vals = df_f2["Valor"]
      receitas = df_f2[df_f2["Tipo"].str.lower().str.contains("receita|entrada", na=False)]["Valor"].sum()
      despesas = abs(df_f2[df_f2["Tipo"].str.lower().str.contains("despesa|saída", na=False)]["Valor"].sum())
      if despesas == 0:
        despesas = abs(vals[vals < 0].sum())
      if receitas == 0:
        receitas = vals[vals > 0].sum()

      # ==================== CÁLCULO DOS 20 KPIS INÉDITOS ====================
      # 1. VaR Histórico (95%)
      var_hist = np.percentile(vals, 5) if len(vals) > 1 else vals.min()
      # 2. Expected Shortfall (CVaR)
      cvar = vals[vals <= var_hist].mean() if len(vals[vals <= var_hist]) > 0 else var_hist
      # 3. Índice de Cobertura de Despesas (ICD)
      icd = (receitas / despesas) if despesas > 0 else 0.0
      # 4. Burn Rate Volatility (Desvio padrão móvel / desvio padrão global)
      burn_vol = vals.std() / (abs(vals.mean()) + 1e-9)
      # 5. Índice de Concentração de Gasto de Cauda (Top 10% Share)
      top_10_val = np.percentile(vals.abs(), 90) if len(vals) > 1 else vals.abs().max()
      top10_share = (vals.abs()[vals.abs() >= top_10_val].sum() / (vals.abs().sum() + 1e-9)) * 100
      # 6. Fator de Resiliência de Caixa (Median / Mean ratio)
      resilience_factor = (vals.median() / (vals.mean() + 1e-9))
      # 7. Coeficiente de Risco de Impacto (Skewness * Desvio Padrão)
      risk_impact_coef = vals.skew() * vals.std() if len(vals) > 2 else 0.0
      # 8. Índice de Estabilidade de Frequência Temporal (Dias únicos transacionados vs total dias)
      if "Data" in df_f2.columns and not df_f2["Data"].isna().all():
        total_dias_intervalo = max(1, (df_f2["Data"].max() - df_f2["Data"].min()).days + 1)
        dias_com_transacao = df_f2["Data"].nunique()
        freq_stability = (dias_com_transacao / total_dias_intervalo) * 100
      else:
        freq_stability = 100.0
      # 9. Índice de Amplitude Relativa (IQR / Média)
      q75, q25 = np.percentile(vals, [75, 25]) if len(vals) > 1 else (vals.max(), vals.min())
      iqr = q75 - q25
      rel_iqr = (iqr / (abs(vals.mean()) + 1e-9)) * 100
      # 10. Taxa de Variação de Cauda Esquerda (Tail Ratio)
      p95_val = np.percentile(vals.abs(), 95) if len(vals) > 1 else vals.abs().max()
      p05_val = np.percentile(vals.abs(), 5) if len(vals) > 1 else vals.abs().min()
      tail_ratio = (p95_val / (p05_val + 1e-9))
      # 11. Índice de Dispersão Exponencial (Var / Mean)
      disp_exp = (vals.var() / (abs(vals.mean()) + 1e-9)) if vals.mean() != 0 else 0.0
      # 12. Índice de Elasticidade de Categoria (Desvio padrão das categorias / Média global)
      cat_std = df_f2.groupby("Categoria")["Valor"].sum().std() if len(df_f2["Categoria"].unique()) > 1 else 0.0
      cat_elasticity = cat_std / (abs(vals.mean()) + 1e-9)
      # 13. Índice de Eficiência de Fluxo Líquido (Net Flow / Gross Total Volume)
      gross_vol = vals.abs().sum()
      net_flow_eff = (vals.sum() / (gross_vol + 1e-9)) * 100
      # 14. Índice de Inércia de Transação (Autocorrelação Lag-1 aproximada)
      if len(vals) > 2:
        val_shifted = vals.shift(1).fillna(vals.mean())
        autocorr = np.corrcoef(vals, val_shifted)[0, 1]
        if np.isnan(autocorr):
          autocorr = 0.0
      else:
        autocorr = 0.0
      # 15. Índice de Z-Score Máximo Absoluto (Outlier severity)
      if vals.std() > 0:
        max_z = np.max(np.abs((vals - vals.mean()) / vals.std()))
      else:
        max_z = 0.0
      # 16. Índice de Concentração de Contas (HHI de Contas)
      conta_shares = df_f2.groupby("Conta")["Valor"].sum().abs() / (vals.abs().sum() + 1e-9)
      conta_hhi = (conta_shares ** 2).sum() * 100
      # 17. Fator de Assimetria de Fluxo (Receitas vs Despesas proporção estatística)
      flow_skew_factor = (receitas / (despesas + 1e-9)) * (1 + abs(vals.skew()))
      # 18. Média Geométrica Ajustada de Valores Positivos
      pos_vals = vals[vals > 0]
      if len(pos_vals) > 0:
        geom_mean = np.exp(np.log(pos_vals).mean())
      else:
        geom_mean = 0.0
      # 19. Índice de Volatilidade Ponderada por Volume (VWCV)
      vwcv = (vals.std() * vals.abs().sum()) / (vals.mean() ** 2 + 1e-9) if vals.mean() != 0 else 0.0
      # 20. Índice de Estresse Sintético (Synthetic Stress Indicator)
      synth_stress = abs(var_hist) * (1 + burn_vol) / (icd + 0.1)

      # ==================== EXIBIÇÃO EM BLOCOS DE CARDS ====================
      st.markdown("### 🏆 Bloco 1: Gestão de Risco e Cauda Estatística")
      k1, k2, k3, k4, k5 = st.columns(5)
      k1.metric("1. VaR Histórico (95%)", f"R$ {var_hist:,.2f}", help="Pior cenário esperado em 95% dos lançamentos.")
      k2.metric("2. Expected Shortfall (CVaR)", f"R$ {cvar:,.2f}", help="Média dos impactos nos 5% piores cenários de cauda.")
      k3.metric("3. Índice Cobertura (ICD)", f"{icd:.2f}x", help="Razão entre receitas e despesas filtradas.")
      k4.metric("4. Volatilidade de Burn Rate", f"{burn_vol:.2f}", help="Relação entre desvio padrão e média absoluta.")
      k5.metric("5. Share Top 10% Cauda", f"{top10_share:.1f}%", help="Percentual do volume total concentrado nos 10% maiores valores.")

      st.markdown("### 📊 Bloco 2: Estrutura, Resiliência e Dinâmica de Fluxo")
      k6, k7, k8, k9, k10 = st.columns(5)
      k6.metric("6. Fator de Resiliência", f"{resilience_factor:.2f}", help="Proporção entre Mediana e Média dos lançamentos.")
      k7.metric("7. Coeficiente Risco-Impacto", f"{risk_impact_coef:,.2f}", help="Cruzamento entre assimetria e volatilidade.")
      k8.metric("8. Estabilidade de Frequência", f"{freq_stability:.1f}%", help="Percentual de dias com movimentação no intervalo.")
      k9.metric("9. Amplitude Relativa (IQR)", f"{rel_iqr:.1f}%", help="Dispersão interquartil normalizada pela média.")
      k10.metric("10. Razão de Cauda (Tail Ratio)", f"{tail_ratio:.2f}", help="Relação entre o percentil 95 e o percentil 5 absoluto.")

      st.markdown("### ⚙️ Bloco 3: Dispersão, Inércia e Concentração Sistêmica")
      k11, k12, k13, k14, k15 = st.columns(5)
      k11.metric("11. Dispersão Exponencial", f"{disp_exp:,.2f}", help="Variância dividida pela média absoluta.")
      k12.metric("12. Elasticidade por Categoria", f"{cat_elasticity:.2f}", help="Volatilidade entre as diferentes categorias de fluxo.")
      k13.metric("13. Eficiência de Fluxo Líquido", f"{net_flow_eff:.1f}%", help="Saldo líquido dividido pelo volume bruto movimentado.")
      k14.metric("14. Inércia de Transação (Lag-1)", f"{autocorr:.2f}", help="Grau de correlação sequencial entre lançamentos.")
      k15.metric("15. Z-Score Máximo (Outlier)", f"{max_z:.2f}", help="Severidade do maior ponto fora da curva estatística.")

      st.markdown("### 💎 Bloco 4: Concentração, Geometria e Estresse de Caixa")
      k16, k17, k18, k19, k20 = st.columns(5)
      k16.metric("16. Concentração de Contas (HHI)", f"{conta_hhi:.1f}%", help="Índice Herfindahl-Hirschman de concentração por conta.")
      k17.metric("17. Fator de Assimetria de Fluxo", f"{flow_skew_factor:.2f}", help="Proporção de receitas/despesas ponderada pela assimetria.")
      k18.metric("18. Média Geométrica Positiva", f"R$ {geom_mean:,.2f}", help="Média geométrica dos valores estritamente positivos.")
      k19.metric("19. Volatilidade Ponderada (VWCV)", f"{vwcv:,.2f}", help="Volatilidade ajustada pelo volume financeiro total.")
      k20.metric("20. Indicador de Estresse Sintético", f"{synth_stress:,.2f}", help="Métrica combinada de risco de cauda e cobertura.")

      # ==================== GRÁFICOS DINÂMICOS DA ABA 2 ====================
      st.markdown("---")
      st.subheader("📈 Análises Gráficas Avançadas — Advanced KPIs 2")
      
      gc1, gc2 = st.columns(2)

      with gc1:
        st.markdown("**Evolução Temporal do VaR e Valores Registrados**")
        if "Data" in df_f2.columns and not df_f2["Data"].isna().all():
          df_time_agg = df_f2.groupby(df_f2["Data"].dt.date)["Valor"].sum().reset_index()
          fig_line = px.line(
              df_time_agg,
              x="Data",
              y="Valor",
              title="Série Temporal Diária de Fluxo Líquido",
              markers=True,
              color_discrete_sequence=["#1f77b4"],
          )
          st.plotly_chart(fig_line, use_container_width=True)
        else:
          st.info("Necessário dados de data válidos para gerar o gráfico temporal.")

      with gc2:
        st.markdown("**Concentração de Volume por Conta (HHI Breakdown)**")
        conta_group = df_f2.groupby("Conta")["Valor"].sum().reset_index()
        fig_bar = px.bar(
            conta_group,
            x="Conta",
            y="Valor",
            title="Volume Consolidado por Conta Bancária",
            color="Conta",
            text_auto=True,
        )
        st.plotly_chart(fig_bar, use_container_width=True)


# ==================== RESTANTE DAS ABAS ORIGINAIS DO SEU APP ====================
elif aba == "Sophisticated Graphics":
  st.title("Sophisticated Graphics")
  st.info("Abra o menu lateral para navegar ou adicionar gráficos sofisticados.")

elif aba == "Graphics":
  st.title("Graphics")
  st.info("Painel gráfico padrão.")

elif aba == "KPIs":
  st.title("KPIs")
  st.info("Painel de KPIs tradicionais.")

elif aba == "Dashboard":
  st.title("Dashboard")
  st.info("Dashboard executivo geral.")

elif aba == "Statistics":
  st.title("Statistics")
  st.info("Estatísticas básicas do sistema.")

elif aba == "Statistic2":
  st.title("Statistic2")
  st.info("Estatísticas complementares.")

elif aba == "Financial Analysis":
  st.title("Financial Analysis")
  st.info("Análise financeira detalhada.")

elif aba == "🤖 IA & Assistant":
  st.title("🤖 IA & Assistant")
  st.info("Assistente inteligente.")

elif aba == "Lançamentos":
  st.title("Lançamentos")
  st.markdown("Gerencie seus lançamentos financeiros aqui.")
  
  # Formulário rápido para testes e população do app
  with st.form("form_lanc"):
    col_a, col_b, col_c = st.columns(3)
    t_tipo = col_a.selectbox("Tipo", ["Receita", "Despesa"])
    t_conta = col_b.selectbox("Conta", st.session_state.contas)
    t_cat = col_c.selectbox("Categoria", st.session_state.categorias)
    
    col_d, col_e, col_f = st.columns(3)
    t_desc = col_d.text_input("Descrição", "Ex: Supermercado")
    t_val = col_e.number_input("Valor", value=150.0, format="%.2f")
    t_data = col_f.date_input("Data")
    
    submitted = st.form_submit_button("Adicionar Lançamento")
    if submitted:
      novo_reg = pd.DataFrame([{
          "Tipo": t_tipo,
          "Conta": t_conta,
          "Conta Destino": "",
          "Categoria": t_cat,
          "Descrição": t_desc,
          "Valor": t_val if t_tipo == "Receita" else -abs(t_val),
          "Data": pd.to_datetime(t_data),
          "Parcelas": "1/1",
          "Modo Valor": "À vista",
          "Status": "Efetivado",
          "Cenario": "Efetivado"
      }])
      st.session_state.lancamentos = pd.concat([st.session_state.lancamentos, novo_reg], ignore_index=True)
      st.success("Lançamento adicionado com sucesso! Navegue para as abas de KPIs para visualizar.")

  if not st.session_state.lancamentos.empty:
    st.dataframe(st.session_state.lancamentos, use_container_width=True)

elif aba == "Cadastro":
  st.title("Cadastro")

elif aba == "Cadastro de Categorias e Contas":
  st.title("Cadastro de Categorias e Contas")

elif aba == "Cartões de Crédito":
  st.title("Cartões de Crédito")

elif aba == "Backup & Segurança":
  st.title("Backup & Segurança")


# ==================== ABA 1: ADVANCED ANALYTICS & STATISTICAL KPIS ====================
if aba == "🚀 Advanced Analytics & KPIs":
  st.title("🚀 Advanced Analytics & Statistical KPIs — Fluxo 106")
  st.markdown(
      "Painel executivo de inteligência analítica com filtros dinâmicos,"
      " estatística robusta, dispersão de cauda, entropia informacional e"
      " índices de rastreamento."
  )

  df = st.session_state.lancamentos.copy()

  if df.empty:
    st.info(
        "📭 Nenhum lançamento cadastrado ainda. Adicione transações na aba"
        " **Lançamentos** para popular o painel estatístico avançado."
    )
  else:
    # Tratamento inicial de tipos de dados
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0.0)

    # ==================== FILTROS PODEROSOS ====================
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔍 Filtros Poderosos (Fluxo 106)")

    tipos_disp = df["Tipo"].dropna().unique().tolist()
    cats_disp = df["Categoria"].dropna().unique().tolist()
    contas_disp = df["Conta"].dropna().unique().tolist()
    cenarios_disp = (
        df["Cenario"].dropna().unique().tolist()
        if "Cenario" in df.columns
        else ["Efetivado"]
    )

    sel_tipos = st.sidebar.multiselect(
        "Filtrar por Tipo", options=tipos_disp, default=tipos_disp
    )
    sel_cats = st.sidebar.multiselect(
        "Filtrar por Categoria", options=cats_disp, default=cats_disp
    )
    sel_contas = st.sidebar.multiselect(
        "Filtrar por Conta", options=contas_disp, default=contas_disp
    )
    sel_cenarios = st.sidebar.multiselect(
        "Filtrar por Cenário", options=cenarios_disp, default=cenarios_disp
    )

    # Filtragem Principal
    df_filtrado = df[
        df["Tipo"].isin(sel_tipos)
        & df["Categoria"].isin(sel_cats)
        & df["Conta"].isin(sel_contas)
        & df["Cenario"].isin(sel_cenarios)
    ]

    if df_filtrado.empty:
      st.warning("⚠️ Nenhum registro encontrado com os filtros selecionados.")
    else:
      valores = df_filtrado["Valor"]

      # ==================== CÁLCULOS ESTATÍSTICOS AVANÇADOS ====================
      n_obs = len(valores)
      media = valores.mean()
      mediana = valores.median()
      desvio_padrao = valores.std()
      cv = (
          (desvio_padrao / media) * 100
          if media != 0 and not np.isnan(media)
          else 0.0
      )

      # Desvio Absoluto Mediano (MAD) - Robusto contra Outliers
      mad = np.median(np.abs(valores - mediana))
      # Escore Z Robusto
      robust_z = (
          (0.6745 * (valores - mediana) / mad)
          if mad != 0
          else np.zeros_like(valores)
      )

      # Percentis de Cauda
      p90 = np.percentile(valores, 90) if n_obs > 1 else valores.max()
      p95 = np.percentile(valores, 95) if n_obs > 1 else valores.max()
      p99 = np.percentile(valores, 99) if n_obs > 1 else valores.max()

      # Assimetria e Curtose
      skewness = valores.skew() if n_obs > 2 else 0.0
      kurtosis = valores.kurtosis() if n_obs > 2 else 0.0

      # Entropia de Shannon (Distribuição de Categorias)
      cat_counts = df_filtrado["Categoria"].value_counts(normalize=True)
      shannon_entropy = -(cat_counts * np.log2(cat_counts + 1e-9)).sum()

      # Coeficiente de Gini (Concentração de Valores)
      sorted_vals = np.sort(valores.abs())
      if n_obs > 0 and sorted_vals.sum() > 0:
        index = np.arange(1, n_obs + 1)
        gini = (
            (2 * np.sum(index * sorted_vals)) / (n_obs * sorted_vals.sum())
            - (n_obs + 1) / n_obs
        )
      else:
        gini = 0.0

      # ==================== EXIBIÇÃO DE METRICS (CARDS) ====================
      st.markdown("### 📊 Indicadores de Estatística Robusta e Dispersão")
      col1, col2, col3, col4 = st.columns(4)
      col1.metric(
          "Coeficiente de Variação (CV)",
          f"{cv:.2f}%",
          help="Volatilidade relativa (Desvio Padrão / Média).",
      )
      col2.metric(
          "Desvio Absoluto Mediano (MAD)",
          f"R$ {mad:,.2f}",
          help="Dispersão imune a valores extremos (outliers).",
      )
      col3.metric(
          "Percentil P95 (Cauda)",
          f"R$ {p95:,.2f}",
          help="Valor limite que engloba 95% do volume transacionado.",
      )
      col4.metric(
          "Entropia de Shannon",
          f"{shannon_entropy:.2f} bits",
          help=(
              "Mede a diversidade e imprevisibilidade das categorias de fluxo."
          ),
      )

      col5, col6, col7, col8 = st.columns(4)
      col5.metric(
          "Assimetria (Skewness)",
          f"{skewness:.2f}",
          help="Indica o viés de distribuição (caudas longas à direita/esquerda).",
      )
      col6.metric(
          "Curtose",
          f"{kurtosis:.2f}",
          help="Mede a propensão do sistema a choques ou surpresas extremas.",
      )
      col7.metric(
          "Índice Gini",
          f"{gini:.2f}",
          help="Concentração de volume entre os lançamentos (0 a 1).",
      )
      col8.metric(
          "Total Filtrado",
          f"R$ {valores.sum():,.2f}",
          help="Soma líquida/total dos registros filtrados.",
      )

      # ==================== GRÁFICOS ANALÍTICOS ====================
      st.markdown("---")
      c_gr1, c_gr2 = st.columns(2)

      with c_gr1:
        st.subheader("📈 Distribuição de Frequência (Histograma)")
        fig_hist = px.histogram(
            df_filtrado,
            x="Valor",
            nbins=20,
            title="Densidade de Valores por Lançamento",
            color_discrete_sequence=["#2ca02c"],
        )
        st.plotly_chart(fig_hist, use_container_width=True)

      with c_gr2:
        st.subheader("🎯 Concentração por Categoria (Gini / Share)")
        cat_group = (
            df_filtrado.groupby("Categoria")["Valor"].sum().reset_index()
        )
        fig_pie = px.pie(
            cat_group,
            names="Categoria",
            values="Valor",
            title="Participação Percentual por Categoria",
            hole=0.4,
        )
        st.plotly_chart(fig_pie, use_container_width=True)


# ==================== ABA: STATISTIC2 ====================
if aba == "Statistic2":
  st.title("📊 Statistic 2: Indicadores Econométricos & Quantitativos")
  st.write(
      "Painel avançado de métricas estatísticas, econométricas e gráficos"
      " interativos com filtros multidimensionais."
  )

  df_full = st.session_state.lancamentos.copy()

  if df_full.empty:
    st.info(
        "Nenhum lançamento cadastrado ainda. Cadastre transações na aba"
        " 'Lançamentos' para habilitar as análises estatísticas e gráficos."
    )
  else:
    # Garantir conversões básicas
    df_full["Valor"] = pd.to_numeric(df_full["Valor"], errors="coerce").fillna(0)
    df_full["Data"] = pd.to_datetime(df_full["Data"], errors="coerce")

    # Garante colunas de status e cenário caso venham vazias/faltantes
    if "Status" not in df_full.columns:
      df_full["Status"] = "Efetivado"
    if "Cenario" not in df_full.columns:
      df_full["Cenario"] = "Efetivado"

    # ==================== FILTROS PODEROSOS MULTIDIMENSIONAIS ====================
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎛️ Filtros Poderosos (Statistic2)")

    # 1. Presets Temporais Rápidos
    preset_temporal = st.sidebar.selectbox(
        "Preset Temporal",
        ["Todo o histórico", "Últimos 30 dias", "Últimos 90 dias", "Ano corrente", "Personalizado"],
    )

    hoje = pd.Timestamp.today().normalize()
    if preset_temporal == "Últimos 30 dias":
      data_inicio = hoje - pd.Timedelta(days=30)
      data_fim = hoje
    elif preset_temporal == "Últimos 90 dias":
      data_inicio = hoje - pd.Timedelta(days=90)
      data_fim = hoje
    elif preset_temporal == "Ano corrente":
      data_inicio = pd.Timestamp(f"{hoje.year}-01-01")
      data_fim = pd.Timestamp(f"{hoje.year}-12-31")
    elif preset_temporal == "Personalizado":
      min_date = df_full["Data"].min() if not df_full["Data"].isna().all() else hoje.date()
      max_date = df_full["Data"].max() if not df_full["Data"].isna().all() else hoje.date()
      if pd.isna(min_date):
        min_date = hoje.date()
      if pd.isna(max_date):
        max_date = hoje.date()
      
      intervalo_datas = st.sidebar.date_input(
          "Período",
          value=(pd.to_datetime(min_date).date(), pd.to_datetime(max_date).date())
      )
      if isinstance(intervalo_datas, tuple) and len(intervalo_datas) == 2:
        data_inicio, data_fim = pd.to_datetime(intervalo_datas[0]), pd.to_datetime(intervalo_datas[1])
      else:
        data_inicio, data_fim = pd.to_datetime(min_date), pd.to_datetime(max_date)
    else:  # Todo o histórico
      data_inicio = pd.Timestamp("1900-01-01")
      data_fim = pd.Timestamp("2100-12-31")

    # 2. Multi-seleção: Cenários, Status, Tipos, Contas, Categorias
    cenarios_disp = df_full["Cenario"].dropna().unique().tolist()
    cenario_sel = st.sidebar.multiselect("Cenários", options=cenarios_disp, default=cenarios_disp)

    status_disp = df_full["Status"].dropna().unique().tolist()
    status_sel = st.sidebar.multiselect("Status", options=status_disp, default=status_disp)

    tipos_disp = df_full["Tipo"].dropna().unique().tolist()
    tipo_sel = st.sidebar.multiselect("Tipos", options=tipos_disp, default=tipos_disp)

    contas_disp = df_full["Conta"].dropna().unique().tolist()
    conta_sel = st.sidebar.multiselect("Contas / Cartões", options=contas_disp, default=contas_disp)

    categorias_disp = df_full["Categoria"].dropna().unique().tolist()
    categoria_sel = st.sidebar.multiselect("Categorias", options=categorias_disp, default=categorias_disp)

    # 3. Filtro de Calendário (Todos os dias, Dias Úteis ou Fins de Semana)
    filtro_dia_util = st.sidebar.selectbox(
        "Filtro de Calendário",
        ["Todos os dias", "Dias Úteis (Seg-Sex)", "Fins de Semana (Sáb-Dom)"]
    )

    # Aplicando os filtros no DataFrame
    df_f = df_full.copy()
    if not df_f["Data"].isna().all():
      df_f = df_f[(df_f["Data"] >= data_inicio) & (df_f["Data"] <= data_fim)]
    
    if cenario_sel:
      df_f = df_f[df_f["Cenario"].isin(cenario_sel)]
    if status_sel:
      df_f = df_f[df_f["Status"].isin(status_sel)]
    if tipo_sel:
      df_f = df_f[df_f["Tipo"].isin(tipo_sel)]
    if conta_sel:
      df_f = df_f[df_f["Conta"].isin(conta_sel)]
    if categoria_sel:
      df_f = df_f[df_f["Categoria"].isin(categoria_sel)]

    if filtro_dia_util == "Dias Úteis (Seg-Sex)":
      df_f = df_f[df_f["Data"].dt.dayofweek < 5]
    elif filtro_dia_util == "Fins de Semana (Sáb-Dom)":
      df_f = df_f[df_f["Data"].dt.dayofweek >= 5]

    if df_f.empty:
      st.warning("Nenhum dado encontrado com os filtros selecionados.")
    else:
      despesas_arr = df_f[df_f["Tipo"] == "Despesa"]["Valor"].values
      total_despesas = despesas_arr[despesas_arr > 0] if len(despesas_arr) > 0 else np.array([0])

      st.markdown("### 📈 16 Indicadores Econométricos & Quantitativos")
      col1, col2, col3, col4 = st.columns(4)

      with col1:
        geo_mean = np.exp(np.mean(np.log(total_despesas))) if len(total_despesas) > 0 and np.all(total_despesas > 0) else 0.0
        st.metric("1. Média Geométrica", f"R$ {geo_mean:,.2f}")

        harm_mean = len(total_despesas) / np.sum(1.0 / total_despesas) if len(total_despesas) > 0 and np.all(total_despesas > 0) else 0.0
        st.metric("2. Média Harmônica", f"R$ {harm_mean:,.2f}")

        if len(total_despesas) > 5:
          trimmed = np.sort(total_despesas)
          trim_cut = int(0.1 * len(trimmed))
          trimmed_mean = np.mean(trimmed[trim_cut:-trim_cut] if trim_cut > 0 else trimmed)
        else:
          trimmed_mean = np.mean(total_despesas) if len(total_despesas) > 0 else 0.0
        st.metric("3. Média Aparada (10%)", f"R$ {trimmed_mean:,.2f}")

        iqr_val = np.percentile(total_despesas, 75) - np.percentile(total_despesas, 25) if len(total_despesas) > 0 else 0.0
        st.metric("4. Dispersão IQR", f"R$ {iqr_val:,.2f}")

      with col2:
        mean_val = np.mean(total_despesas) if len(total_despesas) > 0 else 0
        negative_diffs = total_despesas[total_despesas < mean_val] - mean_val
        semi_std = np.sqrt(np.mean(negative_diffs**2)) if len(negative_diffs) > 0 else 0.0
        st.metric("5. Semi-Desvio Padrão", f"R$ {semi_std:,.2f}")

        std_val = np.std(total_despesas) if len(total_despesas) > 0 else 0
        cv_val = (std_val / mean_val * 100) if mean_val > 0 else 0.0
        st.metric("6. Coeficiente de Variação", f"{cv_val:.2f}%")

        sharpe = (mean_val / std_val) if std_val > 0 else 0.0
        st.metric("7. Índice Sharpe Pessoal", f"{sharpe:.2f}")

        sortino = (mean_val / semi_std) if semi_std > 0 else 0.0
        st.metric("8. Índice Sortino", f"{sortino:.2f}")

      with col3:
        var_95 = np.percentile(total_despesas, 95) if len(total_despesas) > 0 else 0.0
        st.metric("9. Value at Risk (VaR 95%)", f"R$ {var_95:,.2f}")

        cvar_95 = np.mean(total_despesas[total_despesas >= var_95]) if len(total_despesas[total_despesas >= var_95]) > 0 else var_95
        st.metric("10. CVaR / Expected Shortfall", f"R$ {cvar_95:,.2f}")

        if len(total_despesas) > 0 and np.sum(total_despesas) > 0:
          sorted_exp = np.sort(total_despesas)
          n = len(sorted_exp)
          gini = (2 * np.sum((np.arange(1, n + 1)) * sorted_exp) / (n * np.sum(sorted_exp))) - ((n + 1) / n)
        else:
          gini = 0.0
        st.metric("11. Coeficiente de Gini", f"{gini:.4f}")

        if len(total_despesas) > 0 and np.sum(total_despesas) > 0:
          proportions = total_despesas / np.sum(total_despesas)
          shannon = -np.sum(proportions * np.log2(proportions + 1e-12))
        else:
          shannon = 0.0
        st.metric("12. Entropia de Shannon", f"{shannon:.4f} bits")

      with col4:
        z_score = (mean_val / (std_val + 1e-12)) if std_val > 0 else 0.0
        st.metric("13. Z-Score de Solvência", f"{z_score:.2f}")

        receitas = df_f[df_f["Tipo"] == "Receita"]["Valor"].sum()
        despesas_tot = df_f[df_f["Tipo"] == "Despesa"]["Valor"].sum()
        saving_rate = ((receitas - despesas_tot) / receitas * 100) if receitas > 0 else 0.0
        st.metric("14. Taxa de Poupança Efetiva", f"{saving_rate:.2f}%")

        net_margin = ((receitas - despesas_tot) / receitas) if receitas > 0 else 0.0
        st.metric("15. Margem Operacional", f"{net_margin:.2%}")

        cash_coverage = (receitas / (despesas_tot + 1e-12)) if despesas_tot > 0 else 0.0
        st.metric("16. Cobertura de Caixa", f"{cash_coverage:.2f}x")

      # ==================== PAINEL DE GRÁFICOS INTERATIVOS AVANÇADOS ====================
      st.markdown("---")
      st.markdown("### 📊 Painel de Gráficos Interativos Avançados")

      df_sorted = df_f.sort_values("Data") if "Data" in df_f.columns else df_f

      # 1. Bandas de Bollinger & Tendência OLS (Despesas)
      st.subheader("1. Bandas de Bollinger & Tendência OLS (Despesas)")
      df_esp = df_sorted[df_sorted["Tipo"] == "Despesa"].groupby("Data")["Valor"].sum().reset_index()
      if not df_esp.empty and len(df_esp) > 1:
        df_esp["MA20"] = df_esp["Valor"].rolling(window=min(20, len(df_esp)), min_periods=1).mean()
        df_esp["STD20"] = df_esp["Valor"].rolling(window=min(20, len(df_esp)), min_periods=1).std().fillna(0)
        df_esp["Bands_High"] = df_esp["MA20"] + (2 * df_esp["STD20"])
        df_esp["Bands_Low"] = df_esp["MA20"] - (2 * df_esp["STD20"])
        
        # OLS Trendline simples
        x_vals = np.arange(len(df_esp))
        y_vals = df_esp["Valor"].values
        if len(x_vals) > 1:
          slope, intercept = np.polyfit(x_vals, y_vals, 1)
          df_esp["OLS_Trend"] = intercept + slope * x_vals
        else:
          df_esp["OLS_Trend"] = y_vals

        fig_boll = go.Figure()
        fig_boll.add_trace(go.Scatter(x=df_esp["Data"], y=df_esp["Bands_High"], name="Banda Superior (+2σ)", line=dict(color="rgba(173,204,255,0.5)", dash="dash")))
        fig_boll.add_trace(go.Scatter(x=df_esp["Data"], y=df_esp["MA20"], name="Média Móvel (MA)", line=dict(color="blue")))
        fig_boll.add_trace(go.Scatter(x=df_esp["Data"], y=df_esp["Bands_Low"], name="Banda Inferior (-2σ)", line=dict(color="rgba(173,204,255,0.5)", dash="dash"), fill="tonexty"))
        fig_boll.add_trace(go.Scatter(x=df_esp["Data"], y=df_esp["Valor"], name="Despesas Diárias", mode="markers+lines", marker=dict(color="red")))
        fig_boll.add_trace(go.Scatter(x=df_esp["Data"], y=df_esp["OLS_Trend"], name="Tendência OLS", line=dict(color="green", dash="dot")))
        fig_boll.update_layout(title="Bandas de Bollinger & Regressão Linear OLS", xaxis_title="Data", yaxis_title="Valor (R$)")
        st.plotly_chart(fig_boll, use_container_width=True)
      else:
        st.info("Dados insuficientes para gerar as Bandas de Bollinger.")

      # 2. Histograma Empírico vs Normal Teórica
      st.subheader("2. Histograma Empírico vs Normal Teórica")
      if len(total_despesas) > 1:
        mu, std_n = norm.fit(total_despesas)
        fig_hist = go.Figure()
        fig_hist.add_trace(go.Histogram(x=total_despesas, histnorm="probability density", name="Empírico", marker_color="royalblue"))
        
        xmin, xmax = min(total_despesas), max(total_despesas)
        x_axis = np.linspace(xmin, xmax, 100)
        p = norm.pdf(x_axis, mu, std_n)
        fig_hist.add_trace(go.Scatter(x=x_axis, y=p, mode="lines", name="Normal Teórica", line=dict(color="crimson", width=3)))
        fig_hist.update_layout(title="Aderência Gaussiana das Despesas", xaxis_title="Valor", yaxis_title="Densidade")
        st.plotly_chart(fig_hist, use_container_width=True)
      else:
        st.info("Dados insuficientes para o histograma.")

      # 3. Curva de Lorenz & Pareto
      st.subheader("3. Curva de Lorenz & Pareto")
      df_cat = df_f[df_f["Tipo"] == "Despesa"].groupby("Categoria")["Valor"].sum().reset_index()
      if not df_cat.empty and df_cat["Valor"].sum() > 0:
        df_cat = df_cat.sort_values(by="Valor", ascending=False).reset_index(drop=True)
        df_cat["Pct"] = df_cat["Valor"] / df_cat["Valor"].sum()
        df_cat["CumPct"] = df_cat["Pct"].cumsum()
        df_cat["PopPct"] = (np.arange(len(df_cat)) + 1) / len(df_cat)

        fig_lorenz = go.Figure()
        fig_lorenz.add_trace(go.Scatter(x=df_cat["PopPct"], y=df_cat["CumPct"], mode="lines+markers", name="Curva de Lorenz", line=dict(color="purple", width=3)))
        fig_lorenz.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", name="Linha de Igualdade", line=dict(color="gray", dash="dash")))
        fig_lorenz.update_layout(title="Concentração de Gastos (Curva de Lorenz)", xaxis_title="Kumulativo de Categorias", yaxis_title="Kumulativo de Gastos")
        st.plotly_chart(fig_lorenz, use_container_width=True)
      else:
        st.info("Sem dados de despesa por categoria para a Curva de Lorenz.")

      # 4. Curva de Drawdown Histórico
      st.subheader("4. Curva de Drawdown Histórico")
      df_fluxo = df_sorted.copy()
      if not df_fluxo.empty:
        df_fluxo["FluxoDiario"] = df_fluxo.apply(lambda r: r["Valor"] if r["Tipo"] == "Receita" else -r["Valor"], axis=1)
        df_fluxo = df_fluxo.groupby("Data")["FluxoDiario"].sum().reset_index()
        df_fluxo["Acumulado"] = df_fluxo["FluxoDiario"].cumsum()
        df_fluxo["Pico"] = df_fluxo["Acumulado"].cummax()
        df_fluxo["Drawdown"] = df_fluxo["Acumulado"] - df_fluxo["Pico"]

        fig_dd = px.area(df_fluxo, x="Data", y="Drawdown", title="Drawdown Histórico do Capital Acumulado")
        fig_dd.update_traces(line_color="red", fillcolor="rgba(255,0,0,0.2)")
        st.plotly_chart(fig_dd, use_container_width=True)
      else:
        st.info("Sem dados para calcular o Drawdown.")

      # 5. Análise ABC de Pareto (Barras + Curva Acumulada)
      st.subheader("5. Análise ABC de Pareto por Categoria")
      if not df_cat.empty and df_cat["Valor"].sum() > 0:
        fig_pareto = go.Figure()
        fig_pareto.add_trace(go.Bar(x=df_cat["Categoria"], y=df_cat["Valor"], name="Valor por Categoria", marker_color="teal"))
        fig_pareto.add_trace(go.Scatter(x=df_cat["Categoria"], y=df_cat["CumPct"] * 100, name="% Acumulado", yaxis="y2", mode="lines+markers", line=dict(color="orange", width=2)))
        fig_pareto.update_layout(
            title="Matriz ABC de Pareto",
            xaxis_title="Categoria",
            yaxis=dict(title="Valor Total (R$)"),
            yaxis2=dict(title="% Acumulado", overlaying="y", side="right", range=[0, 105])
        )
        st.plotly_chart(fig_pareto, use_container_width=True)
      else:
        st.info("Sem dados para o gráfico de Pareto.")

      # 6. Dispersão de Transações & Detecção de Outliers
      st.subheader("6. Dispersão de Transações & Detecção de Outliers")
      if not df_f.empty:
        fig_disp = px.scatter(df_f, x="Data", y="Valor", color="Tipo", symbol="Categoria", hover_data=["Descrição", "Conta"], title="Dispersão Temporal de Transações")
        st.plotly_chart(fig_disp, use_container_width=True)

      # 7. Fluxo Periódico vs Patrimônio Acumulado
      st.subheader("7. Fluxo Periódico vs Patrimônio Acumulado")
      if not df_fluxo.empty:
        fig_pat = go.Figure()
        fig_pat.add_trace(go.Bar(x=df_fluxo["Data"], y=df_fluxo["FluxoDiario"], name="Fluxo Periódico", marker_color="lightblue"))
        fig_pat.add_trace(go.Scatter(x=df_fluxo["Data"], y=df_fluxo["Acumulado"], name="Patrimônio Acumulado", yaxis="y2", line=dict(color="darkblue", width=3)))
        fig_pat.update_layout(
            title="Evolução do Saldo Líquido e Curva Patrimonial",
            xaxis_title="Data",
            yaxis=dict(title="Fluxo Periódico (R$)"),
            yaxis2=dict(title="Patrimônio Acumulado (R$)", overlaying="y", side="right")
        )
        st.plotly_chart(fig_pat, use_container_width=True)

      # 8. Absorção de Liquidez (Entradas vs Saídas)
      st.subheader("8. Absorção de Liquidez (Entradas vs Saídas)")
      df_liq = df_sorted.groupby(["Data", "Tipo"])["Valor"].sum().unstack(fill_value=0).reset_index()
      if "Receita" in df_liq.columns and "Despesa" in df_liq.columns:
        fig_liq = go.Figure()
        fig_liq.add_trace(go.Bar(x=df_liq["Data"], y=df_liq["Receita"], name="Entradas", marker_color="green"))
        fig_liq.add_trace(go.Bar(x=df_liq["Data"], y=-df_liq["Despesa"], name="Saídas", marker_color="crimson"))
        fig_liq.update_layout(barmode="relative", title="Absorção de Liquidez Diária (Entradas vs Saídas)", xaxis_title="Data", yaxis_title="Volume (R$)")
        st.plotly_chart(fig_liq, use_container_width=True)
      else:
        st.info("Dados insuficientes para a absorção de liquidez.")



# ==================== FUNÇÕES AUXILIARES: BUDGET AUTOMÁTICO DE CARTÃO ====================
PREFIXO_AUTO = "[AUTO] Fatura "
CATEGORIA_FATURA = "Fatura Cartão"


def garantir_colunas(df):
  """Garante que Status e Cenario existam e estejam preenchidos."""
  if "Status" not in df.columns:
    df["Status"] = "Efetivado"
  df["Status"] = df["Status"].fillna("Efetivado")
  if "Cenario" not in df.columns:
    df["Cenario"] = df["Status"].apply(
        lambda s: "Budget" if s == "Orçado" else "Efetivado"
    )
  df["Cenario"] = df["Cenario"].fillna("Efetivado")
  return df


def _data_segura(ano, mes, dia):
  ultimo = calendar.monthrange(ano, mes)[1]
  return pd.Timestamp(year=ano, month=mes, day=min(dia, ultimo))


def vencimento_da_fatura(data_compra, fechamento, vencimento):
  """Compra até o dia do fechamento entra na fatura do mês; depois, na seguinte.
  Se o vencimento <= fechamento, ele cai no mês seguinte ao fechamento."""
  d = pd.to_datetime(data_compra)
  ref = pd.Timestamp(d.year, d.month, 1)
  if d.day > fechamento:
    ref += pd.DateOffset(months=1)
  if vencimento <= fechamento:
    ref += pd.DateOffset(months=1)
  return _data_segura(ref.year, ref.month, int(vencimento)).date()


def sincronizar_budget_cartao(nome_cartao=None):
  """Recria os budgets automáticos (Orçado) das faturas a partir das compras Efetivadas."""
  df = st.session_state.lancamentos.copy()
  if df.empty:
    return
  df = garantir_colunas(df)

  if CATEGORIA_FATURA not in st.session_state.categorias:
    st.session_state.categorias.append(CATEGORIA_FATURA)

  cartoes = [
      c
      for c in st.session_state.cartoes
      if nome_cartao is None or c["Nome"] == nome_cartao
  ]
  novos = []
  for c in cartoes:
    nome = c["Nome"]
    prefixo = f"{PREFIXO_AUTO}{nome} |"
    # remove budgets automáticos antigos desse cartão
    eh_auto = df["Descrição"].astype(str).str.startswith(prefixo)
    df = df[~eh_auto]

    gastos = df[
        (df["Conta"] == nome)
        & (df["Tipo"] == "Despesa")
        & (df["Status"] == "Efetivado")
    ].copy()
    if gastos.empty:
      continue
    gastos["Valor"] = pd.to_numeric(gastos["Valor"], errors="coerce").fillna(0.0)
    gastos["Venc"] = gastos["Data"].apply(
        lambda x: vencimento_da_fatura(x, c["Fechamento"], c["Vencimento"])
    )
    # pagamentos efetivados (Transferência com destino no cartão)
    pagos = pd.to_numeric(
        df[
            (df["Conta Destino"] == nome)
            & (df["Tipo"] == "Transferência")
            & (df["Status"] == "Efetivado")
        ]["Valor"],
        errors="coerce",
    ).fillna(0.0).sum()
    restante = float(pagos)

    # faturas da mais antiga para a mais nova: o pagamento quita na ordem
    for venc, total in sorted(
        gastos.groupby("Venc")["Valor"].sum().items(), key=lambda x: x[0]
    ):
      total = float(total)
      paga = restante >= total - 0.005
      if paga:
        restante -= total
      descricao_fatura = f"{prefixo} {pd.Timestamp(venc).strftime('%Y-%m')}"
      if paga:
        descricao_fatura += " ✅ Paga"
      novos.append([
          "Despesa",
          nome,
          "-",
          CATEGORIA_FATURA,
          descricao_fatura,
          total,
          venc,
          "Única",
          "Integral",
          "Efetivado" if paga else "Orçado",
          "Efetivado" if paga else "Budget",
      ])
  if novos:
    df_novos = pd.DataFrame(novos, columns=COLUNAS_LANC)
    df = pd.concat([df, df_novos], ignore_index=True)
  st.session_state.lancamentos = df.reset_index(drop=True)


# =====================================================================
# ABA: "Sophisticated Graphics" (20 Gráficos + Regressão + Média Ponderada)
# =====================================================================
if aba == "Sophisticated Graphics":
  st.markdown("# 🚀 Sophisticated Graphics: Painel 360° com Média Ponderada")
  st.markdown(
      "Análise visual avançada com **20 gráficos estatísticos e preditivos**"
      " (incluindo Regressão OLS e Média Móvel Ponderada), 100% vinculados aos"
      " seus filtros poderosos."
  )

  df = st.session_state.get("lancamentos", pd.DataFrame()).copy()

  if df.empty:
    st.warning(
        "⚠️ Nenhum lançamento cadastrado ainda. Vá até a aba de Lançamentos para"
        " popular seus dados."
    )
  else:
    # Tratamento e tipagem
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    df["AnoMês"] = df["Data"].dt.to_period("M").astype(str)
    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0.0)

    if "Status" not in df.columns:
      df["Status"] = "Efetivado"
    if "Cenario" not in df.columns:
      df["Cenario"] = "Efetivado"
    df["Cenario"] = df["Cenario"].fillna("Efetivado")
    if "Tipo" not in df.columns:
      df["Tipo"] = "Despesa"

    # ==================== BARRA DE FILTROS PODEROSOS ====================
    with st.expander(
        "🎛️ Filtros Poderosos Globais (Comandam os 20 Gráficos)", expanded=True
    ):
      f_col1, f_col2, f_col3, f_col4 = st.columns(4)

      with f_col1:
        cenarios_disp = (
            df["Cenario"].unique().tolist()
            if "Cenario" in df.columns
            else ["Efetivado", "Budget"]
        )
        filtro_cenario = st.multiselect(
            "Cenário (Budget vs Efetivado)",
            options=cenarios_disp,
            default=cenarios_disp,
        )
        filtro_status = st.multiselect(
            "Status",
            options=df["Status"].unique().tolist(),
            default=df["Status"].unique().tolist(),
        )

      with f_col2:
        tipos_disp = df["Tipo"].unique().tolist()
        filtro_tipos = st.multiselect(
            "Tipo de Movimento", options=tipos_disp, default=tipos_disp
        )
        contas_disp = (
            df["Conta"].unique().tolist() if "Conta" in df.columns else []
        )
        filtro_contas = st.multiselect(
            "Contas / Cartões", options=contas_disp, default=[]
        )

      with f_col3:
        categorias_disp = (
            df["Categoria"].unique().tolist()
            if "Categoria" in df.columns
            else []
        )
        filtro_categorias = st.multiselect(
            "Categorias", options=categorias_disp, default=[]
        )
        anos_disp = sorted(df["Data"].dt.year.dropna().unique().tolist())
        filtro_anos = st.multiselect(
            "Anos", options=anos_disp, default=anos_disp
        )

      with f_col4:
        usar_data_custom = st.checkbox("Ativar Intervalo de Datas Específico")
        if usar_data_custom:
          min_d, max_d = df["Data"].min(), df["Data"].max()
          intervalo_datas = st.date_input(
              "Período de Análise", value=[min_d, max_d]
          )

    # ==================== APLICAÇÃO DOS FILTROS ====================
    df_f = df.copy()
    if filtro_cenario and "Cenario" in df_f.columns:
      df_f = df_f[df_f["Cenario"].isin(filtro_cenario)]
    if filtro_status:
      df_f = df_f[df_f["Status"].isin(filtro_status)]
    if filtro_tipos and "Tipo" in df_f.columns:
      df_f = df_f[df_f["Tipo"].isin(filtro_tipos)]
    if filtro_contas and "Conta" in df_f.columns:
      df_f = df_f[df_f["Conta"].isin(filtro_contas)]
    if filtro_categorias and "Categoria" in df_f.columns:
      df_f = df_f[df_f["Categoria"].isin(filtro_categorias)]
    if filtro_anos:
      df_f = df_f[df_f["Data"].dt.year.isin(filtro_anos)]
    if usar_data_custom and len(intervalo_datas) == 2:
      d_ini, d_fim = pd.to_datetime(intervalo_datas[0]), pd.to_datetime(
          intervalo_datas[1]
      )
      df_f = df_f[(df_f["Data"] >= d_ini) & (df_f["Data"] <= d_fim)]

    if df_f.empty:
      st.warning(
          "⚠️ Nenhum dado encontrado para os filtros selecionados. Altere os"
          " filtros para visualizar os gráficos."
      )
    else:
      # Preparação de Bases Consolidadas
      rec_df = df_f[df_f["Tipo"].str.lower() == "receita"]
      desp_df = df_f[df_f["Tipo"].str.lower() == "despesa"]

      df_mensal = (
          df_f.groupby(["AnoMês", "Tipo"])["Valor"]
          .sum()
          .unstack(fill_value=0.0)
      )
      if "Receita" not in df_mensal.columns:
        df_mensal["Receita"] = 0.0
      if "Despesa" not in df_mensal.columns:
        df_mensal["Despesa"] = 0.0
      df_mensal["CashFlow"] = df_mensal["Receita"] - df_mensal["Despesa"]
      df_mensal["Acumulado"] = df_mensal["CashFlow"].cumsum()
      df_mensal = df_mensal.reset_index()

      # ===================================================================
      # GRÁFICOS 1 A 5: TENDÊNCIAS, CASH FLOW E CURVAS DE ACUMULADO
      # ===================================================================
      st.markdown("---")
      st.subheader(
          "📈 Bloco 1: Dinâmica de Cash Flow, Tendência & Curvas Acumuladas"
      )

      gc1, gc2 = st.columns(2)

      with gc1:
        fig1 = px.line(
            df_mensal,
            x="AnoMês",
            y="CashFlow",
            markers=True,
            title="1. Evolução do Fluxo de Caixa Mensal (Efetivo/Budget)",
            color_discrete_sequence=["#00CC96"],
        )
        fig1.add_hline(
            y=0, line_dash="dash", line_color="red", annotation_text="Break-even"
        )
        st.plotly_chart(fig1, use_container_width=True)

        fig3 = px.area(
            df_mensal,
            x="AnoMês",
            y=["Receita", "Despesa"],
            title=(
                "3. Volume de Entradas vs Saídas (Área de Absorção de Liquidez)"
            ),
            color_discrete_map={"Receita": "#00CC96", "Despesa": "#EF553B"},
        )
        st.plotly_chart(fig3, use_container_width=True)

        fig5 = px.scatter(
            df_f,
            x="Data",
            y="Valor",
            color="Tipo",
            size="Valor",
            hover_data=["Categoria", "Conta"],
            title="5. Dispersão de Impacto Financeiro por Transação",
            color_discrete_map={"Receita": "#00CC96", "Despesa": "#EF553B"},
        )
        st.plotly_chart(fig5, use_container_width=True)

      with gc2:
        fig2 = px.area(
            df_mensal,
            x="AnoMês",
            y="Acumulado",
            title="2. Curva de Crescimento do Cash Flow Acumulado",
            color_discrete_sequence=["#636EFA"],
        )
        st.plotly_chart(fig2, use_container_width=True)

        fig4 = px.bar(
            df_mensal,
            x="AnoMês",
            y=["Receita", "Despesa"],
            barmode="group",
            title="4. Comparativo Mensal de Receitas e Despesas",
            color_discrete_map={"Receita": "#00CC96", "Despesa": "#EF553B"},
        )
        st.plotly_chart(fig4, use_container_width=True)

      # ===================================================================
      # GRÁFICOS 6 A 10: CATEGORIAS, DISTRIBUIÇÕES E VOLATILIDADE
      # ===================================================================
      st.markdown("---")
      st.subheader("📊 Bloco 2: Estrutura de Gastos, Categorias & Volatilidade")

      gc3, gc4 = st.columns(2)

      with gc3:
        if not desp_df.empty:
          cat_desp = (
              desp_df.groupby("Categoria")["Valor"].sum().reset_index()
          )
          fig6 = px.pie(
              cat_desp,
              names="Categoria",
              values="Valor",
              hole=0.4,
              title="6. Concentração de Despesas por Categoria",
          )
          st.plotly_chart(fig6, use_container_width=True)
        else:
          st.info("Sem dados de despesa para o gráfico 6.")

        if not desp_df.empty:
          fig8 = px.box(
              desp_df,
              x="Categoria",
              y="Valor",
              color="Categoria",
              title="8. Análise de Dispersão e Outliers (Box Plot por Categoria)",
          )
          st.plotly_chart(fig8, use_container_width=True)
        else:
          st.info("Sem dados suficientes para o gráfico 8.")

        if not df_f.empty:
          fig10 = px.violin(
              df_f,
              y="Valor",
              x="Tipo",
              box=True,
              points="all",
              color="Tipo",
              title="10. Perfil de Densidade de Valores (Violin Plot)",
          )
          st.plotly_chart(fig10, use_container_width=True)
        else:
          st.info("Sem dados para o gráfico 10.")

      with gc4:
        if not rec_df.empty:
          cat_rec = rec_df.groupby("Categoria")["Valor"].sum().reset_index()
          fig7 = px.pie(
              cat_rec,
              names="Categoria",
              values="Valor",
              hole=0.4,
              title="7. Fontes e Origens de Receitas",
          )
          st.plotly_chart(fig7, use_container_width=True)
        else:
          st.info("Sem dados de receita para o gráfico 7.")

        if not df_f.empty:
          fig9 = px.treemap(
              df_f,
              path=["Tipo", "Categoria", "Descrição"],
              values="Valor",
              title="9. Mapa Hierárquico de Alocação (Treemap 360°)",
          )
          st.plotly_chart(fig9, use_container_width=True)
        else:
          st.info("Sem dados para o gráfico 9.")

      # ===================================================================
      # GRÁFICOS 11 A 15: CONTAS, CENÁRIOS, STATUS E PROGRESSÕES
      # ===================================================================
      st.markdown("---")
      st.subheader(
          "⚡ Bloco 3: Contas, Cenários (Budget vs Efetivado) & Status"
      )

      gc5, gc6 = st.columns(2)

      with gc5:
        if "Conta" in df_f.columns and not df_f.empty:
          conta_df = df_f.groupby(["Conta", "Tipo"])["Valor"].sum().reset_index()
          fig11 = px.bar(
              conta_df,
              y="Conta",
              x="Valor",
              color="Tipo",
              barmode="stack",
              orientation="h",
              title="11. Saldo Consolidado por Conta / Cartão",
              color_discrete_map={"Receita": "#00CC96", "Despesa": "#EF553B"},
          )
          st.plotly_chart(fig11, use_container_width=True)
        else:
          st.info("Coluna Conta não disponível para o gráfico 11.")

        if "Cenario" in df_f.columns and not df_f.empty:
          cenario_df = (
              df_f.groupby(["Cenario", "Tipo"])["Valor"].sum().reset_index()
          )
          fig13 = px.bar(
              cenario_df,
              x="Cenario",
              y="Valor",
              color="Tipo",
              barmode="group",
              title="13. Desvio Orçamentário: Budget vs Efetivado",
              color_discrete_map={"Receita": "#00CC96", "Despesa": "#EF553B"},
          )
          st.plotly_chart(fig13, use_container_width=True)
        else:
          st.info("Coluna Cenário não disponível para o gráfico 13.")

        if "Status" in df_f.columns and not df_f.empty:
          fig15 = px.sunburst(
              df_f,
              path=["Tipo", "Status", "Categoria"],
              values="Valor",
              title="15. Estrutura Multidimensional (Sunburst)",
          )
          st.plotly_chart(fig15, use_container_width=True)
        else:
          st.info("Dados insuficientes para o gráfico 15.")

      with gc6:
        if "Status" in df_f.columns and not df_f.empty:
          status_df = (
              df_f.groupby(["Status", "Tipo"])["Valor"].sum().reset_index()
          )
          fig12 = px.bar(
              status_df,
              x="Status",
              y="Valor",
              color="Tipo",
              barmode="group",
              title="12. Impacto Financeiro por Status Operacional",
              color_discrete_map={"Receita": "#00CC96", "Despesa": "#EF553B"},
          )
          st.plotly_chart(fig12, use_container_width=True)
        else:
          st.info("Coluna Status não disponível para o gráfico 12.")

        if not desp_df.empty:
          radar_df = (
              desp_df.groupby("Categoria")["Valor"].sum().reset_index()
          )
          fig14 = px.line_polar(
              radar_df,
              r="Valor",
              theta="Categoria",
              line_close=True,
              title="14. Radar de Vulnerabilidade e Exposição por Categoria",
          )
          fig14.update_traces(fill="toself")
          st.plotly_chart(fig14, use_container_width=True)
        else:
          st.info("Dados de despesa insuficientes para o gráfico 14.")

      # ===================================================================
      # GRÁFICOS 16 A 20: REGRESSÃO OLS & MÉDIA MÓVEL PONDERADA (WMA)
      # ===================================================================
      st.markdown("---")
      st.subheader(
          "🔮 Bloco 4: Regressão OLS & Média Móvel Ponderada (WMA) de"
          " Previsibilidade"
      )

      gc7, gc8 = st.columns(2)

      with gc7:
        # Gráfico 16: Regressão + Média Móvel Ponderada (WMA) de Despesas
        if not desp_df.empty:
          desp_temp = desp_df.groupby("Data")["Valor"].sum().reset_index()
          window = 3
          weights = np.arange(1, window + 1)
          desp_temp["WMA"] = (
              desp_temp["Valor"]
              .rolling(window)
              .apply(
                  lambda x: np.dot(x, weights) / weights.sum(), raw=True
              )
          )

          fig16 = px.scatter(
              desp_temp,
              x="Data",
              y="Valor",
              trendline="ols",
              title=(
                  "16. Despesas: Regressão OLS + Média Móvel Ponderada (WMA)"
              ),
          )
          fig16.add_trace(
              go.Scatter(
                  x=desp_temp["Data"],
                  y=desp_temp["WMA"],
                  mode="lines",
                  name="WMA (Ponderada)",
                  line=dict(color="orange", width=3, dash="dot"),
              )
          )
          st.plotly_chart(fig16, use_container_width=True)
        else:
          st.info("Dados insuficientes para o gráfico 16.")

        # Gráfico 18: Histograma com Curva de Densidade de Gastos
        if not desp_df.empty:
          fig18 = px.histogram(
              desp_df,
              x="Valor",
              marginal="rug",
              nbins=30,
              title="18. Distribuição de Frequência e Densidade de Despesas",
              color_discrete_sequence=["#EF553B"],
          )
          st.plotly_chart(fig18, use_container_width=True)
        else:
          st.info("Dados insuficientes para o gráfico 18.")

        # Gráfico 20: Cascata de Impacto Líquido (Waterfall)
        if not df_f.empty:
          tot_rec = rec_df["Valor"].sum()
          tot_desp = desp_df["Valor"].sum()
          fig20 = go.Figure(
              go.Waterfall(
                  name="Cash Flow",
                  orientation="v",
                  measure=["relative", "relative", "total"],
                  x=["Receitas Totais", "Despesas Totais", "Saldo Líquido"],
                  textposition="outside",
                  text=[
                      f"R$ {tot_rec:,.2f}",
                      f"-R$ {tot_desp:,.2f}",
                      f"R$ {tot_rec - tot_desp:,.2f}",
                  ],
                  y=[tot_rec, -tot_desp, tot_rec - tot_desp],
                  connector={"line": {"color": "rgb(63, 63, 63)"}},
              )
          )
          fig20.update_layout(
              title="20. Cascata de Impacto Líquido (Waterfall Cash Flow)",
              showlegend=False,
          )
          st.plotly_chart(fig20, use_container_width=True)
        else:
          st.info("Dados insuficientes para o gráfico 20.")

      with gc8:
        # Gráfico 17: Regressão + Média Móvel Ponderada (WMA) de Receitas
        if not rec_df.empty:
          rec_temp = rec_df.groupby("Data")["Valor"].sum().reset_index()
          window = 3
          weights = np.arange(1, window + 1)
          rec_temp["WMA"] = (
              rec_temp["Valor"]
              .rolling(window)
              .apply(
                  lambda x: np.dot(x, weights) / weights.sum(), raw=True
              )
          )

          fig17 = px.scatter(
              rec_temp,
              x="Data",
              y="Valor",
              trendline="ols",
              title=(
                  "17. Receitas: Regressão OLS + Média Móvel Ponderada (WMA)"
              ),
          )
          fig17.add_trace(
              go.Scatter(
                  x=rec_temp["Data"],
                  y=rec_temp["WMA"],
                  mode="lines",
                  name="WMA (Ponderada)",
                  line=dict(color="green", width=3, dash="dot"),
              )
          )
          st.plotly_chart(fig17, use_container_width=True)
        else:
          st.info("Dados insuficientes para o gráfico 17.")

        # Gráfico 19: Curva de Progressão Contínua do Patrimônio
        if not df_f.empty:
          df_sorted = df_f.sort_values(by="Data").copy()
          df_sorted["ValorAcum"] = df_sorted["Valor"].cumsum()
          fig19 = px.line(
              df_sorted,
              x="Data",
              y="ValorAcum",
              title="19. Curva de Progressão Contínua do Patrimônio Filtrado",
              color_discrete_sequence=["#00CC96"],
          )
          st.plotly_chart(fig19, use_container_width=True)
        else:
          st.info("Dashboard sem dados suficientes para o gráfico 19.")


# =====================================================================
# LÓGICA DA ABA: "Graphics" (Predições, Cash Flow & 20 KPIs Integrados)
# =====================================================================
if aba == "Graphics":
  st.markdown("# 🔮 Predições, Cash Flow & Painel Executivo 360°")
  st.markdown(
      "Painel avançado de inteligência preditiva onde **todos os 20 KPIs e"
      " gráficos** respondem dinamicamente aos filtros de Data, Budget/Efetivado,"
      " Categorias e Status."
  )

  df = st.session_state.get("lancamentos", pd.DataFrame()).copy()

  if df.empty:
    st.warning(
        "⚠️ Nenhum lançamento cadastrado ainda. Vá até a aba de Lançamentos para"
        " popular seus dados."
    )
  else:
    # Tratamento e tipagem robusta de dados
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    df["AnoMês"] = df["Data"].dt.to_period("M").astype(str)
    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0.0)

    if "Status" not in df.columns:
      df["Status"] = "Efetivado"
    if "Cenario" not in df.columns:
      df["Cenario"] = "Efetivado"
    df["Cenario"] = df["Cenario"].fillna("Efetivado")
    if "Tipo" not in df.columns:
      df["Tipo"] = "Despesa"

    # ==================== BARRA DE FILTROS PODEROSOS ====================
    with st.expander(
        "🎛️ Filtros Poderosos Globais (Afetam Todos os KPIs e Gráficos)",
        expanded=True,
    ):
      f_col1, f_col2, f_col3, f_col4 = st.columns(4)

      with f_col1:
        cenarios_disp = (
            df["Cenario"].unique().tolist()
            if "Cenario" in df.columns
            else ["Efetivado", "Budget"]
        )
        filtro_cenario = st.multiselect(
            "Cenário (Budget vs Efetivado)",
            options=cenarios_disp,
            default=cenarios_disp,
        )

        filtro_status = st.multiselect(
            "Status",
            options=df["Status"].unique().tolist(),
            default=df["Status"].unique().tolist(),
        )

      with f_col2:
        tipos_disp = df["Tipo"].unique().tolist()
        filtro_tipos = st.multiselect(
            "Tipo de Movimento", options=tipos_disp, default=tipos_disp
        )

        contas_disp = (
            df["Conta"].unique().tolist() if "Conta" in df.columns else []
        )
        filtro_contas = st.multiselect(
            "Contas / Cartões", options=contas_disp, default=[]
        )

      with f_col3:
        categorias_disp = (
            df["Categoria"].unique().tolist()
            if "Categoria" in df.columns
            else []
        )
        filtro_categorias = st.multiselect(
            "Categorias", options=categorias_disp, default=[]
        )

        anos_disp = sorted(df["Data"].dt.year.dropna().unique().tolist())
        filtro_anos = st.multiselect(
            "Anos", options=anos_disp, default=anos_disp
        )

      with f_col4:
        usar_data_custom = st.checkbox("Ativar Intervalo de Datas Específico")
        if usar_data_custom:
          min_d, max_d = df["Data"].min(), df["Data"].max()
          intervalo_datas = st.date_input(
              "Período de Análise", value=[min_d, max_d]
          )

    # ==================== APLICAÇÃO RIGOROSA DOS FILTROS ====================
    df_f = df.copy()
    if filtro_cenario and "Cenario" in df_f.columns:
      df_f = df_f[df_f["Cenario"].isin(filtro_cenario)]
    if filtro_status:
      df_f = df_f[df_f["Status"].isin(filtro_status)]
    if filtro_tipos and "Tipo" in df_f.columns:
      df_f = df_f[df_f["Tipo"].isin(filtro_tipos)]
    if filtro_contas and "Conta" in df_f.columns:
      df_f = df_f[df_f["Conta"].isin(filtro_contas)]
    if filtro_categorias and "Categoria" in df_f.columns:
      df_f = df_f[df_f["Categoria"].isin(filtro_categorias)]
    if filtro_anos:
      df_f = df_f[df_f["Data"].dt.year.isin(filtro_anos)]
    if usar_data_custom and len(intervalo_datas) == 2:
      d_ini, d_fim = pd.to_datetime(intervalo_datas[0]), pd.to_datetime(
          intervalo_datas[1]
      )
      df_f = df_f[(df_f["Data"] >= d_ini) & (df_f["Data"] <= d_fim)]

    # ==================== CÁLCULOS 100% BASEADOS NO DF_FILTRADO ====================
    receitas_df = df_f[df_f["Tipo"].str.lower() == "receita"]
    despesas_df = df_f[df_f["Tipo"].str.lower() == "despesa"]

    total_receitas = receitas_df["Valor"].sum()
    total_despesas = despesas_df["Valor"].sum()
    saldo_liquido = total_receitas - total_despesas

    meses_unicos = df_f["AnoMês"].nunique() if not df_f.empty else 1
    meses_unicos = max(meses_unicos, 1)

    media_mensal_receita = total_receitas / meses_unicos
    media_mensal_despesa = total_despesas / meses_unicos
    media_mensal_liquida = saldo_liquido / meses_unicos

    dias_periodo = (
        (df_f["Data"].max() - df_f["Data"].min()).days + 1
        if not df_f.empty
        else 1
    )
    dias_periodo = max(dias_periodo, 1)

    custo_medio_diario = total_despesas / dias_periodo
    burn_rate_mensal = media_mensal_despesa

    cobertura_reserva = (
        (total_receitas - total_despesas) / burn_rate_mensal
        if burn_rate_mensal > 0
        else 0.0
    )

    essenciais = ["Moradia", "Alimentação", "Saúde", "Educação", "Contas Básicas"]
    desp_essencial = despesas_df[
        despesas_df["Categoria"].isin(essenciais)
    ]["Valor"].sum()
    comprometimento_essencial = (
        (desp_essencial / total_receitas * 100) if total_receitas > 0 else 0.0
    )

    ticket_medio_transacao = (
        (total_despesas / len(despesas_df)) if not despesas_df.empty else 0.0
    )
    maior_pico_gasto = (
        despesas_df["Valor"].max() if not despesas_df.empty else 0.0
    )

    projecao_caixa_3m = saldo_liquido + (media_mensal_liquida * 3)
    projecao_caixa_6m = saldo_liquido + (media_mensal_liquida * 6)

    desp_por_mes = despesas_df.groupby("AnoMês")["Valor"].sum()
    volatilidade_gastos = (
        desp_por_mes.std() if len(desp_por_mes) > 1 else 0.0
    )

    discricionarias = ["Lazer", "Viagem", "Entretenimento", "Compras"]
    desp_disc = despesas_df[
        despesas_df["Categoria"].isin(discricionarias)
    ]["Valor"].sum()
    gasto_discricionario_pct = (
        (desp_disc / total_despesas * 100) if total_despesas > 0 else 0.0
    )

    volume_transacional = len(df_f)
    eficiencia_arrecadacao = (
        (total_receitas / (total_despesas + 1)) if total_despesas > 0 else 100.0
    )
    runway_dias = (
        (saldo_liquido / custo_medio_diario)
        if custo_medio_diario > 0 and saldo_liquido > 0
        else 0.0
    )
    taxa_poupanca = (
        (saldo_liquido / total_receitas * 100) if total_receitas > 0 else 0.0
    )

    parcelados = (
        df_f[
            df_f["Parcelas"].notna()
            & (df_f["Parcelas"] != "")
            & (df_f["Parcelas"] != "1")
            & (df_f["Parcelas"] != "Única")
        ]
        if "Parcelas" in df_f.columns
        else pd.DataFrame()
    )
    transacoes_parceladas = len(parcelados)
    potencial_anual_cagr = media_mensal_liquida * 12

    # ==================== DIAGNÓSTICO INTELIGENTE REATIVO ====================
    st.markdown("---")
    st.markdown("### 🔍 Diagnóstico Executivo Reativo (Baseado nos Filtros)")
    if saldo_liquido >= 0:
      st.success(
          f"🟢 **Status Superavitário:** Para os filtros selecionados, o saldo"
          f" líquido é de **R$ {saldo_liquido:,.2f}** (Média de R$"
          f" {media_mensal_liquida:,.2f}/mês)."
      )
    else:
      st.warning(
          f"⚠️ **Status Deficitário:** Os filtros aplicados revelam um déficit"
          f" de **R$ {saldo_liquido:,.2f}**. Reveja as categorias e o cenário"
          " de Budget."
      )

    # ==================== OS 20 KPIS VINCULADOS AOS FILTROS ====================
    st.markdown("---")
    st.subheader("📊 Bloco 1: Visão Patrimonial & Fluxo Filtrado")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(
        "1. Saldo Líquido",
        f"R$ {saldo_liquido:,.2f}",
        delta=f"R$ {media_mensal_liquida:,.2f}/mês",
    )
    c2.metric("2. Total Receitas", f"R$ {total_receitas:,.2f}")
    c3.metric("3. Total Despesas", f"R$ {total_despesas:,.2f}", delta_color="inverse")
    c4.metric(
        "4. Taxa de Poupança",
        f"{taxa_poupanca:.1f}%",
        delta="Meta > 20%",
        delta_color="normal" if taxa_poupanca >= 20 else "inverse",
    )
    c5.metric("5. Cobertura do Período", f"{cobertura_reserva:.1f} meses")

    st.markdown("---")
    st.subheader("⚡ Bloco 2: Ritmo, Custos & Riscos Filtrados")
    c6, c7, c8, c9, c10 = st.columns(5)
    c6.metric("6. Custo Médio Diário", f"R$ {custo_medio_diario:,.2f} / dia")
    c7.metric("7. Burn Rate Mensal", f"R$ {burn_rate_mensal:,.2f} / mês")
    c8.metric("8. Comprometimento Essencial", f"{comprometimento_essencial:.1f}%")
    c9.metric("9. Ticket Médio Despesa", f"R$ {ticket_medio_transacao:,.2f}")
    c10.metric(
        "10. Maior Pico de Gasto",
        f"R$ {maior_pico_gasto:,.2f}",
        delta_color="inverse",
    )

    st.markdown("---")
    st.subheader("🔮 Bloco 3: Projeções Futuras & Eficiência")
    c11, c12, c13, c14, c15 = st.columns(5)
    c11.metric(
        "11. Projeção Caixa (+3M)",
        f"R$ {projecao_caixa_3m:,.2f}",
        delta="Tendência Linear",
    )
    c12.metric(
        "12. Projeção Caixa (+6M)",
        f"R$ {projecao_caixa_6m:,.2f}",
        delta="Horizonte Longo",
    )
    c13.metric(
        "13. Volatilidade Mensal",
        f"R$ {volatilidade_gastos:,.2f}",
        delta="Desvio Padrão",
    )
    c14.metric("14. Gasto Discricionário", f"{gasto_discricionario_pct:.1f}%")
    c15.metric("15. Volume Transacional", f"{volume_transacional} lçs")

    st.markdown("---")
    st.subheader("🎯 Bloco 4: Resiliência & Indicadores Avançados")
    c16, c17, c18, c19, c20 = st.columns(5)
    c16.metric("16. Eficiência de Arrecadação", f"{eficiencia_arrecadacao:.2f}x")
    c17.metric("17. Runway Financeiro", f"{runway_dias:.0f} dias")
    c18.metric("18. Margem Pessoal (%)", f"{taxa_poupanca:.1f}%")
    c19.metric("19. Transações Parceladas", f"{transacoes_parceladas} ativas")
    c20.metric("20. Potencial Anual (CAGR)", f"R$ {potencial_anual_cagr:,.2f}")

    # ==================== GRÁFICOS REATIVOS ====================
    st.markdown("---")
    st.subheader("📈 Análise Gráfica Dinâmica (Reage aos Filtros)")

    if not df_f.empty:
      df_mensal = (
          df_f.groupby(["AnoMês", "Tipo"])["Valor"]
          .sum()
          .unstack(fill_value=0.0)
      )
      if "Receita" not in df_mensal.columns:
        df_mensal["Receita"] = 0.0
      if "Despesa" not in df_mensal.columns:
        df_mensal["Despesa"] = 0.0
      df_mensal["Cash Flow Mensal"] = (
          df_mensal["Receita"] - df_mensal["Despesa"]
      )
      df_mensal["Acumulado"] = df_mensal["Cash Flow Mensal"].cumsum()

      g_col1, g_col2 = st.columns(2)
      with g_col1:
        st.markdown("##### 📊 Fluxo Mensal (Receitas vs Despesas)")
        st.bar_chart(df_mensal[["Receita", "Despesa"]])
      with g_col2:
        st.markdown("##### 📉 Curva de Cash Flow Acumulado")
        st.line_chart(df_mensal["Acumulado"])

      st.markdown("##### 🌊 Saldo Líquido Mensal")
      st.line_chart(df_mensal["Cash Flow Mensal"])
    else:
      st.info("Nenhum dado encontrado para os filtros selecionados.")

    # ==================== TABELA DETALHADA REATIVA ====================
    st.markdown("---")
    st.subheader("🔍 Auditoria de Lançamentos Filtrados")

    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
      st.write("Registros correspondentes aos filtros ativos:")
    with col_t2:
      qtd_exibida = st.selectbox(
          "Linhas visíveis", options=[25, 50, 100, "Todas"], index=0
      )

    if not df_f.empty:
      cols_mostrar = [
          c
          for c in [
              "Data",
              "Cenario",
              "Status",
              "Tipo",
              "Conta",
              "Categoria",
              "Valor",
              "Parcelas",
          ]
          if c in df_f.columns
      ]
      df_exibicao = df_f[cols_mostrar].sort_values(by="Data", ascending=False)
      if qtd_exibida != "Todas":
        df_exibicao = df_exibicao.head(int(qtd_exibida))

      st.dataframe(df_exibicao, use_container_width=True)

      csv_data = df_f.to_csv(index=False).encode("utf-8")
      st.download_button(
          label="📥 Baixar Dados Filtrados (CSV)",
          data=csv_data,
          file_name="cash_flow_filtrado.csv",
          mime="text/csv",
      )
    else:
      st.write("Nenhum registro para exibir.")


# ==================== LÓGICA DA ABA "Graphics" (BI / ANALÍTICO) ====================
if aba == "Graphics":
  st.subheader("📈 Business Intelligence & Painel Analítico Avançado")
  st.markdown(
      "Análise macro e microeconômica de performance financeira com foco em"
      " inteligência de dados."
  )

  df = st.session_state.lancamentos.copy()

  if df.empty:
    st.warning(
        "⚠️ Nenhum lançamento cadastrado ainda. Vá em 'Lançamentos' para"
        " adicionar dados."
    )
  else:
    # Tratamento de dados essenciais e engenharia de features para análise
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    df["Ano"] = df["Data"].dt.year
    df["Mês"] = df["Data"].dt.to_period("M").astype(str)
    df["DiaDaSemana"] = df["Data"].dt.day_name()
    dias_map = {
        "Monday": "Segunda",
        "Tuesday": "Terça",
        "Wednesday": "Quarta",
        "Thursday": "Quinta",
        "Friday": "Sexta",
        "Saturday": "Sábado",
        "Sunday": "Domingo",
    }
    df["DiaDaSemanaPt"] = df["DiaDaSemana"].map(dias_map)
    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0.0)
    if "Status" not in df.columns:
      df["Status"] = "Efetivado"

    # --- FILTROS ESPECÍFICOS DA ABA GRAPHICS ---
    with st.expander(
        "🎛️ Filtros Avançados de Análise Gráfica & Segmentação", expanded=True
    ):
      col_f1, col_f2, col_f3 = st.columns(3)
      with col_f1:
        anos_disponiveis = sorted(df["Ano"].dropna().unique().astype(int))
        filtro_ano_graf = st.multiselect(
            "Filtrar por Ano",
            options=anos_disponiveis,
            default=anos_disponiveis,
            key="graf_ano",
        )
      with col_f2:
        contas_disponiveis = df["Conta"].dropna().unique().tolist()
        filtro_conta_graf = st.multiselect(
            "Filtrar por Conta",
            options=contas_disponiveis,
            default=contas_disponiveis,
            key="graf_conta",
        )
      with col_f3:
        status_disponiveis = df["Status"].dropna().unique().tolist()
        filtro_status_graf = st.multiselect(
            "Filtrar por Status",
            options=status_disponiveis,
            default=status_disponiveis,
            key="graf_status",
        )

    # Aplicar filtros
    df_filtrado = df[
        (df["Ano"].isin(filtro_ano_graf))
        & (df["Conta"].isin(filtro_conta_graf))
        & (df["Status"].isin(filtro_status_graf))
    ]

    if df_filtrado.empty:
      st.info(
          "Nenhum dado encontrado para os filtros selecionados nesta aba."
      )
    else:
      # --- CÁLCULO DAS 10 KPIS AVANÇADAS ---
      receitas_totais = df_filtrado[df_filtrado["Tipo"] == "Receita"][
          "Valor"
      ].sum()
      despesas_totais = df_filtrado[df_filtrado["Tipo"] == "Despesa"][
          "Valor"
      ].sum()
      fluxo_caixa_livre = receitas_totais - despesas_totais

      taxa_poupanca = (
          (fluxo_caixa_livre / receitas_totais * 100)
          if receitas_totais > 0
          else 0.0
      )
      meses_unicos = df_filtrado["Mês"].nunique()
      burn_rate = despesas_totais / meses_unicos if meses_unicos > 0 else 0.0
      saldo_atual = receitas_totais - despesas_totais
      runway = (
          (saldo_atual / burn_rate)
          if burn_rate > 0 and saldo_atual > 0
          else 0.0
      )

      despesas_cartao = df_filtrado[
          df_filtrado["Conta"].str.contains(
              "Cartão|Credit|Nubank|Inter", case=False, na=False
          )
      ]["Valor"].sum()
      comprometimento_cartao = (
          (despesas_cartao / receitas_totais * 100)
          if receitas_totais > 0
          else 0.0
      )

      gasto_por_cat = (
          df_filtrado[df_filtrado["Tipo"] == "Despesa"]
          .groupby("Categoria")["Valor"]
          .sum()
      )
      max_cat_valor = gasto_por_cat.max() if not gasto_por_cat.empty else 0.0
      concentracao_cat = (
          (max_cat_valor / despesas_totais * 100)
          if despesas_totais > 0
          else 0.0
      )
      maior_categoria = (
          gasto_por_cat.idxmax() if not gasto_por_cat.empty else "N/A"
      )

      gastos_mensais = (
          df_filtrado[df_filtrado["Tipo"] == "Despesa"]
          .groupby("Mês")["Valor"]
          .sum()
      )
      volatilidade = (
          float(gastos_mensais.std()) if len(gastos_mensais) > 1 else 0.0
      )
      qtd_despesas = len(df_filtrado[df_filtrado["Tipo"] == "Despesa"])
      ticket_medio = (
          (despesas_totais / qtd_despesas) if qtd_despesas > 0 else 0.0
      )

      essenciais = ["Alimentação", "Moradia", "Transporte"]
      gasto_essencial = df_filtrado[
          df_filtrado["Categoria"].isin(essenciais)
      ]["Valor"].sum()
      cobertura_essencial = (
          (receitas_totais / gasto_essencial)
          if gasto_essencial > 0
          else 999.0
      )

      meses_ordenados = sorted(gastos_mensais.index.tolist())
      if len(meses_ordenados) >= 2:
        ult_mes = gastos_mensais.loc[meses_ordenados[-1]]
        penult_mes = gastos_mensais.loc[meses_ordenados[-2]]
        crescimento_mom = (
            ((ult_mes - penult_mes) / penult_mes * 100)
            if penult_mes > 0
            else 0.0
        )
      else:
        crescimento_mom = 0.0

      # --- RENDERIZAÇÃO DOS 10 KPIs EM CARDS ---
      st.markdown("### 📌 Indicadores Estratégicos de Desempenho (KPIs)")

      c1, c2, c3, c4 = st.columns(4)
      c1.metric(
          "Taxa de Poupança",
          f"{taxa_poupanca:.1f}%",
          delta="Saudável" if taxa_poupanca > 20 else "Atenção",
      )
      c2.metric("Burn Rate Mensal", f"R$ {burn_rate:,.2f}")
      c3.metric(
          "Runway (Meses)",
          f"{runway:.1f} meses" if runway > 0 else "0 meses",
          delta_color="off",
      )
      c4.metric(
          "Fluxo de Caixa Livre",
          f"R$ {fluxo_caixa_livre:,.2f}",
          delta="Positivo" if fluxo_caixa_livre >= 0 else "Negativo",
      )

      c5, c6, c7, c8 = st.columns(4)
      c5.metric("Comprometimento Cartão", f"{comprometimento_cartao:.1f}%")
      c6.metric(
          "Maior Foco de Gasto",
          f"{maior_categoria}",
          f"{concentracao_cat:.1f}% do total",
      )
      c7.metric("Volatilidade Mensal", f"R$ {volatilidade:,.2f}")
      c8.metric("Ticket Médio (Despesa)", f"R$ {ticket_medio:,.2f}")

      c9, c10, _, _ = st.columns(4)
      c9.metric("Cobertura Essenciais", f"{cobertura_essencial:.2f}x")
      c10.metric("Variação MoM (Despesas)", f"{crescimento_mom:+.1f}%")

      st.markdown("---")

      # ==================== PAINEL DE 8 GRÁFICOS AVANÇADOS ====================
      st.markdown("### 📊 Visualizações Analíticas & Comportamentais")

      col_g1, col_g2 = st.columns(2)

      with col_g1:
        st.subheader("Evolução Temporal: Receitas vs Despesas")
        df_temporal = (
            df_filtrado.groupby(["Mês", "Tipo"])["Valor"].sum().reset_index()
        )
        fig_evolucao = px.bar(
            df_temporal,
            x="Mês",
            y="Valor",
            color="Tipo",
            barmode="group",
            color_discrete_map={"Receita": "#2ecc71", "Despesa": "#e74c3c"},
            template="plotly_dark",
        )
        st.plotly_chart(fig_evolucao, use_container_width=True)

      with col_g2:
        st.subheader("Composição de Despesas por Categoria")
        df_cat = (
            df_filtrado[df_filtrado["Tipo"] == "Despesa"]
            .groupby("Categoria")["Valor"]
            .sum()
            .reset_index()
        )
        if not df_cat.empty:
          fig_pizza = px.pie(
              df_cat,
              names="Categoria",
              values="Valor",
              hole=0.4,
              template="plotly_dark",
          )
          st.plotly_chart(fig_pizza, use_container_width=True)
        else:
          st.info("Sem dados de despesas para exibir o gráfico de categorias.")

      col_g3, col_g4 = st.columns(2)

      with col_g3:
        st.subheader("Tendência de Acumulado de Caixa (Fluxo Livre)")
        df_fluxo = (
            df_filtrado.pivot_table(
                index="Mês", columns="Tipo", values="Valor", aggfunc="sum"
            )
            .fillna(0)
            .reset_index()
        )
        if "Receita" not in df_fluxo.columns:
          df_fluxo["Receita"] = 0
        if "Despesa" not in df_fluxo.columns:
          df_fluxo["Despesa"] = 0
        df_fluxo["Livre"] = df_fluxo["Receita"] - df_fluxo["Despesa"]
        df_fluxo["Acumulado"] = df_fluxo["Livre"].cumsum()

        fig_linha = px.line(
            df_fluxo,
            x="Mês",
            y="Acumulado",
            markers=True,
            template="plotly_dark",
            title="Patrimônio Líquido Acumulado no Período",
        )
        fig_linha.update_traces(line_color="#3498db", line_width=3)
        st.plotly_chart(fig_linha, use_container_width=True)

      with col_g4:
        st.subheader("Distribuição de Gastos por Conta / Origem")
        df_conta = (
            df_filtrado[df_filtrado["Tipo"] == "Despesa"]
            .groupby("Conta")["Valor"]
            .sum()
            .reset_index()
        )
        if not df_conta.empty:
          fig_bar_h = px.bar(
              df_conta,
              x="Valor",
              y="Conta",
              orientation="h",
              template="plotly_dark",
              color="Valor",
              color_continuous_scale="Reds",
          )
          st.plotly_chart(fig_bar_h, use_container_width=True)
        else:
          st.info("Sem dados por conta para exibir.")

      st.markdown("---")
      st.markdown("### 🔬 Analytics Avançado (Novas Perspectivas)")

      col_g5, col_g6 = st.columns(2)

      with col_g5:
        st.subheader("Boxplot: Dispersão e Outliers de Despesas")
        df_despesas = df_filtrado[df_filtrado["Tipo"] == "Despesa"]
        if not df_despesas.empty:
          fig_box = px.box(
              df_despesas,
              x="Categoria",
              y="Valor",
              color="Categoria",
              template="plotly_dark",
              title="Análise de Assimetria e Fugas de Orçamento por Categoria",
          )
          fig_box.update_layout(showlegend=False)
          st.plotly_chart(fig_box, use_container_width=True)
        else:
          st.info("Sem dados suficientes de despesas para gerar o Boxplot.")

      with col_g6:
        st.subheader("Heatmap: Sazonalidade de Gastos (Dia da Semana)")
        df_heatmap = (
            df_despesas.groupby(["Mês", "DiaDaSemanaPt"])["Valor"]
            .sum()
            .reset_index()
        )
        if not df_heatmap.empty:
          dias_ordem = [
              "Segunda",
              "Terça",
              "Quarta",
              "Quinta",
              "Sexta",
              "Sábado",
              "Domingo",
          ]
          fig_heat = px.density_heatmap(
              df_heatmap,
              x="DiaDaSemanaPt",
              y="Mês",
              z="Valor",
              category_orders={"DiaDaSemanaPt": dias_ordem},
              color_continuous_scale="YlOrRd",
              template="plotly_dark",
              title="Intensidade de Gastos por Dia da Semana ao Longo dos Meses",
          )
          st.plotly_chart(fig_heat, use_container_width=True)
        else:
          st.info("Sem dados para gerar o Mapa de Calor temporal.")

      col_g7, col_g8 = st.columns(2)

      with col_g7:
        st.subheader("Waterfall: Composição do Fluxo de Caixa")
        cat_desp = (
            df_filtrado[df_filtrado["Tipo"] == "Despesa"]
            .groupby("Categoria")["Valor"]
            .sum()
        )

        medidas = ["absolute"] + ["relative"] * len(cat_desp) + ["total"]
        x_vals = ["Receitas Totais"] + list(cat_desp.index) + ["Caixa Líquido"]
        y_vals = (
            [receitas_totais]
            + [-v for v in cat_desp.values]
            + [fluxo_caixa_livre]
        )

        fig_waterfall = go.Figure(
            go.Waterfall(
                name="Fluxo",
                orientation="v",
                measure=medidas,
                x=x_vals,
                textposition="outside",
                text=[f"R$ {val:,.2f}" for val in y_vals],
                y=y_vals,
                connector={"line": {"color": "rgb(63, 63, 63)"}},
            )
        )
        fig_waterfall.update_layout(
            template="plotly_dark",
            title="Impacto de Cada Categoria sobre o Saldo Inicial",
            showlegend=False,
        )
        st.plotly_chart(fig_waterfall, use_container_width=True)

      with col_g8:
        st.subheader("Radar Chart: Perfil de Peso das Categorias")
        if not cat_desp.empty and despesas_totais > 0:
          cat_perc = (cat_desp / despesas_totais * 100).reset_index()
          fig_radar = px.line_polar(
              cat_perc,
              r="Valor",
              theta="Categoria",
              line_close=True,
              template="plotly_dark",
              title="Distribuição Percentual de Alocação de Gastos",
          )
          fig_radar.update_traces(fill="toself", line_color="#e74c3c")
          st.plotly_chart(fig_radar, use_container_width=True)
        else:
          st.info(
              "Dados insuficientes para gerar o Radar de Alocação de Gastos."
          )

# ==================== FILTROS GLOBAIS PODEROSOS (BARRA LATERAL) ====================
st.sidebar.markdown("---")
st.sidebar.subheader("🎛️ Filtros Globais Poderosos")

df_global = st.session_state.lancamentos.copy()
if not df_global.empty:
  df_global["Data"] = pd.to_datetime(df_global["Data"], errors="coerce")
  if "Status" not in df_global.columns:
    df_global["Status"] = "Efetivado"
  df_global["Status"] = df_global["Status"].fillna("Efetivado")

  # 1. Filtro de Status
  status_disponiveis = df_global["Status"].unique().tolist()
  filtro_status = st.sidebar.multiselect(
      "📌 Status do Lançamento",
      options=status_disponiveis,
      default=status_disponiveis,
  )

  # 2. Filtro de Tipo
  tipos_disponiveis = (
      df_global["Tipo"].dropna().unique().tolist()
      if "Tipo" in df_global.columns
      else ["Receita", "Despesa"]
  )
  filtro_tipos = st.sidebar.multiselect(
      "💰 Tipo de Movimentação",
      options=tipos_disponiveis,
      default=tipos_disponiveis,
  )

  # 3. Filtro de Anos
  anos_disponíveis = (
      sorted(df_global["Data"].dt.year.dropna().unique().astype(int))
      if not df_global["Data"].dropna().empty
      else [2026]
  )
  filtro_anos = st.sidebar.multiselect(
      "📅 Anos de Referência",
      options=anos_disponíveis,
      default=anos_disponíveis,
  )

  # 4. Filtro de Contas
  contas_disponíveis = (
      df_global["Conta"].dropna().unique().tolist()
      if "Conta" in df_global.columns
      else []
  )
  filtro_contas = st.sidebar.multiselect(
      "🏦 Contas / Carteiras",
      options=contas_disponíveis,
      default=contas_disponíveis,
  )

  # 5. Filtro de Categorias
  categorias_disponíveis = (
      df_global["Categoria"].dropna().unique().tolist()
      if "Categoria" in df_global.columns
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
  if usar_filtro_data and not df_global["Data"].dropna().empty:
    min_d = df_global["Data"].min().date()
    max_d = df_global["Data"].max().date()
    intervalo_datas = st.sidebar.date_input(
        "Selecione o Período", value=(min_d, max_d)
    )
else:
  filtro_status, filtro_tipos, filtro_anos, filtro_contas, filtro_categorias = (
      [],
      [],
      [],
      [],
      [],
  )
  usar_filtro_data = False


# ==================== ABA KPIS ====================
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

    # ==================== CÁLCULO DOS 25 KPIS ====================
    kpi_1 = saldo_liquido
    kpi_2 = total_receitas
    kpi_3 = total_despesas
    kpi_4 = (
        (saldo_liquido / total_receitas * 100) if total_receitas > 0 else 0.0
    )

    dias_periodo = (
        (df_filtrado["Data"].max() - df_filtrado["Data"].min()).days + 1
        if not df_filtrado.empty
        else 1
    )
    dias_periodo = max(dias_periodo, 1)
    kpi_5 = total_despesas / dias_periodo

    meses_unicos = (
        df_filtrado["AnoMês"].nunique() if not df_filtrado.empty else 1
    )
    kpi_6 = total_despesas / max(meses_unicos, 1)

    caixa_total = (
        df[df["Tipo"].str.lower() == "receita"]["Valor"].sum()
        - df[df["Tipo"].str.lower() == "despesa"]["Valor"].sum()
    )
    kpi_7 = caixa_total / kpi_6 if kpi_6 > 0 else 0.0

    essenciais = ["Moradia", "Alimentação"]
    desp_essencial = despesas_df[
        despesas_df["Categoria"].isin(essenciais)
    ]["Valor"].sum()
    kpi_8 = (
        (desp_essencial / total_receitas * 100) if total_receitas > 0 else 0.0
    )

    kpi_9 = (
        total_despesas / len(despesas_df) if not despesas_df.empty else 0.0
    )
    kpi_10 = (
        despesas_df["Valor"].max() if not despesas_df.empty else 0.0
    )

    media_mensal_liquida = (
        (total_receitas - total_despesas) / max(meses_unicos, 1)
    )
    kpi_11 = caixa_total + (media_mensal_liquida * 3)

    salarios = receitas_df[
        receitas_df["Categoria"].str.lower() == "salário"
    ]["Valor"].sum()
    kpi_12 = (
        ((total_receitas - salarios) / total_receitas * 100)
        if total_receitas > 0
        else 0.0
    )

    desp_por_mes = despesas_df.groupby("AnoMês")["Valor"].sum()
    kpi_13 = (
        desp_por_mes.std() if len(desp_por_mes) > 1 else 0.0
    )

    discricionarias = ["Lazer"]
    desp_disc = despesas_df[
        despesas_df["Categoria"].isin(discricionarias)
    ]["Valor"].sum()
    kpi_14 = (
        (desp_disc / total_despesas * 100) if total_despesas > 0 else 0.0
    )

    kpi_15 = len(df_filtrado)
    kpi_16 = (
        (total_receitas / (total_despesas + 1)) if total_despesas > 0 else 100.0
    )
    kpi_17 = (
        (caixa_total / kpi_5) if kpi_5 > 0 else 0.0
    )
    kpi_18 = kpi_4

    parcelados = (
        df_filtrado[
            df_filtrado["Parcelas"].notna()
            & (df_filtrado["Parcelas"] != "")
            & (df_filtrado["Parcelas"] != "1")
            & (df_filtrado["Parcelas"] != "Única")
        ]
        if "Parcelas" in df_filtrado.columns
        else pd.DataFrame()
    )
    kpi_19 = len(parcelados)
    kpi_20 = media_mensal_liquida * 12

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
            - (min(kpi_7, 6) / 6 * 20),
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
      df_temp = df_temp[
          df_temp["Categoria"].isin(categoria_selecionada)
          | (df_temp["Tipo"] == "Transferência")
      ]
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
      df_stat = df_stat[
          df_stat["Categoria"].isin(cat_stat_sel)
          | (df_stat["Tipo"] == "Transferência")
      ]
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
      df_fin = df_fin[
          df_fin["Categoria"].isin(cat_fin_sel)
          | (df_fin["Tipo"] == "Transferência")
      ]
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


# ==================== IA & ASSISTANT (GEMINI API) ====================
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
      st.caption(
          "ℹ️ Os budgets automáticos de fatura de cartão ([AUTO]) são recalculados"
          " sozinhos após editar ou excluir compras."
      )
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
                  if "Status" in reg_atual and pd.notna(reg_atual["Status"])
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
              st.session_state.lancamentos.loc[id_para_editar, "Cenario"] = (
                  "Budget" if novo_status == "Orçado" else "Efetivado"
              )
              sincronizar_budget_cartao()
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
          sincronizar_budget_cartao()
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
            sincronizar_budget_cartao()
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

  nomes_cartoes_cad = [c["Nome"] for c in st.session_state.cartoes]
  if tipo == "Despesa" and status_lancamento == "Efetivado" and conta in nomes_cartoes_cad:
    st.info(
        f"💳 '{conta}' é um cartão: o Budget da fatura será criado/atualizado"
        " automaticamente."
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
      cenario_lanc = "Budget" if status_lancamento == "Orçado" else "Efetivado"
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
            cenario_lanc,
        ])

      df_novos = pd.DataFrame(novos_registros, columns=COLUNAS_LANC)
      st.session_state.lancamentos = pd.concat(
          [st.session_state.lancamentos, df_novos], ignore_index=True
      )

      # Budget automático da fatura quando a compra é Efetivada no cartão
      if (
          tipo == "Despesa"
          and status_lancamento == "Efetivado"
          and conta in nomes_cartoes_cad
      ):
        sincronizar_budget_cartao(conta)
      elif (
          tipo == "Transferência"
          and status_lancamento == "Efetivado"
          and conta_destino in nomes_cartoes_cad
      ):
        sincronizar_budget_cartao(conta_destino)

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


# ==================== CARTÕES DE CRÉDITO (COM BUDGET AUTOMÁTICO) ====================
elif aba == "Cartões de Crédito":
  st.title("💳 Gestão de Cartões de Crédito")
  st.write(
      "Cadastre cartões, lance compras e o sistema cria o Budget da fatura"
      " automaticamente conforme fechamento e vencimento."
  )

  tab_gerenciar, tab_compra, tab_faturas = st.tabs(
      ["📝 Meus Cartões", "🛒 Lançar Compra", "📊 Faturas & Limites"]
  )

  # ---------- CADASTRO DE CARTÕES ----------
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
            "Dia de Fechamento", min_value=1, max_value=31, value=1, step=1
        )
        dia_vencimento = st.number_input(
            "Dia de Vencimento", min_value=1, max_value=31, value=10, step=1
        )
      if st.form_submit_button("💾 Salvar Cartão", use_container_width=True):
        if not nome_cartao:
          st.error("O nome do cartão não pode estar vazio.")
        elif limite_cartao <= 0:
          st.error("O limite deve ser maior que zero.")
        elif nome_cartao in [c["Nome"] for c in st.session_state.cartoes]:
          st.warning("Já existe um cartão com esse nome.")
        else:
          st.session_state.cartoes.append({
              "Nome": nome_cartao,
              "Limite": limite_cartao,
              "Fechamento": int(dia_fechamento),
              "Vencimento": int(dia_vencimento),
          })
          if nome_cartao not in st.session_state.contas:
            st.session_state.contas.append(nome_cartao)
          st.success(f"Cartão '{nome_cartao}' cadastrado!")
          st.rerun()

    st.markdown("---")
    st.subheader("Cartões Cadastrados")
    if st.session_state.cartoes:
      st.dataframe(
          pd.DataFrame(st.session_state.cartoes), use_container_width=True
      )
    else:
      st.info("Nenhum cartão cadastrado.")

  # ---------- LANÇAR COMPRA (GERA BUDGET AUTOMÁTICO) ----------
  with tab_compra:
    st.subheader("Lançar Compra no Cartão")
    st.caption(
        "Compra até o dia do fechamento entra na fatura do mês; depois do"
        " fechamento, vai para a fatura seguinte. O Budget é criado na data de"
        " vencimento."
    )
    if not st.session_state.cartoes:
      st.warning("Cadastre um cartão primeiro.")
    else:
      with st.form("form_compra_cartao"):
        c1, c2 = st.columns(2)
        with c1:
          cartao_compra = st.selectbox(
              "Cartão", [c["Nome"] for c in st.session_state.cartoes]
          )
          desc_compra = st.text_input("Descrição")
          cat_compra = st.selectbox("Categoria", st.session_state.categorias)
        with c2:
          valor_compra = st.number_input(
              "Valor Total (R$)", min_value=0.0, step=10.0, format="%.2f"
          )
          data_compra = st.date_input("Data da Compra")
          parcelas_compra = st.number_input(
              "Parcelas", min_value=1, max_value=60, value=1, step=1
          )
        modo_compra = st.radio(
            "Valor das parcelas",
            ["Dividir (Total ÷ Parcelas)", "Replicar (Valor integral por parcela)"],
            horizontal=True,
        )

        if st.form_submit_button("💾 Salvar Compra", use_container_width=True):
          if not desc_compra or valor_compra <= 0:
            st.error("Informe a descrição e um valor maior que zero.")
          else:
            cfg = next(
                c for c in st.session_state.cartoes if c["Nome"] == cartao_compra
            )
            linhas = []
            for i in range(int(parcelas_compra)):
              dt = pd.to_datetime(data_compra) + pd.DateOffset(months=i)
              v = (
                  valor_compra / parcelas_compra
                  if (parcelas_compra > 1 and "Dividir" in modo_compra)
                  else valor_compra
              )
              linhas.append([
                  "Despesa",
                  cartao_compra,
                  "-",
                  cat_compra,
                  f"{desc_compra} ({i+1}/{int(parcelas_compra)})"
                  if parcelas_compra > 1
                  else desc_compra,
                  v,
                  dt.date(),
                  f"{i+1}/{int(parcelas_compra)}" if parcelas_compra > 1 else "Única",
                  "Integral",
                  "Efetivado",
                  "Efetivado",
              ])
            df_novos = pd.DataFrame(linhas, columns=COLUNAS_LANC)
            st.session_state.lancamentos = pd.concat(
                [st.session_state.lancamentos, df_novos], ignore_index=True
            )
            sincronizar_budget_cartao(cartao_compra)
            venc1 = vencimento_da_fatura(
                data_compra, cfg["Fechamento"], cfg["Vencimento"]
            )
            st.success(
                f"Compra salva! Budget da fatura atualizado. 1ª parcela vence em"
                f" {venc1.strftime('%d/%m/%Y')}."
            )

  # ---------- FATURAS & LIMITES ----------
  with tab_faturas:
    st.subheader("Faturas e Limites")
    if not st.session_state.cartoes:
      st.warning("Cadastre pelo menos um cartão.")
    else:
      cartao_sel = st.selectbox(
          "Selecione o Cartão",
          [c["Nome"] for c in st.session_state.cartoes],
          key="select_cartao_detalhe",
      )
      dados = next(
          c for c in st.session_state.cartoes if c["Nome"] == cartao_sel
      )
      limite_total = dados["Limite"]

      df_l = st.session_state.lancamentos.copy()
      if not df_l.empty:
        df_l["Status"] = df_l["Status"].fillna("Efetivado")
        df_cartao = df_l[
            (df_l["Conta"] == cartao_sel) | (df_l["Conta Destino"] == cartao_sel)
        ]
        gasto = df_l[
            (df_l["Conta"] == cartao_sel)
            & (df_l["Tipo"] == "Despesa")
            & (df_l["Status"] == "Efetivado")
            & ~df_l["Descrição"].astype(str).str.startswith(PREFIXO_AUTO)
        ]["Valor"].sum()
        pago = df_l[
            (df_l["Conta Destino"] == cartao_sel)
            & (df_l["Tipo"] == "Transferência")
            & (df_l["Status"] == "Efetivado")
        ]["Valor"].sum()
        comprometido = gasto - pago
      else:
        df_cartao = pd.DataFrame()
        comprometido = 0.0

      disponivel = limite_total - comprometido
      m1, m2, m3 = st.columns(3)
      m1.metric("Limite Total", f"R$ {limite_total:,.2f}")
      m2.metric(
          "Comprometido (compras − pagamentos)",
          f"R$ {comprometido:,.2f}",
          delta=f"Fecha dia {dados['Fechamento']} | Vence dia {dados['Vencimento']}",
          delta_color="off",
      )
      m3.metric(
          "Limite Disponível",
          f"R$ {disponivel:,.2f}",
          delta="Saudável" if disponivel >= 0 else "Limite ultrapassado!",
      )

      # Budgets automáticos das faturas
      st.markdown("---")
      st.markdown("#### 🗓️ Faturas Previstas (Budget Automático)")
      if not df_cartao.empty:
        auto = df_cartao[
            df_cartao["Descrição"].astype(str).str.startswith(
                f"{PREFIXO_AUTO}{cartao_sel} |"
            )
        ][["Data", "Descrição", "Valor", "Status"]].sort_values("Data")
        if auto.empty:
          st.info("Nenhuma fatura prevista ainda.")
        else:
          st.dataframe(
              auto.style.format({"Valor": "R$ {:,.2f}"}),
              use_container_width=True,
              hide_index=True,
          )
      else:
        st.info("Nenhuma fatura prevista ainda.")
      if st.button("🔄 Recalcular Budgets deste Cartão"):
        sincronizar_budget_cartao(cartao_sel)
        st.success("Budgets recalculados!")
        st.rerun()

      # Pagamento de fatura
      st.markdown("---")
      st.markdown(f"💳 **Registrar Pagamento de Fatura: {cartao_sel}**")
      with st.form("form_pagamento_fatura"):
        p1, p2, p3 = st.columns(3)
        with p1:
          origem = st.selectbox(
              "Conta de Origem",
              [c for c in st.session_state.contas if c != cartao_sel],
          )
        with p2:
          val_pag = st.number_input(
              "Valor (R$)", min_value=0.0, step=10.0, format="%.2f"
          )
        with p3:
          data_pag = st.date_input("Data do Pagamento")
        if st.form_submit_button("✅ Registrar Pagamento", use_container_width=True):
          if val_pag <= 0:
            st.error("O valor deve ser maior que zero.")
          else:
            novo = pd.DataFrame(
                [[
                    "Transferência",
                    origem,
                    cartao_sel,
                    "Pagamento de Fatura",
                    f"Pagamento Fatura {cartao_sel}",
                    val_pag,
                    data_pag,
                    "Única",
                    "Integral",
                    "Efetivado",
                    "Efetivado",
                ]],
                columns=COLUNAS_LANC,
            )
            st.session_state.lancamentos = pd.concat(
                [st.session_state.lancamentos, novo], ignore_index=True
            )
            sincronizar_budget_cartao(cartao_sel)
            st.success(
                "Pagamento registrado! Faturas quitadas viraram 'Efetivado'"
                " automaticamente."
            )
            st.rerun()

      st.markdown("---")
      st.markdown(f"### Lançamentos do Cartão: **{cartao_sel}**")
      if not df_cartao.empty:
        st.dataframe(df_cartao, use_container_width=True)
      else:
        st.info("Nenhum lançamento para este cartão.")


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
                st.session_state.lancamentos = garantir_colunas(pd.read_csv(f))

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
            st.session_state.lancamentos = garantir_colunas(
                pd.DataFrame(conteudo["lancamentos"])
            )
          if "categorias" in conteudo:
            st.session_state.categorias = conteudo["categorias"]
          if "contas" in conteudo:
            st.session_state.contas = conteudo["contas"]
          if "cartoes" in conteudo:
            st.session_state.cartoes = conteudo["cartoes"]
          st.success("Backup JSON importado e restaurado com sucesso!")

        elif extensao == "csv":
          df_importado = garantir_colunas(pd.read_csv(arquivo_subido))
          st.session_state.lancamentos = pd.concat(
              [st.session_state.lancamentos, df_importado], ignore_index=True
          )
          st.success("Lançamentos do CSV adicionados com sucesso!")

        elif extensao in ["xlsx", "xls"]:
          df_importado = garantir_colunas(pd.read_excel(arquivo_subido))
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
            st.session_state.lancamentos = garantir_colunas(
                pd.DataFrame(dados_locais["lancamentos"])
            )
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
