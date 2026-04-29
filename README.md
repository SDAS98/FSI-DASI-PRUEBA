# 🧠 Sistema Multiagente de Negociación (Catan)

## 🚀 Ejecución

### 1. Instalar dependencias
pip install -r requirements.txt

### 2. Ejecutar Ollama
ollama run ministral-3:8B

### 3. Lanzar el sistema
python3 main.py

---

## 🧱 Arquitectura

FDI_DASI/
├── pyproject.toml       <---
├── requirements.txt     <--- Dependencias (fastapi, uvicorn, httpx, loguru)
├── main.py              <--- Punto de entrada
├── README.md            <--- Detalles del codigo
├── comando              <--- Instrucciones
└── modulos/             # Carpeta de lógica
    ├── __init__.py      <--- Puede estar vacio
    ├── agent_logic.py   <--- Lógica con Ollama y Tools
    ├── agent_loop.py    <--- Bucle asíncrono de monitoreo
    ├── agent_memory.py  <--- lógica del agente (el historial de decisiones)
    ├── config.py        <--- IPs y tiempos (Butler: 147.96.80.224)
    ├── server_api.py    <--- Comunicación con el Butler
    └── tools.py         <--- defines la lógica determinista (por ejemplo, comprobar si tienes suficiente recursos para aceptar un trato)

---

## ⚙️ Funcionamiento

1. El agente se registra en Butler
2. Obtiene estado del juego (recursos + objetivo)
3. Recibe mensajes de otros agentes
4. Usa IA (Ollama) para decidir
5. Mantiene memoria del rival
6. Reintenta negociación si no hay respuesta

---

## 🤖 Inteligencia Artificial

- Uso de modelos LLM (Ollama)
- Uso de tools para decisiones estructuradas
- Estrategia adaptativa según rival

---

## 🔥 Mejoras implementadas

- Eliminación de threading → uso de asyncio
- Reducción de llamadas HTTP duplicadas
- Eliminación de regex (interpretación delegada al modelo)
- Agente activo (no pasivo)

---

## 🗣️ Defensa

“Se ha desarrollado un sistema multiagente con negociación adaptativa,
usando modelos LLM, tools estructuradas y arquitectura asíncrona optimizada.”
