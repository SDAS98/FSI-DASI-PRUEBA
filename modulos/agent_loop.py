import asyncio
import time
import httpx
from loguru import logger
from .config import settings
from .server_api import get_gente, get_game_state # Importamos el estado del juego

# Diccionario para controlar cuándo fue la última vez que hablamos con cada IP
ip_time = {}

async def monitor_loop():
    """Bucle autónomo que busca agentes activos y gestiona la proactividad personalizada."""
    while True:
        try:
            logger.info("Monitor: Verificando agentes activos en la red...")
            
            # 1. Obtenemos la lista de gente conectada
            gente = await get_gente()
            
            # 2. Obtenemos NUESTROS datos actuales (recursos y objetivos) del Butler
            estado_actual = await get_game_state()
            mis_recursos = estado_actual.get("recursos", {})
            mi_objetivo = estado_actual.get("objetivo", {})
            
            now = time.time()
            
            # Iteramos sobre la lista de agentes detectados
            for persona in gente:
                alias = persona.get("alias")
                ip = persona.get("ip")

                # Seguridad: No intentar hablar con nosotros mismos
                if alias == settings.MI_ALIAS:
                    continue
                
                # Solo enviamos mensaje si es la primera vez o si ha pasado el PING_TIME
                if ip not in ip_time or (now - ip_time[ip] > settings.PING_TIME):
                    logger.debug(f"Monitor: Iniciando contacto proactivo con {alias} ({ip})")
                    
                    # Lanzamos la tarea de notificación pasando la información de intercambio
                    asyncio.create_task(notificar_rival(ip, alias, mis_recursos, mi_objetivo))
            
        except Exception as e:
            logger.error(f"Error en el bucle del monitor: {e}")
        
        # Esperamos el tiempo configurado (SLEEP_TIME) antes de la siguiente vuelta
        await asyncio.sleep(settings.SLEEP_TIME)

async def notificar_rival(ip, alias_rival, recursos, objetivo):
    """Envía un mensaje estructurado con recursos reales al buzón del rival."""
    async with httpx.AsyncClient() as client:
        try:
            # Los agentes escuchan en el puerto configurado (ej: 7720)
            url = f"http://{ip}:{settings.MI_PUERTO}/buzon"
            
            # Construimos el mensaje con el formato natural
            texto_mensaje = (
                f"Hola soy {settings.MI_ALIAS} y tengo {recursos}. "
                f"¿Te interesaría intercambiar algo por mi objetivo: {objetivo}?"
            )
            
            payload = {"msg": texto_mensaje}
            
            # Intentamos el envío al buzón del agente rival
            response = await client.post(url, json=payload, timeout=3.0)
            
            if response.status_code == 200:
                # Actualizamos el timestamp para evitar spam
                ip_time[ip] = time.time()
                logger.success(f"Propuesta enviada con éxito a {alias_rival} ({ip})")
            else:
                logger.warning(f"Rival {alias_rival} respondió con error {response.status_code}")
                
        except Exception as e:
            # Error silencioso para fallos de red comunes (agente offline, puerto cerrado)
            logger.trace(f"Imposible contactar con {ip}: {e}")
            pass