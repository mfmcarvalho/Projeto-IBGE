# IBGE Data Pipeline — Municipal GDP

Data pipeline that extracts Brazilian municipal GDP data through the IBGE public API, using a medallion architecture (Bronze, Silver, and Gold), including ingestion, processing, validation, and modeling stages, with the resulting data made available in PostgreSQL through a relational model.

## Architecture

```text
IBGE / SIDRA API
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

Responsible for ingesting and storing data from IBGE APIs in a format close to the original source.

Data coming directly from the API includes GDP consolidated by **year and municipality**, obtained from **SIDRA table 5938** in the IBGE database, covering the period from **2002 to 2023**.

Subsequently, data on **total GDP, taxes, and GDP by sector** — agriculture, industry, public administration, services, among others — is obtained by **microregion, mesoregion, region, and state (UF)**.

The Bronze layer stores:

* state and municipality data;
* relationships between municipalities, states (UFs), and regions;
* SIDRA table metadata;
* available periods;
* historical GDP data.

In addition to table `5938`, metadata from other SIDRA tables is maintained in the Bronze layer for future expansion of the project:

| Table | Information |
| ------ | ----------- |
| `5938` | Gross Domestic Product of Municipalities |
| `6803` | Water supply |
| `6804` | Piped water |
| `6805` | Sanitary sewage |
| `6892` | Waste disposal |

### Silver

Processing, cleaning, and consolidation of raw data at the **year and municipality** level, stored in **Parquet** format.

The resulting granularity is:

```text
Municipality × Year
```

### Gold

Creation of the analytical model for the relational database, containing the following tables:

* `dim_cidade`
* `dim_uf`
* `dim_regiao`
* `dim_tempo`
* `fact_pib`

The tables are stored in **Parquet** format before being loaded into the **PostgreSQL** database.

---

## Data Model

The final model organizes the geographic and temporal hierarchy used by the fact table:

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

| Table | Description |
| ----- | ----------- |
| `dim_regiao` | Brazilian regions |
| `dim_uf` | Brazilian states (Federative Units) |
| `dim_cidade` | Brazilian municipalities |
| `dim_tempo` | Available time periods |
| `fact_pib` | Economic indicators by municipality and year |

The relationships are:

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

## Data Sources

The data is obtained from the public APIs of the **Brazilian Institute of Geography and Statistics (IBGE)**.

The main source currently used is:

**SIDRA 5938 — Gross Domestic Product of Municipalities**

Processed period:

```text
2002–2023
```

The **IBGE Localities API** is also used to obtain the geographic structure of Brazilian municipalities.

---

## Technologies

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

## Project Structure

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

## How to Run

### Prerequisites

* Python
* Docker
* Docker Compose
* Git

### 1. Clone the repository

```bash
git clone <REPOSITORY_URL>
cd projto_ibge
```

### 2. Create a virtual environment

```powershell
python -m venv .venv
```

On Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install the dependencies

```powershell
pip install -r requirements.txt
```

Dependencies used:

```text
pandas==2.3.3
pyarrow==25.0.1
requests==2.34.2
psycopg[binary]==3.3.6
```

### 4. Start PostgreSQL

```powershell
docker compose -f .\docker\docker_compose.yml up -d
```

### 5. Run the Bronze ingestion

```powershell
python .\ingestion\atualizar_bronze_ibge.py
```

### 6. Create the Silver layer

```powershell
python .\ingestion\criar_silver_ibge.py
```

### 7. Create the Gold layer

```powershell
python .\ingestion\criar_gold_ibge.py
```

### 8. Load the data into PostgreSQL

```powershell
python .\ingestion\carregar_postgres.py
```

---

## Current Results

| Information | Count |
| ----------- | ----: |
| Regions | 5 |
| States (UFs) | 27 |
| Municipalities | 5,570 |
| Years | 22 |
| Records in `fact_pib` | 122,540 |
| Period | 2002–2023 |

---

## Next Steps

* include infrastructure and sanitation indicators;
* create new fact tables;
* expand the dimensional model;
* create dashboards;
* implement automated data quality tests;
* improve pipeline monitoring and logging.

---

## Author

Project developed as a practical application of **Data Engineering** concepts, including API consumption, medallion architecture, data transformation and validation, Parquet storage, relational modeling, PostgreSQL, Docker, and SQL.

## Data Sources

Public data provided by **IBGE — Brazilian Institute of Geography and Statistics**, through the Localities and SIDRA APIs.
