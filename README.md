# 🎓 Desempenho Escolar no Brasil

Projeto da Avaliação G1 da disciplina Linguagem de Programação — Análise e Visualização de Dados com Python.

**Aluno:** Pedro Augusto Pereira da Silva
**Professor:** Alexandre Neves Louzada

## Links

- Dashboard: https://projetoescola-knd.streamlit.app/
- Pages: https://peugusto.github.io/ProjetoEscola/

## Pergunta de negócio

Como região, rede de ensino, disciplina, renda familiar e acesso à internet se relacionam com o desempenho escolar no Brasil entre 2015 e 2024?

## Objetivos

* analisar a evolução das notas ao longo do tempo;
* comparar regiões e estados;
* comparar redes pública e privada;
* identificar as disciplinas com menor rendimento;
* relacionar renda e acesso à internet com o desempenho;
* calcular KPIs;
* disponibilizar um dashboard interativo.

## Tecnologias

* Python
* Pandas
* NumPy
* Matplotlib
* Seaborn
* Plotly
* Streamlit
* GitHub
* GitHub Pages

## Estrutura

```
ProjetoEscola/
├── app.py
├── requirements.txt
├── README.md
├── index.html
├── dados/
│   └── simulacao_desempenho_escolar_brasil.csv
└── notebooks/
    └── analise_desempenho_escolar.ipynb
```

## Funcionalidades intermediárias

* filtros múltiplos (ano, semestre, região, estado, rede, disciplina e nível);
* KPIs dinâmicos;
* análise temporal;
* visualizações comparativas;
* dashboard organizado em seções;
* gráficos interativos.

## Funcionalidades avançadas

* correlação estatística (Pearson com p-valor);
* série temporal com média móvel e linha de tendência.

## Como executar localmente

```
pip install -r requirements.txt
streamlit run app.py
```
