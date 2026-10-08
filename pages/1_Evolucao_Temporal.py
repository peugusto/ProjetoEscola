"""Página 1 — Evolução temporal do desempenho (séries temporais avançadas)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from utils.carga import obter_base
from utils.dados import ROTULOS, matriz_heatmap, serie_temporal
from utils.filtros import filtros_sidebar, resumo_filtros
from utils.graficos import heatmap_semestral, linha_temporal
from utils.interface import aviso_vazio, cabecalho, configurar_pagina, interpretacao, rodape

configurar_pagina("Evolução Temporal", "📈")
base = obter_base()
df = filtros_sidebar(base)

cabecalho(
    "Evolução temporal do desempenho",
    "Houve melhoria no desempenho ao longo do tempo? Esta página acompanha as métricas semestre a semestre, "
    "com média móvel, variação anual e decomposição por região, rede ou nível.",
    "📈",
)
st.caption(f"Seleção atual: **{resumo_filtros()}**")

if df.empty:
    aviso_vazio()
    st.stop()

col_m, col_s, col_j = st.columns([1.2, 1, 1])
metrica = col_m.selectbox("Métrica", ["media_notas", "indice_desempenho", "taxa_aprovacao", "taxa_reprovacao", "acesso_internet"], format_func=lambda m: ROTULOS[m])
segmento = col_s.selectbox("Segmentar por", [None, "regiao", "rede_ensino", "nivel_desempenho", "disciplina"], format_func=lambda s: "Média geral" if s is None else ROTULOS[s])
janela = col_j.slider("Janela da média móvel (semestres)", 1, 6, 2)

# --------------------------------------------------------------------------- #
# Linha temporal
# --------------------------------------------------------------------------- #
serie = serie_temporal(df, metrica, segmento)
st.plotly_chart(linha_temporal(serie, metrica, segmento), width="stretch")

# --------------------------------------------------------------------------- #
# Série anual com média móvel e variação (Pandas/NumPy)
# --------------------------------------------------------------------------- #
st.markdown("### Média anual, média móvel e variação")
anual = df.groupby("ano", observed=True)[metrica].agg(["mean", "std", "count"]).reset_index()
anual.columns = ["ano", "media", "desvio", "registros"]
anual["media_movel"] = anual["media"].rolling(janela, min_periods=1).mean()
anual["variacao_abs"] = anual["media"].diff()
anual["variacao_pct"] = anual["media"].pct_change() * 100
anual["acumulado_pct"] = (anual["media"] / anual["media"].iloc[0] - 1) * 100

import plotly.graph_objects as go  # noqa: E402

fig = go.Figure()
fig.add_trace(go.Bar(x=anual["ano"], y=anual["variacao_abs"], name="Variação anual (pontos)", marker_color=np.where(anual["variacao_abs"] >= 0, "#8AB17D", "#E76F51"), yaxis="y2", opacity=0.55))
fig.add_trace(go.Scatter(x=anual["ano"], y=anual["media"], name="Média anual", mode="lines+markers", line=dict(color="#264653", width=3)))
fig.add_trace(go.Scatter(x=anual["ano"], y=anual["media_movel"], name=f"Média móvel ({janela} anos)", mode="lines", line=dict(color="#2A9D8F", dash="dash", width=2)))
fig.add_trace(
    go.Scatter(
        x=pd.concat([anual["ano"], anual["ano"][::-1]]),
        y=pd.concat([anual["media"] + anual["desvio"], (anual["media"] - anual["desvio"])[::-1]]),
        fill="toself",
        fillcolor="rgba(38,70,83,0.08)",
        line=dict(color="rgba(0,0,0,0)"),
        name="± 1 desvio-padrão",
        hoverinfo="skip",
    )
)
fig.update_layout(
    template="plotly_white",
    height=440,
    title=dict(text=f"{ROTULOS[metrica]} — média anual e variação", x=0.01, y=0.98, yref="container", yanchor="top"),
    yaxis=dict(title=ROTULOS[metrica]),
    yaxis2=dict(title="Variação (pontos)", overlaying="y", side="right", showgrid=False),
    legend=dict(orientation="h", y=1.0, yanchor="bottom", x=1, xanchor="right", title_text=""),
    margin=dict(l=20, r=20, t=95, b=20),
)
st.plotly_chart(fig, width="stretch")

# --------------------------------------------------------------------------- #
# Heatmap semestral
# --------------------------------------------------------------------------- #
st.markdown("### Heatmap semestral")
linhas = st.radio("Linhas do heatmap", ["regiao", "uf", "disciplina", "rede_ensino"], format_func=lambda c: ROTULOS[c], horizontal=True)
tabela = matriz_heatmap(df, metrica, linhas=linhas)
cmap = "YlOrRd" if metrica == "taxa_reprovacao" else "YlGnBu"
st.pyplot(heatmap_semestral(tabela, f"{ROTULOS[metrica]} por {ROTULOS[linhas].lower()} e semestre"), width="stretch")

# --------------------------------------------------------------------------- #
# Interpretação
# --------------------------------------------------------------------------- #
coef = np.polyfit(np.arange(len(anual)), anual["media"], 1)[0] if len(anual) >= 2 else 0.0
melhor_ano = anual.loc[anual["media"].idxmax()]
pior_ano = anual.loc[anual["media"].idxmin()]
pandemia = df[df["periodo_pandemia"]][metrica].mean()
fora = df[~df["periodo_pandemia"]][metrica].mean()
sem = df.groupby("semestre", observed=True)[metrica].mean()

interpretacao(
    f"""
    <ul>
      <li>A tendência linear da média anual é de <strong>{coef:+.2f} ponto(s) por ano</strong>
          ({"leve melhora" if coef > 0.1 else "leve piora" if coef < -0.1 else "praticamente estável"}),
          com variação acumulada de {anual['acumulado_pct'].iloc[-1]:+.1f}% entre {int(anual['ano'].iloc[0])} e {int(anual['ano'].iloc[-1])}.</li>
      <li>Melhor ano: <strong>{int(melhor_ano['ano'])}</strong> ({melhor_ano['media']:.1f}); pior ano:
          <strong>{int(pior_ano['ano'])}</strong> ({pior_ano['media']:.1f}).</li>
      <li>Período da pandemia (2020–2021): média {pandemia:.1f} contra {fora:.1f} nos demais anos
          ({pandemia - fora:+.1f} pontos){" — não há sinal de queda relevante nesta base." if abs(pandemia - fora) < 1 else "."}</li>
      <li>Comparação de semestres: 1º semestre {sem.get(1, np.nan):.1f} × 2º semestre {sem.get(2, np.nan):.1f}.</li>
      <li>O desvio-padrão anual (faixa sombreada) mostra que a dispersão entre municípios/disciplinas é muito maior do que
          a variação entre anos, ou seja, as desigualdades internas pesam mais do que a tendência temporal.</li>
    </ul>
    """
)

with st.expander("📋 Tabela anual"):
    st.dataframe(
        anual.rename(columns={"ano": "Ano", "media": "Média", "desvio": "Desvio-padrão", "registros": "Registros", "media_movel": "Média móvel", "variacao_abs": "Variação (pts)", "variacao_pct": "Variação (%)", "acumulado_pct": "Acumulado (%)"}).style.format({"Média": "{:.2f}", "Desvio-padrão": "{:.2f}", "Média móvel": "{:.2f}", "Variação (pts)": "{:+.2f}", "Variação (%)": "{:+.2f}", "Acumulado (%)": "{:+.2f}"}, na_rep="—"),
        width="stretch",
        hide_index=True,
    )

rodape()
