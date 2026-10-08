"""
Dashboard — Desempenho Escolar no Brasil (2015–2024)
Ponto de entrada: define a navegação multipágina (st.navigation) e executa a
página selecionada. O conteúdo de cada página fica em `pages/`.

Executar localmente:
    streamlit run app.py
"""
from __future__ import annotations

import streamlit as st

PAGINAS = [
    st.Page("pages/0_Visao_Geral.py", title="Visão Geral", icon="🏠", default=True),
    st.Page("pages/1_Evolucao_Temporal.py", title="Evolução Temporal", icon="📈"),
    st.Page("pages/2_Comparacao_Regional.py", title="Comparação Regional", icon="🗺️"),
    st.Page("pages/3_Redes_e_Disciplinas.py", title="Redes e Disciplinas", icon="🏫"),
    st.Page("pages/4_Fatores_Socioeconomicos.py", title="Fatores Socioeconômicos", icon="💰"),
    st.Page("pages/5_Explorador_de_Dados.py", title="Explorador de Dados", icon="🔎"),
]

pagina = st.navigation(PAGINAS, position="sidebar")
pagina.run()
