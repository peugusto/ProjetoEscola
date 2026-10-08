"""Página 3 — Redes de ensino (pública x privada) e análise por disciplina."""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from utils.carga import obter_base
from utils.dados import ORDEM_NIVEL, ROTULOS, serie_temporal
from utils.filtros import filtros_sidebar, resumo_filtros
from utils.graficos import CORES_NIVEL, CORES_REDE, barras_categoria, boxplot, linha_temporal
from utils.interface import aviso_vazio, cabecalho, configurar_pagina, interpretacao, rodape

configurar_pagina("Redes e Disciplinas", "🏫")
base = obter_base()
df = filtros_sidebar(base)

cabecalho(
    "Redes de ensino e disciplinas",
    "Existem diferenças entre escolas públicas e privadas? Quais disciplinas apresentam menor rendimento? "
    "Comparações diretas, distribuição dos níveis de desempenho e evolução por rede.",
    "🏫",
)
st.caption(f"Seleção atual: **{resumo_filtros()}**")

if df.empty:
    aviso_vazio()
    st.stop()

metrica = st.selectbox("Métrica", ["media_notas", "indice_desempenho", "taxa_aprovacao", "taxa_reprovacao"], format_func=lambda m: ROTULOS[m])

# --------------------------------------------------------------------------- #
# Pública x privada
# --------------------------------------------------------------------------- #
st.markdown("### Pública × Privada")
redes = df.groupby("rede_ensino", observed=True).agg(
    media_notas=("media_notas", "mean"),
    taxa_aprovacao=("taxa_aprovacao", "mean"),
    taxa_reprovacao=("taxa_reprovacao", "mean"),
    indice_desempenho=("indice_desempenho", "mean"),
    acesso_internet=("acesso_internet", "mean"),
    renda_media_familiar=("renda_media_familiar", "mean"),
    registros=("media_notas", "size"),
)
cols = st.columns(len(redes))
for coluna, (rede, linha) in zip(cols, redes.iterrows()):
    with coluna:
        st.markdown(f"#### {'🏛️' if rede == 'Pública' else '🏢'} Rede {rede}")
        m1, m2, m3 = st.columns(3)
        m1.metric("Nota média", f"{linha['media_notas']:.1f}")
        m2.metric("Aprovação", f"{linha['taxa_aprovacao']:.1f}%")
        m3.metric("Índice", f"{linha['indice_desempenho']:.1f}")
        st.caption(f"{int(linha['registros'])} registros · renda média R$ {linha['renda_media_familiar']:,.0f} · internet {linha['acesso_internet']:.0f}%".replace(",", "."))

c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(boxplot(df, "rede_ensino", metrica, f"Distribuição de {ROTULOS[metrica].lower()} por rede"), width="stretch")
with c2:
    serie = serie_temporal(df, metrica, "rede_ensino")
    st.plotly_chart(linha_temporal(serie, metrica, "rede_ensino", f"Evolução de {ROTULOS[metrica].lower()} por rede"), width="stretch")

# Diferença (gap) entre redes por estado
st.markdown("#### Diferença privada − pública por estado")
gap = df.pivot_table(index="uf", columns="rede_ensino", values=metrica, aggfunc="mean", observed=True)
if {"Privada", "Pública"}.issubset(gap.columns):
    gap["gap"] = gap["Privada"] - gap["Pública"]
    gap = gap.dropna(subset=["gap"]).sort_values("gap").reset_index()
    import plotly.express as px  # noqa: E402

    fig_gap = px.bar(
        gap,
        x="uf",
        y="gap",
        color=np.where(gap["gap"] >= 0, "Privada à frente", "Pública à frente"),
        color_discrete_map={"Privada à frente": CORES_REDE["Privada"], "Pública à frente": CORES_REDE["Pública"]},
        labels={"uf": "UF", "gap": f"Diferença em {ROTULOS[metrica].lower()}", "color": ""},
        text=gap["gap"].round(1),
    )
    fig_gap.update_traces(textposition="outside", cliponaxis=False)
    fig_gap.update_layout(template="plotly_white", height=380, margin=dict(l=20, r=20, t=70, b=20), legend=dict(orientation="h", y=1.0, yanchor="bottom", x=1, xanchor="right", title_text=""))
    st.plotly_chart(fig_gap, width="stretch")
else:
    st.info("Selecione as duas redes de ensino para visualizar a diferença por estado.")

# --------------------------------------------------------------------------- #
# Disciplinas
# --------------------------------------------------------------------------- #
st.markdown("### Disciplinas")
c3, c4 = st.columns(2)
with c3:
    st.plotly_chart(barras_categoria(df, "disciplina", metrica, f"{ROTULOS[metrica]} por disciplina"), width="stretch")
with c4:
    st.plotly_chart(barras_categoria(df, "disciplina", metrica, f"{ROTULOS[metrica]} por disciplina e rede", cor="rede_ensino"), width="stretch")

# Distribuição dos níveis de desempenho por disciplina (barras empilhadas 100%)
dist = pd.crosstab(df["disciplina"], df["nivel_desempenho"], normalize="index").reindex(columns=ORDEM_NIVEL, fill_value=0) * 100
dist = dist.reset_index().melt(id_vars="disciplina", var_name="nivel_desempenho", value_name="percentual")
import plotly.express as px  # noqa: E402

fig_dist = px.bar(
    dist,
    x="disciplina",
    y="percentual",
    color="nivel_desempenho",
    color_discrete_map=CORES_NIVEL,
    category_orders={"nivel_desempenho": ORDEM_NIVEL},
    labels={"disciplina": "Disciplina", "percentual": "% dos registros", "nivel_desempenho": "Nível"},
    text=dist["percentual"].round(0).astype(int).astype(str) + "%",
)
fig_dist.update_layout(template="plotly_white", height=400, barmode="stack", title=dict(text="Distribuição dos níveis de desempenho por disciplina", x=0.01, y=0.98, yref="container", yanchor="top"), margin=dict(l=20, r=20, t=95, b=20), legend=dict(orientation="h", y=1.0, yanchor="bottom", x=1, xanchor="right", title_text=""))
fig_dist.update_traces(textposition="inside")
st.plotly_chart(fig_dist, width="stretch")

# Tabela por disciplina
tabela_disc = (
    df.groupby("disciplina", observed=True)
    .agg(media_notas=("media_notas", "mean"), taxa_aprovacao=("taxa_aprovacao", "mean"), taxa_reprovacao=("taxa_reprovacao", "mean"), indice_desempenho=("indice_desempenho", "mean"), desvio_notas=("media_notas", "std"), registros=("media_notas", "size"))
    .sort_values("media_notas")
    .reset_index()
)
st.dataframe(
    tabela_disc.rename(columns=ROTULOS | {"desvio_notas": "Desvio das notas", "registros": "Registros"}).style.format({c: "{:.1f}" for c in ["Média das notas", "Taxa de aprovação (%)", "Taxa de reprovação (%)", "Índice de desempenho", "Desvio das notas"]}).background_gradient(subset=["Média das notas"], cmap="RdYlGn"),
    width="stretch",
    hide_index=True,
)

# --------------------------------------------------------------------------- #
# Interpretação
# --------------------------------------------------------------------------- #
pior = tabela_disc.iloc[0]
melhor = tabela_disc.iloc[-1]
if {"Privada", "Pública"}.issubset(redes.index):
    dif = redes.loc["Privada", "media_notas"] - redes.loc["Pública", "media_notas"]
    dif_apr = redes.loc["Privada", "taxa_aprovacao"] - redes.loc["Pública", "taxa_aprovacao"]
    texto_rede = (
        f"A rede <strong>privada</strong> tem nota média {dif:+.2f} pontos em relação à pública e taxa de aprovação {dif_apr:+.2f} p.p. "
        f"{'A diferença é pequena: nesta base, a rede de ensino não separa claramente os resultados.' if abs(dif) < 2 else 'A diferença é relevante e persiste na maioria dos estados.'}"
    )
    if "gap" in locals() and isinstance(gap, pd.DataFrame) and "gap" in gap.columns:
        n_priv = int((gap["gap"] > 0).sum())
        texto_rede += f" Em {n_priv} de {len(gap)} estados a rede privada fica à frente."
else:
    texto_rede = "Selecione ambas as redes para comparar pública e privada."

interpretacao(
    f"""
    <ul>
      <li><strong>Redes de ensino:</strong> {texto_rede}</li>
      <li><strong>Disciplina mais crítica:</strong> {pior['disciplina']} (nota média {pior['media_notas']:.1f},
          reprovação {pior['taxa_reprovacao']:.1f}%). <strong>Melhor rendimento:</strong> {melhor['disciplina']} ({melhor['media_notas']:.1f}).</li>
      <li>A amplitude entre a melhor e a pior disciplina é de {melhor['media_notas'] - pior['media_notas']:.1f} pontos,
          {"pequena" if melhor['media_notas'] - pior['media_notas'] < 3 else "expressiva"} diante do desvio-padrão médio das notas ({tabela_disc['desvio_notas'].mean():.1f}).</li>
      <li>A distribuição dos níveis de desempenho é parecida entre disciplinas — os quatro níveis aparecem em proporções
          próximas, o que reforça que a variabilidade está mais ligada ao município e ao período do que à disciplina.</li>
    </ul>
    """
)

rodape()
