'''
from fastapi import FastAPI, Request
from pydantic import BaseModel
from loguru import logger
import httpx
import asyncio
import json
import time

# IMPORTACIONES DESDE TUS MÓDULOS (Sin puntos para ejecución directa)
from modulos.config import settings
from modulos.server_api import post_name, get_game_state
from modulos.agent_logic import procesar_mensaje
from modulos.agent_loop import monitor_loop

app = FastAPI(title=f"Agente {settings.MI_ALIAS}")

class Mensaje(BaseModel):
    msg: str

# --- RUTAS ---

@app.get("/")
async def root():
    return {"agente": settings.MI_ALIAS, "status": "online"}

@app.post("/buzon")
async def buzon(request: Mensaje):
    client_ip = request.client.host
    
    try:
        # 1. Intentamos leer el cuerpo de la petición como JSON
        data = await request.json()
        
        # 2. Buscamos el mensaje en diferentes campos posibles (msg, mensaje, content...)
        # Esto hace que tu agente sea más inteligente y no falle por una palabra
        mensaje_texto = data.get("msg") or data.get("mensaje") or data.get("text") or str(data)
        
        logger.info(f"Mensaje recibido de {client_ip}: {mensaje_texto}")

        # 3. Procesamos con tu lógica habitual
        decision = await procesar_mensaje(client_ip, mensaje_texto)
        return {"status": "procesado", "decision": decision}

    except Exception as e:
        # Si ni siquiera es un JSON válido, capturamos el error
        logger.error(f"Error al decodificar petición de {client_ip}: {e}")
        return {"status": "error", "detalle": "Formato no soportado"}

# --- CICLO DE VIDA ---

@app.on_event("startup")
async def startup():
    """
    Se ejecuta al arrancar el agente.
    """
    logger.info(f"Arrancando agente {settings.MI_ALIAS}...")
    
    # 1. Registro en el Butler (usando la función de server_api)
    await post_name()
    
    # 2. Lanzar el monitor autónomo en segundo plano (de agent_loop)
    # Este se encarga de buscar gente y enviar pings cada X segundos
    asyncio.create_task(monitor_loop())
    
    logger.success("Agente listo y monitor activado.")

# --- EJECUCIÓN ---

if __name__ == "__main__":
    import uvicorn
    # Lanzamos el servidor en el puerto 7720
    uvicorn.run(app, host="0.0.0.0", port=settings.MI_PUERTO)
    '''
import uvicorn
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, BackgroundTasks
from pydantic import BaseModel
from loguru import logger

# Importaciones de tus módulos locales
from modulos.config import settings
from modulos.server_api import post_name
from modulos.agent_loop import monitor_loop
from modulos.agent_logic import procesar_mensaje

# 1. Definición del ciclo de vida (Lifespan) - Reemplaza a on_event("startup")
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- CÓDIGO AL ARRANCAR ---
    logger.info(f"Arrancando agente {settings.MI_ALIAS}...")
    
    # Registro inicial en el Butler
    try:
        await post_name()
        logger.success(f"Registro exitoso en el servidor como {settings.MI_ALIAS}")
    except Exception as e:
        logger.error(f"Error de registro: {e}")

    # Lanzar el monitor proactivo en segundo plano
    monitor_task = asyncio.create_task(monitor_loop())
    logger.info("Monitor de agentes activos iniciado.")
    
    yield  # Aquí es donde el servidor se queda "corriendo"
    
    # --- CÓDIGO AL CERRAR ---
    logger.info("Cerrando agente y cancelando tareas...")
    monitor_task.cancel()

# 2. Inicialización de FastAPI con Lifespan
app = FastAPI(
    title=f"Agente FH",
    lifespan=lifespan
)

# 3. Modelo de datos para el buzón
class Mensaje(BaseModel):
    msg: str

# 4. Endpoint del Buzón (Puerto 7720)
@app.post("/buzon")
async def buzon(mensaje: Mensaje, request: Request, background_tasks: BackgroundTasks):
    ip_origen = request.client.host
    logger.info(f"Mensaje recibido de {ip_origen}: {mensaje.msg}")

    # Procesamos la IA en segundo plano para responder rápido al POST
    background_tasks.add_task(procesar_mensaje, ip_origen, mensaje.msg)

    return {
        "status": "Mensaje entregado",
        "remitente": settings.MI_ALIAS
    }

# 5. Ejecución
if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=settings.MI_PUERTO, 
        reload=False
    )