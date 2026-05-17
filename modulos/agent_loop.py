import asyncio
import time
import httpx
from loguru import logger
from .config import settings
from .server_api import get_gente, get_game_state

# Control de inundación para evitar saturaciones (Flood Control)
ip_time = {}

async def monitor_loop():
    """
    Bucle principal que busca agentes y envía propuestas
    """
    while True:
        try:
            logger.info("Monitor: Verificando estado y agentes activos...")
            
            # 1. Obtener datos del servidor (Butler)
            gente = await get_gente()
            estado = await get_game_state()
            
            # --- EXTRACCIÓN SEGURA DE DATOS ---
            # Convertimos a diccionario si es un objeto Pydantic para evitar errores
            if hasattr(estado, "dict"):
                data = estado.dict()
            else:
                data = estado if isinstance(estado, dict) else {}

            mis_recursos = data.get("recursos", {})
            mi_objetivo = data.get("objetivo", "completar mi estrategia")

            # --- FORMATEO DE MENSAJE HUMANO ---
            # Solo listamos recursos que tengamos (cantidad > 0)
            if isinstance(mis_recursos, dict) and mis_recursos:
                # Solo incluimos lo que tenemos en cantidad mayor a 0
                activos = [f"{v} {k}" for k, v in mis_recursos.items() if v > 0]
                mis_recursos = ", ".join(activos) if activos else "pocos recursos"
            else:
                mis_recursos = "buscando recursos"

            now = time.time()
            
            #if isinstance(mis_recursos, dict) and mis_recursos:
            #    activos = [f"{v} {k}" for k, v in mis_recursos.items() if v > 0]
            #    recursos_texto = ", ".join(activos) if activos else "actualmente buscando recursos"
            #else:
            #    recursos_texto = "pocos recursos"

            #if mis_recursos:
            #    recursos_str = ", ".join([f"{v} {k}" for k, v in mis_recursos.items() if v > 0])
            #else:
            #    recursos_str = "pocos recursos"      
            
            # 2. Notificar a los compañeros
            for persona in gente:
                alias = persona.get("alias")
                ip = persona.get("ip")

                if alias == settings.MI_ALIAS or not ip:
                    continue
                
                # Solo enviamos si no hemos hablado con ellos recientemente
                if ip not in ip_time or (now - ip_time[ip] > settings.PING_TIME):
                    # Pasamos recursos_texto y el objetivo como string
                    asyncio.create_task(
                        notificar_rival(ip, alias, mis_recursos, str(mi_objetivo))
                    )
            
        except Exception as e:
            logger.error(f"Error en el bucle del monitor: {e}")
        
        # Pausa antes de la siguiente verificación (según settings.SLEEP_TIME)
        await asyncio.sleep(settings.SLEEP_TIME)

async def notificar_rival(ip, alias_rival, recursos_str, objetivo_str):
    """
    Envía el mensaje de FH a los demás agentes.
    """
    async with httpx.AsyncClient() as client:
        try:
            url = f"http://{ip}:{settings.MI_PUERTO}/buzon"
            
            # Construcción del mensaje para los rivales
            cuerpo = {
                "msg": (
                    f"¡Hola! Soy {settings.MI_ALIAS}. "
                    f"Tengo disponible: {recursos_str}. "
                    f"Busco conseguir: {objetivo_str}. "
                    "¿Te interesa un intercambio de recursos?"
                )
            }
            
            await client.post(url, json=cuerpo, timeout=2.0)
            ip_time[ip] = time.time()
            logger.success(f"Propuesta enviada a {alias_rival} ({ip})")
                
        except Exception:
            # Fallo silencioso si el rival no está disponible
            pass
                
'''     # Timeout corto para no bloquear el agente si el compañero está offline
            response = await client.post(url, json=cuerpo, timeout=2.0)
            
            if response.status_code == 200:
                ip_time[ip] = time.time()
                logger.success(f"Propuesta enviada con éxito a {alias_rival} ({ip})")
        '''