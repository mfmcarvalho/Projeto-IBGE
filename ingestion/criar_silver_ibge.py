from pathlib import Path
import json
import time

import pandas as pd


# ============================================================
# CONFIGURAÇÕES
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

BRONZE = PROJECT_ROOT / "data" / "bronze" / "ibge"
SILVER = PROJECT_ROOT / "data" / "silver" / "ibge"

DIR_SIDRA = BRONZE / "sidra"
DIR_TABELA = DIR_SIDRA / "5938"

DIR_SILVER = SILVER / "fact_pib"

ARQUIVO_SILVER = DIR_SILVER / "fact_pib.parquet"


# ============================================================
# VARIÁVEIS DA TABELA 5938
# ============================================================

VARIAVEIS = {
    "37": "pib_total",
    "543": "impostos_liquidos",
    "498": "vab_total",
    "513": "vab_agropecuaria",
    "517": "vab_industria",
    "6575": "vab_servicos_exclusive_adm",
    "525": "vab_administracao",
}


# ============================================================
# COLUNAS DO SILVER
# ============================================================

COLUNAS = [
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


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def carregar_json(caminho):
    """
    Carrega um arquivo JSON.
    """

    with open(
        caminho,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


def converter_valor(valor):
    """
    Converte valores numéricos do SIDRA.

    Valores como:
        ...
        None
        ""

    são tratados como NULL.
    """

    if valor in (
        None,
        "",
        "..."
    ):
        return None

    try:
        return float(valor)

    except (ValueError, TypeError):
        return None


def converter_codigo_ibge(valor):
    """
    Converte o código do município para inteiro.
    """

    if valor in (
        None,
        "",
        "..."
    ):
        return None

    try:
        return int(valor)

    except (ValueError, TypeError):
        return None


# ============================================================
# DESCOBRIR ARQUIVOS DA BRONZE
# ============================================================

def descobrir_arquivos_periodo():
    """
    Localiza automaticamente todos os arquivos:

        dados_AAAA.json

    existentes na Bronze.
    """

    if not DIR_TABELA.exists():

        raise FileNotFoundError(
            f"Diretório Bronze não encontrado: "
            f"{DIR_TABELA}"
        )

    arquivos = []

    for arquivo in DIR_TABELA.glob(
        "dados_*.json"
    ):

        try:

            ano = int(
                arquivo.stem.replace(
                    "dados_",
                    ""
                )
            )

        except ValueError:

            continue

        arquivos.append(
            (ano, arquivo)
        )

    arquivos.sort(
        key=lambda x: x[0]
    )

    return arquivos


# ============================================================
# PROCESSAR UM PERÍODO
# ============================================================

def processar_periodo(ano, caminho):
    """
    Processa um arquivo dados_AAAA.json.

    Estrutura real do SIDRA:

        [
            {
                "id": "37",
                ...
                "resultados": [
                    {
                        "classificacoes": [...],
                        "series": [
                            {
                                "localidade": {
                                    "id": "1100015",
                                    "nivel": {
                                        "id": "N6",
                                        "nome": "Município"
                                    },
                                    "nome": "Alta Floresta D'Oeste - RO"
                                },
                                "serie": {
                                    "2002": "..."
                                }
                            }
                        ]
                    }
                ]
            }
        ]
    """

    print(
        f"Processando {ano}: "
        f"{caminho.name}"
    )

    dados = carregar_json(caminho)

    if not isinstance(dados, list):

        raise ValueError(
            f"Formato inesperado em {caminho}. "
            f"Esperado: lista."
        )

    # --------------------------------------------------------
    # Dicionário final dos municípios
    # --------------------------------------------------------

    municipios = {}

    # --------------------------------------------------------
    # Cada bloco representa uma variável
    # --------------------------------------------------------

    for bloco in dados:

        if not isinstance(bloco, dict):
            continue

        # ----------------------------------------------------
        # ID da variável
        # ----------------------------------------------------

        variavel = str(
            bloco.get("id", "")
        )

        if variavel not in VARIAVEIS:
            continue

        coluna = VARIAVEIS[variavel]

        # ----------------------------------------------------
        # Resultados
        # ----------------------------------------------------

        resultados = bloco.get(
            "resultados",
            []
        )

        if not isinstance(resultados, list):
            continue

        # ----------------------------------------------------
        # Cada resultado contém as séries
        # ----------------------------------------------------

        for resultado in resultados:

            if not isinstance(resultado, dict):
                continue

            series = resultado.get(
                "series",
                []
            )

            if not isinstance(series, list):
                continue

            # ------------------------------------------------
            # Cada série representa um município
            # ------------------------------------------------

            for item in series:

                if not isinstance(item, dict):
                    continue

                # --------------------------------------------
                # Localidade
                # --------------------------------------------

                localidade = item.get(
                    "localidade",
                    {}
                )

                if not isinstance(
                    localidade,
                    dict
                ):
                    continue

                # --------------------------------------------
                # Garantir que estamos tratando municípios
                # --------------------------------------------

                nivel = localidade.get(
                    "nivel",
                    {}
                )

                if isinstance(nivel, dict):

                    nivel_id = str(
                        nivel.get("id", "")
                    )

                    if nivel_id != "N6":
                        continue

                # --------------------------------------------
                # Código IBGE
                # --------------------------------------------

                codigo_ibge = converter_codigo_ibge(
                    localidade.get("id")
                )

                if codigo_ibge is None:
                    continue

                # --------------------------------------------
                # Série temporal
                # --------------------------------------------

                serie = item.get(
                    "serie",
                    {}
                )

                if not isinstance(
                    serie,
                    dict
                ):
                    continue

                valor = serie.get(
                    str(ano)
                )

                # --------------------------------------------
                # Inicializar município
                # --------------------------------------------

                if codigo_ibge not in municipios:

                    municipios[codigo_ibge] = {
                        "codigo_ibge": codigo_ibge,
                        "ano": ano,
                        "pib_total": None,
                        "impostos_liquidos": None,
                        "vab_total": None,
                        "vab_agropecuaria": None,
                        "vab_industria": None,
                        "vab_servicos_exclusive_adm": None,
                        "vab_administracao": None,
                    }

                # --------------------------------------------
                # Gravar variável
                # --------------------------------------------

                municipios[codigo_ibge][coluna] = (
                    converter_valor(valor)
                )

    # --------------------------------------------------------
    # DataFrame
    # --------------------------------------------------------

    df = pd.DataFrame(
        municipios.values(),
        columns=COLUNAS
    )

    return df


# ============================================================
# VALIDAR PERÍODO
# ============================================================

def validar_periodo(df, ano):
    """
    Valida os dados de um determinado ano.
    """

    quantidade = len(df)

    print(
        f"  Municípios encontrados: "
        f"{quantidade}"
    )

    if quantidade == 0:

        raise ValueError(
            f"Nenhum município encontrado "
            f"para o ano {ano}."
        )

    # --------------------------------------------------------
    # Duplicidades
    # --------------------------------------------------------

    duplicados = df.duplicated(
        subset=[
            "codigo_ibge",
            "ano"
        ]
    ).sum()

    if duplicados > 0:

        raise ValueError(
            f"Foram encontrados "
            f"{duplicados} registros duplicados "
            f"para o ano {ano}."
        )

    # --------------------------------------------------------
    # Validação de quantidade
    #
    # Esperamos aproximadamente 5.570 municípios.
    # Boa Esperança do Norte é ignorada conforme
    # decisão do projeto.
    # --------------------------------------------------------

    if quantidade < 5500:

        print(
            f"  AVISO: quantidade de municípios "
            f"abaixo do esperado: {quantidade}"
        )


# ============================================================
# CRIAR SILVER
# ============================================================

def criar_silver():

    inicio = time.time()

    print("=" * 70)
    print("CRIAÇÃO DO SILVER - PIB DOS MUNICÍPIOS")
    print("=" * 70)

    # --------------------------------------------------------
    # Criar diretório
    # --------------------------------------------------------

    DIR_SILVER.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Descobrir períodos
    # --------------------------------------------------------

    arquivos = descobrir_arquivos_periodo()

    if not arquivos:

        raise FileNotFoundError(
            "Nenhum arquivo dados_AAAA.json "
            "foi encontrado na Bronze."
        )

    print()

    print(
        f"Períodos encontrados: "
        f"{len(arquivos)}"
    )

    print(
        f"Primeiro período: "
        f"{arquivos[0][0]}"
    )

    print(
        f"Último período: "
        f"{arquivos[-1][0]}"
    )

    print()

    # --------------------------------------------------------
    # Processar períodos
    # --------------------------------------------------------

    dataframes = []

    for ano, caminho in arquivos:

        inicio_ano = time.time()

        df_ano = processar_periodo(
            ano,
            caminho
        )

        validar_periodo(
            df_ano,
            ano
        )

        dataframes.append(
            df_ano
        )

        tempo_ano = time.time() - inicio_ano

        print(
            f"  Tempo: "
            f"{tempo_ano:.2f} segundos"
        )

        print()

    # --------------------------------------------------------
    # Consolidar
    # --------------------------------------------------------

    print(
        "Consolidando períodos..."
    )

    df_final = pd.concat(
        dataframes,
        ignore_index=True
    )

    # --------------------------------------------------------
    # Ordenar
    # --------------------------------------------------------

    df_final = df_final.sort_values(
        by=[
            "ano",
            "codigo_ibge"
        ]
    ).reset_index(
        drop=True
    )

    # --------------------------------------------------------
    # Tipos
    # --------------------------------------------------------

    df_final["codigo_ibge"] = (
        pd.to_numeric(
            df_final["codigo_ibge"],
            errors="coerce"
        ).astype("Int64")
    )

    df_final["ano"] = (
        pd.to_numeric(
            df_final["ano"],
            errors="coerce"
        ).astype("Int64")
    )

    colunas_valores = [
        "pib_total",
        "impostos_liquidos",
        "vab_total",
        "vab_agropecuaria",
        "vab_industria",
        "vab_servicos_exclusive_adm",
        "vab_administracao",
    ]

    for coluna in colunas_valores:

        df_final[coluna] = pd.to_numeric(
            df_final[coluna],
            errors="coerce"
        )

    # --------------------------------------------------------
    # Validação final
    # --------------------------------------------------------

    print()
    print(
        "Validação final..."
    )

    duplicados = df_final.duplicated(
        subset=[
            "codigo_ibge",
            "ano"
        ]
    ).sum()

    if duplicados > 0:

        raise ValueError(
            f"O Silver possui "
            f"{duplicados} registros duplicados."
        )

    # --------------------------------------------------------
    # Estatísticas
    # --------------------------------------------------------

    print(
        f"Total de registros: "
        f"{len(df_final)}"
    )

    print(
        f"Municípios distintos: "
        f"{df_final['codigo_ibge'].nunique()}"
    )

    print(
        f"Anos distintos: "
        f"{df_final['ano'].nunique()}"
    )

    print(
        f"Período: "
        f"{df_final['ano'].min()} "
        f"até "
        f"{df_final['ano'].max()}"
    )

    print()

    # --------------------------------------------------------
    # Salvar Parquet
    # --------------------------------------------------------

    print(
        f"Salvando: "
        f"{ARQUIVO_SILVER}"
    )

    df_final.to_parquet(
        ARQUIVO_SILVER,
        index=False,
        engine="pyarrow"
    )

    # --------------------------------------------------------
    # Final
    # --------------------------------------------------------

    tempo_total = time.time() - inicio

    print()
    print("=" * 70)
    print("SILVER CONCLUÍDO")
    print("=" * 70)

    print(
        f"Arquivo: "
        f"{ARQUIVO_SILVER}"
    )

    print(
        f"Registros: "
        f"{len(df_final)}"
    )

    print(
        f"Municípios: "
        f"{df_final['codigo_ibge'].nunique()}"
    )

    print(
        f"Anos: "
        f"{df_final['ano'].min()} "
        f"até "
        f"{df_final['ano'].max()}"
    )

    print(
        f"Tempo total: "
        f"{tempo_total:.2f} segundos"
    )

    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

def main():

    try:

        criar_silver()

    except Exception as e:

        print()
        print("=" * 70)
        print("ERRO NA CRIAÇÃO DO SILVER")
        print("=" * 70)

        print(
            f"{type(e).__name__}: {e}"
        )

        print("=" * 70)

        raise


if __name__ == "__main__":
    main()