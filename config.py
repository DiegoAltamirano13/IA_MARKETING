import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de OpenRouter
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "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")
OPENROUTER_APP_NAME = "ALMAssist-Chatbot"
OPENROUTER_APP_URL = "http://localhost:5000"

# Configuración de Oracle
ORACLE_URL = "10.10.2.197:1526/ORACBA"
ORACLE_USER = "xds"
ORACLE_PASSWORD = "xds2001"

# Configuración de seguridad
MAX_ROWS_RETURNED = 50  # Límite máximo de filas devueltas
ALLOWED_TABLES = []     # Lista vacía = todas las tablas (pero solo SELECT)
BLOCKED_KEYWORDS = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE', 'TRUNCATE']

# Información de la empresa
EMPRESA_INFO = {
    "nombre": "Argo Almacenadora",
    "servicios": [
        "Almacenamiento de productos perecederos",
        "Distribución logística nacional",
        "Gestión de inventarios inteligente"
    ],
    "ubicaciones": [],
    "contacto": {
        "telefono": "+52 55 1234 5678",
        "email": "info@argoalmacenadora.com",
        "sitio_web": "www.argoalmacenadora.com"
    }
}

# Contexto general para el asistente
CONTEXTO_GENERAL = f"""Eres ALMAssist, el asistente virtual de {EMPRESA_INFO['nombre']}. 
Eres especializado en proporcionar información sobre nuestros servicios de almacenamiento y logística.

Información de la empresa:
- Nombre: {EMPRESA_INFO['nombre']}
- Servicios: {', '.join(EMPRESA_INFO['servicios'])}
- Ubicaciones: {', '.join(EMPRESA_INFO['ubicaciones'])}
- Contacto: Teléfono: {EMPRESA_INFO['contacto']['telefono']}, Email: {EMPRESA_INFO['contacto']['email']}

Responde de manera:
✅ Natural y conversacional
✅ Informativa y precisa
✅ Amable y servicial
✅ Concisa pero completa

Si no sabes algo, admítelo amablemente."""

# Función para actualizar el contexto con ubicaciones desde el módulo
def actualizar_contexto_con_ubicaciones(db_manager):
    """Actualiza el contexto general con las ubicaciones desde el módulo"""
    global CONTEXTO_GENERAL, EMPRESA_INFO
    
    try:
        # Importar y crear instancia temporal del módulo
        from modules.ubicaciones_module import UbicacionesModule
        from utils.context_manager import ContextManager
        
        # Crear instancia temporal del módulo
        context_manager_temp = ContextManager()
        ubicaciones_module = UbicacionesModule(db_manager, context_manager_temp)
        
        # Usar el método del módulo para obtener todas las ubicaciones
        ubicaciones = ubicaciones_module.obtener_todas_las_ubicaciones()
        
        # Si no se obtuvieron ubicaciones, usar valores por defecto
        if not ubicaciones:
            ubicaciones = ["Ciudad de México", "Guadalajara", "Monterrey"]
            
    except ImportError as e:
        print(f"Error importando módulo de ubicaciones: {str(e)}")
        ubicaciones = ["Ciudad de México", "Guadalajara", "Monterrey"]
    except Exception as e:
        print(f"Error usando módulo de ubicaciones: {str(e)}")
        ubicaciones = ["Ciudad de México", "Guadalajara", "Monterrey"]
    
    # Actualizar la información de la empresa
    EMPRESA_INFO["ubicaciones"] = ubicaciones
    
    # Actualizar el contexto general
    CONTEXTO_GENERAL = CONTEXTO_GENERAL_TEMPLATE.format(
        nombre=EMPRESA_INFO['nombre'],
        servicios=', '.join(EMPRESA_INFO['servicios']),
        ubicaciones=', '.join(ubicaciones),
        telefono=EMPRESA_INFO['contacto']['telefono'],
        email=EMPRESA_INFO['contacto']['email']
    )
    
    print(f"Contexto actualizado con {len(ubicaciones)} ubicaciones desde el módulo")
    return CONTEXTO_GENERAL