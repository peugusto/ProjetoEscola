"""Componentes visuais compartilhados: cabeçalho, cartões de KPI e rodapé."""
from __future__ import annotations

import numpy as np
import streamlit as st

TITULO_PROJETO = "Desempenho Escolar no Brasil (2015–2024)"
SUBTITULO_PROJETO = "Análise e visualização de indicadores educacionais por região, estado, rede de ensino e disciplina"

CSS = """
<style>
    .block-container {padding-top: 1.6rem; padding-bottom: 2rem;}
    .kpi-card {
        background: linear-gradient(135deg, #f8fafc 0%, #eef2f7 100%);
        border: 1px solid #e2e8f0;
        border-left: 5px solid #264653;
        border-radius: 12px;
        padding: 0.9rem 1rem 0.8rem 1rem;
        min-height: 118px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .kpi-card.destaque {border-left-color: #2A9D8F;}
    .kpi-card.alerta {border-left-color: #E76F51;}
    .kpi-titulo {font-size: 0.78rem; color: #475569; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 0.25rem;}
    .kpi-valor {font-size: 1.75rem; font-weight: 700; color: #0f172a; line-height: 1.1;}
    .kpi-valor.texto {font-size: 1.25rem; line-height: 1.2; word-break: keep-all; overflow-wrap: normal;}
    .kpi-detalhe {font-size: 0.8rem; color: #64748b; margin-top: 0.3rem;}
    .kpi-delta-pos {color: #15803d; font-weight: 600;}
    .kpi-delta-neg {color: #b91c1c; font-weight: 600;}
    .caixa-interpretacao {
        background: #fffbeb; border: 1px solid #fde68a; border-radius: 10px;
        padding: 0.9rem 1.1rem; margin: 0.4rem 0 1rem 0;
    }
    .caixa-conclusao {
        background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 10px;
        padding: 1rem 1.2rem; margin: 0.4rem 0 1rem 0;
    }
    .rodape {color: #94a3b8; font-size: 0.8rem; text-align: center; margin-top: 2rem;}
</style>
"""


def configurar_pagina(titulo_aba: str, icone: str = "🎓") -> None:
    """Configuração padrão de página + CSS global."""
    st.set_page_config(page_title=f"{titulo_aba} · Desempenho Escolar", page_icon=icone, layout="wide", initial_sidebar_state="expanded")
    st.markdown(CSS, unsafe_allow_html=True)


def cabecalho(titulo: str, descricao: str | None = None, icone: str = "🎓") -> None:
    st.markdown(f"# {icone} {titulo}")
    if descricao:
        st.markdown(descricao)


def _formatar(valor, casas: int = 1, sufixo: str = "") -> str:
    if valor is None or (isinstance(valor, float) and np.isnan(valor)):
        return "—"
    if isinstance(valor, (int, np.integer)):
        return f"{valor:,}".replace(",", ".")
    return f"{valor:,.{casas}f}{sufixo}".replace(",", "X").replace(".", ",").replace("X", ".")


def cartao_kpi(coluna, titulo: str, valor, detalhe: str = "", delta: float | None = None, casas: int = 1, sufixo: str = "", estilo: str = "") -> None:
    """Cartão de KPI em HTML. `delta` é a diferença em relação à base completa."""
    html_delta = ""
    if delta is not None and not (isinstance(delta, float) and np.isnan(delta)) and abs(delta) >= 0.005:
        classe = "kpi-delta-pos" if delta > 0 else "kpi-delta-neg"
        seta = "▲" if delta > 0 else "▼"
        html_delta = f' <span class="{classe}">{seta} {_formatar(abs(delta), casas)}</span>'
    coluna.markdown(
        f"""
        <div class="kpi-card {estilo}">
            <div class="kpi-titulo">{titulo}</div>
            <div class="kpi-valor{' texto' if isinstance(valor, str) else ''}">{_formatar(valor, casas, sufixo) if not isinstance(valor, str) else valor}</div>
            <div class="kpi-detalhe">{detalhe}{html_delta}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def mostrar_kpis(kpis: dict, kpis_base: dict | None = None) -> None:
    """Linha com os seis KPIs exigidos pelo tema (dinâmicos, reagem aos filtros)."""
    base = kpis_base or {}
    c1, c2, c3, c4, c5, c6 = st.columns(6)

    def delta(chave):
        if chave in base and not np.isnan(kpis.get(chave, np.nan)):
            return kpis[chave] - base[chave]
        return None

    cartao_kpi(c1, "Média geral das notas", kpis["media_notas"], "vs. base completa", delta("media_notas"))
    cartao_kpi(c2, "Taxa média de aprovação", kpis["taxa_aprovacao"], "vs. base completa", delta("taxa_aprovacao"), sufixo="%")
    cartao_kpi(c3, "Índice médio de desempenho", kpis["indice_desempenho"], "vs. base completa", delta("indice_desempenho"))
    cartao_kpi(c4, "Estado com melhor desempenho", kpis["melhor_uf"], f"índice médio {_formatar(kpis['melhor_uf_valor'])}", estilo="destaque")
    cartao_kpi(c5, "Rede com maior desempenho", kpis["melhor_rede"], f"nota média {_formatar(kpis['melhor_rede_valor'])}", estilo="destaque")
    cartao_kpi(c6, "Disciplina mais crítica", kpis["disciplina_critica"], f"nota média {_formatar(kpis['disciplina_critica_valor'])}", estilo="alerta")


def interpretacao(texto: str, titulo: str = "📝 Interpretação") -> None:
    st.markdown(f'<div class="caixa-interpretacao"><strong>{titulo}</strong><br>{texto}</div>', unsafe_allow_html=True)


def conclusao(texto: str, titulo: str = "✅ Conclusão executiva") -> None:
    st.markdown(f'<div class="caixa-conclusao"><strong>{titulo}</strong><br>{texto}</div>', unsafe_allow_html=True)


def aviso_vazio() -> bool:
    """Mostra aviso e devolve True quando a seleção não retornou registros."""
    st.warning("Nenhum registro atende aos filtros selecionados. Ajuste os filtros na barra lateral.")
    return True


def rodape() -> None:
    st.markdown(
        '<div class="rodape">Projeto G1 · Análise e Visualização de Dados com Python · '
        "Dados simulados fornecidos pela disciplina · Construído com Streamlit, Pandas, Matplotlib, Seaborn, Plotly e SQLAlchemy</div>",
        unsafe_allow_html=True,
    )
