'''import httpx
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

    return decision '''

import httpx
import json
from loguru import logger
from .config import settings
from .server_api import get_game_state
from .agent_memory import registrar, perfil_rival
# Importamos la lógica local por si la IA quiere validar algo antes
from .tools import evaluar_oferta 

# Definición de Tool optimizada
TOOLS = [{
    "type": "function",
    "function": {
        "name": "evaluar_oferta",
        "description": "Decide si un intercambio de recursos en Catan es beneficioso.",
        "parameters": {
            "type": "object",
            "properties": {
                "accion": {"enum": ["aceptar", "contraoferta", "rechazar"]},
                "recurso_ofrecer": {"type": "string", "description": "Qué recurso daríamos"},
                "cantidad_ofrecer": {"type": "integer", "description": "Cuánta cantidad"},
                "motivo": {"type": "string", "description": "Breve explicación de la decisión"}
            },
            "required": ["accion"]
        }
    }
}]

async def procesar_mensaje(ip, msg):
    """
    Lógica principal: Consulta estado, pregunta a Ollama, guarda en memoria y responde.
    """
    # 1. Obtener contexto actual
    game = await get_game_state()
    historia_rival = perfil_rival(ip) # Consultamos si es de fiar
    
    logger.info(f"Procesando mensaje de {ip}. Perfil rival: {historia_rival}")

    async with httpx.AsyncClient() as client:
        try:
            # 2. Llamada a Ollama con soporte de Tools
            payload = {
                "model": settings.DEFAULT_MODEL,
                "messages": [
                    {
                        "role": "system", 
                        "content": (
                            f"Eres un agente de Catan llamado {settings.MI_ALIAS}. "
                            f"Tus recursos: {game.get('recursos')}. "
                            f"Tu objetivo: {game.get('objetivo')}. "
                            f"El rival con IP {ip} tiene un perfil: {historia_rival}. "
                            "Sé estratégico. Si te ofrecen algo que no necesitas, rechaza o pide lo que te falta."
                        )
                    },
                    {"role": "user", "content": f"He recibido este mensaje: '{msg}'. ¿Qué debo hacer?"}
                ],
                "tools": TOOLS,
                "stream": False
            }

            r = await client.post(settings.OLLAMA_URL, json=payload, timeout=30)
            r.raise_for_status()
            
            # 3. Extraer la decisión de los Tool Calls
            response_data = r.json()
            message = response_data.get("message", {})
            tool_calls = message.get("tool_calls", [])

            if tool_calls:
                # Pillamos los argumentos de la primera función llamada
                decision = json.loads(tool_calls[0]["function"]["arguments"])
            else:
                # Si la IA responde texto plano, por defecto rechazamos por seguridad
                decision = {"accion": "rechazar", "motivo": "No se detectó una oferta clara"}

            # 4. MEMORIA: Guardamos lo que hemos decidido para este rival
            registrar(ip, decision)
            
            logger.success(f"Decisión para {ip}: {decision['accion']} - {decision.get('motivo', '')}")
            
            # 5. Envío de respuesta al buzón del rival (Puerto 7720)
            # Enviamos un JSON limpio, no un string de un JSON
            try:
                respuesta_rival = {
                    "from": settings.MI_ALIAS,
                    "decision": decision
                }
                await client.post(f"http://{ip}:7720/buzon", json=respuesta_rival, timeout=5)
            except Exception as e:
                logger.error(f"No se pudo enviar respuesta a {ip}: {e}")

            return decision

        except Exception as e:
            logger.error(f"Error crítico en agent_logic: {e}")
            return {"accion": "rechazar", "error": str(e)}