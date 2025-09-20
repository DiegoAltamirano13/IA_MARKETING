import requests
from config import OPENROUTER_API_URL, OPENROUTER_API_KEY, OPENROUTER_APP_NAME, OPENROUTER_APP_URL, CONTEXTO_GENERAL, EMPRESA_INFO

def verificar_limites_openrouter():
    """
    Verifica los límites de uso usando el endpoint correcto de OpenRouter
    """
    try:
        headers = {
            'Authorization': f'Bearer {OPENROUTER_API_KEY}',
            'HTTP-Referer': OPENROUTER_APP_URL,
            'X-Title': OPENROUTER_APP_NAME
        }
        
        # Endpoint correcto para información de la clave API
        response = requests.get('https://openrouter.ai/api/v1/auth/key', headers=headers)
        response.raise_for_status()
        
        data = response.json()
        print("🔍 Información de la clave API:")
        print(f"Nombre: {data.get('data', {}).get('label', 'No disponible')}")
        print(f"Creación: {data.get('data', {}).get('created_at', 'No disponible')}")
        print(f"Límite de tasa: {data.get('data', {}).get('rate_limit', 'No disponible')}")
        print(data)
        # Para planes gratuitos, los límites diarios suelen no mostrarse
        # Implementaremos un sistema de monitoreo propio
        
        return data
        
    except Exception as e:
        print(f"❌ Error al verificar límites: {str(e)}")
        return None

# Llamar a la función
verificar_limites_openrouter()