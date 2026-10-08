"""
Construtores de gráficos reutilizados pelo dashboard.

Plotly para gráficos interativos; Matplotlib/Seaborn para heatmaps e
dispersões com linha de tendência (bibliotecas obrigatórias da disciplina).
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")  # backend sem janela, necessário no Streamlit Cloud

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns

from utils.dados import ORDEM_NIVEL, ORDEM_REGIAO, ROTULOS, COORDENADAS_UF

# Paleta única para todo o projeto (acessível e consistente).
CORES_REGIAO = {
    "Norte": "#2A9D8F",
    "Nordeste": "#E76F51",
    "Centro-Oeste": "#E9C46A",
    "Sudeste": "#264653",
    "Sul": "#8AB17D",
}
CORES_REDE = {"Pública": "#264653", "Privada": "#E76F51"}
CORES_NIVEL = {"Baixo": "#E76F51", "Médio": "#E9C46A", "Alto": "#8AB17D", "Excelente": "#2A9D8F"}
ESCALA_SEQUENCIAL = "Teal"
PLOTLY_TEMPLATE = "plotly_white"

sns.set_theme(style="whitegrid", palette="deep", font_scale=0.95)


def _layout_padrao(fig: go.Figure, titulo: str, altura: int = 420) -> go.Figure:
    fig.update_layout(
        title=dict(text=titulo, x=0.01, xref="paper", y=0.98, yref="container", yanchor="top", font=dict(size=17)),
        template=PLOTLY_TEMPLATE,
        height=altura,
        margin=dict(l=20, r=20, t=95, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="right", x=1, title_text=""),
        hoverlabel=dict(bgcolor="white"),
    )
    return fig


# --------------------------------------------------------------------------- #
# Linha temporal
# --------------------------------------------------------------------------- #
def linha_temporal(serie: pd.DataFrame, metrica: str, por: str | None = None, titulo: str | None = None) -> go.Figure:
    cores = None
    if por == "regiao":
        cores = CORES_REGIAO
    elif por == "rede_ensino":
        cores = CORES_REDE
    elif por == "nivel_desempenho":
        cores = CORES_NIVEL
    fig = px.line(
        serie,
        x="periodo",
        y=metrica,
        color=por,
        markers=True,
        color_discrete_map=cores,
        labels=ROTULOS,
        category_orders={"regiao": ORDEM_REGIAO, "nivel_desempenho": ORDEM_NIVEL},
    )
    if por is None:
        # Linha de tendência (regressão linear simples) sobre a média geral.
        x = np.arange(len(serie))
        if len(x) >= 2:
            coef = np.polyfit(x, serie[metrica].to_numpy(), 1)
            fig.add_trace(
                go.Scatter(
                    x=serie["periodo"],
                    y=np.polyval(coef, x),
                    mode="lines",
                    name=f"Tendência ({coef[0]:+.2f}/semestre)",
                    line=dict(dash="dash", color="#E76F51"),
                )
            )
        fig.update_traces(selector=dict(mode="lines+markers"), line=dict(color="#264653", width=3))
    fig.update_xaxes(tickangle=-45)
    return _layout_padrao(fig, titulo or f"Evolução de {ROTULOS.get(metrica, metrica).lower()} por semestre")


# --------------------------------------------------------------------------- #
# Barras por estado / região / disciplina
# --------------------------------------------------------------------------- #
def barras_ranking(df_rank: pd.DataFrame, metrica: str, titulo: str, destacar_top: int = 3) -> go.Figure:
    df_rank = df_rank.copy()
    fig = px.bar(
        df_rank,
        x="valor",
        y="uf",
        color="regiao",
        orientation="h",
        color_discrete_map=CORES_REGIAO,
        labels={"valor": ROTULOS.get(metrica, metrica), "uf": "UF", "regiao": "Região"},
        hover_data={"nome_uf": True, "registros": True, "valor": ":.2f"},
        category_orders={"regiao": ORDEM_REGIAO},
        text=df_rank["valor"].round(1),
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_yaxes(categoryorder="total ascending")
    media = df_rank["valor"].mean()
    fig.add_vline(x=media, line_dash="dot", line_color="#555", annotation_text=f"Média {media:.1f}", annotation_position="top")
    return _layout_padrao(fig, titulo, altura=max(420, 24 * len(df_rank) + 120))


def barras_categoria(df: pd.DataFrame, categoria: str, metrica: str, titulo: str, cor: str | None = None, ordenar: bool = True) -> go.Figure:
    agrupado = df.groupby([categoria] + ([cor] if cor and cor != categoria else []), observed=True)[metrica].mean().reset_index()
    if ordenar and cor in (None, categoria):
        agrupado = agrupado.sort_values(metrica, ascending=False)
    mapa_cores = None
    if cor == "rede_ensino":
        mapa_cores = CORES_REDE
    elif cor == "regiao":
        mapa_cores = CORES_REGIAO
    elif cor == "nivel_desempenho":
        mapa_cores = CORES_NIVEL
    fig = px.bar(
        agrupado,
        x=categoria,
        y=metrica,
        color=cor,
        barmode="group",
        color_discrete_map=mapa_cores,
        labels=ROTULOS,
        text=agrupado[metrica].round(1),
        category_orders={"regiao": ORDEM_REGIAO, "nivel_desempenho": ORDEM_NIVEL},
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    return _layout_padrao(fig, titulo)


# --------------------------------------------------------------------------- #
# Heatmap semestral (Seaborn)
# --------------------------------------------------------------------------- #
def heatmap_semestral(tabela: pd.DataFrame, titulo: str, fmt: str = ".1f", cmap: str = "YlGnBu"):
    altura = max(3.2, 0.45 * len(tabela) + 1.6)
    fig, ax = plt.subplots(figsize=(13, altura))
    sns.heatmap(
        tabela,
        annot=len(tabela.columns) <= 24,
        fmt=fmt,
        cmap=cmap,
        linewidths=0.4,
        linecolor="white",
        cbar_kws={"shrink": 0.8},
        ax=ax,
        annot_kws={"size": 8},
    )
    ax.set_title(titulo, loc="left", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Período (ano/semestre)")
    ax.set_ylabel("")
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    fig.tight_layout()
    return fig


# --------------------------------------------------------------------------- #
# Dispersão renda x notas
# --------------------------------------------------------------------------- #
def dispersao_plotly(df: pd.DataFrame, x: str, y: str, cor: str = "rede_ensino", titulo: str | None = None) -> go.Figure:
    mapa = CORES_REDE if cor == "rede_ensino" else CORES_REGIAO if cor == "regiao" else CORES_NIVEL
    fig = px.scatter(
        df,
        x=x,
        y=y,
        color=cor,
        trendline="ols" if _statsmodels_disponivel() else None,
        opacity=0.65,
        color_discrete_map=mapa,
        labels=ROTULOS,
        hover_data=["uf", "municipio", "disciplina", "ano"],
        category_orders={"regiao": ORDEM_REGIAO, "nivel_desempenho": ORDEM_NIVEL},
    )
    if not _statsmodels_disponivel():
        # Linha de tendência manual (regressão linear com NumPy).
        sub = df[[x, y]].dropna()
        if len(sub) >= 2:
            coef = np.polyfit(sub[x], sub[y], 1)
            xs = np.linspace(sub[x].min(), sub[x].max(), 50)
            fig.add_trace(go.Scatter(x=xs, y=np.polyval(coef, xs), mode="lines", name="Tendência linear", line=dict(color="#333", dash="dash")))
    return _layout_padrao(fig, titulo or f"{ROTULOS.get(x, x)} x {ROTULOS.get(y, y)}", altura=460)


def _statsmodels_disponivel() -> bool:
    try:
        import statsmodels  # noqa: F401

        return True
    except ImportError:
        return False


def dispersao_seaborn(df: pd.DataFrame, x: str, y: str, hue: str, titulo: str):
    fig, ax = plt.subplots(figsize=(9, 5.5))
    paleta = CORES_REDE if hue == "rede_ensino" else CORES_REGIAO
    sns.scatterplot(data=df, x=x, y=y, hue=hue, alpha=0.6, palette=paleta, ax=ax)
    sns.regplot(data=df, x=x, y=y, scatter=False, color="#333", line_kws={"linestyle": "--", "linewidth": 1.5}, ax=ax)
    ax.set_title(titulo, loc="left", fontsize=13, fontweight="bold")
    ax.set_xlabel(ROTULOS.get(x, x))
    ax.set_ylabel(ROTULOS.get(y, y))
    ax.legend(title=ROTULOS.get(hue, hue), frameon=False)
    fig.tight_layout()
    return fig


# --------------------------------------------------------------------------- #
# Correlação (Seaborn)
# --------------------------------------------------------------------------- #
def heatmap_correlacao(matriz: pd.DataFrame, titulo: str = "Matriz de correlação (Pearson)"):
    fig, ax = plt.subplots(figsize=(8, 6))
    mascara = np.triu(np.ones_like(matriz, dtype=bool))
    sns.heatmap(
        matriz.rename(index=ROTULOS, columns=ROTULOS),
        mask=mascara,
        annot=True,
        fmt=".2f",
        cmap="RdBu_r",
        vmin=-1,
        vmax=1,
        center=0,
        linewidths=0.5,
        square=True,
        cbar_kws={"shrink": 0.8},
        ax=ax,
    )
    ax.set_title(titulo, loc="left", fontsize=13, fontweight="bold", pad=12)
    plt.setp(ax.get_xticklabels(), rotation=35, ha="right")
    fig.tight_layout()
    return fig


# --------------------------------------------------------------------------- #
# Boxplot (distribuições)
# --------------------------------------------------------------------------- #
def boxplot(df: pd.DataFrame, x: str, y: str, titulo: str, cor: str | None = None) -> go.Figure:
    mapa = CORES_REDE if (cor or x) == "rede_ensino" else CORES_REGIAO if (cor or x) == "regiao" else CORES_NIVEL
    fig = px.box(
        df,
        x=x,
        y=y,
        color=cor or x,
        color_discrete_map=mapa,
        labels=ROTULOS,
        points="outliers",
        category_orders={"regiao": ORDEM_REGIAO, "nivel_desempenho": ORDEM_NIVEL},
    )
    return _layout_padrao(fig, titulo)


# --------------------------------------------------------------------------- #
# Mapa
# --------------------------------------------------------------------------- #
def mapa_brasil(df_rank: pd.DataFrame, metrica: str, geojson: dict | None, titulo: str) -> go.Figure:
    rotulo = ROTULOS.get(metrica, metrica)
    if geojson is not None:
        fig = px.choropleth(
            df_rank,
            geojson=geojson,
            locations="uf",
            featureidkey="properties.sigla",
            color="valor",
            color_continuous_scale=ESCALA_SEQUENCIAL,
            hover_name="nome_uf",
            hover_data={"uf": False, "valor": ":.2f", "registros": True, "regiao": True},
            labels={"valor": rotulo, "registros": "Registros", "regiao": "Região"},
        )
        fig.update_geos(fitbounds="locations", visible=False)
    else:
        pontos = df_rank.copy()
        pontos["lat"] = pontos["uf"].map(lambda s: COORDENADAS_UF.get(s, (np.nan, np.nan))[0])
        pontos["lon"] = pontos["uf"].map(lambda s: COORDENADAS_UF.get(s, (np.nan, np.nan))[1])
        fig = px.scatter_geo(
            pontos,
            lat="lat",
            lon="lon",
            color="valor",
            size="registros",
            hover_name="nome_uf",
            color_continuous_scale=ESCALA_SEQUENCIAL,
            scope="south america",
            labels={"valor": rotulo},
            text="uf",
        )
        fig.update_traces(textposition="top center")
        fig.update_geos(center=dict(lat=-15, lon=-53), projection_scale=2.4, showcountries=True)
    fig = _layout_padrao(fig, titulo, altura=560)
    fig.update_layout(coloraxis_colorbar=dict(title=rotulo, len=0.7))
    return fig
