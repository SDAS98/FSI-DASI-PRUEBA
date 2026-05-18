import asyncio
import time
import httpx
from loguru import logger
from .config import settings
from .server_api import get_gente

ip_time = {}

async def monitor_loop():
    """Bucle autónomo que busca agentes activos y gestiona la proactividad."""
    while True:
        try:
            logger.info("Monitor: Verificando agentes activos en la red...")
            gente = await get_gente()
            now = time.time()

            for persona in gente:
                alias = persona.get("alias")
                ip = persona.get("ip")

                if alias == settings.MI_ALIAS:
                    continue

                if ip not in ip_time or (now - ip_time[ip] > settings.PING_TIME):
                    logger.debug(f"Monitor: Iniciando contacto proactivo con {alias} ({ip})")
                    asyncio.create_task(notificar_rival(ip))

        except Exception as e:
            logger.error(f"Error en el bucle del monitor: {e}")

        await asyncio.sleep(settings.SLEEP_TIME)


async def notificar_rival(ip):
    """Envía un mensaje al rival con lógica de reintentos."""
    intentos_max = 3
    espera_entre_intentos = 2

    async with httpx.AsyncClient() as client:
        for intento in range(intentos_max):
            try:
                url = f"http://{ip}:{settings.MI_PUERTO}/buzon"
                payload = {"msg": "Hola, ¿tienes algún intercambio beneficioso?"}
                response = await client.post(url, json=payload, timeout=3.0)

                if response.status_code == 200:
                    ip_time[ip] = time.time()
                    logger.success(f"Éxito al contactar a {ip} (intento {intento + 1})")
                    return

            except Exception as e:
                logger.warning(f"Intento {intento + 1} fallido para {ip}: {e}")
                if intento < intentos_max - 1:
                    await asyncio.sleep(espera_entre_intentos)
                else:
                    logger.error(f"Imposible contactar con {ip} tras {intentos_max} intentos.")