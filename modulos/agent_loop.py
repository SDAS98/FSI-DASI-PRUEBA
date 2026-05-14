'''import asyncio
import time
import httpx
from loguru import logger
from .config import settings
from .server_api import get_gente, get_game_state

# Diccionario para el control de inundación (Flood Control)
ip_time = {}

async def monitor_loop():
    """
    Bucle principal proactivo: busca agentes y envía propuestas con datos reales.
    """
    while True:
        try:
            logger.info("Monitor: Verificando estado y agentes activos...")
            
            # 1. Obtener datos del servidor (Butler)
            gente = await get_gente()
            estado = await get_game_state()
            
            # --- EXTRACCIÓN DINÁMICA (CORREGIDO) ---
            # Si 'estado' es un objeto de Pydantic, usamos .dict(), si no, lo tratamos como diccionario
            if hasattr(estado, "dict"):
                data = estado.dict()
            else:
                data = estado if isinstance(estado, dict) else {}

            mis_recursos = data.get("recursos", {})
            mi_objetivo = data.get("objetivo", "completar mi estrategia")

            # --- FORMATEO DE MENSAJE HUMANO ---
            # Solo listamos recursos que tengamos (cantidad > 0)
            #if isinstance(mis_recursos, dict) and mis_recursos:
            #    activos = [f"{v} {k}" for k, v in mis_recursos.items() if v > 0]
            #    recursos_texto = ", ".join(activos) if activos else "actualmente buscando materiales"
            #else:
            #    recursos_texto = "pocos recursos"

            if mis_recursos:
                recursos_str = ", ".join([f"{v} {k}" for k, v in mis_recursos.items() if v > 0])
            else:
                recursos_str = "pocos recursos"
            
            for persona in gente:
                alias = persona.get("alias")
                ip = persona.get("ip")

                # No nos enviamos mensajes a nosotros mismos
                if alias == settings.MI_ALIAS or not ip:
                    continue
                
                # Control de tiempo para no saturar al mismo compañero
                if ip not in ip_time or (now - ip_time[ip] > settings.PING_TIME):
                    # Lanzamos la tarea de envío
                    asyncio.create_task(
                        notificar_rival(ip, alias, recursos_texto, str(mi_objetivo))
                    )
            
        except Exception as e:
            logger.error(f"Error en el bucle del monitor: {e}")
        
        # Pausa antes de la siguiente verificación (según settings.SLEEP_TIME)
        await asyncio.sleep(settings.SLEEP_TIME)

async def notificar_rival(ip, alias_rival, recursos_str, objetivo_str):
    """
    Envía el mensaje formal de FH al buzón del rival (puerto 7720).
    """
    async with httpx.AsyncClient() as client:
        try:
            url = f"http://{ip}:{settings.MI_PUERTO}/buzon"
            
            # Construcción del mensaje para tus compañeros
            cuerpo = {
                "msg": (
                    f"¡Hola! Soy {settings.MI_ALIAS}. "
                    f"En este momento tengo: {recursos_str}. "
                    f"Mi objetivo principal es: {objetivo_str}. "
                    "¿Te interesa realizar un intercambio simétrico?"
                )
            }
            
            # Timeout corto para no bloquear el agente si el compañero está offline
            response = await client.post(url, json=cuerpo, timeout=2.0)
            
            if response.status_code == 200:
                ip_time[ip] = time.time()
                logger.success(f"Propuesta enviada con éxito a {alias_rival} ({ip})")
                
        except Exception:
            # Fallo silencioso: el rival no está disponible o tiene el firewall activo
            pass 
        '''

import asyncio
import time
import httpx
from loguru import logger
from .config import settings
from .server_api import get_gente, get_game_state

# Control de inundación para no saturar a los compañeros
ip_time = {}

async def monitor_loop():
    """
    Bucle principal que busca agentes y envía propuestas con datos reales.
    """
    while True:
        try:
            logger.info("Monitor: Verificando estado y agentes activos...")
            
            # 1. Obtener datos actualizados del servidor
            gente = await get_gente()
            estado = await get_game_state()
            
            # --- EXTRACCIÓN SEGURA DE DATOS ---
            # Convertimos a diccionario si es un objeto Pydantic para evitar errores
            if hasattr(estado, "dict"):
                data = estado.dict()
            else:
                data = estado if isinstance(estado, dict) else {}

            mis_recursos = data.get("recursos", {})
            mi_objetivo = data.get("objetivo", "completar mi inventario")

            # --- CONSTRUCCIÓN DE LA VARIABLE recursos_texto ---
            # Esto corrige el error 'not defined' asegurando que la variable exista siempre
            if isinstance(mis_recursos, dict) and mis_recursos:
                # Solo incluimos lo que tenemos en cantidad mayor a 0
                activos = [f"{v} {k}" for k, v in mis_recursos.items() if v > 0]
                recursos_texto = ", ".join(activos) if activos else "pocos materiales"
            else:
                recursos_texto = "buscando recursos"

            now = time.time()
            
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
                        notificar_rival(ip, alias, recursos_texto, str(mi_objetivo))
                    )
            
        except Exception as e:
            logger.error(f"Error en el bucle del monitor: {e}")
        
        await asyncio.sleep(settings.SLEEP_TIME)

async def notificar_rival(ip, alias_rival, recursos_str, objetivo_str):
    """
    Envía el mensaje de FH a los demás agentes.
    """
    async with httpx.AsyncClient() as client:
        try:
            url = f"http://{ip}:{settings.MI_PUERTO}/buzon"
            
            cuerpo = {
                "msg": (
                    f"¡Hola! Soy {settings.MI_ALIAS}. "
                    f"Tengo disponible: {recursos_str}. "
                    f"Busco conseguir: {objetivo_str}. ¿Hacemos trato?"
                )
            }
            
            await client.post(url, json=cuerpo, timeout=2.0)
            ip_time[ip] = time.time()
            logger.success(f"Propuesta enviada a {alias_rival} ({ip})")
                
        except Exception:
            # Fallo silencioso si el rival no está disponible
            pass