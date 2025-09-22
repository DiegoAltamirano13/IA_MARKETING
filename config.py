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
En ARGO ofrecemos soluciones integrales de almacenaje,
logística y comercio exterior para optimizar tu cadena de suministro y reducir tiempos y costos.
Con más de 34 años de experiencia y una infraestructura especializada en puntos estratégicos de
la República Mexicana, buscamos ser más que un proveedor, un aliado estratégico de nuestros
clientes. Contamos con la autorización de la Secretaría de Hacienda y Crédito Público (SHCP) para
operar como Almacén General de Depósito y ofrecer el servicio de almacenaje de mercancía
nacional o de importación (Almacén Fiscal) amparadas por Certificados de Depósito; ya sea en
nuestros almacenes operados de forma directa o mediante un esquema de Habilitación de
instalaciones de terceros (almacenes, bodegas, silos, entre otros)."""

# Función para actualizar el contexto con ubicaciones desde el módulo
def actualizar_contexto_con_ubicaciones(db_manager):
    """Actualiza el contexto general con las ubicaciones desde el módulo"""
    
    return CONTEXTO_GENERAL