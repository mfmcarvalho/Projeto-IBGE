# Pipeline de Dados IBGE — PIB dos Municípios

Pipeline de dados que extrai informações do PIB dos municípios brasileiros via API pública do IBGE, com processamento em arquitetura medalhão (Bronze, Silver e Gold), incluindo etapas de ingestão, tratamento, validação e modelagem, e disponibilização dos dados em PostgreSQL com modelo relacional.

## Arquitetura

```text
API IBGE / SIDRA
        │
        ▼
     Bronze
        │
        ▼
     Silver
        │
        ▼
      Gold
        │
        ▼
   PostgreSQL
        │
        ▼
 SQL / Analytics
```

### Bronze

Responsável pela ingestão e armazenamento dos dados provenientes das APIs do IBGE em formato próximo ao original.

Vindos diretamente da API, são armazenados os dados do PIB consolidados por **ano e município**, provenientes da **tabela SIDRA 5938** da base do IBGE, abrangendo o período de **2002 a 2023**.

Posteriormente, são obtidos os dados de **PIB total, impostos e PIB por setor** — agropecuária, indústria, administração, serviços, entre outros — por **microrregião, mesorregião, região e UF**.

São armazenados na Bronze:

* dados de estados e municípios;
* relacionamento entre municípios, UFs e regiões;
* metadados das tabelas SIDRA;
* períodos disponíveis;
* dados históricos do PIB.

Além da tabela `5938`, são mantidos na Bronze metadados de outras tabelas SIDRA para expansão futura do projeto:

| Tabela | Informação                           |
| ------ | ------------------------------------ |
| `5938` | Produto Interno Bruto dos Municípios |
| `6803` | Abastecimento de água                |
| `6804` | Canalização de água                  |
| `6805` | Esgotamento sanitário                |
| `6892` | Destino do lixo                      |

### Silver

Tratamento, limpeza e consolidação dos dados brutos no nível de **ano e município**, armazenados em formato **Parquet**.

A granularidade resultante é:

```text
Município × Ano
```

### Gold

Criação do modelo analítico do banco de dados relacional, contendo as tabelas:

* `dim_cidade`
* `dim_uf`
* `dim_regiao`
* `dim_tempo`
* `fact_pib`

As tabelas são armazenadas em formato **Parquet** antes da carga no banco de dados **PostgreSQL**.

---

## Modelo de dados

O modelo final organiza a hierarquia geográfica e temporal utilizada pela tabela fato:

```text
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
```

| Tabela       | Descrição                                  |
| ------------ | ------------------------------------------ |
| `dim_regiao` | Regiões brasileiras                        |
| `dim_uf`     | Unidades Federativas                       |
| `dim_cidade` | Municípios brasileiros                     |
| `dim_tempo`  | Períodos disponíveis                       |
| `fact_pib`   | Indicadores econômicos por município e ano |

Os relacionamentos são:

```text
dim_uf.codigo_regiao
    → dim_regiao.codigo_regiao

dim_cidade.codigo_uf
    → dim_uf.codigo_uf

fact_pib.codigo_ibge
    → dim_cidade.codigo_ibge

fact_pib.ano
    → dim_tempo.ano
```

---

## Fonte dos dados

Os dados são obtidos das APIs públicas do **Instituto Brasileiro de Geografia e Estatística (IBGE)**.

A principal fonte utilizada atualmente é:

**SIDRA 5938 — Produto Interno Bruto dos Municípios**

Período processado:

```text
2002–2023
```

Também é utilizada a **API de Localidades do IBGE** para obtenção da estrutura geográfica dos municípios brasileiros.

---

## Tecnologias

* Python
* Pandas
* PyArrow
* Requests
* PostgreSQL 16
* Psycopg
* Docker
* Docker Compose
* SQL
* Git

---

## Estrutura do projeto

```text
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
```

---

## Como executar

### Pré-requisitos

* Python
* Docker
* Docker Compose
* Git

### 1. Clone o repositório

```bash
git clone <URL_DO_REPOSITORIO>
cd projto_ibge
```

### 2. Crie o ambiente virtual

```powershell
python -m venv .venv
```

No Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Instale as dependências

```powershell
pip install -r requirements.txt
```

Dependências utilizadas:

```text
pandas==2.3.3
pyarrow==25.0.1
requests==2.34.2
psycopg[binary]==3.3.6
```

### 4. Inicie o PostgreSQL

```powershell
docker compose -f .\docker\docker_compose.yml up -d
```

### 5. Execute a ingestão Bronze

```powershell
python .\ingestion\atualizar_bronze_ibge.py
```

### 6. Crie a camada Silver

```powershell
python .\ingestion\criar_silver_ibge.py
```

### 7. Crie a camada Gold

```powershell
python .\ingestion\criar_gold_ibge.py
```

### 8. Carregue o PostgreSQL

```powershell
python .\ingestion\carregar_postgres.py
```

---

## Resultado atual

| Informação              | Quantidade |
| ----------------------- | ---------: |
| Regiões                 |          5 |
| UFs                     |         27 |
| Municípios              |      5.570 |
| Anos                    |         22 |
| Registros na `fact_pib` |    122.540 |
| Período                 |  2002–2023 |

---

## Próximos passos

* inclusão de indicadores de infraestrutura e saneamento;
* criação de novas tabelas fato;
* ampliação do modelo dimensional;
* criação de dashboards;
* testes automatizados de qualidade dos dados;
* evolução do monitoramento e logging da pipeline.

---

## Autor

Projeto desenvolvido como aplicação prática de conceitos de **Engenharia de Dados**, incluindo consumo de APIs, arquitetura medalhão, transformação e validação de dados, armazenamento em Parquet, modelagem relacional, PostgreSQL, Docker e SQL.

## Fonte dos dados

Dados públicos disponibilizados pelo **IBGE — Instituto Brasileiro de Geografia e Estatística**, por meio das APIs de Localidades e do SIDRA.
