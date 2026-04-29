import httpx
import json
from loguru import logger
from .config import settings
from .server_api import get_game_state
from .agent_memory import registrar, perfil_rival
from .tools import evaluar_oferta

# Definición de Tool según notas: "no responde en JSON, es un tool-call"
TOOLS = [{
    "type": "function",
    "function": {
        "name": "evaluar_oferta",
        "description": "Decide si un intercambio acerca al agente a su objetivo",
        "parameters": {
            "type": "object",
            "properties": {
                "accion": {"enum": ["aceptar", "contraoferta", "rechazar"]},
                "recurso_ofrecer": {"type": "string"},
                "cantidad_ofrecer": {"type": "integer"}
            },
            "required": ["accion"]
        }
    }
}]

async def procesar_mensaje(ip, msg):
    game = await get_game_state()
    logger.info(f"Procesando mensaje de {ip}. Objetivo: {game['objetivo']}")

    async with httpx.AsyncClient() as client:
        r = await client.post(settings.OLLAMA_URL, json={
            "model": settings.DEFAULT_MODEL,
            "messages": [
                {"role": "system", "content": f"Agente Catan. Recursos: {game['recursos']}. Objetivo: {game['objetivo']}"},
                {"role": "user", "content": msg}
            ],
            "tools": TOOLS,
            "stream": False
        })
        
        # Interpretación delegada al modelo vía Tools (sin regex)
        tool_calls = r.json().get("message", {}).get("tool_calls", [])
        if tool_calls:
            decision = json.loads(tool_calls[0]["function"]["arguments"])
        else:
            decision = {"accion": "rechazar"}

        logger.success(f"Decisión para {ip}: {decision['accion']}")
        
        # Envío al buzón del rival
        try:
            await client.post(f"http://{ip}:7720/buzon", json={"msg": json.dumps(decision)}, timeout=5)
        except Exception as e:
            logger.error(f"Error enviando respuesta a {ip}: {e}")

    return decision