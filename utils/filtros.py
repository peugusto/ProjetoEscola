"""
Filtros da barra lateral, compartilhados por todas as páginas do dashboard.

As seleções ficam em st.session_state (chaves com prefixo "f_") para
persistirem ao navegar entre páginas.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.dados import ORDEM_NIVEL, ORDEM_REGIAO, aplicar_filtros

CHAVES = ["f_anos", "f_semestres", "f_regioes", "f_ufs", "f_redes", "f_disciplinas", "f_niveis"]


def _lembrar(chave: str) -> None:
    """Copia o valor do widget para uma chave persistente."""
    st.session_state[f"_{chave}"] = st.session_state[chave]


def _padrao(chave: str, valor_inicial):
    """Valor inicial do widget: o que o usuário escolheu antes ou o padrão."""
    return st.session_state.get(f"_{chave}", valor_inicial)


def limpar_filtros() -> None:
    for chave in CHAVES:
        st.session_state.pop(chave, None)
        st.session_state.pop(f"_{chave}", None)


def filtros_sidebar(df: pd.DataFrame) -> pd.DataFrame:
    """Renderiza os filtros obrigatórios e devolve o DataFrame filtrado."""
    with st.sidebar:
        st.markdown("## 🎛️ Filtros")
        st.caption("As seleções valem para todas as páginas.")

        anos_disponiveis = sorted(df["ano"].unique().tolist())
        ano_min, ano_max = int(anos_disponiveis[0]), int(anos_disponiveis[-1])
        anos = st.slider(
            "Ano letivo",
            min_value=ano_min,
            max_value=ano_max,
            value=_padrao("f_anos", (ano_min, ano_max)),
            key="f_anos",
            on_change=_lembrar,
            args=("f_anos",),
        )

        semestres = st.multiselect(
            "Semestre",
            options=[1, 2],
            default=_padrao("f_semestres", [1, 2]),
            format_func=lambda s: f"{s}º semestre",
            key="f_semestres",
            on_change=_lembrar,
            args=("f_semestres",),
        )

        regioes_disponiveis = [r for r in ORDEM_REGIAO if r in set(df["regiao"].astype(str))]
        regioes = st.multiselect(
            "Região",
            options=regioes_disponiveis,
            default=_padrao("f_regioes", []),
            placeholder="Todas as regiões",
            key="f_regioes",
            on_change=_lembrar,
            args=("f_regioes",),
        )

        # Estados dependem das regiões selecionadas (filtro em cascata).
        base_uf = df if not regioes else df[df["regiao"].isin(regioes)]
        ufs_disponiveis = sorted(base_uf["uf"].unique().tolist())
        ufs_lembradas = [u for u in _padrao("f_ufs", []) if u in ufs_disponiveis]
        ufs = st.multiselect(
            "Estado (UF)",
            options=ufs_disponiveis,
            default=ufs_lembradas,
            placeholder="Todos os estados",
            key="f_ufs",
            on_change=_lembrar,
            args=("f_ufs",),
        )

        redes = st.multiselect(
            "Rede de ensino",
            options=sorted(df["rede_ensino"].unique().tolist()),
            default=_padrao("f_redes", []),
            placeholder="Pública e privada",
            key="f_redes",
            on_change=_lembrar,
            args=("f_redes",),
        )

        disciplinas = st.multiselect(
            "Disciplina",
            options=sorted(df["disciplina"].unique().tolist()),
            default=_padrao("f_disciplinas", []),
            placeholder="Todas as disciplinas",
            key="f_disciplinas",
            on_change=_lembrar,
            args=("f_disciplinas",),
        )

        niveis = st.multiselect(
            "Nível de desempenho",
            options=ORDEM_NIVEL,
            default=_padrao("f_niveis", []),
            placeholder="Todos os níveis",
            key="f_niveis",
            on_change=_lembrar,
            args=("f_niveis",),
        )

        st.button("🔄 Limpar filtros", on_click=limpar_filtros, width="stretch")

    filtrado = aplicar_filtros(
        df,
        anos=anos,
        semestres=semestres,
        regioes=regioes,
        ufs=ufs,
        redes=redes,
        disciplinas=disciplinas,
        niveis=niveis,
    )

    with st.sidebar:
        st.markdown("---")
        st.metric("Registros selecionados", f"{len(filtrado):,}".replace(",", "."), f"de {len(df):,}".replace(",", "."), delta_color="off")
        st.caption("Fonte: dataset simulado fornecido pela disciplina (2015–2024).")

    return filtrado


def resumo_filtros() -> str:
    """Texto curto descrevendo os filtros ativos (para títulos e interpretações)."""
    partes = []
    anos = st.session_state.get("f_anos")
    if anos:
        partes.append(f"{anos[0]}–{anos[1]}" if anos[0] != anos[1] else str(anos[0]))
    for chave, nome in [
        ("f_semestres", "semestre"),
        ("f_regioes", "região"),
        ("f_ufs", "UF"),
        ("f_redes", "rede"),
        ("f_disciplinas", "disciplina"),
        ("f_niveis", "nível"),
    ]:
        valores = st.session_state.get(chave) or []
        if chave == "f_semestres" and len(valores) == 2:
            continue
        if valores:
            partes.append(f"{nome}: {', '.join(str(v) for v in valores)}")
    return " · ".join(partes) if partes else "todos os registros"
