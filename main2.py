from fastapi import FastAPI, Request
from pydantic import BaseModel
from loguru import logger
import httpx
import asyncio
import json
import time

# Importaciones de tus módulos locales
from .modulos.config import settings
from .modulos.server_api import post_name, get_game_state
from .modulos.agent_logic import procesar_mensaje
from .modulos.agent_loop import monitor_loop

app = FastAPI(title="Agente FDI-DASI Bunnydos")

# Estado del sistema para control de presencia
ip_time = {}

class Mensaje(BaseModel):
    msg: str

# --- UTILIDADES DEL SERVIDOR (BUTLER) ---

async def get_butler_data(endpoint: str):
    """Consulta al Butler usando la configuración centralizada."""
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(f"{settings.SERVER_URL}{endpoint}", timeout=5)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.error(f"Error conectando al Butler en {endpoint}: {e}")
            return {}

# --- LÓGICA DE NEGOCIACIÓN ---

@app.post("/buzon")
async def buzon(request: Request, mensaje: Mensaje):
    client_ip = request.client.host
    logger.info(f"Mensaje recibido de {client_ip}")

    # Delegamos el procesamiento a la lógica del agente que usa Tools
    # Se lanza como tarea para no bloquear la respuesta HTTP
    asyncio.create_task(procesar_mensaje(client_ip, mensaje.msg))
    
    # Actualizamos el rastro de tiempo de este agente
    ip_time[client_ip] = time.time()
    
    return {"status": "recibido y procesando"}

# --- MONITOR Y REACTIVIDAD ---

async def enviar_ping(ip, msg):
    """Envía un mensaje proactivo a otro agente."""
    url = f"http://{ip}:7720/buzon"
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(url, json=msg, timeout=5)
            if r.status_code == 200:
                ip_time[ip] = time.time()
                return r.json()
        except Exception:
            pass
    return None

# --- CICLO DE VIDA ---

@app.on_event("startup")
async def startup():
    logger.info("Iniciando Agente...")
    
    # 1. Registrar nombre en el Butler (147.96.80.224)
    try:
        await post_name("bunnydos")
        logger.success("Registro inicial completado")
    except Exception as e:
        logger.error(f"No se pudo registrar el alias: {e}")

    # 2. Lanzar el monitor autónomo de agentes
    # Este loop revisará la lista de 'gente' cada settings.SLEEP_TIME
    asyncio.create_task(monitor_loop())

if __name__ == "__main__":
    import uvicorn
    # Ejecución del servidor en el puerto 7720
    uvicorn.run(app, host="0.0.0.0", port=7720)