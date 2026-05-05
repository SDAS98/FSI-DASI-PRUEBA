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
    game = await get_game_state() # Obtenemos recursos y objetivos reales del servidor
    historia_rival = perfil_rival(ip) # Analizamos el perfil del rival según el historial de interacciones
    
    logger.info(f"Procesando mensaje de {ip}. Perfil: {historia_rival}")

    async with httpx.AsyncClient() as client:
        try:
            # 1. Llamada a la IA con lógica de paridad y límite de 2
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
                            "REGLAS CRÍTICAS DE NEGOCIACIÓN:"
                            "1. PARIDAD: Debes dar la misma cantidad de recursos que pides (ej: 1x1 o 2x2)."
                            "2. LÍMITE MÁXIMO: No puedes intercambiar más de 2 unidades por bando."
                            "3. Si te piden 1 recurso, responde ofreciendo 1. Si te piden 2, ofrece 2."
                            "Responde siempre usando la función evaluar_oferta."
                        )
                    },
                    {"role": "user", "content": f"Mensaje recibido: '{msg}'"}
                ],
                "tools": TOOLS,
                "stream": False
            }
            
            # Llamada a la IA local (Ollama) Limite de recursos a enviar 2 (1x1 o 2x2)
            r = await client.post(settings.OLLAMA_URL, json=payload, timeout=30)
            response_data = r.json()
            tool_calls = response_data.get("message", {}).get("tool_calls", [])
            
            # Decisión de la IA (si la hay)
            if tool_calls:
                decision = json.loads(tool_calls[0]["function"]["arguments"])
                
                # VALIDACIÓN DE SEGURIDAD: Paridad y Límite de 2
                cant_dar = decision.get("cantidad_dar", 0)
                cant_pedir = decision.get("cantidad_pedir", 0)

                # Regla: No más de 2 unidades en total por bando
                if cant_dar > 2 or cant_pedir > 2:
                    logger.warning(f"IA intentó exceder límite (Dar: {cant_dar}, Pedir: {cant_pedir}). Forzando rechazo.")
                    decision = {"accion": "rechazar", "motivo": "No se permiten más de 2 unidades por intercambio"}
                
                # Regla: Cantidad simétrica (Paridad de recursos)
                elif cant_dar != cant_pedir and decision["accion"] == "aceptar":
                    logger.warning(f"IA intentó intercambio asimétrico ({cant_dar} vs {cant_pedir}). Forzando rechazo.")
                    decision = {"accion": "rechazar", "motivo": "Solo acepto intercambios simétricos (misma cantidad)"}
            else:
                decision = {"accion": "rechazar", "motivo": "No se entendió la propuesta"}
                
            # --- ACCIÓN DE INTERCAMBIO ---
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
                # Solo intentamos responder si la IP no es la nuestra (localhost)
                if ip != "127.0.0.1":
                    url_rival = f"http://{ip}:{settings.MI_PUERTO}/buzon"
                    # Enviamos mensaje formal identificándonos como FH
                    respuesta_formal = {
                        "from": settings.MI_ALIAS,
                        "msg": f"Hola, soy {settings.MI_ALIAS}. Mi decisión es: {decision['accion']}. {decision.get('motivo', '')}",
                        "decision": decision
                    }
                    await client.post(url_rival, json=respuesta_formal, timeout=5)
                else:
                    logger.info("Prueba manual detectada: No se envía respuesta al buzón propio.")
            except Exception as e:
                logger.warning(f"No se pudo avisar a la IP {ip} por su buzón: {e}")

            return decision

        except Exception as e:
            logger.error(f"Error en la lógica del agente: {e}")
            return {"accion": "rechazar", "error": str(e)}