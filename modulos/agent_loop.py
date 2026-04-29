import asyncio
import time
import httpx
from loguru import logger
from .config import settings
from .server_api import get_gente

# Diccionario para controlar cuándo fue la última vez que hablamos con cada IP
ip_time = {}

async def monitor_loop():
    """Bucle autónomo que busca agentes activos y gestiona la proactividad."""
    while True:
        try:
            logger.info("Monitor: Verificando agentes activos en la red...")
            
            # El Butler devuelve una LISTA: [{"alias": "...", "ip": "..."}, ...]
            gente = await get_gente()
            now = time.time()
            
            # Corregimos el bucle para iterar sobre la lista de diccionarios
            for persona in gente:
                alias = persona.get("alias")
                ip = persona.get("ip")

                # 1. Seguridad: No intentar hablar con nosotros mismos
                if alias == settings.MI_ALIAS:
                    continue
                
                # 2. Control de inundación (Flood control): 
                # Solo enviamos mensaje si es la primera vez o si ha pasado el PING_TIME
                if ip not in ip_time or (now - ip_time[ip] > settings.PING_TIME):
                    logger.debug(f"Monitor: Iniciando contacto proactivo con {alias} ({ip})")
                    # No usamos await aquí para no bloquear el bucle si un agente tarda en responder
                    asyncio.create_task(notificar_rival(ip))
            
        except Exception as e:
            logger.error(f"Error en el bucle del monitor: {e}")
        
        # Esperamos el tiempo configurado antes de la siguiente vuelta
        await asyncio.sleep(settings.SLEEP_TIME)

async def notificar_rival(ip):
    """Envía un mensaje de saludo al buzón del rival para iniciar negociación."""
    async with httpx.AsyncClient() as client:
        try:
            # Importante: Los agentes escuchan en el puerto 7720 (MI_PUERTO)
            url = f"http://{ip}:{settings.MI_PUERTO}/buzon"
            
            payload = {"msg": "Hola, ¿tienes algún intercambio beneficioso?"}
            
            response = await client.post(url, json=payload, timeout=2.0)
            
            if response.status_code == 200:
                # Actualizamos el timestamp solo si el envío fue exitoso
                ip_time[ip] = time.time()
                logger.success(f"Ping enviado con éxito a {ip}")
                
        except Exception:
            # Si el rival está caído, fallará silenciosamente para no llenar la consola de errores
            pass