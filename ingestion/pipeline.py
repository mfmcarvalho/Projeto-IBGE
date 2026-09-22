from pathlib import Path
import logging
import subprocess
import sys
import time


# ============================================================
# CONFIGURAÇÃO
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INGESTION_DIR = PROJECT_ROOT / "ingestion"

SCRIPT_BRONZE = INGESTION_DIR / "atualizar_bronze_ibge.py"
SCRIPT_SILVER = INGESTION_DIR / "criar_silver_ibge.py"
SCRIPT_GOLD = INGESTION_DIR / "criar_gold_ibge.py"

LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

ARQUIVO_LOG = LOG_DIR / "pipeline.log"


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(
            ARQUIVO_LOG,
            encoding="utf-8"
        ),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


# ============================================================
# EXECUTAR SCRIPT
# ============================================================

def executar_script(nome, caminho_script):
    logger.info("=" * 70)
    logger.info("INICIANDO: %s", nome)
    logger.info("=" * 70)

    inicio = time.time()

    if not caminho_script.exists():
        raise FileNotFoundError(
            f"Script não encontrado: {caminho_script}"
        )

    processo = subprocess.Popen(
        [sys.executable, str(caminho_script)],
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1
    )

    try:
        for linha in processo.stdout:
            linha = linha.rstrip()

            if linha:
                logger.info("[%s] %s", nome, linha)

        processo.wait()

    except KeyboardInterrupt:
        logger.warning(
            "%s interrompido pelo usuário.",
            nome
        )

        processo.terminate()

        try:
            processo.wait(timeout=10)
        except subprocess.TimeoutExpired:
            processo.kill()

        raise

    tempo = time.time() - inicio

    if processo.returncode != 0:
        logger.error(
            "%s FALHOU | código=%s | tempo=%.2f segundos",
            nome,
            processo.returncode,
            tempo
        )

        raise RuntimeError(
            f"{nome} falhou com código {processo.returncode}"
        )

    logger.info(
        "%s CONCLUÍDO | tempo=%.2f segundos",
        nome,
        tempo
    )

    return processo.returncode


# ============================================================
# PIPELINE
# ============================================================

# ============================================================
# PIPELINE
# ============================================================

def executar_pipeline():
    inicio_pipeline = time.time()

    logger.info("")
    logger.info("=" * 70)
    logger.info("PIPELINE IBGE - INÍCIO")
    logger.info("=" * 70)

    try:

        # ----------------------------------------------------
        # BRONZE
        # ----------------------------------------------------

        executar_script(
            "BRONZE",
            SCRIPT_BRONZE
        )

        # ----------------------------------------------------
        # SILVER
        # ----------------------------------------------------

        executar_script(
            "SILVER",
            SCRIPT_SILVER
        )

        # ----------------------------------------------------
        # GOLD
        # ----------------------------------------------------

        executar_script(
            "GOLD",
            SCRIPT_GOLD
        )

        # ----------------------------------------------------
        # SUCESSO
        # ----------------------------------------------------

        tempo_total = time.time() - inicio_pipeline

        logger.info("")
        logger.info("=" * 70)
        logger.info("PIPELINE IBGE - CONCLUÍDO COM SUCESSO")
        logger.info("=" * 70)
        logger.info("Etapas executadas:")
        logger.info("  BRONZE -> OK")
        logger.info("  SILVER -> OK")
        logger.info("  GOLD   -> OK")
        logger.info(
            "Tempo total: %.2f segundos",
            tempo_total
        )
        logger.info("=" * 70)

        return 0

    except KeyboardInterrupt:

        tempo_total = time.time() - inicio_pipeline

        logger.warning("")
        logger.warning("=" * 70)
        logger.warning("PIPELINE IBGE - INTERROMPIDO PELO USUÁRIO")
        logger.warning(
            "Tempo até a interrupção: %.2f segundos",
            tempo_total
        )
        logger.warning("=" * 70)

        return 130

    except Exception:

        tempo_total = time.time() - inicio_pipeline

        logger.exception("Erro durante a execução do pipeline.")

        logger.error("=" * 70)
        logger.error("PIPELINE IBGE - FALHOU")
        logger.error(
            "Tempo até a falha: %.2f segundos",
            tempo_total
        )
        logger.error("=" * 70)

        return 1


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    codigo_saida = executar_pipeline()
    sys.exit(codigo_saida)