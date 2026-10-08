# 🎓 Desempenho Escolar no Brasil (2015–2024)

Projeto G1 — **Análise e Visualização de Dados com Python** · Tema 24

Aplicação analítica para investigar indicadores de desempenho escolar no Brasil entre 2015 e 2024:
evolução das notas, comparação entre regiões e estados, diferenças entre redes pública e privada,
análise por disciplina e relação com fatores socioeconômicos (renda e acesso à internet).

| Entrega | Link |
|---|---|
| 💻 Código-fonte (GitHub) | `https://github.com/SEU-USUARIO/projeto-desempenho-escolar` |
| 🌐 Página do projeto (GitHub Pages) | `https://SEU-USUARIO.github.io/projeto-desempenho-escolar/` |
| 📊 Dashboard (Streamlit Community Cloud) | `https://SEU-APP.streamlit.app` |
| 📓 Notebook de análise | [`notebooks/analise_desempenho_escolar.ipynb`](notebooks/analise_desempenho_escolar.ipynb) |

> Substitua os links acima após publicar (ver seção **Publicação**).

---

## 1. Problema e perguntas orientadoras

O desempenho escolar é um indicador central da qualidade da educação e influencia formação profissional,
inclusão social e desenvolvimento econômico. O projeto responde a sete perguntas:

1. Quais estados apresentam melhor desempenho escolar?
2. Existem diferenças entre escolas públicas e privadas?
3. Houve melhoria no desempenho ao longo do tempo?
4. Existe relação entre renda e desempenho?
5. Como o acesso à internet impacta o aprendizado?
6. Quais disciplinas apresentam menor rendimento?
7. Existem desigualdades regionais relevantes?

## 2. Base de dados

`dados/simulacao_desempenho_escolar_brasil.csv` — dataset **simulado** fornecido pela disciplina, com 740
observações (município × rede × disciplina × semestre) e as colunas:

`ano, semestre, data, regiao, uf, municipio, rede_ensino, disciplina, media_notas, taxa_aprovacao,
taxa_reprovacao, acesso_internet, renda_media_familiar, indice_desempenho, nivel_desempenho`

Arquivos derivados (gerados pelo notebook): `dados/desempenho_escolar_tratado.csv`, `dados/resumo_kpis.json`
e o banco `database/desempenho_escolar.db`.

## 3. Estrutura do projeto

```
projeto-desempenho-escolar/
│
├── app.py                      # Dashboard Streamlit — ponto de entrada (st.navigation)
├── pages/                      # Dashboard multipágina
│   ├── 0_Visao_Geral.py                # título, problema, KPIs, gráficos, conclusão
│   ├── 1_Evolucao_Temporal.py
│   ├── 2_Comparacao_Regional.py        # mapa interativo (Plotly) + API IBGE
│   ├── 3_Redes_e_Disciplinas.py
│   ├── 4_Fatores_Socioeconomicos.py    # correlação estatística
│   └── 5_Explorador_de_Dados.py        # tabela dinâmica, upload CSV, SQL
├── utils/                      # Camada compartilhada (notebook + dashboard)
│   ├── dados.py                # leitura, tratamento, engenharia de atributos, KPIs
│   ├── graficos.py             # construtores Plotly / Matplotlib / Seaborn
│   ├── filtros.py              # filtros da barra lateral (persistem entre páginas)
│   ├── apis.py                 # Requests: API IBGE + GeoJSON das UFs
│   ├── carga.py                # cache do Streamlit
│   └── interface.py            # KPIs, caixas de interpretação e conclusão
├── database/
│   ├── modelos.py              # SQLAlchemy ORM (esquema estrela)
│   ├── criar_banco.py          # cria/popula o SQLite e a view vw_desempenho
│   └── desempenho_escolar.db   # banco gerado
├── notebooks/
│   └── analise_desempenho_escolar.ipynb
├── dados/
│   └── simulacao_desempenho_escolar_brasil.csv
├── imagens/                    # gráficos gerados pelo notebook (usados no index.html)
├── index.html                  # página de apresentação (GitHub Pages)
├── requirements.txt
├── README.md
└── .streamlit/config.toml      # tema do dashboard
```

## 4. Tecnologias

| Obrigatórias | Recomendadas / avançadas |
|---|---|
| Python 3.10+ · Pandas · Matplotlib · Seaborn · Streamlit · GitHub | NumPy · Plotly · SQLAlchemy · SQLite · Requests |

### Funcionalidades intermediárias
filtros múltiplos em cascata · KPIs dinâmicos · gráficos interativos · análise temporal · tratamento avançado
(flags de consistência, imputação, nível recalculado) · upload de arquivos · dashboard em seções · visualizações
comparativas · análise geográfica

### Funcionalidades avançadas
| Funcionalidade | Onde |
|---|---|
| **Dashboard multipágina** (Streamlit) | `app.py` + `pages/` |
| **Persistência em banco + modelagem relacional** (SQLAlchemy + SQLite) | `database/`, página *Explorador* |
| **Consumo de API** (Requests) — API de Localidades do IBGE + GeoJSON | `utils/apis.py`, página *Comparação Regional* |
| **Mapas interativos** (Plotly choropleth) | página *Comparação Regional* |
| **Correlação estatística** (Pearson, r², t, p-valor) | `utils/dados.py`, página *Fatores Socioeconômicos* |
| **Séries temporais avançadas** (média móvel, variação, tendência) | página *Evolução Temporal* |
| **Integração de múltiplas fontes** (CSV + API + banco) | todo o dashboard |

## 5. Como executar localmente

```bash
git clone https://github.com/SEU-USUARIO/projeto-desempenho-escolar.git
cd projeto-desempenho-escolar
python -m venv .venv
# Windows: .venv\Scripts\activate   |   Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

> **Windows com bloqueio de DLL (Controle de Aplicativos / Smart App Control):** se aparecer
> `DLL load failed while importing _immutabledict_cy` (SQLAlchemy) ou `... importing rpds`, instale as
> versões sem binários:
>
> ```bash
> pip install --no-binary sqlalchemy --force-reinstall sqlalchemy
> pip install "jsonschema<4.18"
> ```

Para recriar o banco SQLite manualmente:

```bash
python database/criar_banco.py
```

Para executar o notebook (opcional, requer `jupyter`):

```bash
pip install jupyter
jupyter notebook notebooks/analise_desempenho_escolar.ipynb
```

## 6. Dashboard

| Página | Conteúdo |
|---|---|
| **Visão Geral** | título, descrição do problema, 6 KPIs dinâmicos, linha temporal, barras por disciplina, ranking de estados, heatmap semestral, dispersão renda × notas, tabela resumo, interpretação e conclusão executiva |
| **Evolução Temporal** | série semestral segmentada, média anual com média móvel/variação/desvio, heatmap semestral configurável |
| **Comparação Regional** | mapa coroplético do Brasil, ranking de estados, barras e boxplots por região, medidas de desigualdade |
| **Redes e Disciplinas** | pública × privada, gap por estado, barras por disciplina, distribuição dos níveis |
| **Fatores Socioeconômicos** | dispersões (Plotly e Seaborn), Pearson com significância, faixas de renda/internet, matriz de correlação |
| **Explorador de Dados** | tabela dinâmica, download, upload de CSV, (re)criação do banco e consultas SQL |

**Filtros obrigatórios** (barra lateral, valem para todas as páginas): ano, semestre, região, estado,
rede de ensino, disciplina e nível de desempenho.

## 7. Principais resultados

- **Estabilidade temporal:** a média das notas oscila em torno de 65 pontos, sem tendência consistente de melhora.
- **Redes de ensino:** diferença de 0,15 ponto entre pública e privada (pública ligeiramente à frente) — a rede não discrimina resultados nesta base.
- **Fatores socioeconômicos:** correlações de renda e acesso à internet com as notas praticamente nulas.
- **Disciplina crítica:** Português apresenta a menor média; Matemática, a maior.
- **Desigualdade regional:** cerca de 5,7 pontos entre Centro-Oeste (68,9) e Norte (63,2); a dispersão dentro das regiões (desvio ≈ 17 pontos) é bem maior.
- **Qualidade dos dados:** ~40 % dos registros têm aprovação + reprovação > 100 % e o nível informado não acompanha o índice — a base é simulada com variáveis independentes, e as conclusões demonstram o método, não um diagnóstico real.

Detalhes e gráficos no [notebook](notebooks/analise_desempenho_escolar.ipynb) e na pasta [`imagens/`](imagens/).

## 8. Publicação

1. **GitHub** — crie o repositório `projeto-desempenho-escolar`, envie todos os arquivos (`git push`).
2. **GitHub Pages** — em *Settings → Pages*, escolha *Deploy from a branch*, branch `main`, pasta `/ (root)`.
   O `index.html` da raiz será servido em `https://SEU-USUARIO.github.io/projeto-desempenho-escolar/`.
3. **Streamlit Community Cloud** — em [share.streamlit.io](https://share.streamlit.io), *New app* → selecione o
   repositório, branch `main` e *Main file path* `app.py`. O `requirements.txt` é instalado automaticamente.
4. Atualize os links no topo deste README e no `index.html`.

---

Projeto acadêmico · dados simulados fornecidos pela disciplina.
