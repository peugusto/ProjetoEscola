"""
Camada de dados do projeto: leitura, tratamento, engenharia de atributos,
filtros e KPIs. É compartilhada pelo dashboard (app.py e pages/), pelo
notebook e pelo script de criação do banco SQLite.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------- #
# Caminhos
# --------------------------------------------------------------------------- #
RAIZ = Path(__file__).resolve().parent.parent
CAMINHO_CSV = RAIZ / "dados" / "simulacao_desempenho_escolar_brasil.csv"
CAMINHO_CSV_TRATADO = RAIZ / "dados" / "desempenho_escolar_tratado.csv"
CAMINHO_DB = RAIZ / "database" / "desempenho_escolar.db"
PASTA_IMAGENS = RAIZ / "imagens"

# --------------------------------------------------------------------------- #
# Constantes de domínio
# --------------------------------------------------------------------------- #
ORDEM_NIVEL = ["Baixo", "Médio", "Alto", "Excelente"]
ORDEM_REGIAO = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]
COLUNAS_NUMERICAS = [
    "media_notas",
    "taxa_aprovacao",
    "taxa_reprovacao",
    "acesso_internet",
    "renda_media_familiar",
    "indice_desempenho",
]
ROTULOS = {
    "media_notas": "Média das notas",
    "taxa_aprovacao": "Taxa de aprovação (%)",
    "taxa_reprovacao": "Taxa de reprovação (%)",
    "acesso_internet": "Acesso à internet (%)",
    "renda_media_familiar": "Renda média familiar (R$)",
    "indice_desempenho": "Índice de desempenho",
    "ano": "Ano",
    "semestre": "Semestre",
    "regiao": "Região",
    "uf": "UF",
    "municipio": "Município",
    "rede_ensino": "Rede de ensino",
    "disciplina": "Disciplina",
    "nivel_desempenho": "Nível de desempenho",
    "periodo": "Período",
    "faixa_renda": "Faixa de renda",
    "faixa_internet": "Faixa de acesso à internet",
    "nivel_calculado": "Nível calculado (pelo índice)",
}

# Nomes dos estados — usado como reserva caso a API do IBGE esteja indisponível.
NOMES_UF = {
    "AC": "Acre", "AL": "Alagoas", "AM": "Amazonas", "AP": "Amapá", "BA": "Bahia",
    "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás",
    "MA": "Maranhão", "MG": "Minas Gerais", "MS": "Mato Grosso do Sul",
    "MT": "Mato Grosso", "PA": "Pará", "PB": "Paraíba", "PE": "Pernambuco",
    "PI": "Piauí", "PR": "Paraná", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte",
    "RO": "Rondônia", "RR": "Roraima", "RS": "Rio Grande do Sul", "SC": "Santa Catarina",
    "SE": "Sergipe", "SP": "São Paulo", "TO": "Tocantins",
}

# Coordenadas aproximadas das capitais — reserva para o mapa quando o GeoJSON
# não puder ser baixado.
COORDENADAS_UF = {
    "AM": (-3.12, -60.02), "PA": (-1.46, -48.49), "RO": (-8.76, -63.90), "TO": (-10.18, -48.33),
    "BA": (-12.97, -38.51), "PE": (-8.05, -34.88), "CE": (-3.72, -38.54), "MA": (-2.53, -44.30),
    "PB": (-7.12, -34.86), "DF": (-15.79, -47.88), "GO": (-16.68, -49.25), "MT": (-15.60, -56.10),
    "MS": (-20.44, -54.65), "SP": (-23.55, -46.63), "RJ": (-22.91, -43.17), "MG": (-19.92, -43.94),
    "ES": (-20.32, -40.34), "PR": (-25.43, -49.27), "SC": (-27.59, -48.55), "RS": (-30.03, -51.23),
    "AC": (-9.97, -67.81), "AP": (0.03, -51.07), "RR": (2.82, -60.67), "AL": (-9.67, -35.74),
    "SE": (-10.91, -37.07), "RN": (-5.79, -35.21), "PI": (-5.09, -42.80),
}


# --------------------------------------------------------------------------- #
# Leitura
# --------------------------------------------------------------------------- #
def carregar_dados_brutos(caminho: str | Path | None = None) -> pd.DataFrame:
    """Lê o CSV original. Aceita caminho alternativo ou objeto tipo arquivo (upload)."""
    origem = caminho if caminho is not None else CAMINHO_CSV
    return pd.read_csv(origem, encoding="utf-8-sig")


# --------------------------------------------------------------------------- #
# Limpeza e preparação
# --------------------------------------------------------------------------- #
def tratar_dados(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpeza e preparação:
    - padroniza nomes de colunas e textos;
    - converte tipos (datas, inteiros, numéricos);
    - remove duplicatas e linhas sem chave;
    - trata valores ausentes nas métricas (mediana por UF/disciplina);
    - limita percentuais ao intervalo [0, 100];
    - cria flag de inconsistência quando aprovação + reprovação > 100 %.
    """
    df = df.copy()
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # Textos: remove espaços extras e padroniza capitalização de rede/região.
    for col in ["regiao", "uf", "municipio", "rede_ensino", "disciplina", "nivel_desempenho"]:
        if col in df.columns:
            df[col] = df[col].astype("string").str.strip()
    if "uf" in df.columns:
        df["uf"] = df["uf"].str.upper()
    if "rede_ensino" in df.columns:
        df["rede_ensino"] = df["rede_ensino"].str.capitalize()

    # Tipos.
    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    df["ano"] = pd.to_numeric(df["ano"], errors="coerce")
    df["semestre"] = pd.to_numeric(df["semestre"], errors="coerce")
    for col in COLUNAS_NUMERICAS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Linhas sem chave temporal/geográfica não têm uso analítico.
    df = df.dropna(subset=["ano", "semestre", "uf", "disciplina"])
    df["ano"] = df["ano"].astype(int)
    df["semestre"] = df["semestre"].astype(int)

    # Datas ausentes são reconstruídas a partir de ano/semestre.
    mes = np.where(df["semestre"] == 1, 6, 12)
    data_reconstruida = pd.to_datetime(
        {"year": df["ano"], "month": mes, "day": 1}, errors="coerce"
    )
    df["data"] = df["data"].fillna(data_reconstruida)

    # Duplicatas exatas.
    df = df.drop_duplicates().reset_index(drop=True)

    # Valores ausentes nas métricas: mediana do grupo (UF, disciplina), depois geral.
    for col in COLUNAS_NUMERICAS:
        if df[col].isna().any():
            df[col] = df[col].fillna(df.groupby(["uf", "disciplina"])[col].transform("median"))
            df[col] = df[col].fillna(df[col].median())

    # Percentuais fora de [0, 100] são erros de registro.
    for col in ["taxa_aprovacao", "taxa_reprovacao", "acesso_internet"]:
        df[col] = df[col].clip(lower=0, upper=100)

    # Flag de inconsistência (a base simulada gera taxas independentes).
    df["taxas_inconsistentes"] = (df["taxa_aprovacao"] + df["taxa_reprovacao"]) > 100.0

    # Categorias ordenadas.
    df["nivel_desempenho"] = pd.Categorical(
        df["nivel_desempenho"].astype(str), categories=ORDEM_NIVEL, ordered=True
    )
    df["regiao"] = pd.Categorical(
        df["regiao"].astype(str), categories=ORDEM_REGIAO, ordered=True
    )
    return df


# --------------------------------------------------------------------------- #
# Engenharia de atributos
# --------------------------------------------------------------------------- #
def engenharia_atributos(df: pd.DataFrame) -> pd.DataFrame:
    """
    Novas variáveis:
    - periodo: rótulo "AAAA/S1" para séries temporais e heatmap semestral;
    - nome_uf: nome completo do estado;
    - faixa_renda: quartis da renda média familiar;
    - faixa_internet: faixas de acesso digital;
    - nivel_calculado: nível derivado do índice de desempenho (faixas fixas);
    - score_composto: média entre nota e índice, em escala 0–100;
    - periodo_pandemia: marcador para 2020–2021.
    """
    df = df.copy()
    df["periodo"] = df["ano"].astype(str) + "/S" + df["semestre"].astype(str)
    df["nome_uf"] = df["uf"].map(NOMES_UF).fillna(df["uf"])

    df["faixa_renda"] = pd.qcut(
        df["renda_media_familiar"],
        q=4,
        labels=["Q1 (menor renda)", "Q2", "Q3", "Q4 (maior renda)"],
    )
    df["faixa_internet"] = pd.cut(
        df["acesso_internet"],
        bins=[0, 50, 65, 80, 100],
        labels=["Até 50%", "50–65%", "65–80%", "Acima de 80%"],
        include_lowest=True,
    )
    df["nivel_calculado"] = pd.cut(
        df["indice_desempenho"],
        bins=[0, 50, 65, 80, 100],
        labels=ORDEM_NIVEL,
        include_lowest=True,
    )
    df["score_composto"] = ((df["media_notas"] + df["indice_desempenho"]) / 2).round(2)
    df["periodo_pandemia"] = df["ano"].between(2020, 2021)
    return df


def preparar_base(caminho: str | Path | None = None) -> pd.DataFrame:
    """Pipeline completo: leitura -> tratamento -> engenharia de atributos."""
    return engenharia_atributos(tratar_dados(carregar_dados_brutos(caminho)))


# --------------------------------------------------------------------------- #
# Filtros
# --------------------------------------------------------------------------- #
def aplicar_filtros(
    df: pd.DataFrame,
    anos: tuple[int, int] | None = None,
    semestres: list[int] | None = None,
    regioes: list[str] | None = None,
    ufs: list[str] | None = None,
    redes: list[str] | None = None,
    disciplinas: list[str] | None = None,
    niveis: list[str] | None = None,
) -> pd.DataFrame:
    """Aplica os filtros obrigatórios do dashboard. Listas vazias/None não filtram."""
    mascara = pd.Series(True, index=df.index)
    if anos:
        mascara &= df["ano"].between(anos[0], anos[1])
    if semestres:
        mascara &= df["semestre"].isin(semestres)
    if regioes:
        mascara &= df["regiao"].isin(regioes)
    if ufs:
        mascara &= df["uf"].isin(ufs)
    if redes:
        mascara &= df["rede_ensino"].isin(redes)
    if disciplinas:
        mascara &= df["disciplina"].isin(disciplinas)
    if niveis:
        mascara &= df["nivel_desempenho"].isin(niveis)
    return df[mascara]


# --------------------------------------------------------------------------- #
# KPIs
# --------------------------------------------------------------------------- #
def calcular_kpis(df: pd.DataFrame) -> dict:
    """KPIs exigidos pelo tema. Retorna dicionário com valores e rótulos."""
    if df.empty:
        return {
            "media_notas": np.nan,
            "taxa_aprovacao": np.nan,
            "indice_desempenho": np.nan,
            "melhor_uf": "—",
            "melhor_uf_valor": np.nan,
            "melhor_rede": "—",
            "melhor_rede_valor": np.nan,
            "disciplina_critica": "—",
            "disciplina_critica_valor": np.nan,
            "registros": 0,
        }
    por_uf = df.groupby("uf", observed=True)["indice_desempenho"].mean().sort_values(ascending=False)
    por_rede = df.groupby("rede_ensino", observed=True)["media_notas"].mean().sort_values(ascending=False)
    por_disc = df.groupby("disciplina", observed=True)["media_notas"].mean().sort_values()
    return {
        "media_notas": float(df["media_notas"].mean()),
        "taxa_aprovacao": float(df["taxa_aprovacao"].mean()),
        "indice_desempenho": float(df["indice_desempenho"].mean()),
        "melhor_uf": por_uf.index[0],
        "melhor_uf_valor": float(por_uf.iloc[0]),
        "melhor_rede": por_rede.index[0],
        "melhor_rede_valor": float(por_rede.iloc[0]),
        "disciplina_critica": por_disc.index[0],
        "disciplina_critica_valor": float(por_disc.iloc[0]),
        "registros": int(len(df)),
    }


# --------------------------------------------------------------------------- #
# Agregações reutilizadas em gráficos
# --------------------------------------------------------------------------- #
def serie_temporal(df: pd.DataFrame, metrica: str = "media_notas", por: str | None = None) -> pd.DataFrame:
    """Média da métrica por período (ano/semestre), opcionalmente segmentada."""
    chaves = ["ano", "semestre", "periodo"] + ([por] if por else [])
    return (
        df.groupby(chaves, observed=True)[metrica]
        .mean()
        .reset_index()
        .sort_values(["ano", "semestre"])
    )


def ranking_uf(df: pd.DataFrame, metrica: str = "indice_desempenho") -> pd.DataFrame:
    """Ranking de estados pela média da métrica, com região e nome do estado."""
    return (
        df.groupby(["regiao", "uf", "nome_uf"], observed=True)
        .agg(valor=(metrica, "mean"), registros=(metrica, "size"))
        .reset_index()
        .sort_values("valor", ascending=False)
        .reset_index(drop=True)
    )


def matriz_heatmap(df: pd.DataFrame, metrica: str = "media_notas", linhas: str = "regiao") -> pd.DataFrame:
    """Tabela linhas x período para heatmap semestral."""
    tabela = df.pivot_table(index=linhas, columns="periodo", values=metrica, aggfunc="mean", observed=True)
    colunas_ordenadas = sorted(tabela.columns, key=lambda p: (int(p[:4]), int(p[-1])))
    return tabela[colunas_ordenadas]


def correlacoes(df: pd.DataFrame) -> pd.DataFrame:
    """Matriz de correlação de Pearson entre as variáveis numéricas."""
    return df[COLUNAS_NUMERICAS].corr(method="pearson")


def correlacao_com_significancia(df: pd.DataFrame, x: str, y: str) -> dict:
    """
    Correlação de Pearson com teste de significância (estatística t, aproximação
    pela distribuição normal para n grande). Implementado só com NumPy/Pandas,
    sem dependência do SciPy.
    """
    sub = df[[x, y]].dropna()
    n = len(sub)
    if n < 3:
        return {"r": np.nan, "n": n, "t": np.nan, "p_aprox": np.nan}
    r = float(sub[x].corr(sub[y]))
    r_ajustado = min(max(r, -0.999999), 0.999999)
    t = r_ajustado * np.sqrt((n - 2) / (1 - r_ajustado**2))
    # p-valor bicaudal aproximado pela normal padrão (válido para n > 30).
    p = float(2 * (1 - _cdf_normal(abs(t))))
    return {"r": r, "n": n, "t": float(t), "p_aprox": p}


def _cdf_normal(z: float) -> float:
    """Função de distribuição acumulada da normal padrão (via erf)."""
    from math import erf, sqrt

    return 0.5 * (1 + erf(z / sqrt(2)))


def interpretar_correlacao(r: float) -> str:
    """Descrição textual da força da correlação."""
    if np.isnan(r):
        return "indefinida"
    forca = abs(r)
    if forca < 0.1:
        grau = "praticamente nula"
    elif forca < 0.3:
        grau = "fraca"
    elif forca < 0.5:
        grau = "moderada"
    elif forca < 0.7:
        grau = "forte"
    else:
        grau = "muito forte"
    sinal = "positiva" if r > 0 else "negativa"
    return f"{grau} e {sinal}" if forca >= 0.1 else grau
