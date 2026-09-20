# Projeto-IBGE
Pipeline de dados que extrai informações do PIB dos municípios brasileiros via API pública do IBGE, com processamento em arquitetura medalhão (Bronze, Silver e Gold), incluindo etapas de ingestão, tratamento, validação e modelagem, e disponibilização dos dados em PostgreSQL com modelo relacional.

Arquitetura:
Arquitetura

O projeto utiliza uma arquitetura em camadas para separar os diferentes estágios de processamento dos dados:

             API IBGE / SIDRA
                    │
                    ▼
              ┌──────────┐
              │  BRONZE  │
              │   JSON   │
              └────┬─────┘
                   │
                   ▼
              ┌──────────┐
              │  SILVER  │
              │ Parquet  │
              └────┬─────┘
                   │
                   ▼
              ┌──────────┐
              │   GOLD   │
              │ Parquet  │
              └────┬─────┘
                   │
                   ▼
             ┌────────────┐
             │ PostgreSQL │
             │   Docker   │
             └─────┬──────┘
                   │
                   ▼
             SQL / Analytics
Bronze

Responsável pela ingestão e armazenamento dos dados provenientes das APIs do IBGE em formato próximo ao original.

Vindo direto da API, são armazenados os dados dados do PIB consolidados por ano e município (tabela SIDRA 5938 da base do IBGE), abrangendo dados de 2002 até 2023.

Posteriormente são obtidos os dados de pib total, impostos e os pibs por setor (Agrupecuária, indústria, administração, entre outros) por microrregião, mesorregião, região e UF. 

São armazenados na Bronze:
dados de estados e municípios;
relacionamento entre municípios, UFs e regiões;
metadados das tabelas SIDRA;
períodos disponíveis;
dados históricos do PIB.

Silver:
Tratamento, limpeza e consolidação dos dados brutos a nível de ano e município em formato Parquet.

Gold: Criação do modelo analítico do banco de dados relacional, contendo as tabelas
dim_cidade
dim_municipio
dim_uf
dim_regiao
dim_tempo
fact_pib

que são armazenadas em formato parquet antes da carga no banco de dados PostGresSQL
################################################################################################################################################################
Modelo de dados final:

O modelo final organiza a hierarquia geográfica e temporal utilizada pela tabela fato.

dim_regiao
    │
    │ 1:N
    ▼
dim_uf
    │
    │ 1:N
    ▼
dim_cidade
    │
    │ 1:N
    ▼
fact_pib
    │
    │ N:1
    ▼
dim_tempo
Tabelas
Tabela	       |     Descrição
dim_regiao	   |     Regiões brasileiras
dim_uf	       |     Unidades Federativas
dim_cidade	   |     Municípios brasileiros
dim_tempo	     |     Períodos disponíveis
fact_pib	     |     PIB por município e ano

Fonte dos dados

Os dados são obtidos das APIs públicas do Instituto Brasileiro de Geografia e Estatística (IBGE).

A principal fonte utilizada atualmente é a tabela:

SIDRA 5938 — Produto Interno Bruto dos Municípios

Período processado:

2002–2023

Também é utilizada a API de Localidades do IBGE para obtenção da estrutura geográfica dos municípios brasileiros.

Tecnologias
Python
Pandas
PyArrow
Requests
PostgreSQL 16
Psycopg
Docker
Docker Compose
SQL
Git

Estrutura do projeto
projto_ibge/
│
├── data/
│   ├── bronze/
│   │   └── ibge/
│   │       ├── localidades/
│   │       └── sidra/
│   │
│   ├── silver/
│   │   └── ibge/
│   │
│   └── gold/
│       └── ibge/
│           ├── dim_regiao/
│           ├── dim_uf/
│           ├── dim_cidade/
│           ├── dim_tempo/
│           └── fact_pib/
│
├── ingestion/
│   ├── atualizar_bronze_ibge.py
│   ├── criar_silver_ibge.py
│   ├── criar_gold_ibge.py
│   ├── carregar_postgres.py
│   └── pipeline.py
│
├── docker/
│   └── docker_compose.yml
│
├── scripts/
│   └── executar_pipeline.bat
│
├── sql/
│   └── exploracao.sql
│
├── logs/
│
├── requirements.txt
└── README.md

Como executar
Pré-requisitos

É necessário possuir:

Python;
Docker;
Docker Compose;
Git.
1. Clone o repositório
git clone <URL_DO_REPOSITORIO>
cd projto_ibge
2. Crie o ambiente virtual
python -m venv .venv

No Windows:

.\.venv\Scripts\Activate.ps1
3. Instale as dependências
pip install -r requirements.txt

O projeto utiliza:

pandas==2.3.3
pyarrow==25.0.1
requests==2.34.2
psycopg[binary]==3.3.6
4. Inicie o PostgreSQL
docker compose -f .\docker\docker_compose.yml up -d
5. Execute a ingestão Bronze
python .\ingestion\atualizar_bronze_ibge.py
6. Crie a camada Silver
python .\ingestion\criar_silver_ibge.py
7. Crie a camada Gold
python .\ingestion\criar_gold_ibge.py
8. Carregue o PostgreSQL
python .\ingestion\carregar_postgres.py

Algumas evoluções planejadas:

inclusão de indicadores de infraestrutura e saneamento;
criação de novas tabelas fato;
ampliação do modelo dimensional;
criação de dashboards;
testes automatizados de qualidade de dados;
evolução do monitoramento e logging da pipeline.
