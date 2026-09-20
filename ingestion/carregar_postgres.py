from pathlib import Path
from dotenv import load_dotenv
import time
import os
import pandas as pd
import psycopg


# ============================================================
# CONFIGURAÇÕES
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

GOLD = PROJECT_ROOT / "data" / "gold" / "ibge"

ARQUIVO_DIM_REGIAO = (
    GOLD / "dim_regiao" / "dim_regiao.parquet"
)

ARQUIVO_DIM_TEMPO = (
    GOLD / "dim_tempo" / "dim_tempo.parquet"
)

ARQUIVO_DIM_UF = (
    GOLD / "dim_uf" / "dim_uf.parquet"
)

ARQUIVO_DIM_CIDADE = (
    GOLD / "dim_cidade" / "dim_cidade.parquet"
)

ARQUIVO_FACT_PIB = (
    GOLD / "fact_pib" / "fact_pib.parquet"
)


# ============================================================
# POSTGRESQL
# ============================================================

load_dotenv(PROJECT_ROOT / "docker" / ".env")

DB_HOST = "localhost"
DB_PORT = 15432
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")


# ============================================================
# AUXILIARES
# ============================================================

def conectar():
    """
    Abre conexão com PostgreSQL.
    """

    return psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )


def verificar_arquivos():
    """
    Verifica se todos os arquivos Gold existem.
    """

    print("\n" + "=" * 70)
    print("VERIFICANDO ARQUIVOS GOLD")
    print("=" * 70)

    arquivos = [
        ARQUIVO_DIM_REGIAO,
        ARQUIVO_DIM_UF,
        ARQUIVO_DIM_TEMPO,
        ARQUIVO_DIM_CIDADE,
        ARQUIVO_FACT_PIB
    ]

    for arquivo in arquivos:

        if not arquivo.exists():
            raise FileNotFoundError(
                f"Arquivo não encontrado:\n{arquivo}"
            )

        print(f"OK: {arquivo}")


# ============================================================
# CRIAÇÃO DO SCHEMA/TABELAS
# ============================================================

def criar_estrutura(conn):

    print("\n" + "=" * 70)
    print("CRIANDO ESTRUTURA DO POSTGRESQL")
    print("=" * 70)

    sql = """
    CREATE SCHEMA IF NOT EXISTS ibge;

    CREATE TABLE IF NOT EXISTS ibge.dim_regiao (
        codigo_regiao INTEGER PRIMARY KEY,
        nome_regiao VARCHAR(100) NOT NULL
    );

    CREATE TABLE IF NOT EXISTS ibge.dim_tempo (
        ano INTEGER PRIMARY KEY,
        decada INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS ibge.dim_uf (
        codigo_uf INTEGER PRIMARY KEY,
        sigla_uf VARCHAR(2) NOT NULL,
        nome_uf VARCHAR(100) NOT NULL,
        codigo_regiao INTEGER NOT NULL,

        CONSTRAINT fk_dim_uf_regiao
            FOREIGN KEY (codigo_regiao)
            REFERENCES ibge.dim_regiao(codigo_regiao)
    );

    CREATE TABLE IF NOT EXISTS ibge.dim_cidade (
        codigo_ibge BIGINT PRIMARY KEY,
        nome_municipio VARCHAR(150) NOT NULL,
        codigo_uf INTEGER NOT NULL,

        CONSTRAINT fk_dim_cidade_uf
            FOREIGN KEY (codigo_uf)
            REFERENCES ibge.dim_uf(codigo_uf)
    );

    CREATE TABLE IF NOT EXISTS ibge.fact_pib (
        codigo_ibge BIGINT NOT NULL,
        ano INTEGER NOT NULL,

        pib_total DOUBLE PRECISION,
        impostos_liquidos DOUBLE PRECISION,
        vab_total DOUBLE PRECISION,
        vab_agropecuaria DOUBLE PRECISION,
        vab_industria DOUBLE PRECISION,
        vab_servicos_exclusive_adm DOUBLE PRECISION,
        vab_administracao DOUBLE PRECISION,

        CONSTRAINT pk_fact_pib
            PRIMARY KEY (codigo_ibge, ano),

        CONSTRAINT fk_fact_pib_tempo
            FOREIGN KEY (ano)
            REFERENCES ibge.dim_tempo(ano)
    );

    CREATE INDEX IF NOT EXISTS idx_fact_pib_ano
        ON ibge.fact_pib(ano);

    CREATE INDEX IF NOT EXISTS idx_fact_pib_cidade
        ON ibge.fact_pib(codigo_ibge);

    CREATE INDEX IF NOT EXISTS idx_dim_cidade_uf
        ON ibge.dim_cidade(codigo_uf);

    CREATE INDEX IF NOT EXISTS idx_dim_uf_regiao
        ON ibge.dim_uf(codigo_regiao);
    """

    with conn.cursor() as cursor:
        cursor.execute(sql)

    print("Schema ibge: OK")
    print("Tabelas: OK")
    print("Índices: OK")

# ============================================================
# LEITURA GOLD
# ============================================================

def carregar_gold():

    print("\n" + "=" * 70)
    print("LENDO CAMADA GOLD")
    print("=" * 70)

    df_regiao = pd.read_parquet(
        ARQUIVO_DIM_REGIAO
    )

    df_uf = pd.read_parquet(
        ARQUIVO_DIM_UF
    )

    df_tempo = pd.read_parquet(
        ARQUIVO_DIM_TEMPO
    )

    df_cidade = pd.read_parquet(
        ARQUIVO_DIM_CIDADE
    )

    df_fact = pd.read_parquet(
        ARQUIVO_FACT_PIB
    )

    print(f"dim_regiao: {len(df_regiao)} linhas")
    print(f"dim_uf:     {len(df_uf)} linhas")
    print(f"dim_tempo:  {len(df_tempo)} linhas")
    print(f"dim_cidade: {len(df_cidade)} linhas")
    print(f"fact_pib:   {len(df_fact)} linhas")

    return (
        df_regiao,
        df_uf,
        df_tempo,
        df_cidade,
        df_fact
    )

# ============================================================
# CONVERSÃO NULL
# ============================================================

def valor_sql(valor):
    """
    Converte valores nulos do Pandas/Numpy para None,
    permitindo gravá-los como NULL no PostgreSQL.
    """

    if pd.isna(valor):
        return None

    # Converte escalares numpy para tipos nativos Python.
    if hasattr(valor, "item"):
        return valor.item()

    return valor


# ============================================================
# CARGA DIM_REGIAO
# ============================================================

def carregar_dim_regiao(conn, df):
    """
    Insere/atualiza dim_regiao.
    """

    print("\nCarregando dim_regiao...")

    sql = """
        INSERT INTO ibge.dim_regiao (
            codigo_regiao,
            nome_regiao
        )
        VALUES (%s, %s)

        ON CONFLICT (codigo_regiao)
        DO UPDATE SET
            nome_regiao = EXCLUDED.nome_regiao;
    """

    registros = [
        (
            valor_sql(row.codigo_regiao),
            valor_sql(row.nome_regiao)
        )
        for row in df.itertuples(index=False)
    ]

    with conn.cursor() as cursor:
        cursor.executemany(sql, registros)

    print(f"dim_regiao: {len(registros)} registros processados.")


# ============================================================
# CARGA DIM_TEMPO
# ============================================================

def carregar_dim_tempo(conn, df):
    """
    Insere/atualiza dim_tempo.
    """

    print("\nCarregando dim_tempo...")

    sql = """
        INSERT INTO ibge.dim_tempo (
            ano,
            decada
        )
        VALUES (%s, %s)

        ON CONFLICT (ano)
        DO UPDATE SET
            decada = EXCLUDED.decada;
    """

    registros = [
        (
            valor_sql(row.ano),
            valor_sql(row.decada)
        )
        for row in df.itertuples(index=False)
    ]

    with conn.cursor() as cursor:
        cursor.executemany(sql, registros)

    print(f"dim_tempo: {len(registros)} registros processados.")


# ============================================================
# CARGA DIM_UF e DIM_CIDADE
# ============================================================
def carregar_dim_uf(conn, df):

    print("\nCarregando dim_uf...")

    sql = """
        INSERT INTO ibge.dim_uf (
            codigo_uf,
            sigla_uf,
            nome_uf,
            codigo_regiao
        )
        VALUES (%s, %s, %s, %s)

        ON CONFLICT (codigo_uf)
        DO UPDATE SET
            sigla_uf = EXCLUDED.sigla_uf,
            nome_uf = EXCLUDED.nome_uf,
            codigo_regiao = EXCLUDED.codigo_regiao;
    """

    registros = [
        (
            valor_sql(row.codigo_uf),
            valor_sql(row.sigla_uf),
            valor_sql(row.nome_uf),
            valor_sql(row.codigo_regiao)
        )
        for row in df.itertuples(index=False)
    ]

    with conn.cursor() as cursor:
        cursor.executemany(sql, registros)

    print(
        f"dim_uf: {len(registros)} registros processados."
    )


def carregar_dim_cidade(conn, df):

    print("\nCarregando dim_cidade...")

    sql = """
        INSERT INTO ibge.dim_cidade (
            codigo_ibge,
            nome_municipio,
            codigo_uf
        )
        VALUES (%s, %s, %s)

        ON CONFLICT (codigo_ibge)
        DO UPDATE SET
            nome_municipio = EXCLUDED.nome_municipio,
            codigo_uf = EXCLUDED.codigo_uf;
    """

    registros = [
        (
            valor_sql(row.codigo_ibge),
            valor_sql(row.nome_municipio),
            valor_sql(row.codigo_uf)
        )
        for row in df.itertuples(index=False)
    ]

    with conn.cursor() as cursor:
        cursor.executemany(sql, registros)

    print(
        f"dim_cidade: {len(registros)} registros processados."
    )

def migrar_fact_para_dim_cidade(conn):

    print("\nMigrando FK fact_pib -> dim_cidade...")

    sql = """
        ALTER TABLE ibge.fact_pib
        DROP CONSTRAINT IF EXISTS fk_fact_pib_municipio;

        ALTER TABLE ibge.fact_pib
        DROP CONSTRAINT IF EXISTS fk_fact_pib_cidade;

        ALTER TABLE ibge.fact_pib
        ADD CONSTRAINT fk_fact_pib_cidade
            FOREIGN KEY (codigo_ibge)
            REFERENCES ibge.dim_cidade(codigo_ibge);
    """

    with conn.cursor() as cursor:
        cursor.execute(sql)

    print("FK fact_pib -> dim_cidade: OK")


# ============================================================
# CARGA FACT_PIB
# ============================================================

def carregar_fact_pib(conn, df):
    """
    Insere/atualiza fact_pib.

    Os NULLs da Gold continuam NULL no PostgreSQL.
    """

    print("\nCarregando fact_pib...")

    sql = """
        INSERT INTO ibge.fact_pib (
            codigo_ibge,
            ano,
            pib_total,
            impostos_liquidos,
            vab_total,
            vab_agropecuaria,
            vab_industria,
            vab_servicos_exclusive_adm,
            vab_administracao
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s
        )

        ON CONFLICT (codigo_ibge, ano)
        DO UPDATE SET
            pib_total = EXCLUDED.pib_total,
            impostos_liquidos = EXCLUDED.impostos_liquidos,
            vab_total = EXCLUDED.vab_total,
            vab_agropecuaria = EXCLUDED.vab_agropecuaria,
            vab_industria = EXCLUDED.vab_industria,
            vab_servicos_exclusive_adm =
                EXCLUDED.vab_servicos_exclusive_adm,
            vab_administracao =
                EXCLUDED.vab_administracao;
    """

    registros = [
        (
            valor_sql(row.codigo_ibge),
            valor_sql(row.ano),
            valor_sql(row.pib_total),
            valor_sql(row.impostos_liquidos),
            valor_sql(row.vab_total),
            valor_sql(row.vab_agropecuaria),
            valor_sql(row.vab_industria),
            valor_sql(row.vab_servicos_exclusive_adm),
            valor_sql(row.vab_administracao)
        )
        for row in df.itertuples(index=False)
    ]

    with conn.cursor() as cursor:

        total = len(registros)
        tamanho_lote = 5000

        for inicio in range(0, total, tamanho_lote):

            fim = min(
                inicio + tamanho_lote,
                total
            )

            lote = registros[inicio:fim]

            cursor.executemany(
                sql,
                lote
            )

            print(
                f"  fact_pib: "
                f"{fim}/{total} registros processados"
            )

    print(
        f"fact_pib: {len(registros)} "
        "registros processados."
    )


# ============================================================
# VALIDAÇÃO POSTGRESQL
# ============================================================

def validar_banco(conn):
    """
    Valida quantidades e integridade após a carga.
    """

    print("\n" + "=" * 70)
    print("VALIDANDO POSTGRESQL")
    print("=" * 70)

    consultas = {
        "dim_regiao":
            "SELECT COUNT(*) FROM ibge.dim_regiao",

        "dim_uf":
            "SELECT COUNT(*) FROM ibge.dim_uf",

        "dim_tempo":
            "SELECT COUNT(*) FROM ibge.dim_tempo",

        "dim_cidade":
            "SELECT COUNT(*) FROM ibge.dim_cidade",

        "fact_pib":
            "SELECT COUNT(*) FROM ibge.fact_pib"
    }

    with conn.cursor() as cursor:

        for tabela, sql in consultas.items():

            cursor.execute(sql)

            quantidade = cursor.fetchone()[0]

            print(
                f"{tabela:<15}: "
                f"{quantidade} linhas"
            )

        # ----------------------------------------------------
        # Anos
        # ----------------------------------------------------

        cursor.execute("""
            SELECT
                MIN(ano),
                MAX(ano),
                COUNT(DISTINCT ano)
            FROM ibge.fact_pib;
        """)

        minimo, maximo, quantidade_anos = cursor.fetchone()

        print("")
        print(f"Ano mínimo:     {minimo}")
        print(f"Ano máximo:     {maximo}")
        print(f"Anos distintos: {quantidade_anos}")

        # ----------------------------------------------------
        # Municípios
        # ----------------------------------------------------

        cursor.execute("""
            SELECT COUNT(DISTINCT codigo_ibge)
            FROM ibge.fact_pib;
        """)

        municipios = cursor.fetchone()[0]

        print(
            f"Municípios na fact: {municipios}"
        )

        # ----------------------------------------------------
        # Órfãos
        # ----------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*)
            FROM ibge.fact_pib f
            LEFT JOIN ibge.dim_cidade c
                ON c.codigo_ibge = f.codigo_ibge
            WHERE c.codigo_ibge IS NULL;
        """)

        orfaos_cidade = cursor.fetchone()[0]


        cursor.execute("""
            SELECT COUNT(*)
            FROM ibge.dim_cidade c
            LEFT JOIN ibge.dim_uf u
                ON u.codigo_uf = c.codigo_uf
            WHERE u.codigo_uf IS NULL;
        """)

        orfaos_uf = cursor.fetchone()[0]


        cursor.execute("""
            SELECT COUNT(*)
            FROM ibge.dim_uf u
            LEFT JOIN ibge.dim_regiao r
                ON r.codigo_regiao = u.codigo_regiao
            WHERE r.codigo_regiao IS NULL;
        """)

        orfaos_regiao = cursor.fetchone()[0]


        cursor.execute("""
            SELECT COUNT(*)
            FROM ibge.fact_pib f
            LEFT JOIN ibge.dim_tempo t
                ON t.ano = f.ano
            WHERE t.ano IS NULL;
        """)

        orfaos_tempo = cursor.fetchone()[0]


        print("")
        print(f"Fatos sem cidade:    {orfaos_cidade}")
        print(f"Cidades sem UF:      {orfaos_uf}")
        print(f"UFs sem região:      {orfaos_regiao}")
        print(f"Fatos sem tempo:     {orfaos_tempo}")


        if orfaos_cidade != 0:
            raise ValueError(
                "Existem fatos sem cidade correspondente."
            )

        if orfaos_uf != 0:
            raise ValueError(
                "Existem cidades sem UF correspondente."
            )

        if orfaos_regiao != 0:
            raise ValueError(
                "Existem UFs sem região correspondente."
            )

        if orfaos_tempo != 0:
            raise ValueError(
                "Existem fatos sem ano correspondente."
            )
    print("\nVALIDAÇÃO DO POSTGRESQL: OK")


# ============================================================
# MAIN
# ============================================================

def carregar_postgres():
    """
    Executa a carga completa da Gold no PostgreSQL.
    """

    inicio = time.time()

    print("")
    print("=" * 70)
    print("IBGE - CARGA GOLD -> POSTGRESQL")
    print("=" * 70)

    verificar_arquivos()

    (
        df_regiao,
        df_uf,
        df_tempo,
        df_cidade,
        df_fact
    ) = carregar_gold()

    print("\n" + "=" * 70)
    print("CONECTANDO AO POSTGRESQL")
    print("=" * 70)

    print(
        f"Host: {DB_HOST}:{DB_PORT}"
    )
    print(
        f"Database: {DB_NAME}"
    )

    # ========================================================
    # TRANSAÇÃO
    # ========================================================

    with conectar() as conn:

        print("Conexão estabelecida.")

        try:

            criar_estrutura(conn)

            carregar_dim_regiao(
                conn,
                df_regiao
            )

            carregar_dim_uf(
                conn,
                df_uf
            )

            carregar_dim_tempo(
                conn,
                df_tempo
            )

            carregar_dim_cidade(
                conn,
                df_cidade
            )

            migrar_fact_para_dim_cidade(conn)

            carregar_fact_pib(
                conn,
                df_fact
            )

            validar_banco(conn)

            conn.commit()

        except Exception:

            print(
                "\nErro detectado. "
                "Executando ROLLBACK..."
            )

            conn.rollback()

            raise

    tempo_total = time.time() - inicio

    print("\n" + "=" * 70)
    print("CARGA POSTGRESQL CONCLUÍDA COM SUCESSO")
    print("=" * 70)

    print(
        f"Tempo total: {tempo_total:.2f} segundos"
    )

    print("=" * 70)


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":

    try:

        carregar_postgres()

    except KeyboardInterrupt:

        print(
            "\nProcesso interrompido pelo usuário."
        )

        raise

    except Exception as erro:

        print("\n" + "=" * 70)
        print("ERRO NA CARGA DO POSTGRESQL")
        print("=" * 70)

        print(erro)

        print("=" * 70)

        raise