import asyncio
import time
import httpx
from loguru import logger
from .config import settings
from .server_api import get_gente

ip_time = {}

async def monitor_loop():
    """Arquitectura asíncrona: Agente activo que no solo responde."""
    async with asyncio.TaskGroup() as tg: [cite: 1]
        while True:
            logger.info("Monitor: Verificando agentes inactivos...")
            gente = await get_gente()
            now = time.time()
            
            for ip in gente.values():
                # Si el agente es nuevo o no responde hace tiempo, reactivar
                if ip not in ip_time or now - ip_time[ip] > settings.PING_TIME:
                    logger.debug(f"Iniciando/Retomando contacto con {ip}")
                    tg.create_task(notificar_rival(ip))
            
            await asyncio.sleep(settings.SLEEP_TIME)

async def notificar_rival(ip):
    async with httpx.AsyncClient() as client:
        try:
            await client.post(f"http://{ip}:7720/buzon", json={"msg": "Hola, ¿negociamos?"})
            ip_time[ip] = time.time()
        except:
            pass
