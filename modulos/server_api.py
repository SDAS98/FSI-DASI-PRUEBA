import httpx
from .config import settings

async def post_name():
    """Registra tu alias en el Butler."""
    async with httpx.AsyncClient() as client:
        try:
            url = f"{settings.SERVER_URL}alias/{settings.MI_ALIAS}"
            await client.post(url)
        except Exception as e:
            print(f"Error al registrar nombre: {e}")

async def get_gente():
    """Obtiene la lista de agentes conectados {alias: ip}."""
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(f"{settings.SERVER_URL}gente")
            return r.json() if r.status_code == 200 else {}
        except:
            return {}

async def get_game_state():
    """Obtiene recursos y objetivos del juego."""
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(f"{settings.SERVER_URL}info")
            return r.json()
        except:
            return {}