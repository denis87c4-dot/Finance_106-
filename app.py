import io
import json
import zipfile
import calendar
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
        "Sophisticated Graphics",
        "Graphics",
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
        vf_ca
