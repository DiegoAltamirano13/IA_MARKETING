def formatear_lista(items, tipo="bullet"):
    """Formatea una lista de items con emojis y saltos de línea reales"""
    if not items:
        return ""
    
    if tipo == "bullet":
        return "\n".join([f"• {item}" for item in items])
    elif tipo == "number":
        return "\n".join([f"{i+1}. {item}" for i, item in enumerate(items)])
    elif tipo == "check":
        return "\n".join([f"✅ {item}" for item in items])
    elif tipo == "location":
        return "\n".join([f"📍 {item}" for item in items])
    else:
        return "\n".join([f"• {item}" for item in items])