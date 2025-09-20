import platform
import struct

def check_architecture():
    """Verifica la arquitectura del Python actual"""
    print("=== Información de arquitectura ===")
    print(f"Python: {platform.architecture()}")
    print(f"Plataforma: {platform.platform()}")
    print(f"Bits: {struct.calcsize('P') * 8}-bit")
    
    # Recomendación basada en la arquitectura
    if struct.calcsize('P') * 8 == 64:
        print("✅ Tienes Python 64-bit")
        print("❌ Pero tienes cliente Oracle 32-bit instalado")
    else:
        print("✅ Tienes Python 32-bit")
        print("⚠️  El cliente Oracle debería ser 32-bit")

check_architecture()