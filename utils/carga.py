"""Carregamento com cache do Streamlit (base, APIs e banco)."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from utils import apis
from utils.dados import engenharia_atributos, preparar_base, tratar_dados


@st.cache_data(show_spinner="Carregando e tratando a base...")
def _base_padrao() -> pd.DataFrame:
    return preparar_base()


@st.cache_data(show_spinner=False)
def _base_enviada(conteudo: bytes) -> pd.DataFrame:
    import io

    bruto = pd.read_csv(io.BytesIO(conteudo), encoding="utf-8-sig")
    return engenharia_atributos(tratar_dados(bruto))


def obter_base() -> pd.DataFrame:
    """
    Base ativa do dashboard: o CSV enviado pelo usuário (página Explorador),
    quando houver, ou a base padrão do projeto.
    """
    conteudo = st.session_state.get("csv_enviado")
    if conteudo:
        try:
            return _base_enviada(conteudo)
        except Exception as erro:  # noqa: BLE001
            st.sidebar.error(f"Arquivo enviado inválido ({erro}). Usando a base padrão.")
            st.session_state.pop("csv_enviado", None)
    return _base_padrao()


def usando_upload() -> bool:
    return bool(st.session_state.get("csv_enviado"))


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def estados_ibge() -> tuple[dict, str]:
    return apis.consultar_estados_ibge()


@st.cache_data(ttl=60 * 60 * 24, show_spinner="Baixando contornos dos estados...")
def geojson_uf() -> dict | None:
    return apis.baixar_geojson_uf()
