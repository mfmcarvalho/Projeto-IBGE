from pathlib import Path


# ============================================================
# CONFIGURAÇÃO
# ============================================================

# Diretório onde este script está localizado
PROJECT_ROOT = Path(__file__).resolve().parent


# ============================================================
# ESTRUTURA DO PROJETO
# ============================================================

DIRETORIOS = [
    # Dados
    "data/bronze/sidra/catalogo",
    "data/bronze/sidra/metadados",
    "data/silver",
    "data/gold",

    # Código-fonte
    "src/ingestion",
    "src/transformation",

    # Documentação
    "docs",

    # Testes
    "tests",
]


# ============================================================
# ARQUIVOS INICIAIS
# ============================================================

ARQUIVOS = [
    "src/main.py",
    "src/ingestion/baixar_metadados_sidra.py",
    "docs/modelo_relacional_sidra.md",
]


# ============================================================
# CRIAÇÃO DOS DIRETÓRIOS
# ============================================================

def criar_diretorios():
    print("=" * 60)
    print("CRIANDO ESTRUTURA DO PROJETO")
    print("=" * 60)
    print()

    for diretorio in DIRETORIOS:

        caminho = PROJECT_ROOT / diretorio

        caminho.mkdir(
            parents=True,
            exist_ok=True
        )

        print(f"[DIR]  {caminho}")


# ============================================================
# CRIAÇÃO DOS ARQUIVOS
# ============================================================

def criar_arquivos():
    print()
    print("=" * 60)
    print("CRIANDO ARQUIVOS")
    print("=" * 60)
    print()

    for arquivo in ARQUIVOS:

        caminho = PROJECT_ROOT / arquivo

        # Garante que o diretório pai exista
        caminho.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        # Só cria se ainda não existir
        if not caminho.exists():

            caminho.touch()

            print(f"[FILE] {caminho}")

        else:

            print(f"[SKIP] {caminho} já existe")


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print(f"Projeto: {PROJECT_ROOT}")
    print()

    criar_diretorios()
    criar_arquivos()

    print()
    print("=" * 60)
    print("ESTRUTURA CRIADA COM SUCESSO")
    print("=" * 60)
    print()

    print("Projeto:")
    print()

    for caminho in sorted(PROJECT_ROOT.rglob("*")):

        # Ignora o ambiente virtual
        if ".venv" in caminho.parts:
            continue

        relativo = caminho.relative_to(PROJECT_ROOT)

        if caminho.is_dir():
            print(f"📁 {relativo}/")
        else:
            print(f"📄 {relativo}")


if __name__ == "__main__":
    main()