from loguru import logger

def evaluar_oferta(recursos_actuales, objetivo, oferta_recibida):
    """
    Lógica determinista para validar una oferta antes de que la IA decida.
    
    recursos_actuales: dict (ej: {"Madera": 2, "Trigo": 1})
    objetivo: dict (ej: {"recurso": "Piedra", "cantidad": 5})
    oferta_recibida: dict (ej: {"ofrece": "Trigo", "cantidad": 1, "pide": "Madera", "cant_pide": 1})
    """
    
    recurso_que_pide_el_rival = oferta_recibida.get("pide")
    cantidad_que_pide_el_rival = oferta_recibida.get("cant_pide", 0)
    
    # 1. VALIDACIÓN DE SEGURIDAD: ¿Tenemos lo que nos piden?
    # Si no tenemos suficiente del recurso que el rival quiere, rechazamos de inmediato.
    stock_actual = recursos_actuales.get(recurso_que_pide_el_rival, 0)
    
    if stock_actual < cantidad_que_pide_el_rival:
        logger.warning(f"Validación Tool: No tenemos {cantidad_que_pide_el_rival} de {recurso_que_pide_el_rival}")
        return {
            "accion": "rechazar", 
            "motivo": f"No tengo suficiente {recurso_que_pide_el_rival} (Tengo: {stock_actual})"
        }

    # 2. LÓGICA ESTRATÉGICA SIMPLE:
    # Si lo que nos dan es el recurso que necesitamos para el objetivo, aceptamos más fácil.
    recurso_que_nos_dan = oferta_recibida.get("ofrece")
    if recurso_que_nos_dan == objetivo.get("recurso"):
        logger.info("Validación Tool: La oferta nos da un recurso de nuestro objetivo.")
        return {"accion": "aceptar", "motivo": "Me acerca al objetivo"}

    # 3. CRITERIO DE CANTIDAD:
    # Si nos dan más o igual de lo que nos piden, suele ser buen trato.
    if oferta_recibida.get("cantidad", 0) >= cantidad_que_pide_el_rival:
        return {"accion": "aceptar", "motivo": "Intercambio equivalente o favorable"}
    
    # Por defecto, si llegamos aquí, dejamos que la IA decida si quiere contraofertar
    return {"accion": "contraoferta"}