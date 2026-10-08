"""Página 2 — Comparação regional e por estado, com mapa interativo (Plotly)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from utils.carga import estados_ibge, geojson_uf, obter_base
from utils.dados import ORDEM_REGIAO, ROTULOS, ranking_uf
from utils.filtros import filtros_sidebar, resumo_filtros
from utils.graficos import barras_categoria, barras_ranking, boxplot, mapa_brasil
from utils.interface import aviso_vazio, cabecalho, configurar_pagina, interpretacao, rodape

configurar_pagina("Comparação Regional", "🗺️")
base = obter_base()
df = filtros_sidebar(base)

cabecalho(
    "Comparação regional e por estado",
    "Quais estados apresentam melhor desempenho? Existem desigualdades regionais relevantes? "
    "Mapa coroplético, ranking de estados e distribuição por região.",
    "🗺️",
)
st.caption(f"Seleção atual: **{resumo_filtros()}**")

if df.empty:
    aviso_vazio()
    st.stop()

metrica = st.selectbox("Métrica", ["indice_desempenho", "media_notas", "taxa_aprovacao", "taxa_reprovacao", "acesso_internet", "renda_media_familiar"], format_func=lambda m: ROTULOS[m])

# --------------------------------------------------------------------------- #
# Integração com a API do IBGE (nomes oficiais) + GeoJSON para o mapa
# --------------------------------------------------------------------------- #
estados, origem = estados_ibge()
rank = ranking_uf(df, metrica)
rank["nome_uf"] = rank["uf"].map(lambda s: estados.get(s, {}).get("nome", s))
geo = geojson_uf()

col_mapa, col_rank = st.columns([1.15, 1])
with col_mapa:
    st.plotly_chart(mapa_brasil(rank, metrica, geo, f"Mapa — {ROTULOS[metrica].lower()} por estado"), width="stretch")
    st.caption(
        f"Nomes dos estados via **{origem}** (API de Localidades do IBGE, Requests). "
        + ("Contornos: GeoJSON das UFs." if geo else "Contornos indisponíveis offline — exibindo capitais como pontos.")
    )
with col_rank:
    st.plotly_chart(barras_ranking(rank, metrica, f"Ranking de estados — {ROTULOS[metrica].lower()}"), width="stretch")

# --------------------------------------------------------------------------- #
# Regiões
# --------------------------------------------------------------------------- #
st.markdown("### Regiões")
c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(barras_categoria(df, "regiao", metrica, f"{ROTULOS[metrica]} por região e rede", cor="rede_ensino", ordenar=False), width="stretch")
with c2:
    st.plotly_chart(boxplot(df, "regiao", metrica, f"Distribuição de {ROTULOS[metrica].lower()} por região"), width="stretch")

# --------------------------------------------------------------------------- #
# Desigualdade: coeficiente de variação e amplitude dentro das regiões
# --------------------------------------------------------------------------- #
st.markdown("### Medidas de desigualdade")
desig = (
    df.groupby("regiao", observed=True)[metrica]
    .agg(media="mean", mediana="median", desvio="std", minimo="min", maximo="max", registros="size")
    .reset_index()
)
desig["coef_variacao_pct"] = desig["desvio"] / desig["media"] * 100
desig["amplitude"] = desig["maximo"] - desig["minimo"]
desig = desig.sort_values("media", ascending=False)
st.dataframe(
    desig.rename(columns={"regiao": "Região", "media": "Média", "mediana": "Mediana", "desvio": "Desvio-padrão", "minimo": "Mínimo", "maximo": "Máximo", "registros": "Registros", "coef_variacao_pct": "Coef. variação (%)", "amplitude": "Amplitude"})
    .style.format({c: "{:.1f}" for c in ["Média", "Mediana", "Desvio-padrão", "Mínimo", "Máximo", "Coef. variação (%)", "Amplitude"]})
    .background_gradient(subset=["Média"], cmap="YlGnBu"),
    width="stretch",
    hide_index=True,
)

# --------------------------------------------------------------------------- #
# Interpretação
# --------------------------------------------------------------------------- #
top3 = rank.head(3)
bottom3 = rank.tail(3)
media_nacional = df[metrica].mean()
acima = (rank["valor"] > media_nacional).sum()
melhor_reg, pior_reg = desig.iloc[0], desig.iloc[-1]
mais_heterogenea = desig.loc[desig["coef_variacao_pct"].idxmax()]
gap_regional = melhor_reg["media"] - pior_reg["media"]

interpretacao(
    f"""
    <ul>
      <li><strong>Melhores estados</strong> ({ROTULOS[metrica].lower()}): {", ".join(f"{r.nome_uf} ({r.valor:.1f})" for r in top3.itertuples())}.</li>
      <li><strong>Estados críticos:</strong> {", ".join(f"{r.nome_uf} ({r.valor:.1f})" for r in bottom3[::-1].itertuples())}.</li>
      <li>{acima} de {len(rank)} estados ficam acima da média da seleção ({media_nacional:.1f}).</li>
      <li><strong>Desigualdade regional:</strong> {melhor_reg['regiao']} ({melhor_reg['media']:.1f}) × {pior_reg['regiao']} ({pior_reg['media']:.1f}),
          diferença de {gap_regional:.1f} pontos — {"pequena frente à dispersão interna de cada região" if gap_regional < desig['desvio'].mean() / 2 else "relevante e consistente com desigualdades estruturais"}.</li>
      <li>A região mais heterogênea internamente é <strong>{mais_heterogenea['regiao']}</strong>
          (coeficiente de variação {mais_heterogenea['coef_variacao_pct']:.1f}%), sinal de que as diferenças entre municípios
          dentro de uma mesma região podem ser maiores do que entre regiões.</li>
    </ul>
    """
)

with st.expander("📋 Ranking completo de estados"):
    st.dataframe(
        rank.assign(posicao=np.arange(1, len(rank) + 1))[["posicao", "uf", "nome_uf", "regiao", "valor", "registros"]]
        .rename(columns={"posicao": "#", "uf": "UF", "nome_uf": "Estado", "regiao": "Região", "valor": ROTULOS[metrica], "registros": "Registros"})
        .style.format({ROTULOS[metrica]: "{:.2f}"}),
        width="stretch",
        hide_index=True,
    )

rodape()
