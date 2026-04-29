from fastapi import FastAPI, Request
from pydantic import BaseModel
from .modulos.config import settings
from .modulos.server_api import post_name
from .modulos.agent_logic import procesar_mensaje
from .modulos.agent_loop import monitor_loop
import asyncio

app = FastAPI()

# Configuración actualizada
SERVER_URL = "http://147.96.80.224:7719/"  # IP Butler
OLLAMA_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "ministral-3:8B"
MI_ALIAS = "bunnydos"

# Estado del sistema
ip_time = {}
list_ping = set()
sleep_time = 30
ping_time = 60

class Mensaje(BaseModel):
    msg: str

# --- UTILIDADES DEL SERVIDOR (BUTLER) ---

async def get_butler_data(endpoint: str):
    """Función asíncrona genérica para consultar al Butler."""
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(f"{SERVER_URL}{endpoint}", timeout=5)
            return r.json()
        except Exception as e:
            logger.error(f"Error Butler ({endpoint}): {e}")
            return {}

async def post_name():
    """Registra el alias si no existe."""
    gente = await get_butler_data("gente")
    if not any(p["alias"] == MI_ALIAS for p in gente):
        async with httpx.AsyncClient() as client:
            await client.post(f"{SERVER_URL}alias/{MI_ALIAS}")
            logger.success(f"Alias {MI_ALIAS} registrado")

# --- LÓGICA DE NEGOCIACIÓN ---

@app.post("/buzon")
async def buzon(request: Request, mensaje: Mensaje):
    client_ip = request.client.host
    logger.info(f"Mensaje de {client_ip}: {mensaje.msg}")

    # 1. Obtener estado unificado (Optimizado)
    info = await get_butler_data("info")
    mis_recursos = info.get("Recursos", {})
    objetivo = info.get("Objetivo", {})

    # 2. IA decide (Delegamos la lógica de 'beneficio' al modelo)
    # En lugar de scores manuales, le damos el objetivo a Ollama
    async with httpx.AsyncClient() as client:
        r = await client.post(OLLAMA_URL, json={
            "model": DEFAULT_MODEL,
            "messages": [
                {
                    "role": "system", 
                    "content": f"Eres un agente de Catan. Tus recursos: {mis_recursos}. Objetivo: {objetivo}. "
                               f"Responde SOLO en JSON: {{\"accion\": \"aceptar\"|\"contraoferta\"|\"rechazar\", \"dar\": str, \"pido\": str}}"
                },
                {"role": "user", "content": mensaje.msg}
            ],
            "stream": False
        })
        
        contenido = r.json().get('message', {}).get('content', '')
        try:
            decision = json.loads(contenido)
        except:
            decision = {"accion": "rechazar", "motivo": "error de formato"}

    # 3. Responder al rival
    ip_time[client_ip] = time.time()
    asyncio.create_task(enviar_ping(client_ip, {"msg": json.dumps(decision)}))

    return {"status": "procesado", "decision": decision}

# --- MONITOR Y REACTIVIDAD ---

async def enviar_ping(ip, msg):
    """Versión asíncrona del envío de mensajes."""
    url = f"http://{ip}:7720/buzon"
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(url, json=msg, timeout=5)
            if r.status_code == 200:
                ip_time[ip] = time.time()
                list_ping.discard(ip)
                return r.json()
        except:
            pass
    return None

async def monitor_loop():
    """Tarea autónoma que gestiona la red."""
    while True:
        try:
            # Actualizar lista de gente
            gente_data = await get_butler_data("gente")
            actuales = {p["ip"] for p in gente_data if p["alias"] != MI_ALIAS}
            
            now = time.time()
            for ip in actuales:
                # Si es nueva o ha pasado el ping_time, reactivar
                if ip not in ip_time or (now - ip_time[ip] > ping_time):
                    logger.warning(f"Reactivando comunicación con {ip}")
                    await enviar_ping(ip, {"msg": "Hola, ¿tienes algún intercambio beneficioso?"})
            
        except Exception as e:
            logger.error(f"Error en monitor: {e}")
            
        await asyncio.sleep(sleep_time)

# --- INICIO ---

@app.on_event("startup")
async def startup():
    await post_name()
    # Iniciamos el monitor como tarea de fondo asíncrona
    asyncio.create_task(monitor_loop())

if __name__ == "__main__":
    import uvicorn
    # Importante: No bloqueamos con hilos, dejamos que FastAPI gestione el loop
    uvicorn.run(app, host="0.0.0.0", port=7720)