"""Página 4 — Fatores socioeconômicos: renda, acesso à internet e correlação estatística."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from utils.carga import obter_base
from utils.dados import (
    COLUNAS_NUMERICAS,
    ROTULOS,
    correlacao_com_significancia,
    correlacoes,
    interpretar_correlacao,
)
from utils.filtros import filtros_sidebar, resumo_filtros
from utils.graficos import CORES_REDE, dispersao_plotly, dispersao_seaborn, heatmap_correlacao
from utils.interface import aviso_vazio, cabecalho, configurar_pagina, interpretacao, rodape

configurar_pagina("Fatores Socioeconômicos", "💰")
base = obter_base()
df = filtros_sidebar(base)

cabecalho(
    "Fatores socioeconômicos e correlação",
    "Existe relação entre renda e desempenho? Como o acesso à internet impacta o aprendizado? "
    "Dispersões com linha de tendência, análise por faixas e matriz de correlação de Pearson com teste de significância.",
    "💰",
)
st.caption(f"Seleção atual: **{resumo_filtros()}**")

if df.empty or len(df) < 3:
    aviso_vazio()
    st.stop()

# --------------------------------------------------------------------------- #
# Dispersões
# --------------------------------------------------------------------------- #
col_x, col_y, col_c = st.columns(3)
x = col_x.selectbox("Eixo X (fator)", ["renda_media_familiar", "acesso_internet", "indice_desempenho", "taxa_aprovacao"], format_func=lambda m: ROTULOS[m])
y = col_y.selectbox("Eixo Y (resultado)", ["media_notas", "indice_desempenho", "taxa_aprovacao", "taxa_reprovacao"], format_func=lambda m: ROTULOS[m])
cor = col_c.selectbox("Cor", ["rede_ensino", "regiao", "nivel_desempenho"], format_func=lambda m: ROTULOS[m])

estat = correlacao_com_significancia(df, x, y)
st.plotly_chart(dispersao_plotly(df, x, y, cor, f"{ROTULOS[x]} × {ROTULOS[y]}"), width="stretch")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Correlação de Pearson (r)", f"{estat['r']:.3f}")
m2.metric("Coeficiente de determinação (r²)", f"{estat['r'] ** 2:.3f}")
m3.metric("Estatística t", f"{estat['t']:.2f}")
m4.metric("p-valor (aprox.)", f"{estat['p_aprox']:.4f}", "significativo" if estat["p_aprox"] < 0.05 else "não significativo", delta_color="off")

with st.expander("📊 Versão estática com regressão linear (Seaborn)"):
    st.pyplot(dispersao_seaborn(df, x, y, "rede_ensino" if cor == "nivel_desempenho" else cor, f"{ROTULOS[x]} × {ROTULOS[y]} — regressão linear"), width="stretch")

# --------------------------------------------------------------------------- #
# Análise por faixas (renda em quartis, internet em faixas)
# --------------------------------------------------------------------------- #
st.markdown("### Desempenho por faixa de renda e de acesso à internet")
c3, c4 = st.columns(2)
with c3:
    por_renda = df.groupby(["faixa_renda", "rede_ensino"], observed=True)[y].mean().reset_index()
    fig = px.bar(por_renda, x="faixa_renda", y=y, color="rede_ensino", barmode="group", color_discrete_map=CORES_REDE, labels=ROTULOS, text=por_renda[y].round(1))
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_layout(template="plotly_white", height=380, title=dict(text=f"{ROTULOS[y]} por quartil de renda", x=0.01, y=0.98, yref="container", yanchor="top"), margin=dict(l=20, r=20, t=95, b=20), legend=dict(orientation="h", y=1.0, yanchor="bottom", x=1, xanchor="right", title_text=""))
    st.plotly_chart(fig, width="stretch")
with c4:
    por_net = df.groupby(["faixa_internet", "rede_ensino"], observed=True)[y].mean().reset_index()
    fig = px.bar(por_net, x="faixa_internet", y=y, color="rede_ensino", barmode="group", color_discrete_map=CORES_REDE, labels=ROTULOS, text=por_net[y].round(1))
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_layout(template="plotly_white", height=380, title=dict(text=f"{ROTULOS[y]} por faixa de acesso à internet", x=0.01, y=0.98, yref="container", yanchor="top"), margin=dict(l=20, r=20, t=95, b=20), legend=dict(orientation="h", y=1.0, yanchor="bottom", x=1, xanchor="right", title_text=""))
    st.plotly_chart(fig, width="stretch")

# --------------------------------------------------------------------------- #
# Matriz de correlação
# --------------------------------------------------------------------------- #
st.markdown("### Matriz de correlação")
matriz = correlacoes(df)
c5, c6 = st.columns([1, 1])
with c5:
    st.pyplot(heatmap_correlacao(matriz), width="stretch")
with c6:
    pares = (
        matriz.where(np.triu(np.ones(matriz.shape, dtype=bool), k=1))
        .stack()
        .reset_index()
        .rename(columns={"level_0": "Variável A", "level_1": "Variável B", 0: "r"})
    )
    pares["|r|"] = pares["r"].abs()
    pares["Força"] = pares["r"].apply(interpretar_correlacao)
    pares = pares.sort_values("|r|", ascending=False)
    pares["Variável A"] = pares["Variável A"].map(ROTULOS)
    pares["Variável B"] = pares["Variável B"].map(ROTULOS)
    st.markdown("**Pares ordenados pela força da correlação**")
    st.dataframe(pares[["Variável A", "Variável B", "r", "Força"]].style.format({"r": "{:+.3f}"}).background_gradient(subset=["r"], cmap="RdBu_r", vmin=-1, vmax=1), width="stretch", hide_index=True)

# --------------------------------------------------------------------------- #
# Interpretação
# --------------------------------------------------------------------------- #
r_renda = correlacao_com_significancia(df, "renda_media_familiar", "media_notas")
r_net = correlacao_com_significancia(df, "acesso_internet", "media_notas")
r_apr = correlacao_com_significancia(df, "taxa_aprovacao", "media_notas")
q = df.groupby("faixa_renda", observed=True)["media_notas"].mean()
dif_q = q.iloc[-1] - q.iloc[0] if len(q) >= 2 else np.nan
par_forte = pares.iloc[0]

interpretacao(
    f"""
    <ul>
      <li><strong>Renda × notas:</strong> r = {r_renda['r']:+.3f}, correlação {interpretar_correlacao(r_renda['r'])}
          (p ≈ {r_renda['p_aprox']:.3f}). Alunos do quartil de maior renda têm nota média {dif_q:+.1f} ponto(s) em relação ao de menor renda.</li>
      <li><strong>Internet × notas:</strong> r = {r_net['r']:+.3f}, correlação {interpretar_correlacao(r_net['r'])}
          (p ≈ {r_net['p_aprox']:.3f}).</li>
      <li><strong>Aprovação × notas:</strong> r = {r_apr['r']:+.3f} — {"as taxas de aprovação acompanham as notas." if abs(r_apr['r']) >= 0.3 else "nesta base, aprovação e nota são praticamente independentes, o que é um alerta sobre a consistência dos indicadores."}</li>
      <li>O par mais correlacionado é <strong>{par_forte['Variável A']} × {par_forte['Variável B']}</strong> (r = {par_forte['r']:+.3f}).</li>
      <li><strong>Leitura analítica:</strong> em dados reais, renda e acesso digital costumam apresentar correlação positiva
          moderada com desempenho. Aqui, as correlações são {interpretar_correlacao(max(r_renda['r'], r_net['r'], key=abs))},
          o que indica que a base simulada gera os fatores de forma quase independente dos resultados. Correlação não implica causalidade;
          um estudo real exigiria controle por outras variáveis (infraestrutura escolar, formação docente, escolaridade dos pais).</li>
    </ul>
    """
)

with st.expander("📋 Estatísticas descritivas das variáveis numéricas"):
    st.dataframe(df[COLUNAS_NUMERICAS].describe().T.rename(index=ROTULOS).style.format("{:.2f}"), width="stretch")

rodape()
