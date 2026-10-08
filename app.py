"""
Desempenho Escolar no Brasil (2015–2024) — Dashboard Streamlit
Projeto G1 · Análise e Visualização de Dados com Python

Executar: streamlit run app.py
"""
from math import erf, sqrt
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
import streamlit as st

# --------------------------------------------------------------------------- #
# Configuração
# --------------------------------------------------------------------------- #
st.set_page_config(page_title="Desempenho Escolar no Brasil", page_icon="🎓", layout="wide")
sns.set_theme(style="whitegrid")

CAMINHO_CSV = Path(__file__).parent / "dados" / "simulacao_desempenho_escolar_brasil.csv"
ORDEM_NIVEL = ["Baixo", "Médio", "Alto", "Excelente"]
ORDEM_REGIAO = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]
NUMERICAS = ["media_notas", "taxa_aprovacao", "taxa_reprovacao", "acesso_internet", "renda_media_familiar", "indice_desempenho"]
ROTULOS = {
    "media_notas": "Média das notas",
    "taxa_aprovacao": "Taxa de aprovação (%)",
    "taxa_reprovacao": "Taxa de reprovação (%)",
    "acesso_internet": "Acesso à internet (%)",
    "renda_media_familiar": "Renda média familiar (R$)",
    "indice_desempenho": "Índice de desempenho",
    "regiao": "Região",
    "uf": "UF",
    "rede_ensino": "Rede de ensino",
    "disciplina": "Disciplina",
    "nivel_desempenho": "Nível de desempenho",
    "periodo": "Período",
    "ano": "Ano",
    "semestre": "Semestre",
}
CORES_REDE = {"Pública": "#264653", "Privada": "#E76F51"}
CORES_REGIAO = {"Norte": "#2A9D8F", "Nordeste": "#E76F51", "Centro-Oeste": "#E9C46A", "Sudeste": "#264653", "Sul": "#8AB17D"}


# --------------------------------------------------------------------------- #
# Dados: leitura, tratamento e engenharia de atributos
# --------------------------------------------------------------------------- #
@st.cache_data
def carregar_dados() -> pd.DataFrame:
    df = pd.read_csv(CAMINHO_CSV, encoding="utf-8-sig")

    # Limpeza: nomes de colunas, textos, tipos, duplicatas
    df.columns = [c.strip().lower() for c in df.columns]
    for col in ["regiao", "uf", "municipio", "rede_ensino", "disciplina", "nivel_desempenho"]:
        df[col] = df[col].astype(str).str.strip()
    df["uf"] = df["uf"].str.upper()
    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    df["ano"] = pd.to_numeric(df["ano"], errors="coerce").astype(int)
    df["semestre"] = pd.to_numeric(df["semestre"], errors="coerce").astype(int)
    for col in NUMERICAS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.drop_duplicates().reset_index(drop=True)

    # Valores ausentes: mediana por UF e disciplina; percentuais limitados a 0–100
    for col in NUMERICAS:
        df[col] = df[col].fillna(df.groupby(["uf", "disciplina"])[col].transform("median"))
    for col in ["taxa_aprovacao", "taxa_reprovacao", "acesso_internet"]:
        df[col] = df[col].clip(0, 100)

    # Engenharia de atributos
    df["periodo"] = df["ano"].astype(str) + "/S" + df["semestre"].astype(str)
    df["faixa_renda"] = pd.qcut(df["renda_media_familiar"], 4, labels=["Q1 (menor renda)", "Q2", "Q3", "Q4 (maior renda)"])
    df["faixa_internet"] = pd.cut(df["acesso_internet"], [0, 50, 65, 80, 100], labels=["Até 50%", "50–65%", "65–80%", "Acima de 80%"], include_lowest=True)
    df["taxas_inconsistentes"] = (df["taxa_aprovacao"] + df["taxa_reprovacao"]) > 100
    df["nivel_desempenho"] = pd.Categorical(df["nivel_desempenho"], categories=ORDEM_NIVEL, ordered=True)
    df["regiao"] = pd.Categorical(df["regiao"], categories=ORDEM_REGIAO, ordered=True)
    return df


def correlacao(df: pd.DataFrame, x: str, y: str) -> tuple[float, float]:
    """Correlação de Pearson e p-valor aproximado (NumPy, sem SciPy)."""
    sub = df[[x, y]].dropna()
    n = len(sub)
    if n < 3:
        return np.nan, np.nan
    r = float(sub[x].corr(sub[y]))
    r_ = min(max(r, -0.999999), 0.999999)
    t = r_ * np.sqrt((n - 2) / (1 - r_**2))
    p = 2 * (1 - 0.5 * (1 + erf(abs(t) / sqrt(2))))
    return r, float(p)


def forca(r: float) -> str:
    a = abs(r)
    if np.isnan(r) or a < 0.1:
        return "praticamente nula"
    grau = "fraca" if a < 0.3 else "moderada" if a < 0.5 else "forte" if a < 0.7 else "muito forte"
    return f"{grau} e {'positiva' if r > 0 else 'negativa'}"


def layout(fig: go.Figure, titulo: str, altura: int = 420) -> go.Figure:
    fig.update_layout(
        title=dict(text=titulo, x=0.01, y=0.98, yref="container", yanchor="top"),
        template="plotly_white",
        height=altura,
        margin=dict(l=20, r=20, t=90, b=20),
        legend=dict(orientation="h", y=1.0, yanchor="bottom", x=1, xanchor="right", title_text=""),
    )
    return fig


base = carregar_dados()

# --------------------------------------------------------------------------- #
# Filtros (barra lateral)
# --------------------------------------------------------------------------- #
st.sidebar.header("🎛️ Filtros")
ano_min, ano_max = int(base["ano"].min()), int(base["ano"].max())
anos = st.sidebar.slider("Ano letivo", ano_min, ano_max, (ano_min, ano_max))
semestres = st.sidebar.multiselect("Semestre", [1, 2], default=[1, 2], format_func=lambda s: f"{s}º semestre")
regioes = st.sidebar.multiselect("Região", ORDEM_REGIAO, placeholder="Todas as regiões")
base_uf = base[base["regiao"].isin(regioes)] if regioes else base
ufs = st.sidebar.multiselect("Estado (UF)", sorted(base_uf["uf"].unique()), placeholder="Todos os estados")
redes = st.sidebar.multiselect("Rede de ensino", sorted(base["rede_ensino"].unique()), placeholder="Pública e privada")
disciplinas = st.sidebar.multiselect("Disciplina", sorted(base["disciplina"].unique()), placeholder="Todas as disciplinas")
niveis = st.sidebar.multiselect("Nível de desempenho", ORDEM_NIVEL, placeholder="Todos os níveis")

df = base[base["ano"].between(*anos)]
if semestres:
    df = df[df["semestre"].isin(semestres)]
if regioes:
    df = df[df["regiao"].isin(regioes)]
if ufs:
    df = df[df["uf"].isin(ufs)]
if redes:
    df = df[df["rede_ensino"].isin(redes)]
if disciplinas:
    df = df[df["disciplina"].isin(disciplinas)]
if niveis:
    df = df[df["nivel_desempenho"].isin(niveis)]

st.sidebar.markdown("---")
st.sidebar.metric("Registros selecionados", len(df), f"de {len(base)}", delta_color="off")
st.sidebar.caption("Fonte: dataset simulado fornecido pela disciplina (2015–2024).")

# --------------------------------------------------------------------------- #
# Título e descrição do problema
# --------------------------------------------------------------------------- #
st.title("🎓 Desempenho Escolar no Brasil (2015–2024)")
st.caption("Disciplina: Linguagem de Programação · Aluno: Pedro Augusto · Professor: Alexandre Neves Louzada ")
st.markdown(
    """
    O desempenho escolar é um indicador central da qualidade da educação e influencia formação profissional,
    inclusão social e desenvolvimento econômico. Este dashboard analisa uma base **simulada** com médias de notas,
    taxas de aprovação e reprovação, acesso à internet, renda familiar e índice de desempenho, por **região, estado,
    rede de ensino e disciplina**, para responder:

    1. Quais estados apresentam melhor desempenho? 2. Existem diferenças entre redes pública e privada?
    3. Houve melhoria ao longo do tempo? 4. Existe relação entre renda e desempenho?
    5. Como o acesso à internet impacta o aprendizado? 6. Quais disciplinas têm menor rendimento?
    7. Existem desigualdades regionais relevantes?
    """
)

if df.empty:
    st.warning("Nenhum registro atende aos filtros selecionados. Ajuste os filtros na barra lateral.")
    st.stop()

# --------------------------------------------------------------------------- #
# KPIs
# --------------------------------------------------------------------------- #
st.header("Indicadores-chave")
por_uf = df.groupby("uf")["indice_desempenho"].mean().sort_values(ascending=False)
por_rede = df.groupby("rede_ensino")["media_notas"].mean().sort_values(ascending=False)
por_disc = df.groupby("disciplina")["media_notas"].mean().sort_values()

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Média geral das notas", f"{df['media_notas'].mean():.1f}", f"{df['media_notas'].mean() - base['media_notas'].mean():+.1f} vs. base")
k2.metric("Taxa média de aprovação", f"{df['taxa_aprovacao'].mean():.1f}%", f"{df['taxa_aprovacao'].mean() - base['taxa_aprovacao'].mean():+.1f} vs. base")
k3.metric("Índice médio de desempenho", f"{df['indice_desempenho'].mean():.1f}", f"{df['indice_desempenho'].mean() - base['indice_desempenho'].mean():+.1f} vs. base")
k4.metric("Estado com melhor desempenho", por_uf.index[0], f"índice {por_uf.iloc[0]:.1f}", delta_color="off")
k5.metric("Rede com maior desempenho", por_rede.index[0], f"nota {por_rede.iloc[0]:.1f}", delta_color="off")
k6.metric("Disciplina mais crítica", por_disc.index[0], f"nota {por_disc.iloc[0]:.1f}", delta_color="off")

metrica = st.radio("Métrica dos gráficos", ["media_notas", "indice_desempenho", "taxa_aprovacao", "taxa_reprovacao"], format_func=lambda m: ROTULOS[m], horizontal=True)

# --------------------------------------------------------------------------- #
# 1. Evolução temporal (linha + média móvel)
# --------------------------------------------------------------------------- #
st.header("Evolução temporal")
serie = df.groupby(["ano", "semestre", "periodo"])[metrica].mean().reset_index().sort_values(["ano", "semestre"])
janela = st.slider("Janela da média móvel (semestres)", 1, 6, 4)
serie["media_movel"] = serie[metrica].rolling(janela, min_periods=1).mean()
coef = np.polyfit(np.arange(len(serie)), serie[metrica], 1) if len(serie) >= 2 else np.array([0.0, serie[metrica].mean()])

fig = go.Figure()
fig.add_trace(go.Scatter(x=serie["periodo"], y=serie[metrica], mode="lines+markers", name=ROTULOS[metrica], line=dict(color="#264653", width=3)))
fig.add_trace(go.Scatter(x=serie["periodo"], y=serie["media_movel"], mode="lines", name=f"Média móvel ({janela} semestres)", line=dict(color="#2A9D8F", width=2, dash="dash")))
fig.add_trace(go.Scatter(x=serie["periodo"], y=np.polyval(coef, np.arange(len(serie))), mode="lines", name=f"Tendência ({coef[0]:+.2f}/semestre)", line=dict(color="#E76F51", dash="dot")))
fig.update_xaxes(tickangle=-45)
st.plotly_chart(layout(fig, f"{ROTULOS[metrica]} por semestre"), width="stretch")

c1, c2 = st.columns(2)
with c1:
    serie_rede = df.groupby(["ano", "semestre", "periodo", "rede_ensino"])[metrica].mean().reset_index().sort_values(["ano", "semestre"])
    fig = px.line(serie_rede, x="periodo", y=metrica, color="rede_ensino", markers=True, color_discrete_map=CORES_REDE, labels=ROTULOS)
    fig.update_xaxes(tickangle=-45)
    st.plotly_chart(layout(fig, f"{ROTULOS[metrica]} por semestre e rede"), width="stretch")
with c2:
    # Heatmap semestral (Seaborn)
    heat = df.pivot_table(index="regiao", columns="periodo", values=metrica, aggfunc="mean", observed=True)
    heat = heat[sorted(heat.columns, key=lambda p: (int(p[:4]), int(p[-1])))]
    fig_h, ax = plt.subplots(figsize=(9, 3.6))
    sns.heatmap(heat, annot=True, fmt=".0f", cmap="YlGnBu", linewidths=0.4, annot_kws={"size": 7}, cbar_kws={"shrink": 0.8}, ax=ax)
    ax.set_title(f"Heatmap semestral — {ROTULOS[metrica].lower()} por região", loc="left", fontweight="bold")
    ax.set_xlabel("")
    ax.set_ylabel("")
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", fontsize=7)
    fig_h.tight_layout()
    st.pyplot(fig_h, width="stretch")

# --------------------------------------------------------------------------- #
# 2. Comparação regional e por estado
# --------------------------------------------------------------------------- #
st.header("Comparação regional")
rank = df.groupby(["uf", "regiao"], observed=True)[metrica].mean().reset_index().sort_values(metrica, ascending=False)
c1, c2 = st.columns([1.2, 1])
with c1:
    fig = px.bar(rank, x=metrica, y="uf", color="regiao", orientation="h", color_discrete_map=CORES_REGIAO, labels=ROTULOS, text=rank[metrica].round(1), category_orders={"regiao": ORDEM_REGIAO})
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_yaxes(categoryorder="total ascending")
    fig.add_vline(x=df[metrica].mean(), line_dash="dot", line_color="#555", annotation_text=f"média {df[metrica].mean():.1f}")
    st.plotly_chart(layout(fig, f"Ranking de estados — {ROTULOS[metrica].lower()}", altura=max(420, 24 * len(rank) + 120)), width="stretch")
with c2:
    reg = df.groupby(["regiao", "rede_ensino"], observed=True)[metrica].mean().reset_index()
    fig = px.bar(reg, x="regiao", y=metrica, color="rede_ensino", barmode="group", color_discrete_map=CORES_REDE, labels=ROTULOS, text=reg[metrica].round(1), category_orders={"regiao": ORDEM_REGIAO})
    fig.update_traces(textposition="outside", cliponaxis=False)
    st.plotly_chart(layout(fig, f"{ROTULOS[metrica]} por região e rede"), width="stretch")
    fig = px.box(df, x="regiao", y=metrica, color="regiao", color_discrete_map=CORES_REGIAO, labels=ROTULOS, category_orders={"regiao": ORDEM_REGIAO})
    fig.update_layout(showlegend=False)
    st.plotly_chart(layout(fig, f"Distribuição de {ROTULOS[metrica].lower()} por região", altura=380), width="stretch")

# --------------------------------------------------------------------------- #
# 3. Redes de ensino e disciplinas
# --------------------------------------------------------------------------- #
st.header("Redes de ensino e disciplinas")
c1, c2 = st.columns(2)
with c1:
    disc = df.groupby(["disciplina", "rede_ensino"])[metrica].mean().reset_index()
    fig = px.bar(disc, x="disciplina", y=metrica, color="rede_ensino", barmode="group", color_discrete_map=CORES_REDE, labels=ROTULOS, text=disc[metrica].round(1))
    fig.update_traces(textposition="outside", cliponaxis=False)
    st.plotly_chart(layout(fig, f"{ROTULOS[metrica]} por disciplina e rede"), width="stretch")
with c2:
    fig = px.box(df, x="rede_ensino", y=metrica, color="rede_ensino", color_discrete_map=CORES_REDE, labels=ROTULOS)
    fig.update_layout(showlegend=False)
    st.plotly_chart(layout(fig, f"Distribuição de {ROTULOS[metrica].lower()} por rede"), width="stretch")

tabela_disc = df.groupby("disciplina")[["media_notas", "taxa_aprovacao", "taxa_reprovacao", "indice_desempenho"]].mean().sort_values("media_notas").rename(columns=ROTULOS)
st.dataframe(tabela_disc.style.format("{:.1f}").background_gradient(subset=["Média das notas"], cmap="RdYlGn"), width="stretch")

# --------------------------------------------------------------------------- #
# 4. Fatores socioeconômicos e correlação
# --------------------------------------------------------------------------- #
st.header("Renda, internet e correlação")
c1, c2 = st.columns(2)
for coluna, (x, titulo) in zip((c1, c2), [("renda_media_familiar", "Renda × notas"), ("acesso_internet", "Internet × notas")]):
    with coluna:
        r, p = correlacao(df, x, "media_notas")
        fig = px.scatter(df, x=x, y="media_notas", color="rede_ensino", opacity=0.65, color_discrete_map=CORES_REDE, labels=ROTULOS, hover_data=["uf", "municipio", "disciplina", "ano"])
        if len(df) >= 2:
            xs = np.linspace(df[x].min(), df[x].max(), 50)
            c = np.polyfit(df[x], df["media_notas"], 1)
            fig.add_trace(go.Scatter(x=xs, y=np.polyval(c, xs), mode="lines", name="Tendência linear", line=dict(color="#333", dash="dash")))
        st.plotly_chart(layout(fig, f"{titulo} (r = {r:+.3f}, p ≈ {p:.3f})"), width="stretch")
r_renda, _ = correlacao(df, "renda_media_familiar", "media_notas")
r_net, _ = correlacao(df, "acesso_internet", "media_notas")

c1, c2 = st.columns(2)
with c1:
    matriz = df[NUMERICAS].corr()
    fig_c, ax = plt.subplots(figsize=(7, 5.5))
    sns.heatmap(matriz.rename(index=ROTULOS, columns=ROTULOS), mask=np.triu(np.ones_like(matriz, dtype=bool)), annot=True, fmt=".2f", cmap="RdBu_r", vmin=-1, vmax=1, center=0, square=True, linewidths=0.5, ax=ax)
    ax.set_title("Matriz de correlação de Pearson", loc="left", fontweight="bold")
    plt.setp(ax.get_xticklabels(), rotation=35, ha="right")
    fig_c.tight_layout()
    st.pyplot(fig_c, width="stretch")
with c2:
    for col, rotulo, titulo in [("faixa_renda", "Faixa de renda", "Média das notas por quartil de renda"), ("faixa_internet", "Acesso à internet", "Média das notas por faixa de acesso à internet")]:
        faixas = df.groupby([col, "rede_ensino"], observed=True)["media_notas"].mean().reset_index()
        fig = px.bar(faixas, x=col, y="media_notas", color="rede_ensino", barmode="group", color_discrete_map=CORES_REDE, labels=ROTULOS | {col: rotulo}, text=faixas["media_notas"].round(1))
        fig.update_traces(textposition="outside", cliponaxis=False)
        st.plotly_chart(layout(fig, titulo, altura=300), width="stretch")

# --------------------------------------------------------------------------- #
# 5. Tabela dinâmica e dados
# --------------------------------------------------------------------------- #
st.header("Tabela dinâmica")
c1, c2, c3 = st.columns(3)
linhas = c1.multiselect("Linhas", ["regiao", "uf", "rede_ensino", "disciplina", "nivel_desempenho", "ano"], default=["regiao", "rede_ensino"], format_func=lambda c: ROTULOS.get(c, c))
colunas = c2.selectbox("Colunas", [None, "ano", "semestre", "rede_ensino", "disciplina", "nivel_desempenho"], format_func=lambda c: "— nenhuma —" if c is None else ROTULOS.get(c, c))
valor = c3.selectbox("Valor", NUMERICAS, format_func=lambda c: ROTULOS[c])
if linhas:
    pivo = pd.pivot_table(df, index=linhas, columns=colunas, values=valor, aggfunc="mean", observed=True, margins=True, margins_name="Total")
    st.dataframe(pivo.style.format("{:.1f}").background_gradient(cmap="YlGnBu", axis=None), width="stretch")

with st.expander("Ver dados filtrados"):
    st.dataframe(df.drop(columns=["data"]), width="stretch", hide_index=True)
    st.download_button("Baixar CSV filtrado", df.to_csv(index=False).encode("utf-8-sig"), "desempenho_escolar_filtrado.csv", "text/csv")

# --------------------------------------------------------------------------- #
# Interpretação e conclusão
# --------------------------------------------------------------------------- #
st.header("Interpretação dos resultados")
variacao = serie[metrica].iloc[-1] - serie[metrica].iloc[0]
tendencia = "melhora" if coef[0] > 0.05 else "piora" if coef[0] < -0.05 else "estabilidade"
melhor, pior = rank.iloc[0], rank.iloc[-1]
por_regiao = df.groupby("regiao", observed=True)[metrica].mean().sort_values(ascending=False)
dif_rede = por_rede.get("Privada", np.nan) - por_rede.get("Pública", np.nan)
inconsist = df["taxas_inconsistentes"].mean() * 100
texto_rede = (
    f"a nota média da rede privada é {dif_rede:+.2f} pontos em relação à pública — "
    + ("diferença pequena; nesta base, a rede não separa os resultados." if abs(dif_rede) < 2 else "diferença relevante.")
    if not np.isnan(dif_rede)
    else "selecione as duas redes para comparar pública e privada."
)

st.markdown(
    f"""
    - **Evolução temporal:** entre {serie['periodo'].iloc[0]} e {serie['periodo'].iloc[-1]}, a métrica *{ROTULOS[metrica].lower()}* variou
      {variacao:+.1f} pontos, com tendência de {coef[0]:+.2f} por semestre, o que indica **{tendencia}**. A média móvel mostra oscilações
      curtas sem direção consistente.
    - **Estados:** {melhor['uf']} lidera ({melhor[metrica]:.1f}) e {pior['uf']} tem o menor valor ({pior[metrica]:.1f}); amplitude de
      {melhor[metrica] - pior[metrica]:.1f} pontos.
    - **Regiões:** {por_regiao.index[0]} tem a maior média ({por_regiao.iloc[0]:.1f}) e {por_regiao.index[-1]} a menor ({por_regiao.iloc[-1]:.1f}).
      A dispersão dentro de cada região (boxplots) é maior do que a diferença entre regiões.
    - **Redes de ensino:** {texto_rede}
    - **Disciplinas:** {por_disc.index[0]} é a mais crítica ({por_disc.iloc[0]:.1f}) e {por_disc.index[-1]} a de melhor rendimento ({por_disc.iloc[-1]:.1f}).
    - **Fatores socioeconômicos:** correlação renda × notas {forca(r_renda)} (r = {r_renda:+.3f}) e internet × notas {forca(r_net)}
      (r = {r_net:+.3f}). Em dados reais essas correlações costumam ser positivas e moderadas.
    - **Qualidade dos dados:** {inconsist:.0f}% dos registros têm aprovação + reprovação acima de 100%, sinal de que a base é simulada
      com variáveis geradas de forma independente.
    """
)

st.header("Conclusão executiva")
st.success(
    f"""
    1. Para a seleção atual, a média geral das notas é **{df['media_notas'].mean():.1f}**, a taxa de aprovação **{df['taxa_aprovacao'].mean():.1f}%**
       e o índice de desempenho **{df['indice_desempenho'].mean():.1f}**.
    2. **{melhor['uf']}** é o estado de referência e **{pior['uf']}** o mais crítico; a região **{por_regiao.index[-1]}** merece prioridade.
    3. A diferença entre redes pública e privada é de {abs(dif_rede) if not np.isnan(dif_rede) else 0:.1f} ponto(s), e a tendência temporal indica **{tendencia}**.
    4. Renda e acesso à internet têm correlação {forca(r_renda)} com as notas nesta base.
    5. **{por_disc.index[0]}** é a disciplina que demanda reforço pedagógico.

    *Os dados são simulados: as conclusões demonstram o método analítico e não um diagnóstico real da educação brasileira.*
    """
)
st.caption("Projeto G1 · Análise e Visualização de Dados com Python · Streamlit, Pandas, NumPy, Matplotlib, Seaborn e Plotly")
