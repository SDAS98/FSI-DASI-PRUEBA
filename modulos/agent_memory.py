historial = {}

def registrar_en_memoria(ip, decision):
    """Guarda las decisiones para adaptar la estrategia según el rival."""
    historial.setdefault(ip, []).append(decision)

def obtener_perfil(ip):
    data = historial.get(ip, [])
    if not data: return "desconocido"
    aceptaciones = sum(1 for d in data if d.get("accion") == "aceptar")
    return "flexible" if aceptaciones > len(data)/2 else "agresivo"