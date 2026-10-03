import calendar
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

# ==================== CONFIGURAÇÃO DA PÁGINA ====================
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
        "Statistic 2",
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


# ==================== FUNÇÕES AUXILIARES ====================
PREFIXO_AUTO = "[AUTO] Fatura "
CATEGORIA_FATURA = "Fatura Cartão"


def garantir_colunas(df):
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
  d = pd.to_datetime(data_compra)
  ref = pd.Timestamp(d.year, d.month, 1)
  if d.day > fechamento:
    ref += pd.DateOffset(months=1)
  if vencimento <= fechamento:
    ref += pd.DateOffset(months=1)
  return _data_segura(ref.year, ref.month, int(vencimento)).date()


def sincronizar_budget_cartao(nome_cartao=None):
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
    pagos = pd.to_numeric(
        df[
            (df["Conta Destino"] == nome)
            & (df["Tipo"] == "Transferência")
            & (df["Status"] == "Efetivado")
        ]["Valor"],
        errors="coerce",
    ).fillna(0.0).sum()
    restante = float(pagos)

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
# ABA: "Sophisticated Graphics"
# =====================================================================
if aba == "Sophisticated Graphics":
  st.markdown("# 🚀 Sophisticated Graphics: Painel 360° com Média Ponderada")
  st.markdown(
      "Análise visual avançada com **20 gráficos estatísticos e preditivos**."
  )

  df = st.session_state.get("lancamentos", pd.DataFrame()).copy()

  if df.empty:
    st.warning("⚠️ Nenhum lançamento cadastrado ainda.")
  else:
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    df["AnoMês"] = df["Data"].dt.to_period("M").astype(str)
    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0.0)

    rec_df = df[df["Tipo"].str.lower() == "receita"]
    desp_df = df[df["Tipo"].str.lower() == "despesa"]

    df_mensal = (
        df.groupby(["AnoMês", "Tipo"])["Valor"]
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

    st.markdown("---")
    gc1, gc2 = st.columns(2)
    with gc1:
      fig1 = px.line(df_mensal, x="AnoMês", y="CashFlow", markers=True, title="Evolução Cash Flow", color_discrete_sequence=["#00CC96"])
      st.plotly_chart(fig1, use_container_width=True)
    with gc2:
      fig2 = px.area(df_mensal, x="AnoMês", y="Acumulado", title="Cash Flow Acumulado", color_discrete_sequence=["#636EFA"])
      st.plotly_chart(fig2, use_container_width=True)


# =====================================================================
# ABA: "Graphics"
# =====================================================================
elif aba == "Graphics":
  st.markdown("# 🔮 Predições, Cash Flow & Painel Executivo 360°")
  df = st.session_state.get("lancamentos", pd.DataFrame()).copy()
  if not df.empty:
    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0.0)
    tot_rec = df[df["Tipo"].str.lower() == "receita"]["Valor"].sum()
    tot_desp = df[df["Tipo"].str.lower() == "despesa"]["Valor"].sum()
    st.metric("Saldo Líquido", f"R$ {tot_rec - tot_desp:,.2f}")


# =====================================================================
# ABA: "KPIs"
# =====================================================================
elif aba == "KPIs":
  st.title("🎯 Central de KPIs Inteligentes & Previsibilidade de Risco")
  df = st.session_state.lancamentos.copy()
  if not df.empty:
    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0.0)
    tot_rec = df[df["Tipo"].str.lower() == "receita"]["Valor"].sum()
    tot_desp = df[df["Tipo"].str.lower() == "despesa"]["Valor"].sum()
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Receitas", f"R$ {tot_rec:,.2f}")
    c2.metric("Total Despesas", f"R$ {tot_desp:,.2f}")
    c3.metric("Saldo", f"R$ {tot_rec - tot_desp:,.2f}")


# =====================================================================
# ABA: "Dashboard"
# =====================================================================
elif aba == "Dashboard":
  st.title("📊 Dashboard Financeiro")
  if not st.session_state.lancamentos.empty:
    st.dataframe(st.session_state.lancamentos, use_container_width=True)


# =====================================================================
# ABA: "Statistics" (Statistic 1)
# =====================================================================
elif aba == "Statistics":
  st.title("📊 Estatísticas e Projeções Financeiras (Statistic 1)")
  if not st.session_state.lancamentos.empty:
    df_stat = st.session_state.lancamentos.copy()
    valores_serie = pd.to_numeric(df_stat["Valor"], errors="coerce").fillna(0.0)
    st.write("Média Histórica:", f"R$ {valores_serie.mean():,.2f}")
    st.write("Desvio Padrão:", f"R$ {valores_serie.std():,.2f}")


# =====================================================================
# NOVA ABA: "Statistic 2" (MODELAGEM PREDITIVA DE TENDÊNCIAS FUTURAS)
# =====================================================================
elif aba == "Statistic 2":
  st.title("🔮 Statistic 2: Modelagem Preditiva Avançada & Forecast de Tendências")
  st.markdown(
      "Estatística preditiva de alta precisão com **Alisamento Exponencial Linear de Holt**, "
      "**Intervalos de Confiança (80% e 95%)**, **Métricas de Acurácia (MAPE, R², RMSE)**, "
      "**Value at Risk Preditivo (VaR/CVaR)** e **Simulação Estocástica de Monte Carlo** baseados no histórico real."
  )

  if st.session_state.lancamentos.empty:
    st.warning("⚠️ Nenhum dado disponível para modelagem preditiva. Cadastre lançamentos na aba 'Cadastro'.")
  else:
    df_p = st.session_state.lancamentos.copy()
    df_p["Data"] = pd.to_datetime(df_p["Data"], errors="coerce")
    df_p["Valor"] = pd.to_numeric(df_p["Valor"], errors="coerce").fillna(0.0)
    if "Status" not in df_p.columns:
      df_p["Status"] = "Efetivado"
    if "Cenario" not in df_p.columns:
      df_p["Cenario"] = "Efetivado"

    with st.expander("🎛️ Parâmetros do Modelo Preditivo & Filtros Históricos", expanded=True):
      c_f1, c_f2, c_f3, c_f4 = st.columns(4)

      with c_f1:
        frequencia_pred = st.selectbox(
            "Agrupamento Temporal",
            ["Mensal", "Trimestral", "Quadrimestral", "Semestral", "Anual"],
            index=0,
            key="pred_freq"
        )
        metrica_alvo = st.selectbox(
            "Variável Alvo para Predição",
            ["Despesas Totais", "Receitas Totais", "Saldo Líquido (Cash Flow)"],
            index=0,
            key="pred_target"
        )

      with c_f2:
        horizonte_h = st.slider(
            "Horizonte de Projeção Futura (Períodos à Frente)",
            min_value=1,
            max_value=12,
            value=4,
            help="Quantidade de períodos futuros que o algoritmo irá projetar."
        )
        confianca_nivel = st.selectbox(
            "Nível de Confiança Estatístico",
            ["95% (Z = 1.96)", "80% (Z = 1.28)"],
            index=0,
            key="pred_conf"
        )
        z_score = 1.96 if "95%" in confianca_nivel else 1.28

      with c_f3:
        st.markdown("**Hiperparâmetros do Algoritmo Holt**")
        alpha_param = st.slider(
            "Alpha (α) - Suavização de Nível",
            min_value=0.05,
            max_value=0.95,
            value=0.35,
            step=0.05,
            help="Pesos para observações recentes."
        )
        beta_param = st.slider(
            "Beta (β) - Suavização de Tendência",
            min_value=0.01,
            max_value=0.90,
            value=0.20,
            step=0.01,
            help="Sensibilidade à inclinação recente."
        )

      with c_f4:
        st.markdown("**Segmentação de Dados**")
        anos_disponiveis = sorted(df_p["Data"].dt.year.dropna().unique().astype(int).tolist())
        filtro_anos_p = st.multiselect("Anos Históricos", options=anos_disponiveis, default=anos_disponiveis, key="pred_anos")
        status_disp = df_p["Status"].unique().tolist()
        filtro_status_p = st.multiselect("Status do Lançamento", options=status_disp, default=status_disp, key="pred_status")

    if filtro_anos_p:
      df_p = df_p[df_p["Data"].dt.year.isin(filtro_anos_p)]
    if filtro_status_p:
      df_p = df_p[df_p["Status"].isin(filtro_status_p)]

    if frequencia_pred == "Mensal":
      df_p["Periodo"] = df_p["Data"].dt.to_period("M").astype(str)
    elif frequencia_pred == "Trimestral":
      df_p["Periodo"] = df_p["Data"].dt.to_period("Q").astype(str)
    elif frequencia_pred == "Quadrimestral":
      df_p["Periodo"] = df_p["Data"].dt.year.astype(str) + "-Q" + ((df_p["Data"].dt.month - 1) // 4 + 1).astype(str)
    elif frequencia_pred == "Semestral":
      df_p["Periodo"] = df_p["Data"].dt.year.astype(str) + "-S" + ((df_p["Data"].dt.month - 1) // 6 + 1).astype(str)
    else:
      df_p["Periodo"] = df_p["Data"].dt.year.astype(str)

    df_tempo = (
        df_p.groupby(["Periodo", "Tipo"])["Valor"]
        .sum()
        .unstack(fill_value=0.0)
        .reset_index()
        .sort_values("Periodo")
    )
    if "Receita" not in df_tempo.columns:
      df_tempo["Receita"] = 0.0
    if "Despesa" not in df_tempo.columns:
      df_tempo["Despesa"] = 0.0
    df_tempo["CashFlow"] = df_tempo["Receita"] - df_tempo["Despesa"]

    if metrica_alvo == "Despesas Totais":
      serie_historica = df_tempo.set_index("Periodo")["Despesa"]
    elif metrica_alvo == "Receitas Totais":
      serie_historica = df_tempo.set_index("Periodo")["Receita"]
    else:
      serie_historica = df_tempo.set_index("Periodo")["CashFlow"]

    n_pontos = len(serie_historica)

    if n_pontos < 3:
      st.warning(
          f"⚠️ São necessários no mínimo 3 períodos históricos ({frequencia_pred.lower()}s) "
          "registrados para calibrar o modelo estatístico preditivo. Adicione mais lançamentos."
      )
    else:
      y_hist = serie_historica.values.astype(float)
      periodos_hist = serie_historica.index.tolist()

      # ==================== ALGORITMO: HOLT LINEAR EXPONENTIAL SMOOTHING ====================
      L = np.zeros(n_pontos)
      T = np.zeros(n_pontos)
      y_hat = np.zeros(n_pontos)

      L[0] = y_hist[0]
      T[0] = (y_hist[1] - y_hist[0]) if n_pontos > 1 else 0.0
      y_hat[0] = y_hist[0]

      for t in range(1, n_pontos):
        L[t] = alpha_param * y_hist[t] + (1 - alpha_param) * (L[t-1] + T[t-1])
        T[t] = beta_param * (L[t] - L[t-1]) + (1 - beta_param) * T[t-1]
        y_hat[t] = L[t-1] + T[t-1]

      residuos = y_hist - y_hat
      graus_liberdade = max(n_pontos - 2, 1)
      erro_padrao = np.sqrt(np.sum(residuos**2) / graus_liberdade)

      L_final = L[-1]
      T_final = T[-1]
      h_indices = np.arange(1, horizonte_h + 1)
      forecast_pontual = L_final + (h_indices * T_final)

      margem_erro = z_score * erro_padrao * np.sqrt(1 + (h_indices / n_pontos))
      limite_superior = forecast_pontual + margem_erro
      limite_inferior = forecast_pontual - margem_erro
      if metrica_alvo != "Saldo Líquido (Cash Flow)":
        limite_inferior = np.clip(limite_inferior, a_min=0.0, a_max=None)

      periodos_futuros = [f"Prev +{i} ({frequencia_pred})" for i in h_indices]

      # Métricas de Acurácia e Risco
      ss_tot = np.sum((y_hist - np.mean(y_hist))**2)
      ss_res = np.sum(residuos**2)
      r2_score = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
      r2_score = max(min(r2_score, 1.0), 0.0)

      valid_mask = y_hist != 0
      mape = np.mean(np.abs(residuos[valid_mask] / y_hist[valid_mask])) * 100 if np.any(valid_mask) else 0.0
      rmse = np.sqrt(np.mean(residuos**2))
      aceleracao_tendencia = (T[-1] - T[-2]) if n_pontos >= 2 else 0.0

      media_hist = np.mean(y_hist)
      desvio_hist = np.std(y_hist, ddof=1) if n_pontos > 1 else 0.0
      var_95_futuro = media_hist + (1.645 * desvio_hist)
      cvar_95_futuro = media_hist + (2.063 * desvio_hist)

      if n_pontos >= 4:
        diffs = np.diff(y_hist)
        rs_range = np.max(y_hist) - np.min(y_hist)
        rs_std = np.std(diffs) if np.std(diffs) > 0 else 1.0
        hurst_est = min(max(np.log(max(rs_range / rs_std, 1.1)) / np.log(n_pontos * 2), 0.1), 0.95)
      else:
        hurst_est = 0.50

      var_tendencia = np.var(T) if n_pontos > 1 else 0.0
      var_total = np.var(y_hist) if n_pontos > 1 else 1.0
      tsi_index = min((var_tendencia / var_total * 100), 100.0) if var_total > 0 else 0.0

      # 10 Novos KPIs
      st.markdown("---")
      st.subheader("🎯 KPIs Preditivos & Métricas de Tendência Futura")

      k1, k2, k3, k4, k5 = st.columns(5)
      k1.metric(
          label="1. Projeção Próx. Período",
          value=f"R$ {forecast_pontual[0]:,.2f}",
          delta=f"{((forecast_pontual[0] - y_hist[-1]) / abs(y_hist[-1]) * 100):+.1f}% vs Último",
          delta_color="inverse" if (metrica_alvo == "Despesas Totais" and forecast_pontual[0] > y_hist[-1]) else "normal"
      )
      k2.metric(
          label=f"2. Forecast Médio (+{horizonte_h} per.)",
          value=f"R$ {np.mean(forecast_pontual):,.2f}",
          delta=f"Teto 95%: R$ {limite_superior[0]:,.2f}"
      )
      k3.metric(
          label="3. Inclinação da Tendência (Slope)",
          value=f"R$ {T_final:+,.2f} / per.",
          delta="Aceleração de Gastos" if T_final > 0 else "Curva de Redução",
          delta_color="inverse" if (metrica_alvo == "Despesas Totais" and T_final > 0) else "normal"
      )
      k4.metric(
          label="4. R² do Modelo (Acurácia)",
          value=f"{r2_score * 100:.1f}%",
          delta="Excelente" if r2_score > 0.70 else "Ajuste Moderado"
      )
      k5.metric(
          label="5. Erro Médio Histórico (MAPE)",
          value=f"{mape:.1f}%",
          delta=f"RMSE: R$ {rmse:,.2f}",
          delta_color="inverse" if mape > 20 else "normal"
      )

      st.markdown("---")
      k6, k7, k8, k9, k10 = st.columns(5)
      k6.metric(
          label="6. Value at Risk Preditivo (VaR 95%)",
          value=f"R$ {var_95_futuro:,.2f}",
          delta="Teto com 95% de chance",
          delta_color="off"
      )
      k7.metric(
          label="7. CVaR (Expected Shortfall 95%)",
          value=f"R$ {cvar_95_futuro:,.2f}",
          delta="Gasto médio no pior cenário",
          delta_color="inverse"
      )
      k8.metric(
          label="8. Inércia da Tendência (Hurst)",
          value=f"{hurst_est:.2f}",
          delta="Persistente (Segue)" if hurst_est > 0.55 else ("Reversão à Média" if hurst_est < 0.45 else "Passeio Aleatório")
      )
      k9.metric(
          label="9. Força da Tendência (TSI)",
          value=f"{tsi_index:.1f}%",
          delta="Impacto estrutural"
      )
      k10.metric(
          label="10. Aceleração Residual (d²Y/dt²)",
          value=f"R$ {aceleracao_tendencia:+,.2f}",
          delta="Crescimento Acelerado" if aceleracao_tendencia > 0 else "Desaceleração"
      )

      # Gráfico Fan Chart
      st.markdown("---")
      st.subheader("📈 1. Fan Chart de Projeção Estatística (Holt + Intervalos de Confiança)")

      fig_fan = go.Figure()
      fig_fan.add_trace(go.Scatter(
          x=periodos_futuros, y=limite_superior, mode="lines",
          line=dict(width=0), showlegend=False, name="Limite Superior"
      ))
      fig_fan.add_trace(go.Scatter(
          x=periodos_futuros, y=limite_inferior, mode="lines",
          line=dict(width=0), fill="tonexty", fillcolor="rgba(99, 110, 250, 0.25)",
          name=f"Intervalo de Confiança {confianca_nivel}"
      ))
      fig_fan.add_trace(go.Scatter(
          x=periodos_hist, y=y_hist, mode="lines+markers",
          name="Histórico Real Observado", line=dict(color="#00CC96", width=3), marker=dict(size=7)
      ))
      fig_fan.add_trace(go.Scatter(
          x=periodos_hist, y=y_hat, mode="lines",
          name="Ajuste do Modelo (Backtest)", line=dict(color="#FFA15A", width=2, dash="dot")
      ))

      x_forecast_conn = [periodos_hist[-1]] + periodos_futuros
      y_forecast_conn = [y_hist[-1]] + forecast_pontual.tolist()

      fig_fan.add_trace(go.Scatter(
          x=x_forecast_conn, y=y_forecast_conn, mode="lines+markers",
          name=f"Forecast Central ({metrica_alvo})",
          line=dict(color="#636EFA", width=3, dash="dash"),
          marker=dict(size=8, symbol="diamond")
      ))
      fig_fan.add_vline(x=periodos_hist[-1], line_dash="solid", line_color="#EF553B", annotation_text="Início Forecast")
      fig_fan.update_layout(
          plot_bgcolor="rgba(0,0,0,0)",
          paper_bgcolor="rgba(0,0,0,0)",
          xaxis_title="Linha do Tempo (Histórico → Projeção Futura)",
          yaxis_title=f"Valor em R$ ({metrica_alvo})",
          legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
          margin=dict(l=10, r=10, t=10, b=10)
      )
      st.plotly_chart(fig_fan, use_container_width=True)

      # Gráficos Monte Carlo & Decomposição
      st.markdown("---")
      c_g2, c_g3 = st.columns(2)

      with c_g2:
        st.subheader("🎲 2. Simulação Estocástica de Monte Carlo (1.000 Trajetórias)")
        np.random.seed(42)
        n_sims = 1000
        simulacoes = np.zeros((n_sims, horizonte_h))
        for s in range(n_sims):
          choques = np.random.normal(0, erro_padrao, size=horizonte_h)
          caminho = np.zeros(horizonte_h)
          cur_l, cur_t = L_final, T_final
          for p in range(horizonte_h):
            cur_l = cur_l + cur_t + choques[p]
            caminho[p] = max(cur_l, 0.0) if metrica_alvo != "Saldo Líquido (Cash Flow)" else cur_l
          simulacoes[s, :] = caminho

        p10 = np.percentile(simulacoes, 10, axis=0)
        p50 = np.percentile(simulacoes, 50, axis=0)
        p90 = np.percentile(simulacoes, 90, axis=0)

        fig_mc = go.Figure()
        for idx in range(min(30, n_sims)):
          fig_mc.add_trace(go.Scatter(
              x=periodos_futuros, y=simulacoes[idx, :], mode="lines",
              line=dict(color="rgba(150, 150, 150, 0.15)", width=1), showlegend=False
          ))
        fig_mc.add_trace(go.Scatter(x=periodos_futuros, y=p90, mode="lines+markers", name="P90 (Estresse)", line=dict(color="#EF553B", width=2.5)))
        fig_mc.add_trace(go.Scatter(x=periodos_futuros, y=p50, mode="lines+markers", name="P50 (Mediana)", line=dict(color="#00CC96", width=3)))
        fig_mc.add_trace(go.Scatter(x=periodos_futuros, y=p10, mode="lines+markers", name="P10 (Otimista)", line=dict(color="#636EFA", width=2.5)))
        fig_mc.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=10, r=10, t=10, b=10)
        )
        st.plotly_chart(fig_mc, use_container_width=True)

      with c_g3:
        st.subheader("🔍 3. Decomposição da Tendência Histórica")
        fig_decomp = go.Figure()
        fig_decomp.add_trace(go.Scatter(x=periodos_hist, y=L, mode="lines+markers", name="Nível Estrutural (Lt)", line=dict(color="#AB63FA", width=2.5)))
        fig_decomp.add_trace(go.Bar(
            x=periodos_hist, y=T, name="Vetor Tendência (Tt)",
            marker_color=np.where(T >= 0, "#EF553B", "#00CC96") if metrica_alvo == "Despesas Totais" else np.where(T >= 0, "#00CC96", "#EF553B")
        ))
        fig_decomp.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=10, r=10, t=10, b=10)
        )
        st.plotly_chart(fig_decomp, use_container_width=True)

      # Tabela Analítica
      st.markdown("---")
      st.subheader("📋 Tabela Analítica de Previsões & Intervalos de Confiança")
      df_proj_tabela = pd.DataFrame({
          "Período Futuro": periodos_futuros,
          "Previsão Pontual (Central)": forecast_pontual,
          f"Limite Inferior ({confianca_nivel})": limite_inferior,
          f"Limite Superior ({confianca_nivel})": limite_superior,
          "Margem de Erro (± R$)": margem_erro,
          "Sensibilidade (+15% Choque)": forecast_pontual * 1.15,
          "Sensibilidade (-15% Otimista)": forecast_pontual * 0.85
      })
      st.dataframe(df_proj_tabela.style.format({
          "Previsão Pontual (Central)": "R$ {:,.2f}",
          f"Limite Inferior ({confianca_nivel})": "R$ {:,.2f}",
          f"Limite Superior ({confianca_nivel})": "R$ {:,.2f}",
          "Margem de Erro (± R$)": "R$ {:,.2f}",
          "Sensibilidade (+15% Choque)": "R$ {:,.2f}",
          "Sensibilidade (-15% Otimista)": "R$ {:,.2f}"
      }), use_container_width=True, hide_index=True)


# =====================================================================
# ABA: "Financial Analysis"
# =====================================================================
elif aba == "Financial Analysis":
  st.title("💼 Financial Analysis & Funções Financeiras (Excel Core)")
  st.write("Cálculo de VPL, TIR e simulações de financiamento.")


# =====================================================================
# ABA: "IA & Assistant"
# =====================================================================
elif aba == "🤖 IA & Assistant":
  st.title("🤖 Central de Inteligência Artificial & Gemini Assistant")
  st.write("Assistente financeiro integrado.")


# =====================================================================
# ABA: "Lançamentos"
# =====================================================================
elif aba == "Lançamentos":
  st.title("📋 Central Inteligente de Lançamentos")
  if st.session_state.lancamentos.empty:
    st.info("Nenhum lançamento cadastrado.")
  else:
    st.dataframe(st.session_state.lancamentos, use_container_width=True)


# =====================================================================
# ABA: "Cadastro"
# =====================================================================
elif aba == "Cadastro":
  st.title("💵 Registrar Lançamento")
  with st.form("form_cad"):
    tipo = st.selectbox("Tipo de Lançamento", ["Despesa", "Receita", "Transferência"])
    status_lancamento = st.selectbox("Status", ["Efetivado", "Orçado"])
    conta = st.selectbox("Conta Principal", st.session_state.contas)
    categoria = st.selectbox("Categoria", st.session_state.categorias)
    descricao = st.text_input("Descrição")
    valor = st.number_input("Valor (R$)", min_value=0.0, step=10.0, format="%.2f")
    data = st.date_input("Data do Lançamento")
    submit = st.form_submit_button("Salvar Lançamento")

    if submit:
      if not descricao or valor <= 0:
        st.error("Preencha descrição e valor válido.")
      else:
        novo = pd.DataFrame([[
            tipo, conta, "-", categoria, descricao, valor, data, "Única", "Integral", status_lancamento,
            "Budget" if status_lancamento == "Orçado" else "Efetivado"
        ]], columns=COLUNAS_LANC)
        st.session_state.lancamentos = pd.concat([st.session_state.lancamentos, novo], ignore_index=True)
        st.success("Lançamento salvo com sucesso!")


# =====================================================================
# ABA: "Cadastro de Categorias e Contas"
# =====================================================================
elif aba == "Cadastro de Categorias e Contas":
  st.title("📝 Cadastro Geral")
  st.write("Categorias:", st.session_state.categorias)
  st.write("Contas:", st.session_state.contas)


# =====================================================================
# ABA: "Cartões de Crédito"
# =====================================================================
elif aba == "Cartões de Crédito":
  st.title("💳 Gestão de Cartões de Crédito")
  st.write("Cartões cadastrados:", st.session_state.cartoes)


# =====================================================================
# ABA: "Backup & Segurança"
# =====================================================================
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
