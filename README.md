# 🧠 Sistema Multiagente de Negociación (Catan)

## 🚀 Ejecución

### 1. Instalar dependencias
pip install -r requirements.txt

### 2. Ejecutar Ollama
ollama run ministral-3:8B

### 3. Lanzar el sistema
python run.py

---

## 🧱 Arquitectura

- app/
  - models/ → estructuras de datos
  - routes/ → endpoints FastAPI
  - services/ → lógica del agente
- config.py → configuración centralizada

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
