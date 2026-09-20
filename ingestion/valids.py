import json
from pathlib import Path

arquivo = Path(
    r"C:\Users\mfmca\projto_ibge\data\bronze\ibge\sidra\5938\metadados.json"
)

with open(arquivo, encoding="utf-8") as f:
    dados = json.load(f)

for v in dados["variaveis"]:
    nome = v["nome"].lower()

    if (
        "valor adicionado bruto" in nome
        and "participação" not in nome
    ) or (
        "impostos, líquidos" in nome
        and "participação" not in nome
    ) or (
        "produto interno bruto" in nome
        and "participação" not in nome
    ):
        print(f'{v["id"]} | {v["nome"]} | {v["unidade"]}')