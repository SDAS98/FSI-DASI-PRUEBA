from loguru import logger

historial = {}

def registrar(ip, decision):
    """Guarda la decisión tomada (aceptar/rechazar) para una IP."""
    if ip not in historial:
        historial[ip] = []
    historial[ip].append(decision)
    logger.debug(f"Memoria: Guardada interacción con {ip}")

def perfil_rival(ip):
    """Analiza si el rival es flexible o agresivo basándose en el historial."""
    interacciones = historial.get(ip, [])
    if not interacciones:
        return "desconocido"
    aceptados = sum(1 for i in interacciones if i.get("accion") == "aceptar")
    return "flexible" if aceptados > len(interacciones) / 2 else "agresivo"