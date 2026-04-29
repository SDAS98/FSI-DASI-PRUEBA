import httpx
from .config import settings

async def get_game_state():
    """Obtiene recursos y objetivos en una sola llamada asíncrona."""
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{settings.SERVER_URL}info")
        info = r.json()
        return {
            "recursos": info.get("Recursos", {}),
            "objetivo": info.get("Objetivo", "")
        }

async def get_gente():
    """Obtiene la lista de agentes (IPs) registrados."""
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{settings.SERVER_URL}gente")
        return {p["alias"]: p["ip"] for p in r.json() if p["alias"] != "bunny"}

async def post_name(alias="bunnydos"):
    """Registra el alias del agente en el Butler."""
    async with httpx.AsyncClient() as client:
        await client.post(f"{settings.SERVER_URL}alias/{alias}")