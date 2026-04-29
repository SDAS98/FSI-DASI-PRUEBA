def evaluar_oferta_logica(ofrezco, cant_ofrezco, pido, cant_pido, recursos):
    """Lógica determinista para validar si tenemos los recursos."""
    if recursos.get(ofrezco, 0) < cant_ofrezco:
        return {"accion": "rechazar", "motivo": "No tengo recursos"}
    
    # El modelo decide si le conviene basándose en el objetivo
    if cant_pido >= cant_ofrezco:
        return {"accion": "aceptar"}
    return {"accion": "contraoferta"}
