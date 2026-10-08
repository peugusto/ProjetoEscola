"""
Dashboard — Desempenho Escolar no Brasil (2015–2024)
Página inicial (Visão Geral). O roteamento das páginas é feito em `app.py` (st.navigation).

Executar localmente:
    streamlit run app.py  (a partir da raiz do projeto)
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from utils.carga import obter_base, usando_upload
from utils.dados import (
    ROTULOS,
    calcular_kpis,
    correlacao_com_significancia,
    interpretar_correlacao,
    matriz_heatmap,
    ranking_uf,
    serie_temporal,
)
from utils.filtros import filtros_sidebar, resumo_filtros
from utils.graficos import (
    barras_categoria,
    barras_ranking,
    dispersao_plotly,
    heatmap_semestral,
    linha_temporal,
)
from utils.interface import (
    SUBTITULO_PROJETO,
    TITULO_PROJETO,
    aviso_vazio,
    cabecalho,
    conclusao,
    configurar_pagina,
    interpretacao,
    mostrar_kpis,
    rodape,
)

configurar_pagina("Visão Geral")

# --------------------------------------------------------------------------- #
# Dados e filtros
# --------------------------------------------------------------------------- #
base = obter_base()
df = filtros_sidebar(base)
kpis_base = calcular_kpis(base)
kpis = calcular_kpis(df)

# --------------------------------------------------------------------------- #
# Cabeçalho e descrição do problema
# --------------------------------------------------------------------------- #
cabecalho(TITULO_PROJETO, SUBTITULO_PROJETO)

if usando_upload():
    st.info("📂 Você está analisando um arquivo CSV enviado na página **Explorador de Dados**. Remova-o lá para voltar à base padrão.")

with st.expander("📌 Descrição do problema e perguntas orientadoras", expanded=True):
    col_a, col_b = st.columns([1.3, 1])
    with col_a:
        st.markdown(
            """
            O desempenho escolar é um indicador central da qualidade da educação e influencia
            formação profissional, inclusão social e desenvolvimento econômico. Este projeto
            investiga indicadores de **desempenho escolar no Brasil entre 2015 e 2024**, a partir
            de uma base simulada com médias de notas, taxas de aprovação e reprovação, acesso à
            internet, renda média familiar e um índice geral de desempenho, detalhados por região,
            estado, município, rede de ensino e disciplina.

            **Objetivos:** analisar a evolução das notas, comparar regiões e estados, investigar
            diferenças entre redes pública e privada, relacionar fatores socioeconômicos ao
            desempenho e identificar regiões críticas.
            """
        )
    with col_b:
        st.markdown(
            """
            **Perguntas orientadoras**
            1. Quais estados apresentam melhor desempenho escolar?
            2. Existem diferenças entre escolas públicas e privadas?
            3. Houve melhoria no desempenho ao longo do tempo?
            4. Existe relação entre renda e desempenho?
            5. Como o acesso à internet impacta o aprendizado?
            6. Quais disciplinas apresentam menor rendimento?
            7. Existem desigualdades regionais relevantes?
            """
        )
    st.caption("Use as páginas no menu lateral para aprofundar cada pergunta. Os filtros valem para todo o dashboard.")

# --------------------------------------------------------------------------- #
# KPIs
# --------------------------------------------------------------------------- #
st.markdown("## 📊 Indicadores-chave")
st.caption(f"Seleção atual: **{resumo_filtros()}** · {kpis['registros']} registros")
if df.empty:
    aviso_vazio()
    rodape()
    st.stop()

mostrar_kpis(kpis, kpis_base)

# --------------------------------------------------------------------------- #
# Visualizações principais
# --------------------------------------------------------------------------- #
st.markdown("## 📈 Panorama")
metrica = st.radio(
    "Métrica analisada",
    options=["indice_desempenho", "media_notas", "taxa_aprovacao", "taxa_reprovacao"],
    format_func=lambda m: ROTULOS[m],
    horizontal=True,
    key="metrica_visao_geral",
)

col1, col2 = st.columns([1.35, 1])
with col1:
    serie = serie_temporal(df, metrica)
    st.plotly_chart(linha_temporal(serie, metrica), width="stretch")
with col2:
    st.plotly_chart(
        barras_categoria(df, "disciplina", metrica, f"{ROTULOS[metrica]} por disciplina", cor="rede_ensino"),
        width="stretch",
    )

col3, col4 = st.columns([1, 1.35])
with col3:
    rank = ranking_uf(df, metrica)
    st.plotly_chart(barras_ranking(rank, metrica, f"Ranking de estados — {ROTULOS[metrica].lower()}"), width="stretch")
with col4:
    st.plotly_chart(
        dispersao_plotly(df, "renda_media_familiar", "media_notas", cor="rede_ensino", titulo="Dispersão — renda média familiar x média das notas"),
        width="stretch",
    )
    st.plotly_chart(
        barras_categoria(df, "regiao", metrica, f"{ROTULOS[metrica]} por região e rede", cor="rede_ensino", ordenar=False),
        width="stretch",
    )

tabela_heat = matriz_heatmap(df, metrica, linhas="regiao")
st.pyplot(heatmap_semestral(tabela_heat, f"Heatmap semestral — {ROTULOS[metrica].lower()} por região"), width="stretch")

# --------------------------------------------------------------------------- #
# Interpretação textual (dinâmica, reage aos filtros)
# --------------------------------------------------------------------------- #
primeiro, ultimo = serie.iloc[0], serie.iloc[-1]
variacao = ultimo[metrica] - primeiro[metrica]
tendencia = "melhora" if variacao > 0.5 else "piora" if variacao < -0.5 else "estabilidade"
melhor_uf, pior_uf = rank.iloc[0], rank.iloc[-1]
amplitude_uf = melhor_uf["valor"] - pior_uf["valor"]
por_regiao = df.groupby("regiao", observed=True)[metrica].mean().sort_values(ascending=False)
por_rede = df.groupby("rede_ensino", observed=True)["media_notas"].mean()
dif_rede = (por_rede.get("Privada", np.nan) - por_rede.get("Pública", np.nan))
corr_renda = correlacao_com_significancia(df, "renda_media_familiar", "media_notas")
corr_net = correlacao_com_significancia(df, "acesso_internet", "media_notas")

interpretacao(
    f"""
    <ul>
      <li><strong>Evolução temporal:</strong> entre {primeiro['periodo']} e {ultimo['periodo']}, a métrica
          <em>{ROTULOS[metrica].lower()}</em> variou {variacao:+.2f} pontos, indicando <strong>{tendencia}</strong>
          no período selecionado, com oscilações semestrais relevantes.</li>
      <li><strong>Estados</strong> (pela métrica selecionada): {melhor_uf['nome_uf']} ({melhor_uf['uf']}) lidera com {melhor_uf['valor']:.1f},
          enquanto {pior_uf['nome_uf']} ({pior_uf['uf']}) tem o menor valor ({pior_uf['valor']:.1f}).
          A amplitude entre extremos é de {amplitude_uf:.1f} pontos.</li>
      <li><strong>Regiões:</strong> {por_regiao.index[0]} apresenta a maior média ({por_regiao.iloc[0]:.1f}) e
          {por_regiao.index[-1]} a menor ({por_regiao.iloc[-1]:.1f}).</li>
      <li><strong>Redes de ensino:</strong> a diferença de nota média entre privada e pública é de
          {dif_rede:+.2f} pontos {"a favor da rede privada" if dif_rede > 0 else "a favor da rede pública"}.</li>
      <li><strong>Fatores socioeconômicos:</strong> a correlação renda x notas é {interpretar_correlacao(corr_renda['r'])}
          (r = {corr_renda['r']:.2f}); acesso à internet x notas é {interpretar_correlacao(corr_net['r'])}
          (r = {corr_net['r']:.2f}).</li>
      <li><strong>Disciplina crítica:</strong> {kpis['disciplina_critica']} tem a menor média
          ({kpis['disciplina_critica_valor']:.1f}).</li>
    </ul>
    """
)

# --------------------------------------------------------------------------- #
# Tabela resumo
# --------------------------------------------------------------------------- #
st.markdown("## 📋 Resumo por região e rede de ensino")
resumo = (
    df.groupby(["regiao", "rede_ensino"], observed=True)
    .agg(
        registros=("media_notas", "size"),
        media_notas=("media_notas", "mean"),
        taxa_aprovacao=("taxa_aprovacao", "mean"),
        taxa_reprovacao=("taxa_reprovacao", "mean"),
        indice_desempenho=("indice_desempenho", "mean"),
        acesso_internet=("acesso_internet", "mean"),
        renda_media_familiar=("renda_media_familiar", "mean"),
    )
    .reset_index()
    .rename(columns=ROTULOS | {"registros": "Registros"})
)
st.dataframe(
    resumo.style.format(
        {c: "{:.1f}" for c in resumo.columns if c not in ("Região", "Rede de ensino", "Registros")}
        | {"Renda média familiar (R$)": "R$ {:,.0f}"}
    ).background_gradient(subset=["Média das notas", "Índice de desempenho"], cmap="YlGnBu"),
    width="stretch",
    hide_index=True,
)

# --------------------------------------------------------------------------- #
# Conclusão executiva
# --------------------------------------------------------------------------- #
st.markdown("## 🎯 Conclusão executiva")
conclusao(
    f"""
    <ol>
      <li>Para a seleção atual, a <strong>média geral das notas</strong> é {kpis['media_notas']:.1f} e a
          <strong>taxa média de aprovação</strong> é {kpis['taxa_aprovacao']:.1f}%, com índice médio de desempenho
          de {kpis['indice_desempenho']:.1f}.</li>
      <li>Pela métrica selecionada ({ROTULOS[metrica].lower()}), <strong>{melhor_uf['nome_uf']}</strong> é o estado de referência; <strong>{pior_uf['nome_uf']}</strong> e a região
          <strong>{por_regiao.index[-1]}</strong> concentram os indicadores mais baixos e merecem prioridade em políticas de apoio.</li>
      <li>A diferença entre redes pública e privada é de {abs(dif_rede):.1f} ponto(s): {"pequena, sugerindo que, nesta base, a rede não é o principal fator de desigualdade" if abs(dif_rede) < 2 else "relevante e deve ser monitorada"}.</li>
      <li>As correlações de renda e acesso à internet com as notas são {interpretar_correlacao(corr_renda['r'])} e
          {interpretar_correlacao(corr_net['r'])}, respectivamente: nesta base simulada, fatores socioeconômicos explicam
          pouco da variação das notas. A tendência temporal indica <strong>{tendencia}</strong>.</li>
      <li><strong>{kpis['disciplina_critica']}</strong> é a disciplina com menor rendimento e deve ser alvo de reforço pedagógico.</li>
    </ol>
    <em>Observação metodológica:</em> os dados são simulados. As conclusões demonstram o método analítico e não devem ser
    lidas como diagnóstico real da educação brasileira.
    """
)

rodape()
