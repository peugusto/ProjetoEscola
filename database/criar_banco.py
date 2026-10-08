"""
Cria (ou recria) o banco SQLite `database/desempenho_escolar.db` a partir do
CSV tratado, usando o modelo relacional de `modelos.py`.

Uso:
    python database/criar_banco.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import Session

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from database.modelos import Avaliacao, Base, Disciplina, Estado, Municipio, Regiao  # noqa: E402
from utils.dados import CAMINHO_DB, NOMES_UF, preparar_base  # noqa: E402


def obter_engine(caminho: Path | None = None):
    caminho = caminho or CAMINHO_DB
    return create_engine(f"sqlite:///{caminho}", future=True)


def banco_disponivel(caminho: Path | None = None) -> bool:
    caminho = caminho or CAMINHO_DB
    return caminho.exists() and caminho.stat().st_size > 0


def criar_banco(df: pd.DataFrame | None = None, caminho: Path | None = None, codigos_ibge: dict | None = None) -> Path:
    """Popula o banco. Retorna o caminho do arquivo criado."""
    caminho = caminho or CAMINHO_DB
    caminho.parent.mkdir(parents=True, exist_ok=True)
    if caminho.exists():
        caminho.unlink()

    df = df if df is not None else preparar_base()
    engine = obter_engine(caminho)
    Base.metadata.create_all(engine)

    with Session(engine) as sessao:
        # Dimensões.
        regioes = {nome: Regiao(nome=nome) for nome in df["regiao"].astype(str).unique()}
        sessao.add_all(regioes.values())
        sessao.flush()

        estados: dict[str, Estado] = {}
        for (sigla, regiao_nome), _ in df.groupby(["uf", df["regiao"].astype(str)], observed=True):
            estados[sigla] = Estado(
                sigla=sigla,
                nome=NOMES_UF.get(sigla, sigla),
                codigo_ibge=(codigos_ibge or {}).get(sigla),
                regiao=regioes[regiao_nome],
            )
        sessao.add_all(estados.values())
        sessao.flush()

        municipios: dict[tuple[str, str], Municipio] = {}
        for (sigla, nome), _ in df.groupby(["uf", "municipio"], observed=True):
            municipios[(sigla, nome)] = Municipio(nome=nome, estado=estados[sigla])
        sessao.add_all(municipios.values())

        disciplinas = {nome: Disciplina(nome=nome) for nome in sorted(df["disciplina"].unique())}
        sessao.add_all(disciplinas.values())
        sessao.flush()

        # Fato.
        registros = [
            Avaliacao(
                ano=int(linha.ano),
                semestre=int(linha.semestre),
                data=linha.data.date(),
                rede_ensino=str(linha.rede_ensino),
                municipio=municipios[(linha.uf, linha.municipio)],
                disciplina=disciplinas[linha.disciplina],
                media_notas=float(linha.media_notas),
                taxa_aprovacao=float(linha.taxa_aprovacao),
                taxa_reprovacao=float(linha.taxa_reprovacao),
                acesso_internet=float(linha.acesso_internet),
                renda_media_familiar=float(linha.renda_media_familiar),
                indice_desempenho=float(linha.indice_desempenho),
                nivel_desempenho=str(linha.nivel_desempenho),
                nivel_calculado=str(linha.nivel_calculado),
                taxas_inconsistentes=bool(linha.taxas_inconsistentes),
            )
            for linha in df.itertuples(index=False)
        ]
        sessao.add_all(registros)
        sessao.commit()

    # Visão analítica (desnormalizada) para consultas SQL simples no dashboard.
    with engine.begin() as conexao:
        conexao.execute(text("DROP VIEW IF EXISTS vw_desempenho"))
        conexao.execute(
            text(
                """
                CREATE VIEW vw_desempenho AS
                SELECT f.id, f.ano, f.semestre, f.data,
                       r.nome AS regiao, e.sigla AS uf, e.nome AS estado, m.nome AS municipio,
                       f.rede_ensino, d.nome AS disciplina,
                       f.media_notas, f.taxa_aprovacao, f.taxa_reprovacao,
                       f.acesso_internet, f.renda_media_familiar, f.indice_desempenho,
                       f.nivel_desempenho, f.nivel_calculado, f.taxas_inconsistentes
                FROM fato_avaliacao f
                JOIN dim_municipio m ON m.id = f.municipio_id
                JOIN dim_estado e ON e.id = m.estado_id
                JOIN dim_regiao r ON r.id = e.regiao_id
                JOIN dim_disciplina d ON d.id = f.disciplina_id
                """
            )
        )
    return caminho


def consultar(sql: str, caminho: Path | None = None) -> pd.DataFrame:
    """Executa uma consulta SQL de leitura e devolve um DataFrame."""
    engine = obter_engine(caminho)
    with engine.connect() as conexao:
        return pd.read_sql_query(text(sql), conexao)


def resumo_banco(caminho: Path | None = None) -> pd.DataFrame:
    """Contagem de linhas por tabela, para exibir no dashboard."""
    engine = obter_engine(caminho)
    linhas = []
    with Session(engine) as sessao:
        for modelo in (Regiao, Estado, Municipio, Disciplina, Avaliacao):
            total = sessao.execute(select(func.count()).select_from(modelo)).scalar_one()
            linhas.append({"tabela": modelo.__tablename__, "linhas": total})
    return pd.DataFrame(linhas)


if __name__ == "__main__":
    destino = criar_banco()
    print(f"Banco criado em: {destino}")
    print(resumo_banco().to_string(index=False))
