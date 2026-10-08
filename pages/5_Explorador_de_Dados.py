"""Página 5 — Explorador: tabela dinâmica, upload de CSV, banco SQLite e consultas SQL."""
from __future__ import annotations

import io

import pandas as pd
import streamlit as st

from database.criar_banco import CAMINHO_DB, banco_disponivel, consultar, criar_banco, resumo_banco
from utils.carga import obter_base, usando_upload
from utils.dados import COLUNAS_NUMERICAS, ROTULOS
from utils.filtros import filtros_sidebar, resumo_filtros
from utils.interface import aviso_vazio, cabecalho, configurar_pagina, interpretacao, rodape

configurar_pagina("Explorador de Dados", "🔎")
base = obter_base()
df = filtros_sidebar(base)

cabecalho(
    "Explorador de dados",
    "Tabela dinâmica configurável, download dos dados filtrados, upload de um novo CSV e consultas SQL "
    "diretamente no banco SQLite (SQLAlchemy).",
    "🔎",
)
st.caption(f"Seleção atual: **{resumo_filtros()}**")

aba_tabela, aba_dados, aba_upload, aba_sql = st.tabs(["📊 Tabela dinâmica", "🗂️ Dados tratados", "📂 Upload de CSV", "🗄️ Banco SQLite / SQL"])

# --------------------------------------------------------------------------- #
# Tabela dinâmica
# --------------------------------------------------------------------------- #
with aba_tabela:
    if df.empty:
        aviso_vazio()
    else:
        c1, c2, c3, c4 = st.columns(4)
        linhas = c1.multiselect("Linhas", ["regiao", "uf", "municipio", "rede_ensino", "disciplina", "nivel_desempenho", "ano", "semestre", "faixa_renda", "faixa_internet"], default=["regiao", "rede_ensino"], format_func=lambda c: ROTULOS[c])
        colunas = c2.selectbox("Colunas", [None, "ano", "semestre", "rede_ensino", "disciplina", "nivel_desempenho", "regiao"], format_func=lambda c: "— nenhuma —" if c is None else ROTULOS[c])
        valores = c3.selectbox("Valor", COLUNAS_NUMERICAS, format_func=lambda c: ROTULOS[c])
        agregacao = c4.selectbox("Agregação", ["mean", "median", "min", "max", "std", "count"], format_func=lambda a: {"mean": "Média", "median": "Mediana", "min": "Mínimo", "max": "Máximo", "std": "Desvio-padrão", "count": "Contagem"}[a])

        if not linhas:
            st.info("Escolha ao menos um campo para as linhas.")
        else:
            pivo = pd.pivot_table(df, index=linhas, columns=colunas, values=valores, aggfunc=agregacao, observed=True, margins=True, margins_name="Total")
            st.dataframe(pivo.style.format("{:.1f}").background_gradient(cmap="YlGnBu", axis=None), width="stretch")
            st.download_button("⬇️ Baixar tabela dinâmica (CSV)", pivo.to_csv(decimal=",", sep=";").encode("utf-8-sig"), "tabela_dinamica.csv", "text/csv")

# --------------------------------------------------------------------------- #
# Dados tratados
# --------------------------------------------------------------------------- #
with aba_dados:
    st.markdown(f"**{len(df)} registros** após filtros · {df.shape[1]} colunas (originais + atributos derivados)")
    colunas_exibir = st.multiselect("Colunas exibidas", df.columns.tolist(), default=["ano", "semestre", "regiao", "uf", "municipio", "rede_ensino", "disciplina", "media_notas", "taxa_aprovacao", "taxa_reprovacao", "acesso_internet", "renda_media_familiar", "indice_desempenho", "nivel_desempenho", "nivel_calculado"])
    busca = st.text_input("Buscar município ou UF", placeholder="Ex.: Recife, SP, Campinas")
    exibir = df[colunas_exibir] if colunas_exibir else df
    if busca:
        mascara = df["municipio"].str.contains(busca, case=False, na=False) | df["uf"].str.contains(busca, case=False, na=False)
        exibir = exibir[mascara]
    st.dataframe(exibir, width="stretch", hide_index=True, height=420)
    st.download_button("⬇️ Baixar dados filtrados (CSV)", exibir.to_csv(index=False).encode("utf-8-sig"), "desempenho_escolar_filtrado.csv", "text/csv")

    with st.expander("ℹ️ Tratamento aplicado e atributos derivados"):
        inconsist = int(df["taxas_inconsistentes"].sum()) if "taxas_inconsistentes" in df else 0
        concord = float((df["nivel_desempenho"].astype(str) == df["nivel_calculado"].astype(str)).mean() * 100) if len(df) else 0
        st.markdown(
            f"""
            **Limpeza:** padronização de textos e tipos, conversão de datas, remoção de duplicatas, imputação de ausentes pela mediana
            (UF × disciplina) e limitação de percentuais ao intervalo 0–100.

            **Verificações de consistência:** {inconsist} registros ({inconsist / max(len(df), 1) * 100:.1f}%) têm aprovação + reprovação acima de 100 %
            (marcados em `taxas_inconsistentes`). O nível de desempenho informado coincide com o nível recalculado a partir do índice
            em apenas {concord:.1f}% dos casos — por isso o dashboard mantém os dois campos.

            **Atributos derivados:** `periodo` (ano/semestre), `nome_uf`, `faixa_renda` (quartis), `faixa_internet`,
            `nivel_calculado`, `score_composto` e `periodo_pandemia`.
            """
        )

# --------------------------------------------------------------------------- #
# Upload
# --------------------------------------------------------------------------- #
with aba_upload:
    st.markdown(
        """
        Envie um CSV com a **mesma estrutura** do dataset original (colunas `ano, semestre, data, regiao, uf, municipio,
        rede_ensino, disciplina, media_notas, taxa_aprovacao, taxa_reprovacao, acesso_internet, renda_media_familiar,
        indice_desempenho, nivel_desempenho`). O arquivo passa pelo mesmo pipeline de tratamento e substitui a base em
        **todas as páginas** enquanto a sessão durar.
        """
    )
    arquivo = st.file_uploader("Arquivo CSV", type=["csv"])
    if arquivo is not None:
        conteudo = arquivo.getvalue()
        try:
            previa = pd.read_csv(io.BytesIO(conteudo), encoding="utf-8-sig", nrows=5)
            obrigatorias = {"ano", "semestre", "regiao", "uf", "municipio", "rede_ensino", "disciplina", "media_notas", "taxa_aprovacao", "taxa_reprovacao", "acesso_internet", "renda_media_familiar", "indice_desempenho", "nivel_desempenho"}
            faltando = obrigatorias - set(c.strip().lower() for c in previa.columns)
            if faltando:
                st.error(f"Colunas ausentes: {', '.join(sorted(faltando))}")
            else:
                st.dataframe(previa, width="stretch", hide_index=True)
                if st.button("✅ Usar este arquivo no dashboard", type="primary"):
                    st.session_state["csv_enviado"] = conteudo
                    st.success("Arquivo carregado. Todas as páginas agora usam esta base.")
                    st.rerun()
        except Exception as erro:  # noqa: BLE001
            st.error(f"Não foi possível ler o arquivo: {erro}")
    if usando_upload():
        st.info("Uma base enviada está ativa.")
        if st.button("↩️ Voltar para a base padrão"):
            st.session_state.pop("csv_enviado", None)
            st.rerun()

# --------------------------------------------------------------------------- #
# Banco SQLite + SQL
# --------------------------------------------------------------------------- #
with aba_sql:
    st.markdown(
        """
        Os dados tratados são persistidos em **SQLite** com modelagem relacional (esquema estrela) via **SQLAlchemy**:
        `dim_regiao` → `dim_estado` → `dim_municipio`, `dim_disciplina` e a tabela fato `fato_avaliacao`.
        A visão `vw_desempenho` junta tudo para consultas simples.
        """
    )
    col_a, col_b = st.columns([1, 2])
    with col_a:
        if not banco_disponivel():
            st.warning("Banco ainda não criado.")
        if st.button("🔁 (Re)criar banco a partir da base tratada"):
            with st.spinner("Gravando tabelas..."):
                criar_banco(base)
            st.success(f"Banco criado em `{CAMINHO_DB.name}`.")
        if banco_disponivel():
            st.dataframe(resumo_banco(), hide_index=True, width="stretch")
    with col_b:
        exemplos = {
            "Média de notas por região e rede": "SELECT regiao, rede_ensino, ROUND(AVG(media_notas), 2) AS media_notas, COUNT(*) AS registros\nFROM vw_desempenho\nGROUP BY regiao, rede_ensino\nORDER BY media_notas DESC;",
            "Top 5 estados por índice de desempenho": "SELECT uf, estado, ROUND(AVG(indice_desempenho), 2) AS indice\nFROM vw_desempenho\nGROUP BY uf, estado\nORDER BY indice DESC\nLIMIT 5;",
            "Disciplina mais crítica por ano": "SELECT ano, disciplina, ROUND(AVG(media_notas), 2) AS media\nFROM vw_desempenho\nGROUP BY ano, disciplina\nHAVING media = (SELECT MIN(m) FROM (SELECT AVG(media_notas) AS m FROM vw_desempenho v2 WHERE v2.ano = vw_desempenho.ano GROUP BY disciplina))\nORDER BY ano;",
            "Join explícito entre fato e dimensões": "SELECT r.nome AS regiao, e.sigla AS uf, m.nome AS municipio, d.nome AS disciplina,\n       ROUND(AVG(f.media_notas), 1) AS media_notas\nFROM fato_avaliacao f\nJOIN dim_municipio m ON m.id = f.municipio_id\nJOIN dim_estado e ON e.id = m.estado_id\nJOIN dim_regiao r ON r.id = e.regiao_id\nJOIN dim_disciplina d ON d.id = f.disciplina_id\nWHERE f.ano >= 2022\nGROUP BY 1, 2, 3, 4\nORDER BY media_notas DESC\nLIMIT 15;",
        }
        escolha = st.selectbox("Consultas de exemplo", list(exemplos))
        sql = st.text_area("SQL (somente leitura)", value=exemplos[escolha], height=180)
        if st.button("▶️ Executar consulta", type="primary", disabled=not banco_disponivel()):
            comando = sql.strip().lower()
            if not comando.startswith(("select", "with")):
                st.error("Apenas consultas SELECT são permitidas.")
            else:
                try:
                    resultado = consultar(sql)
                    st.success(f"{len(resultado)} linha(s) retornada(s).")
                    st.dataframe(resultado, width="stretch", hide_index=True)
                    st.download_button("⬇️ Baixar resultado (CSV)", resultado.to_csv(index=False).encode("utf-8-sig"), "consulta_sql.csv", "text/csv")
                except Exception as erro:  # noqa: BLE001
                    st.error(f"Erro na consulta: {erro}")

interpretacao(
    "O explorador permite validar as conclusões das demais páginas: a tabela dinâmica reproduz qualquer agregação, "
    "o upload testa o pipeline com novos dados e o SQL oferece um caminho independente (banco relacional) para conferir os números.",
    "💡 Para que serve esta página",
)
rodape()
