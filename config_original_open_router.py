import os
import logging
import requests
import time
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()
logger = logging.getLogger(__name__)

class OpenRouterKeyManager:
    def __init__(self):
        self.api_key = None
        self.key_expires_at = None
        self.last_request_time = 0
        self.request_delay = 3  # 2 segundos entre requests para evitar 429
        self.consecutive_errors = 0
        self.max_delay = 30
        self.app_name = "ALMAssist-Chatbot"
        self.app_url = "https://09a4e4543e5d.ngrok-free.app/"
        
    def get_fresh_key(self):
        """Obtiene una API key fresca"""
        if self._key_needs_refresh():
            return self._initialize_key()
        return self.api_key
    
    def _key_needs_refresh(self):
        """Verifica si la key necesita renovación"""
        if not self.api_key or not self.key_expires_at:
            return True
        
        # Renovar 1 hora antes de expirar (por seguridad)
        refresh_time = self.key_expires_at - timedelta(hours=1)
        return datetime.now() >= refresh_time
    
    def _initialize_key(self):
        """Inicializa la API key desde variables de entorno"""
        try:
            self.api_key = os.environ.get("OPENROUTER_API_KEY")
            
            if not self.api_key:
                raise ValueError("❌ OPENROUTER_API_KEY no encontrada en variables de entorno")
            
            # OpenRouter keys no expiran, pero renovamos cada 24h por seguridad
            self.key_expires_at = datetime.now() + timedelta(hours=24)
            logger.info("✅ API key cargada correctamente")
            
            return self.api_key
                
        except Exception as e:
            logger.error(f"❌ Error inicializando API key: {e}")
            raise
    
    def rate_limit(self):
        """Implementa rate limiting para evitar error 429"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
         # Delay base + jitter aleatorio para evitar patrones
        base_delay = self.request_delay
        jitter = random.uniform(0.1, 0.5)  # Aleatoriedad
        total_delay = base_delay + jitter
        
        if elapsed < total_delay:
            sleep_time = total_delay - elapsed
            logger.debug(f"⏳ Rate limiting: esperando {sleep_time:.1f}s")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def handle_429_error(self):
        """Maneja errores 429 aumentando el delay progresivamente"""
        self.consecutive_errors += 1
        
        # Aumento exponencial con backoff
        if self.consecutive_errors == 1:
            self.request_delay = 5  # Primer error: 5 segundos
        elif self.consecutive_errors == 2:
            self.request_delay = 10  # Segundo error: 10 segundos
        elif self.consecutive_errors == 3:
            self.request_delay = 20  # Tercer error: 20 segundos
        else:
            self.request_delay = self.max_delay  # Máximo
        
        logger.warning(f"⚠️ Error 429 - Aumentando delay a {self.request_delay}s")
        
        # Esperar antes del próximo intento
        time.sleep(self.request_delay)

    def reset_error_count(self):
        """Resetea el contador de errores después de una solicitud exitosa"""
        if self.consecutive_errors > 0:
            logger.info("✅ Conexión restaurada - reseteando contador de errores")
            self.consecutive_errors = 0
            self.request_delay = 3  # Volver al delay base
                
# Instancia global del manager
key_manager = OpenRouterKeyManager()

# Configuración de OpenRouter
def get_openrouter_config():
    """Obtiene configuración con rate limiting integrado"""
    key_manager.rate_limit()  # Aplicar rate limiting antes de cada request
    
    api_key = key_manager.get_fresh_key()
    logger.info(api_key)
    return {
        "api_url": "https://openrouter.ai/api/v1/chat/completions",  # ✅ URL CORRECTA
        "api_key": api_key,
        "app_name": "ALMAssist-Chatbot",
        "app_url": "https://09a4e4543e5d.ngrok-free.app/",
        "headers": {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": key_manager.app_url,
            "X-Title": key_manager.app_name
        }
    }

# Función mejorada para manejar errores de API
def handle_openrouter_error(response):
    """Maneja errores específicos de OpenRouter"""
    if response.status_code == 429:
        logger.warning("⚠️ Rate limit excedido, aumentando delay...")
        key_manager.handle_429_error()
        return "Demasiadas solicitudes. Por favor espera un momento."
    elif response.status_code == 401:
        logger.error("❌ API key inválida o expirada")
        # Forzar renovación de key
        key_manager.api_key = None
        key_manager.key_expires_at = None
        return "Error de autenticación. Verifica la API key."
    elif response.status_code == 404:
        logger.error("❌ Endpoint no encontrado - verificar URL de API")
        return "Error de configuración del servicio. Por favor contacta al administrador."
    else:
        logger.error(f"❌ Error OpenRouter {response.status_code}: {response.text}")
        return f"Error del servicio: {response.status_code}"

# Función para hacer solicitudes a OpenRouter
def make_openrouter_request(messages, model="deepseek/deepseek-chat"):
    """Realiza una solicitud a la API de OpenRouter"""
    try:
        config = get_openrouter_config()
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        response = requests.post(
            config["api_url"],
            headers=config["headers"],
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            key_manager.reset_error_count()
            return response.json()["choices"][0]["message"]["content"]
        else:
            error_message = handle_openrouter_error(response)
            return f"Error: {error_message}"
            
    except requests.exceptions.Timeout:
        logger.error("⏰ Timeout en la solicitud a OpenRouter")
        return "Error: Timeout del servicio. Por favor intenta nuevamente."
    except requests.exceptions.ConnectionError:
        logger.error("🔌 Error de conexión con OpenRouter")
        return "Error: No se pudo conectar al servicio. Verifica tu conexión a internet."
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        return "Error inesperado del sistema."


# config.py - VERSIÓN CORREGIDA
import os
import logging
from dotenv import load_dotenv

load_dotenv()

# Configuración directa DeepSeek
DEEPSEEK_CONFIG = {
    "api_url": "https://api.deepseek.com/v1/chat/completions",
    "api_key": os.getenv("DEEPSEEK_API_KEY"),  # ← Esta variable en .env
    "model": "deepseek-chat",
    "temperature": 0.7,
    "max_tokens": 4000
}

def get_deepseek_config():
    return {
        "api_url": DEEPSEEK_CONFIG["api_url"],
        "headers": {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_CONFIG['api_key']}"
        },
        "payload": {
            "model": DEEPSEEK_CONFIG["model"],
            "temperature": DEEPSEEK_CONFIG["temperature"],
            "max_tokens": DEEPSEEK_CONFIG["max_tokens"],
            "stream": False
        }
    }

def make_deepseek_request(messages):
    """Función simplificada para DeepSeek API"""
    import requests
    
    try:
        config = get_deepseek_config()
        payload = config["payload"].copy()
        payload["messages"] = messages
        
        response = requests.post(
            config["api_url"],
            headers=config["headers"],
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            return f"Error: {response.status_code} - {response.text}"
            
    except Exception as e:
        return f"Error de conexión: {e}"
        
# Configuración de OpenRouter
#OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
#OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "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")
#OPENROUTER_APP_NAME = "ALMAssist-Chatbot"
#OPENROUTER_APP_URL = "http://localhost:5000"

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