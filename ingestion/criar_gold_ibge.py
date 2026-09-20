from pathlib import Path
import json
import time
import pandas as pd


# CONFIGURAÇÕES DAS CAMADAS BRONZE, SILVER, GOLD
PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRONZE = PROJECT_ROOT / "data" / "bronze" / "ibge"
SILVER = PROJECT_ROOT / "data" / "silver" / "ibge"
GOLD = PROJECT_ROOT / "data" / "gold" / "ibge"

ARQUIVO_MUNICIPIOS = BRONZE / "localidades" / "municipio_uf.json"
ARQUIVO_FACT_PIB_SILVER = SILVER / "fact_pib" / "fact_pib.parquet"

DIR_DIM_REGIAO = GOLD / "dim_regiao"
DIR_DIM_UF = GOLD / "dim_uf"
DIR_DIM_TEMPO = GOLD / "dim_tempo"
DIR_DIM_CIDADE = GOLD / "dim_cidade"
DIR_FACT_PIB = GOLD / "fact_pib"


# ============================================================ #
# FUNÇÕES AUXILIARES
# ============================================================ #
def carregar_json(caminho):
    with open(caminho, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def salvar_parquet(df, diretorio, nome_arquivo):
    diretorio.mkdir(parents=True, exist_ok=True)
    caminho = diretorio / nome_arquivo
    df.to_parquet(caminho, index=False)
    return caminho


# ============================================================ #
# DIM_REGIAO
# ============================================================ #
def criar_dim_regiao(municipios):
    """
    Cria a dimensão de regiões usando o municipio_uf.json,
    que já possui os dados tratados e achatados.
    """

    print("\n" + "=" * 70)
    print("CRIANDO DIM_REGIAO")
    print("=" * 70)

    if not municipios:
        raise ValueError("municipio_uf.json está vazio.")

    print(
        "Campos encontrados no primeiro registro:",
        list(municipios[0].keys())
    )

    registros = []

    for municipio in municipios:

        codigo_regiao = municipio.get("codigo_regiao")
        nome_regiao = municipio.get("macro_regiao")

        if codigo_regiao is None or nome_regiao is None:
            continue

        registros.append({
            "codigo_regiao": int(codigo_regiao),
            "nome_regiao": nome_regiao
        })

    if not registros:
        raise ValueError(
            "Nenhuma região foi encontrada. "
            "Verifique os campos codigo_regiao e macro_regiao "
            "do municipio_uf.json."
        )

    df = pd.DataFrame(registros)

    df = (
        df
        .drop_duplicates(subset=["codigo_regiao"])
        .sort_values("codigo_regiao")
        .reset_index(drop=True)
    )

    df["codigo_regiao"] = (
        df["codigo_regiao"].astype("int64")
    )

    print(f"Regiões encontradas: {len(df)}")

    print("\nDim_regiao:")
    print(df.to_string(index=False))

    return df
# ============================================================ #
# DIM_TEMPO
# ============================================================ #
def criar_dim_tempo(df_fact):
    print("\n" + "=" * 70)
    print("CRIANDO DIM_TEMPO")
    print("=" * 70)

    anos = (
        df_fact["ano"]
        .dropna()
        .astype(int)
        .drop_duplicates()
        .sort_values()
        .tolist()
    )

    df = pd.DataFrame({"ano": anos})
    df["decada"] = ((df["ano"] // 10) * 10).astype("int64")

    print(f"Anos encontrados: {len(df)}")
    print(f"Ano mínimo: {df['ano'].min()}")
    print(f"Ano máximo: {df['ano'].max()}")
    print("\nDim_tempo:")
    print(df.to_string(index=False))
    return df


def criar_dim_uf(municipios):
    """
    Cria a dimensão de UFs.
    Uma linha por Unidade da Federação.
    """

    print("\n" + "=" * 70)
    print("CRIANDO DIM_UF")
    print("=" * 70)

    registros = []

    for municipio in municipios:

        codigo_uf = municipio.get("codigo_uf")
        sigla_uf = municipio.get("sigla_uf")
        nome_uf = municipio.get("estado")
        codigo_regiao = municipio.get("codigo_regiao")

        if codigo_uf is None:
            continue

        registros.append({
            "codigo_uf": int(codigo_uf),
            "sigla_uf": sigla_uf,
            "nome_uf": nome_uf,
            "codigo_regiao": int(codigo_regiao)
        })

    df = pd.DataFrame(registros)

    df = (
        df
        .drop_duplicates(subset=["codigo_uf"])
        .sort_values("codigo_uf")
        .reset_index(drop=True)
    )

    df["codigo_uf"] = df["codigo_uf"].astype("int64")
    df["codigo_regiao"] = df["codigo_regiao"].astype("int64")

    print(f"UFs encontradas: {len(df)}")

    print("\nDim_uf:")
    print(df.to_string(index=False))

    return df


def criar_dim_cidade(municipios):
    """
    Cria a dimensão de cidades.
    Uma linha por município.
    """

    print("\n" + "=" * 70)
    print("CRIANDO DIM_CIDADE")
    print("=" * 70)

    registros = []
    ignorados = 0

    for municipio in municipios:

        codigo_ibge = municipio.get("codigo_ibge")
        nome_municipio = municipio.get("municipio")
        codigo_uf = municipio.get("codigo_uf")

        if (
            codigo_ibge is None
            or nome_municipio is None
            or codigo_uf is None
        ):
            ignorados += 1
            continue

        registros.append({
            "codigo_ibge": int(codigo_ibge),
            "nome_municipio": nome_municipio,
            "codigo_uf": int(codigo_uf)
        })

    if not registros:
        raise ValueError(
            "Nenhum município válido encontrado."
        )

    df = pd.DataFrame(registros)

    duplicidades = df.duplicated(
        subset=["codigo_ibge"]
    ).sum()

    if duplicidades > 0:

        print(
            f"ATENÇÃO: {duplicidades} duplicidades encontradas."
        )

        df = df.drop_duplicates(
            subset=["codigo_ibge"],
            keep="first"
        )

    df = (
        df
        .sort_values("codigo_ibge")
        .reset_index(drop=True)
    )

    df["codigo_ibge"] = df["codigo_ibge"].astype("int64")
    df["codigo_uf"] = df["codigo_uf"].astype("int64")

    print(f"Cidades válidas: {len(df)}")
    print(f"Registros ignorados: {ignorados}")
    print(f"Duplicidades removidas: {duplicidades}")

    return df

# ============================================================ #
# FACT_PIB
# ============================================================ #
def criar_fact_pib():
    print("\n" + "=" * 70)
    print("CRIANDO FACT_PIB")
    print("=" * 70)

    if not ARQUIVO_FACT_PIB_SILVER.exists():
        raise FileNotFoundError(f"Arquivo Silver não encontrado:\n{ARQUIVO_FACT_PIB_SILVER}")

    df = pd.read_parquet(ARQUIVO_FACT_PIB_SILVER)
    print(f"Linhas Silver: {len(df)}")
    print(f"Colunas Silver: {len(df.columns)}")

    colunas_esperadas = [
        "codigo_ibge",
        "ano",
        "pib_total",
        "impostos_liquidos",
        "vab_total",
        "vab_agropecuaria",
        "vab_industria",
        "vab_servicos_exclusive_adm",
        "vab_administracao",
    ]

    colunas_faltantes = [coluna for coluna in colunas_esperadas if coluna not in df.columns]
    if colunas_faltantes:
        raise ValueError("Colunas esperadas não encontradas na Silver: " + ", ".join(colunas_faltantes))

    df = df[colunas_esperadas].copy()
    df["codigo_ibge"] = df["codigo_ibge"].astype("int64")
    df["ano"] = df["ano"].astype("int64")
    df = df.sort_values(["ano", "codigo_ibge"]).reset_index(drop=True)

    duplicidades = df.duplicated(subset=["codigo_ibge", "ano"]).sum()
    if duplicidades > 0:
        raise ValueError(f"Foram encontradas {duplicidades} duplicidades em (codigo_ibge, ano).")

    print(f"Linhas Gold: {len(df)}")
    print(f"Municípios distintos: {df['codigo_ibge'].nunique()}")
    print(f"Anos distintos: {df['ano'].nunique()}")
    print(f"Ano mínimo: {df['ano'].min()}")
    print(f"Ano máximo: {df['ano'].max()}")
    print(f"Duplicidades: {duplicidades}")
    print("\nNulos:")
    print(df.isna().sum())
    return df


# ============================================================ #
# VALIDAÇÕES FINAIS
# ============================================================ #
def validar_gold(
    df_regiao,
    df_uf,
    df_tempo,
    df_cidade,
    df_fact
):
    print("\n" + "=" * 70)
    print("VALIDANDO GOLD")
    print("=" * 70)

    erros = []

    # ========================================================
    # VALIDAÇÃO DAS CHAVES PRIMÁRIAS
    # ========================================================

    if df_regiao["codigo_regiao"].duplicated().any():
        erros.append(
            "dim_regiao possui códigos de região duplicados."
        )

    if df_uf["codigo_uf"].duplicated().any():
        erros.append(
            "dim_uf possui códigos de UF duplicados."
        )

    if df_tempo["ano"].duplicated().any():
        erros.append(
            "dim_tempo possui anos duplicados."
        )

    if df_cidade["codigo_ibge"].duplicated().any():
        erros.append(
            "dim_cidade possui códigos IBGE duplicados."
        )

    if df_fact.duplicated(
        subset=["codigo_ibge", "ano"]
    ).any():
        erros.append(
            "fact_pib possui duplicidades na chave "
            "(codigo_ibge, ano)."
        )

    # ========================================================
    # VALIDAÇÃO DE NULOS NAS CHAVES
    # ========================================================

    if df_regiao["codigo_regiao"].isna().any():
        erros.append(
            "dim_regiao possui codigo_regiao nulo."
        )

    if df_uf["codigo_uf"].isna().any():
        erros.append(
            "dim_uf possui codigo_uf nulo."
        )

    if df_uf["codigo_regiao"].isna().any():
        erros.append(
            "dim_uf possui codigo_regiao nulo."
        )

    if df_cidade["codigo_ibge"].isna().any():
        erros.append(
            "dim_cidade possui codigo_ibge nulo."
        )

    if df_cidade["codigo_uf"].isna().any():
        erros.append(
            "dim_cidade possui codigo_uf nulo."
        )

    if df_tempo["ano"].isna().any():
        erros.append(
            "dim_tempo possui ano nulo."
        )

    if df_fact["codigo_ibge"].isna().any():
        erros.append(
            "fact_pib possui codigo_ibge nulo."
        )

    if df_fact["ano"].isna().any():
        erros.append(
            "fact_pib possui ano nulo."
        )

    # ========================================================
    # FK: DIM_UF -> DIM_REGIAO
    # ========================================================

    regioes_uf = set(
        df_uf["codigo_regiao"].dropna().unique()
    )

    regioes_dim = set(
        df_regiao["codigo_regiao"].dropna().unique()
    )

    regioes_sem_dim = regioes_uf - regioes_dim

    if regioes_sem_dim:
        erros.append(
            f"Existem {len(regioes_sem_dim)} regiões da "
            "dim_uf que não estão na dim_regiao."
        )

    # ========================================================
    # FK: DIM_CIDADE -> DIM_UF
    # ========================================================

    ufs_cidade = set(
        df_cidade["codigo_uf"].dropna().unique()
    )

    ufs_dim = set(
        df_uf["codigo_uf"].dropna().unique()
    )

    ufs_sem_dim = ufs_cidade - ufs_dim

    if ufs_sem_dim:
        erros.append(
            f"Existem {len(ufs_sem_dim)} UFs da "
            "dim_cidade que não estão na dim_uf."
        )

    # ========================================================
    # FK: FACT_PIB -> DIM_CIDADE
    # ========================================================

    cidades_fact = set(
        df_fact["codigo_ibge"].dropna().unique()
    )

    cidades_dim = set(
        df_cidade["codigo_ibge"].dropna().unique()
    )

    cidades_sem_dim = cidades_fact - cidades_dim

    if cidades_sem_dim:
        erros.append(
            f"Existem {len(cidades_sem_dim)} cidades da "
            "fact_pib que não estão na dim_cidade."
        )

    # ========================================================
    # FK: FACT_PIB -> DIM_TEMPO
    # ========================================================

    anos_fact = set(
        df_fact["ano"].dropna().unique()
    )

    anos_dim = set(
        df_tempo["ano"].dropna().unique()
    )

    anos_sem_dim = anos_fact - anos_dim

    if anos_sem_dim:
        erros.append(
            f"Existem {len(anos_sem_dim)} anos da "
            "fact_pib que não estão na dim_tempo."
        )

    # ========================================================
    # RESULTADO
    # ========================================================

    if erros:

        print("\nVALIDAÇÃO COM ERROS:")

        for erro in erros:
            print(f" - {erro}")

        raise ValueError(
            "A Gold apresentou erros de validação."
        )

    print("\nResumo da Gold:")
    print(f"Regiões:  {len(df_regiao)}")
    print(f"UFs:      {len(df_uf)}")
    print(f"Cidades:  {len(df_cidade)}")
    print(f"Anos:     {len(df_tempo)}")
    print(f"Fact PIB: {len(df_fact)}")

    print("\nVALIDAÇÃO OK")
    print("Todas as validações foram aprovadas.")


# ============================================================ #
# MAIN
# ============================================================ #
def criar_gold():
    inicio = time.time()
    print("")
    print("=" * 70)
    print("IBGE - CRIAÇÃO DA CAMADA GOLD")
    print("=" * 70)

    if not ARQUIVO_MUNICIPIOS.exists():
        raise FileNotFoundError(f"Arquivo de municípios não encontrado:\n{ARQUIVO_MUNICIPIOS}")

    if not ARQUIVO_FACT_PIB_SILVER.exists():
        raise FileNotFoundError(f"Arquivo Silver não encontrado:\n{ARQUIVO_FACT_PIB_SILVER}")

    print("\nCarregando municípios da Bronze...")
    municipios = carregar_json(ARQUIVO_MUNICIPIOS)
    print(f"Municípios carregados: {len(municipios)}")

    df_fact = criar_fact_pib()

    df_regiao = criar_dim_regiao(municipios)

    df_uf = criar_dim_uf(municipios)

    df_tempo = criar_dim_tempo(df_fact)

    df_cidade = criar_dim_cidade(municipios)


    # ============================================================
    # VALIDAÇÃO
    # ============================================================

    validar_gold(
        df_regiao,
        df_uf,
        df_tempo,
        df_cidade,
        df_fact
    )


    # ============================================================
    # SALVAMENTO
    # ============================================================

    print("\n" + "=" * 70)
    print("SALVANDO GOLD")
    print("=" * 70)

    salvar_parquet(df_regiao, DIR_DIM_REGIAO, "dim_regiao.parquet")
    salvar_parquet(df_uf, DIR_DIM_UF, "dim_uf.parquet")
    salvar_parquet(df_tempo, DIR_DIM_TEMPO, "dim_tempo.parquet")
    salvar_parquet(df_cidade, DIR_DIM_CIDADE, "dim_cidade.parquet")
    salvar_parquet(df_fact, DIR_FACT_PIB, "fact_pib.parquet")
    print(f"\nGold salva com sucesso em: {GOLD}")
    print(f"Tempo total: {time.time() - inicio:.2f} segundos")


if __name__ == "__main__":
    criar_gold()