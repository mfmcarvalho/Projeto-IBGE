from pathlib import Path
import hashlib
import json
import time
import requests


# ============================================================
# CONFIGURAÇÃO
# ============================================================

BASE_URL_SIDRA = (
    "https://servicodados.ibge.gov.br/api/v3/agregados"
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]

BRONZE = (
    PROJECT_ROOT
    / "data"
    / "bronze"
    / "ibge"
)

DIR_SIDRA = BRONZE / "sidra"

TABELA = "5938"

VARIAVEIS = (
    "37,543,498,513,517,6575,525"
)

DIR_TABELA = DIR_SIDRA / TABELA

ARQUIVO_METADADOS = (
    DIR_TABELA / "metadados.json"
)

ARQUIVO_PERIODOS = (
    DIR_TABELA / "periodos.json"
)


# ============================================================
# CONFIGURAÇÃO DO INCREMENTAL
# ============================================================

# Verifica o conteúdo do último período disponível.
#
# Exemplo:
#
# 2023 é o último período atual.
#
# O script consulta 2023 novamente para detectar
# eventual correção/alteração feita pelo IBGE.
#
# Os períodos históricos anteriores não são baixados
# novamente todos os dias.
VERIFICAR_ULTIMO_PERIODO = True


# ============================================================
# FUNÇÕES JSON
# ============================================================

def salvar_json(dados, caminho):
    caminho.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        caminho,
        "w",
        encoding="utf-8"
    ) as arquivo:

        json.dump(
            dados,
            arquivo,
            ensure_ascii=False,
            indent=2
        )


def carregar_json(caminho):
    with open(
        caminho,
        "r",
        encoding="utf-8"
    ) as arquivo:

        return json.load(arquivo)


# ============================================================
# HASH CANÔNICO
# ============================================================

def gerar_bytes_canonicos(dados):
    """
    Converte o JSON para uma representação canônica.

    Isso evita falso positivo de alteração causado apenas
    por diferenças de indentação ou formatação.
    """

    return json.dumps(
        dados,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":")
    ).encode("utf-8")


def calcular_hash_json(dados):
    return hashlib.sha256(
        gerar_bytes_canonicos(dados)
    ).hexdigest()


def calcular_hash_arquivo_json(caminho):
    dados = carregar_json(caminho)

    return calcular_hash_json(dados)


# ============================================================
# HTTP
# ============================================================

def get_response(url):
    """
    Executa GET no IBGE.

    timeout:
        10 segundos para conexão
        300 segundos para resposta

    O timeout maior é importante porque a tabela 5938
    pode retornar bastante informação.
    """

    resposta = requests.get(
        url,
        timeout=(
            10,
            300
        )
    )

    resposta.raise_for_status()

    return resposta


def get_json(url):
    resposta = get_response(url)

    return resposta.json()


# ============================================================
# SALVAR RESPOSTA
# ============================================================

def salvar_resposta_json(
    dados,
    caminho
):
    salvar_json(
        dados,
        caminho
    )


# ============================================================
# PERÍODOS
# ============================================================

def obter_periodos():
    print("Consultando períodos disponíveis no SIDRA...")

    url = (
        f"{BASE_URL_SIDRA}"
        f"/{TABELA}"
        f"/periodos"
    )

    dados = get_json(url)

    if not isinstance(dados, list):
        raise ValueError(
            "Resposta de períodos do SIDRA não é uma lista."
        )

    periodos = []

    for item in dados:

        if isinstance(item, dict):

            periodo = item.get("id")

        else:

            periodo = item

        if periodo is None:
            continue

        periodo = str(periodo).strip()

        if periodo:
            periodos.append(periodo)

    # Remove duplicidades e ordena.
    periodos = sorted(
        set(periodos),
        key=lambda x: int(x)
    )

    print(
        f"Períodos encontrados no SIDRA: {len(periodos)}"
    )

    if periodos:
        print(
            f"Primeiro período: {periodos[0]}"
        )

        print(
            f"Último período: {periodos[-1]}"
        )

    return periodos


# ============================================================
# ATUALIZAR METADADOS
# ============================================================

def atualizar_metadados():
    print("Consultando metadados da tabela 5938...")

    inicio = time.time()

    url = (
        f"{BASE_URL_SIDRA}"
        f"/{TABELA}/metadados"
    )

    dados_remotos = get_json(url)

    tempo = time.time() - inicio

    # --------------------------------------------------------
    # Arquivo ainda não existe
    # --------------------------------------------------------

    if not ARQUIVO_METADADOS.exists():

        salvar_resposta_json(
            dados_remotos,
            ARQUIVO_METADADOS
        )

        print(
            "[NOVO] metadados.json"
        )

        return True

    # --------------------------------------------------------
    # Comparar hash
    # --------------------------------------------------------

    dados_locais = carregar_json(
        ARQUIVO_METADADOS
    )

    hash_local = calcular_hash_json(
        dados_locais
    )

    hash_remoto = calcular_hash_json(
        dados_remotos
    )

    if hash_local == hash_remoto:

        print(
            "[SEM ALTERAÇÃO] metadados.json"
            f" | {tempo:.2f}s"
        )

        return False

    # --------------------------------------------------------
    # Alterado
    # --------------------------------------------------------

    salvar_resposta_json(
        dados_remotos,
        ARQUIVO_METADADOS
    )

    print(
        "[ALTERADO] metadados.json"
        f" | {tempo:.2f}s"
    )

    return True


# ============================================================
# ATUALIZAR ARQUIVO DE PERÍODOS
# ============================================================

def atualizar_arquivo_periodos(periodos):

    if not ARQUIVO_PERIODOS.exists():

        salvar_json(
            periodos,
            ARQUIVO_PERIODOS
        )

        print(
            "[NOVO] periodos.json"
        )

        return True

    periodos_locais = carregar_json(
        ARQUIVO_PERIODOS
    )

    if periodos_locais == periodos:

        print(
            "[SEM ALTERAÇÃO] periodos.json"
        )

        return False

    salvar_json(
        periodos,
        ARQUIVO_PERIODOS
    )

    print(
        "[ALTERADO] periodos.json"
    )

    return True


# ============================================================
# URL DOS DADOS
# ============================================================

def montar_url_periodo(periodo):

    return (
        f"{BASE_URL_SIDRA}"
        f"/{TABELA}"
        f"/periodos/{periodo}"
        f"/variaveis/{VARIAVEIS}"
        f"?localidades=N6[all]"
    )


# ============================================================
# ATUALIZAR UM PERÍODO
# ============================================================

def atualizar_periodo(
    periodo,
    forcar=False
):

    caminho = (
        DIR_TABELA
        / f"dados_{periodo}.json"
    )

    print(
        f"Consultando dados do período {periodo}..."
    )

    inicio = time.time()

    url = montar_url_periodo(
        periodo
    )

    dados_remotos = get_json(url)

    tempo = time.time() - inicio

    # --------------------------------------------------------
    # Arquivo não existe
    # --------------------------------------------------------

    if not caminho.exists():

        salvar_resposta_json(
            dados_remotos,
            caminho
        )

        print(
            f"[NOVO] dados_{periodo}.json"
            f" | {tempo:.2f}s"
        )

        return {
            "status": "novo",
            "periodo": periodo,
            "tempo": tempo
        }

    # --------------------------------------------------------
    # Comparação por hash
    # --------------------------------------------------------

    hash_local = calcular_hash_arquivo_json(
        caminho
    )

    hash_remoto = calcular_hash_json(
        dados_remotos
    )

    if hash_local == hash_remoto:

        print(
            f"[SEM ALTERAÇÃO] dados_{periodo}.json"
            f" | {tempo:.2f}s"
        )

        return {
            "status": "sem_alteracao",
            "periodo": periodo,
            "tempo": tempo
        }

    # --------------------------------------------------------
    # Alterado
    # --------------------------------------------------------

    salvar_resposta_json(
        dados_remotos,
        caminho
    )

    print(
        f"[ALTERADO] dados_{periodo}.json"
        f" | {tempo:.2f}s"
    )

    return {
        "status": "alterado",
        "periodo": periodo,
        "tempo": tempo
    }


# ============================================================
# ATUALIZAR PERÍODOS
# ============================================================

def atualizar_periodos(periodos):

    inicio = time.time()

    resultados = {
        "novos": [],
        "alterados": [],
        "sem_alteracao": []
    }

    if not periodos:

        print(
            "Nenhum período disponível."
        )

        return resultados

    # --------------------------------------------------------
    # Descobrir períodos existentes localmente
    # --------------------------------------------------------

    periodos_locais = set()

    for caminho in DIR_TABELA.glob(
        "dados_*.json"
    ):

        nome = caminho.stem

        periodo = nome.replace(
            "dados_",
            ""
        )

        if periodo.isdigit():
            periodos_locais.add(periodo)

    # --------------------------------------------------------
    # NOVOS períodos
    # --------------------------------------------------------

    periodos_novos = [
        periodo
        for periodo in periodos
        if periodo not in periodos_locais
    ]

    print()
    print(
        f"Períodos novos: {len(periodos_novos)}"
    )

    for periodo in periodos_novos:

        resultado = atualizar_periodo(
            periodo
        )

        if resultado["status"] == "novo":

            resultados["novos"].append(
                periodo
            )

    # --------------------------------------------------------
    # VERIFICAR ÚLTIMO PERÍODO
    # --------------------------------------------------------

    ultimo_periodo = periodos[-1]

    if (
        VERIFICAR_ULTIMO_PERIODO
        and ultimo_periodo in periodos_locais
        and ultimo_periodo not in periodos_novos
    ):

        print()
        print(
            f"Verificando possível alteração "
            f"no último período: {ultimo_periodo}"
        )

        resultado = atualizar_periodo(
            ultimo_periodo
        )

        if resultado["status"] == "alterado":

            resultados["alterados"].append(
                ultimo_periodo
            )

        elif resultado["status"] == "sem_alteracao":

            resultados["sem_alteracao"].append(
                ultimo_periodo
            )

    # --------------------------------------------------------
    # Tempo
    # --------------------------------------------------------

    tempo = time.time() - inicio

    print()
    print(
        f"Atualização dos períodos concluída "
        f"em {tempo:.2f}s"
    )

    return resultados


# ============================================================
# ATUALIZAÇÃO BRONZE
# ============================================================

def atualizar_bronze():

    inicio_total = time.time()

    print("=" * 70)
    print("ATUALIZAÇÃO INCREMENTAL DA BRONZE")
    print("=" * 70)

    print()
    print(
        f"Tabela SIDRA: {TABELA}"
    )

    print(
        f"Diretório: {DIR_TABELA}"
    )

    DIR_TABELA.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # METADADOS
    # --------------------------------------------------------

    print()
    print("-" * 70)
    print("ETAPA 1 - METADADOS")
    print("-" * 70)

    metadados_alterados = (
        atualizar_metadados()
    )

    # --------------------------------------------------------
    # PERÍODOS
    # --------------------------------------------------------

    print()
    print("-" * 70)
    print("ETAPA 2 - PERÍODOS")
    print("-" * 70)

    periodos = obter_periodos()

    if not periodos:
        raise ValueError(
            "Nenhum período retornado pelo SIDRA."
        )

    periodos_alterados = (
        atualizar_arquivo_periodos(
            periodos
        )
    )

    # --------------------------------------------------------
    # DADOS
    # --------------------------------------------------------

    print()
    print("-" * 70)
    print("ETAPA 3 - DADOS")
    print("-" * 70)

    resultados = atualizar_periodos(
        periodos
    )

    # --------------------------------------------------------
    # RESUMO
    # --------------------------------------------------------

    tempo_total = (
        time.time()
        - inicio_total
    )

    houve_alteracao = (
        metadados_alterados
        or periodos_alterados
        or bool(resultados["novos"])
        or bool(resultados["alterados"])
    )

    resumo = {
        "tabela": TABELA,
        "periodos_consultados": len(periodos),
        "primeiro_periodo": periodos[0],
        "ultimo_periodo": periodos[-1],
        "novos": len(
            resultados["novos"]
        ),
        "alterados": len(
            resultados["alterados"]
        ),
        "sem_alteracao": len(
            resultados["sem_alteracao"]
        ),
        "metadados_alterados": (
            metadados_alterados
        ),
        "periodos_alterados": (
            periodos_alterados
        ),
        "tempo_segundos": round(
            tempo_total,
            2
        ),
        "houve_alteracao": houve_alteracao
    }

    print()
    print("=" * 70)
    print("RESUMO DA ATUALIZAÇÃO")
    print("=" * 70)

    print(
        f"Tabela: {TABELA}"
    )

    print(
        f"Períodos disponíveis: "
        f"{len(periodos)}"
    )

    print(
        f"Período inicial: "
        f"{periodos[0]}"
    )

    print(
        f"Último período: "
        f"{periodos[-1]}"
    )

    print(
        f"Novos: "
        f"{len(resultados['novos'])}"
    )

    print(
        f"Alterados: "
        f"{len(resultados['alterados'])}"
    )

    print(
        f"Sem alteração: "
        f"{len(resultados['sem_alteracao'])}"
    )

    print(
        f"Metadados alterados: "
        f"{metadados_alterados}"
    )

    print(
        f"Períodos alterados: "
        f"{periodos_alterados}"
    )

    print(
        f"Tempo total: "
        f"{tempo_total:.2f} segundos"
    )

    print(
        f"Houve alteração: "
        f"{houve_alteracao}"
    )

    print("=" * 70)

    return resumo


# ============================================================
# MAIN
# ============================================================

def main():

    try:

        atualizar_bronze()

        return 0

    except KeyboardInterrupt:

        print()
        print(
            "ATUALIZAÇÃO BRONZE "
            "INTERROMPIDA PELO USUÁRIO."
        )

        return 130

    except Exception as erro:

        print()
        print(
            "=" * 70
        )

        print(
            "ERRO NA ATUALIZAÇÃO DA BRONZE"
        )

        print(
            "=" * 70
        )

        print(
            f"{type(erro).__name__}: {erro}"
        )

        raise


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":
    raise SystemExit(
        main()
    )