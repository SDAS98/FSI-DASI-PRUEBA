import httpx
import json
from loguru import logger
from .config import settings
from .server_api import get_game_state, ejecutar_intercambio
from .agent_memory import registrar, perfil_rival

# Definición de Tool genérica para negociación
TOOLS = [{
    "type": "function",
    "function": {
        "name": "evaluar_oferta",
        "description": "Decide si un intercambio de recursos es beneficioso.",
        "parameters": {
            "type": "object",
            "properties": {
                "accion": {"enum": ["aceptar", "contraoferta", "rechazar"]},
                "recurso_dar": {"type": "string"},
                "cantidad_dar": {"type": "integer"},
                "recurso_pedir": {"type": "string"},
                "cantidad_pedir": {"type": "integer"},
                "motivo": {"type": "string"}
            },
            "required": ["accion"]
        }
    }
}]

async def procesar_mensaje(ip, msg):
    """
    Lógica principal: Consulta estado, pregunta a la IA y ejecuta el intercambio.
    """
    game = await get_game_state()
    historia_rival = perfil_rival(ip)
    
    logger.info(f"Procesando mensaje de {ip}. Perfil: {historia_rival}")

    async with httpx.AsyncClient() as client:
        try:
            # 1. Llamada a la IA
            payload = {
                "model": settings.DEFAULT_MODEL,
                "messages": [
                    {
                        "role": "system", 
                        "content": (
                            f"Eres el agente {settings.MI_ALIAS} en un sistema de intercambio. "
                            f"Tus recursos actuales: {game.get('recursos')}. "
                            f"Tu objetivo final: {game.get('objetivo')}. "
                            f"Historial del rival (IP {ip}): {historia_rival}. "
                            "Responde siempre usando la función evaluar_oferta."
                        )
                    },
                    {"role": "user", "content": f"Mensaje recibido: '{msg}'"}
                ],
                "tools": TOOLS,
                "stream": False
            }

            r = await client.post(settings.OLLAMA_URL, json=payload, timeout=30)
            response_data = r.json()
            tool_calls = response_data.get("message", {}).get("tool_calls", [])

            if tool_calls:
                decision = json.loads(tool_calls[0]["function"]["arguments"])
            else:
                decision = {"accion": "rechazar", "motivo": "No se entendió la propuesta"}

            # 2. Si la IA acepta, intentamos el intercambio real en el servidor
            if decision["accion"] == "aceptar":
                exito = await ejecutar_intercambio(
                    ip, 
                    decision.get("recurso_dar"), decision.get("cantidad_dar", 0),
                    decision.get("recurso_pedir"), decision.get("cantidad_pedir", 0)
                )
                if exito:
                    logger.success(f"¡Intercambio realizado con {ip}!")
                else:
                    logger.error(f"El servidor rechazó el intercambio con {ip}")

            # 3. Guardar en memoria y avisar al rival por su buzón
            registrar(ip, decision)
            
            # Intentar avisar al rival (P2P)
            try:
                # Se envía la decisión al puerto del agente rival
                url_rival = f"http://{ip}:{settings.MI_PUERTO}/buzon"
                await client.post(url_rival, json={"from": settings.MI_ALIAS, "decision": decision}, timeout=5)
            except:
                logger.warning(f"No se pudo avisar a la IP {ip} por su buzón, pero se intentó el registro.")

            return decision

        except Exception as e:
            logger.error(f"Error en la lógica del agente: {e}")
            return {"accion": "rechazar", "error": str(e)}