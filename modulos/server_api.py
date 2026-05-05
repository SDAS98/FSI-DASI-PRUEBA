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
            return r.json() if r.status_code == 200 else []
        except:
            return []

async def get_game_state():
    """Consulta al Butler qué recursos tenemos y cuál es nuestro objetivo actual"""
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(f"{settings.SERVER_URL}info")
            return r.json() # Devuelve un dict: {"recursos": {...}, "objetivo": {...}}
        except:
            return {"recursos": {}, "objetivo": {}}

async def ejecutar_intercambio(id_rival, recurso_dar, cant_dar, recurso_recibir, cant_recibir):
    """
    NOTIFICACIÓN AL BUTLER: Esta función hace que el intercambio sea oficial.
    """
    async with httpx.AsyncClient() as client:
        try:
            payload = {
                "emisor": settings.MI_ALIAS,
                "receptor": id_rival,
                "dar": {recurso_dar: cant_dar},
                "recibir": {recurso_recibir: cant_recibir}
            }
            # /trade /confirmar en caso de que intercambiarno sea el endpoint exacto que se use
            url = f"{settings.SERVER_URL}intercambiar"
            r = await client.post(url, json=payload, timeout=10)
            return r.status_code == 200
        except Exception as e:
            print(f"Error registrando intercambio en el servidor: {e}")
            return False