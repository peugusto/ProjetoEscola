"""
Consumo de APIs externas (Requests) com reserva local.

- API de Localidades do IBGE: nomes oficiais dos estados e regiões.
- GeoJSON das UFs brasileiras: contornos para o mapa coroplético.

Todas as funções falham de forma silenciosa e devolvem a reserva local,
para que o dashboard continue funcionando sem internet.
"""
from __future__ import annotations

import requests

from utils.dados import NOMES_UF

URL_IBGE_ESTADOS = "https://servicodados.ibge.gov.br/api/v1/localidades/estados"
URL_GEOJSON_UF = (
    "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/"
    "public/data/brazil-states.geojson"
)
TIMEOUT = 8


def consultar_estados_ibge() -> tuple[dict[str, dict], str]:
    """
    Retorna {sigla: {"nome": ..., "regiao": ..., "id": ...}} e a origem dos
    dados ("API IBGE" ou "reserva local").
    """
    try:
        resposta = requests.get(URL_IBGE_ESTADOS, timeout=TIMEOUT)
        resposta.raise_for_status()
        dados = resposta.json()
        estados = {
            item["sigla"]: {
                "nome": item["nome"],
                "regiao": item["regiao"]["nome"],
                "id": item["id"],
            }
            for item in dados
        }
        if estados:
            return estados, "API IBGE"
    except Exception:  # noqa: BLE001 - qualquer falha de rede cai na reserva
        pass
    return {sigla: {"nome": nome, "regiao": None, "id": None} for sigla, nome in NOMES_UF.items()}, "reserva local"


def baixar_geojson_uf() -> dict | None:
    """GeoJSON com os polígonos das UFs. Propriedade 'sigla' identifica o estado."""
    try:
        resposta = requests.get(URL_GEOJSON_UF, timeout=TIMEOUT)
        resposta.raise_for_status()
        geo = resposta.json()
        if geo.get("features"):
            return geo
    except Exception:  # noqa: BLE001
        pass
    return None
