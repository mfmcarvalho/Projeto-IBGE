from pathlib import Path
import json
import time
import requests


# ============================================================
# CONFIGURAÇÃO
# ============================================================

BASE_URL_SIDRA = (
    "https://servicodados.ibge.gov.br/api/v3/agregados"
)

# Este script está em:
#
# projto_ibge/
# └── ingestion/
#     └── criar_bronze_ibge.py
#
# parents[1] = projto_ibge

PROJECT_ROOT = Path(__file__).resolve().parents[1]

BRONZE = (
    PROJECT_ROOT
    / "data"
    / "bronze"
    / "ibge"
)

DIR_LOCALIDADES = (
    BRONZE
    / "localidades"
)

DIR_SIDRA = (
    BRONZE
    / "sidra"
)


# ============================================================
# ARQUIVOS DE LOCALIDADES
# ============================================================

ARQUIVO_ESTADOS = (
    DIR_LOCALIDADES
    / "estados.json"
)

ARQUIVO_MUNICIPIOS = (
    DIR_LOCALIDADES
    / "municipios.json"
)

ARQUIVO_MUNICIPIO_UF = (
    DIR_LOCALIDADES
    / "municipio_uf.json"
)

ARQUIVO_MUNICIPIOS_INVALIDOS = (
    DIR_LOCALIDADES
    / "municipios_invalidos.json"
)


# ============================================================
# TABELAS SIDRA
# ============================================================

TABELAS_SIDRA = {
    "5938": "PIB dos Municípios",
    "6803": "Abastecimento de água",
    "6804": "Canalização de água",
    "6805": "Esgotamento sanitário",
    "6892": "Destino do lixo",
}


# ============================================================
# UTILITÁRIOS
# ============================================================

def imprimir_progresso(
    atual,
    total,
    prefixo="",
    intervalo=250
):
    """
    Exibe progresso no terminal.

    Não utiliza \\r, evitando problemas de exibição
    em alguns terminais do Windows.
    """

    if total == 0:
        percentual = 100
    else:
        percentual = (
            atual / total
        ) * 100

    if (
        atual == 1
        or atual == total
        or atual % intervalo == 0
    ):
        print(
            f"[PROGRESSO] {prefixo}: "
            f"{atual:,}/{total:,} "
            f"({percentual:6.2f}%)",
            flush=True
        )


def salvar_json(
    caminho: Path,
    dados
):
    """
    Salva dados em JSON UTF-8.
    """

    with caminho.open(
        "w",
        encoding="utf-8"
    ) as arquivo:

        json.dump(
            dados,
            arquivo,
            ensure_ascii=False,
            indent=2
        )


def carregar_json(
    caminho: Path
):
    """
    Carrega JSON de arquivo local.
    """

    print(
        f"[LEITURA] {caminho}",
        flush=True
    )

    inicio = time.time()

    tamanho_mb = (
        caminho.stat().st_size
        / (1024 * 1024)
    )

    print(
        f"[LEITURA] Tamanho: "
        f"{tamanho_mb:.2f} MB",
        flush=True
    )

    with caminho.open(
        "r",
        encoding="utf-8"
    ) as arquivo:

        dados = json.load(arquivo)

    tempo = time.time() - inicio

    print(
        f"[LEITURA] Concluída em "
        f"{tempo:.2f} segundos.",
        flush=True
    )

    return dados


def get_json(url):
    """
    Executa GET e retorna JSON.
    """

    print(
        f"\n[HTTP] GET {url}",
        flush=True
    )

    inicio = time.time()

    response = requests.get(
        url,
        timeout=120
    )

    tempo = time.time() - inicio

    print(
        f"[HTTP] Status: "
        f"{response.status_code}",
        flush=True
    )

    print(
        f"[HTTP] Tempo: "
        f"{tempo:.2f} segundos",
        flush=True
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# DIRETÓRIOS
# ============================================================

def criar_diretorios():

    print(
        "\n[ESTRUTURA] Criando diretórios...",
        flush=True
    )

    DIR_LOCALIDADES.mkdir(
        parents=True,
        exist_ok=True
    )

    DIR_SIDRA.mkdir(
        parents=True,
        exist_ok=True
    )

    for tabela in TABELAS_SIDRA:

        (
            DIR_SIDRA
            / tabela
        ).mkdir(
            parents=True,
            exist_ok=True
        )

    print(
        "[OK] Diretórios preparados.",
        flush=True
    )


# ============================================================
# LOCALIDADES - ESTADOS
# ============================================================

def baixar_estados():

    print(
        "\n[LOCALIDADES] Estados",
        flush=True
    )

    url = (
        "https://servicodados.ibge.gov.br/api/v1/"
        "localidades/estados"
    )

    dados = get_json(url)

    if not isinstance(
        dados,
        list
    ):
        raise ValueError(
            "A API de estados não retornou "
            "uma lista."
        )

    salvar_json(
        ARQUIVO_ESTADOS,
        dados
    )

    print(
        f"[OK] Estados salvos: "
        f"{ARQUIVO_ESTADOS}",
        flush=True
    )

    print(
        f"[OK] Registros: {len(dados):,}",
        flush=True
    )


# ============================================================
# LOCALIDADES - MUNICÍPIOS
# ============================================================

def baixar_municipios():

    print(
        "\n[LOCALIDADES] Municípios",
        flush=True
    )

    url = (
        "https://servicodados.ibge.gov.br/api/v1/"
        "localidades/municipios"
    )

    dados = get_json(url)

    if not isinstance(
        dados,
        list
    ):
        raise ValueError(
            "A API de municípios não retornou "
            "uma lista."
        )

    salvar_json(
        ARQUIVO_MUNICIPIOS,
        dados
    )

    print(
        f"[OK] Municípios salvos: "
        f"{ARQUIVO_MUNICIPIOS}",
        flush=True
    )

    print(
        f"[OK] Registros: {len(dados):,}",
        flush=True
    )


# ============================================================
# DE/PARA MUNICÍPIO → UF
# ============================================================

def criar_municipio_uf():

    inicio_total = time.time()

    print(
        "\n" + "=" * 70,
        flush=True
    )

    print(
        "CRIANDO DE/PARA MUNICÍPIO → UF",
        flush=True
    )

    print(
        "=" * 70,
        flush=True
    )

    # --------------------------------------------------------
    # Verifica arquivos
    # --------------------------------------------------------

    if not ARQUIVO_MUNICIPIOS.exists():

        raise FileNotFoundError(
            f"Arquivo não encontrado:\n"
            f"{ARQUIVO_MUNICIPIOS}"
        )

    if not ARQUIVO_ESTADOS.exists():

        raise FileNotFoundError(
            f"Arquivo não encontrado:\n"
            f"{ARQUIVO_ESTADOS}"
        )

    print(
        "\n[1/5] Carregando municípios...",
        flush=True
    )

    municipios = carregar_json(
        ARQUIVO_MUNICIPIOS
    )

    if not isinstance(
        municipios,
        list
    ):

        raise ValueError(
            "municipios.json não contém "
            "uma lista."
        )

    total_municipios = len(
        municipios
    )

    print(
        f"[OK] Municípios encontrados: "
        f"{total_municipios:,}",
        flush=True
    )

    # --------------------------------------------------------
    # Estados
    # --------------------------------------------------------

    print(
        "\n[2/5] Carregando estados...",
        flush=True
    )

    estados = carregar_json(
        ARQUIVO_ESTADOS
    )

    if not isinstance(
        estados,
        list
    ):

        raise ValueError(
            "estados.json não contém "
            "uma lista."
        )

    estados_por_id = {}

    for estado in estados:

        codigo = estado.get("id")

        if codigo is not None:

            estados_por_id[codigo] = estado

    print(
        f"[OK] Estados encontrados: "
        f"{len(estados):,}",
        flush=True
    )

    # --------------------------------------------------------
    # Processamento
    # --------------------------------------------------------

    print(
        "\n[3/5] Processando municípios...",
        flush=True
    )

    de_para = []

    municipios_invalidos = []

    inicio_processamento = time.time()

    for indice, municipio in enumerate(
        municipios,
        start=1
    ):

        codigo_ibge = (
            municipio.get("id")
        )

        nome_municipio = (
            municipio.get("nome")
        )

        # ----------------------------------------------------
        # Hierarquia territorial
        # ----------------------------------------------------

        microrregiao = (
            municipio.get(
                "microrregiao"
            )
            or {}
        )

        mesorregiao = (
            microrregiao.get(
                "mesorregiao"
            )
            or {}
        )

        uf = (
            mesorregiao.get(
                "UF"
            )
            or {}
        )

        regiao = (
            uf.get(
                "regiao"
            )
            or {}
        )

        # ----------------------------------------------------
        # Detecta problemas
        # ----------------------------------------------------

        problemas = []

        if not codigo_ibge:
            problemas.append(
                "codigo_ibge ausente"
            )

        if not nome_municipio:
            problemas.append(
                "nome do município ausente"
            )

        if not uf:
            problemas.append(
                "UF ausente na hierarquia"
            )

        if not uf.get("id"):
            problemas.append(
                "codigo_uf ausente"
            )

        if not uf.get("sigla"):
            problemas.append(
                "sigla_uf ausente"
            )

        if not uf.get("nome"):
            problemas.append(
                "nome do estado ausente"
            )

        if not regiao.get("id"):
            problemas.append(
                "codigo_regiao ausente"
            )

        if not regiao.get("nome"):
            problemas.append(
                "macro_regiao ausente"
            )

        # ----------------------------------------------------
        # Salva município inválido
        #
        # IMPORTANTE:
        # municipio_original contém o JSON COMPLETO
        # retornado pela API do IBGE.
        # ----------------------------------------------------

        if problemas:

            municipios_invalidos.append(
                {
                    "problemas_detectados": problemas,
                    "municipio_original": municipio
                }
            )

            print(
                "\n[ATENÇÃO] Município inválido:",
                flush=True
            )

            print(
                f"          Código: "
                f"{codigo_ibge}",
                flush=True
            )

            print(
                f"          Nome: "
                f"{nome_municipio}",
                flush=True
            )

            print(
                f"          Problemas: "
                f"{', '.join(problemas)}",
                flush=True
            )

        # ----------------------------------------------------
        # Monta de/para
        # ----------------------------------------------------

        registro = {
            "codigo_ibge": codigo_ibge,
            "municipio": nome_municipio,
            "codigo_uf": uf.get("id"),
            "sigla_uf": uf.get("sigla"),
            "estado": uf.get("nome"),
            "codigo_regiao": regiao.get("id"),
            "macro_regiao": regiao.get("nome"),
        }

        de_para.append(
            registro
        )

        imprimir_progresso(
            indice,
            total_municipios,
            prefixo="Processando"
        )

    print(
        "\n",
        flush=True
    )

    tempo_processamento = (
        time.time()
        - inicio_processamento
    )

    print(
        f"[OK] Processamento concluído "
        f"em {tempo_processamento:.2f} segundos.",
        flush=True
    )

    print(
        f"[OK] Registros gerados: "
        f"{len(de_para):,}",
        flush=True
    )

    print(
        f"[INFO] Municípios inválidos: "
        f"{len(municipios_invalidos):,}",
        flush=True
    )

    # --------------------------------------------------------
    # Validação 1 - campos
    # --------------------------------------------------------

    print(
        "\n[4/5] Validando registros...",
        flush=True
    )

    registros_invalidos = []

    for indice, registro in enumerate(
        de_para,
        start=1
    ):

        campos_invalidos = (
            not registro["codigo_ibge"]
            or not registro["municipio"]
            or not registro["codigo_uf"]
            or not registro["sigla_uf"]
            or not registro["estado"]
            or not registro["macro_regiao"]
        )

        if campos_invalidos:

            registros_invalidos.append(
                registro
            )

        imprimir_progresso(
            indice,
            len(de_para),
            prefixo="Campos"
        )

    print(
        "\n",
        flush=True
    )

    if registros_invalidos:

        print(
            f"[ATENÇÃO] "
            f"{len(registros_invalidos):,} "
            f"registros com campos incompletos.",
            flush=True
        )

    else:

        print(
            "[OK] Campos obrigatórios válidos.",
            flush=True
        )

    # --------------------------------------------------------
    # Validação 2 - UF
    # --------------------------------------------------------

    ufs_invalidas = []

    for indice, registro in enumerate(
        de_para,
        start=1
    ):

        codigo_uf = registro[
            "codigo_uf"
        ]

        if codigo_uf not in estados_por_id:

            ufs_invalidas.append(
                registro
            )

        imprimir_progresso(
            indice,
            len(de_para),
            prefixo="UF"
        )

    print(
        "\n",
        flush=True
    )

    if ufs_invalidas:

        print(
            f"[ATENÇÃO] "
            f"{len(ufs_invalidas):,} "
            f"UFs não encontradas "
            f"em estados.json.",
            flush=True
        )

    else:

        print(
            "[OK] Todas as UFs são válidas.",
            flush=True
        )

    # --------------------------------------------------------
    # Validação 3 - duplicidades
    # --------------------------------------------------------

    duplicados = set()

    codigos = set()

    for indice, registro in enumerate(
        de_para,
        start=1
    ):

        codigo = registro[
            "codigo_ibge"
        ]

        if codigo in codigos:

            duplicados.add(
                codigo
            )

        else:

            codigos.add(
                codigo
            )

        imprimir_progresso(
            indice,
            len(de_para),
            prefixo="Duplicidade"
        )

    print(
        "\n",
        flush=True
    )

    if duplicados:

        raise ValueError(
            "Códigos IBGE duplicados: "
            f"{sorted(duplicados)}"
        )

    print(
        "[OK] Nenhuma duplicidade encontrada.",
        flush=True
    )

    # --------------------------------------------------------
    # Ordenação
    # --------------------------------------------------------

    de_para.sort(
        key=lambda x: (
            int(x["codigo_ibge"])
            if x["codigo_ibge"] is not None
            else 0
        )
    )

    # --------------------------------------------------------
    # Salva município_uf.json
    # --------------------------------------------------------

    print(
        "\n[ARQUIVO] Salvando municipio_uf.json...",
        flush=True
    )

    salvar_json(
        ARQUIVO_MUNICIPIO_UF,
        de_para
    )

    print(
        f"[OK] {ARQUIVO_MUNICIPIO_UF}",
        flush=True
    )

    # --------------------------------------------------------
    # Salva municípios_invalidos.json
    # --------------------------------------------------------

    print(
        "\n[ARQUIVO] Salvando "
        "municipios_invalidos.json...",
        flush=True
    )

    salvar_json(
        ARQUIVO_MUNICIPIOS_INVALIDOS,
        municipios_invalidos
    )

    print(
        f"[OK] {ARQUIVO_MUNICIPIOS_INVALIDOS}",
        flush=True
    )

    # --------------------------------------------------------
    # Amostra
    # --------------------------------------------------------

    print(
        "\nAmostra do de/para:",
        flush=True
    )

    print(
        "-" * 70,
        flush=True
    )

    for registro in de_para[:5]:

        print(
            json.dumps(
                registro,
                ensure_ascii=False,
                indent=2
            ),
            flush=True
        )

        print(
            "-" * 70,
            flush=True
        )

    tempo_total = (
        time.time()
        - inicio_total
    )

    print(
        "\n[RESUMO] De/para concluído.",
        flush=True
    )

    print(
        f"  Municípios: "
        f"{len(de_para):,}",
        flush=True
    )

    print(
        f"  Estados: "
        f"{len(estados_por_id):,}",
        flush=True
    )

    print(
        f"  Municípios inválidos: "
        f"{len(municipios_invalidos):,}",
        flush=True
    )

    print(
        f"  UFs inválidas: "
        f"{len(ufs_invalidas):,}",
        flush=True
    )

    print(
        f"  Duplicidades: "
        f"{len(duplicados):,}",
        flush=True
    )

    print(
        f"  Tempo: "
        f"{tempo_total:.2f} segundos",
        flush=True
    )


# ============================================================
# SIDRA - METADADOS
# ============================================================

def baixar_metadados_sidra(
    tabela,
    descricao
):

    print(
        "\n" + "-" * 70,
        flush=True
    )

    print(
        f"SIDRA {tabela} - {descricao}",
        flush=True
    )

    url = (
        f"{BASE_URL_SIDRA}"
        f"/{tabela}"
        f"/metadados"
    )

    dados = get_json(url)

    caminho = (
        DIR_SIDRA
        / tabela
        / "metadados.json"
    )

    salvar_json(
        caminho,
        dados
    )

    print(
        f"[OK] Metadados: {caminho}",
        flush=True
    )


# ============================================================
# SIDRA - PERÍODOS
# ============================================================

def baixar_periodos_sidra(
    tabela,
    descricao
):

    print(
        f"\nSIDRA {tabela} - períodos",
        flush=True
    )

    url = (
        f"{BASE_URL_SIDRA}"
        f"/{tabela}"
        f"/periodos"
    )

    dados = get_json(url)

    caminho = (
        DIR_SIDRA
        / tabela
        / "periodos.json"
    )

    salvar_json(
        caminho,
        dados
    )

    print(
        f"[OK] Períodos: {caminho}",
        flush=True
    )


# ============================================================
# SIDRA - INGESTÃO
# ============================================================

def baixar_sidra():

    print(
        "\n" + "=" * 70,
        flush=True
    )

    print(
        "INGESTÃO SIDRA",
        flush=True
    )

    print(
        "=" * 70,
        flush=True
    )

    tabela = "5938"
    descricao = TABELAS_SIDRA[tabela]

    ano_inicio = 2002
    ano_fim = 2023

    print(
        f"\n[TABELA] {tabela} - {descricao}",
        flush=True
    )

    print(
        f"[PERÍODO] {ano_inicio} até {ano_fim}",
        flush=True
    )

    print(
        "[VARIÁVEIS]",
        flush=True
    )

    print(
        "37   = PIB total",
        flush=True
    )

    print(
        "543  = Impostos líquidos de subsídios",
        flush=True
    )

    print(
        "498  = VAB total",
        flush=True
    )

    print(
        "513  = VAB agropecuária",
        flush=True
    )

    print(
        "517  = VAB indústria",
        flush=True
    )

    print(
        "6575 = VAB serviços, exclusive administração",
        flush=True
    )

    print(
        "525  = VAB administração, defesa, educação e saúde públicas",
        flush=True
    )

    # --------------------------------------------------------
    # Metadados
    # --------------------------------------------------------

    url_metadados = (
        f"{BASE_URL_SIDRA}"
        f"/{tabela}"
        f"/metadados"
    )

    dados_metadados = get_json(
        url_metadados
    )

    caminho_metadados = (
        DIR_SIDRA
        / tabela
        / "metadados.json"
    )

    salvar_json(
        caminho_metadados,
        dados_metadados
    )

    print(
        f"[OK] Metadados: "
        f"{caminho_metadados}",
        flush=True
    )

    # --------------------------------------------------------
    # Períodos
    # --------------------------------------------------------

    url_periodos = (
        f"{BASE_URL_SIDRA}"
        f"/{tabela}"
        f"/periodos"
    )

    dados_periodos = get_json(
        url_periodos
    )

    caminho_periodos = (
        DIR_SIDRA
        / tabela
        / "periodos.json"
    )

    salvar_json(
        caminho_periodos,
        dados_periodos
    )

    print(
        f"[OK] Períodos: "
        f"{caminho_periodos}",
        flush=True
    )

    # --------------------------------------------------------
    # Variáveis
    # --------------------------------------------------------
    #
    # 37   = Produto Interno Bruto a preços correntes
    # 543  = Impostos, líquidos de subsídios,
    #        sobre produtos a preços correntes
    # 498  = Valor adicionado bruto a preços correntes total
    # 513  = VAB da agropecuária
    # 517  = VAB da indústria
    # 6575 = VAB dos serviços, exclusive administração,
    #        defesa, educação e saúde públicas e seguridade social
    # 525  = VAB da administração, defesa, educação e saúde
    #        públicas e seguridade social
    #
    # N6 = município
    # all = todos os municípios
    #
    # --------------------------------------------------------

    variaveis = (
        "37,543,498,513,517,6575,525"
    )

    # --------------------------------------------------------
    # Dados por ano
    # --------------------------------------------------------

    for ano in range(
        ano_inicio,
        ano_fim + 1
    ):

        print(
            "\n" + "-" * 70,
            flush=True
        )

        print(
            f"[ANO] {ano}",
            flush=True
        )

        print(
            "-" * 70,
            flush=True
        )

        url_dados = (
            f"{BASE_URL_SIDRA}"
            f"/{tabela}"
            f"/periodos/{ano}"
            f"/variaveis/{variaveis}"
            f"?localidades=N6[all]"
        )

        print(
            f"[HTTP] Buscando dados:",
            flush=True
        )

        print(
            f"[HTTP] {url_dados}",
            flush=True
        )

        dados = get_json(
            url_dados
        )

        caminho_dados = (
            DIR_SIDRA
            / tabela
            / f"dados_{ano}.json"
        )

        salvar_json(
            caminho_dados,
            dados
        )

        print(
            f"[OK] Dados salvos: "
            f"{caminho_dados}",
            flush=True
        )

        if isinstance(
            dados,
            list
        ):
            print(
                f"[OK] Registros retornados: "
                f"{len(dados):,}",
                flush=True
            )
        else:
            print(
                "[INFO] Resposta retornada "
                "não é uma lista.",
                flush=True
            )

    # --------------------------------------------------------
    # Finalização
    # --------------------------------------------------------

    print(
        "\n" + "=" * 70,
        flush=True
    )

    print(
        "INGESTÃO SIDRA CONCLUÍDA",
        flush=True
    )

    print(
        f"Tabela: {tabela}",
        flush=True
    )

    print(
        f"Período: {ano_inicio} até {ano_fim}",
        flush=True
    )

    print(
        f"Variáveis: {variaveis}",
        flush=True
    )

    print(
        "=" * 70,
        flush=True
    )
# ============================================================
# MAIN
# ============================================================

def main():

    inicio_total = time.time()

    print(
        "\n" + "=" * 70,
        flush=True
    )

    print(
        "IBGE - INGESTÃO BRONZE",
        flush=True
    )

    print(
        "=" * 70,
        flush=True
    )

    print(
        f"\nProjeto:",
        flush=True
    )

    print(
        f"  {PROJECT_ROOT}",
        flush=True
    )

    print(
        f"\nBronze:",
        flush=True
    )

    print(
        f"  {BRONZE}",
        flush=True
    )

    # ========================================================
    # 1. ESTRUTURA
    # ========================================================

    criar_diretorios()

    # ========================================================
    # 2. LOCALIDADES
    # ========================================================

    print(
        "\n" + "=" * 70,
        flush=True
    )

    print(
        "[1/3] LOCALIDADES",
        flush=True
    )

    print(
        "=" * 70,
        flush=True
    )

    baixar_estados()

    baixar_municipios()

    # ========================================================
    # 3. DE/PARA
    # ========================================================

    print(
        "\n" + "=" * 70,
        flush=True
    )

    print(
        "[2/3] DE/PARA MUNICÍPIO → UF",
        flush=True
    )

    print(
        "=" * 70,
        flush=True
    )

    criar_municipio_uf()

    # ========================================================
    # 4. SIDRA
    # ========================================================

    print(
        "\n" + "=" * 70,
        flush=True
    )

    print(
        "[3/3] SIDRA",
        flush=True
    )

    print(
        "=" * 70,
        flush=True
    )

    baixar_sidra()

    # ========================================================
    # FINAL
    # ========================================================

    tempo_total = (
        time.time()
        - inicio_total
    )

    print(
        "\n" + "=" * 70,
        flush=True
    )

    print(
        "INGESTÃO BRONZE CONCLUÍDA",
        flush=True
    )

    print(
        "=" * 70,
        flush=True
    )

    print(
        f"Tempo total: "
        f"{tempo_total:.2f} segundos",
        flush=True
    )

    print(
        "\nBronze disponível em:",
        flush=True
    )

    print(
        f"{BRONZE}",
        flush=True
    )

    print(
        "\n" + "=" * 70,
        flush=True
    )


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":
    main()

