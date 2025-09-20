import requests
import re
import logging
import random
from autocorrect import Speller
from config import OPENROUTER_API_URL, OPENROUTER_API_KEY, OPENROUTER_APP_NAME, OPENROUTER_APP_URL, CONTEXTO_GENERAL, EMPRESA_INFO
from database import DatabaseManager, SecurityError

# ✅ Importar los nuevos módulos
from modules.ubicaciones_module import UbicacionesModule
from utils.context_manager import ContextManager

logger = logging.getLogger(__name__)

class MotorRespuestasAvanzado:
    def __init__(self):
        logger.info("Inicializando motor con DeepSeek a través de OpenRouter")
        self.historial_conversacion = []
        self.db_manager = DatabaseManager()
        
        self.palabras_personalizadas = set()
            
        # ✅ Inicializar palabras personalizadas
        self.palabras_personalizadas = {
            'argo', 'almacenadora', 'almacén', 'almacen', 'logística',
            'bajio', 'bajío', 'córdoba', 'golfo', 'noreste', 'occidente',
            'peninsula', 'puebla', 'querétaro', 'yucatán', 'jalisco',
            'mercancia', 'mercancía', 'producto', 'cliente', 'pedido',
            'factura', 'servicio', 'almacenamiento', 'distribución'
        }

        # ✅ Inicializar el gestor de contexto
        self.context_manager = ContextManager()
        
        # ✅ Inicializar módulos
        self.modulos = [
            UbicacionesModule(self.db_manager, self.context_manager)
            # Aquí agregarás más módulos después: ServiciosModule, InventarioModule, etc.
        ]
        
        #self._agregar_palabras_personalizadas()

    def _debe_preservar(self, palabra):
        """Determina si una palabra debe preservarse sin cambios"""
        palabra_lower = palabra.lower()
        
        # 1. Preservar palabras del dominio empresarial
        if palabra_lower in self.palabras_personalizadas:
            return True
            
        # 2. Preservar nombres propios (inician con mayúscula)
        if len(palabra) > 1 and palabra[0].isupper():
            return True
            
        # 3. Preservar siglas y acrónimos (todas mayúsculas)
        if palabra.isupper() and len(palabra) <= 6:
            return True
            
        # 4. Preservar palabras muy cortas
        if len(palabra) <= 2:
            return True
            
        # 5. Preservar números y combinaciones alfanuméricas
        if any(char.isdigit() for char in palabra):
            return True
            
        # 6. Preservar emails
        if '@' in palabra and '.' in palabra:
            return True
            
        # 7. Preservar códigos y referencias (patrones comunes)
        if re.match(r'^[A-Z0-9\-_]+$', palabra) and len(palabra) >= 3:
            return True
            
        return False
    
    def _es_correccion_valida(self, original, correccion):
        """Determina si una corrección es válida"""
        # No cambiar si la corrección es muy diferente en longitud
        if abs(len(original) - len(correccion)) > 2:
            return False
            
        # No cambiar si son esencialmente iguales
        if original.lower() == correccion.lower():
            return False
            
        # No cambiar si solo difiere en acentos o mayúsculas
        if original.lower() == correccion.lower().replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u'):
            return False
            
        return True

    def _distancia_levenshtein(self, s1, s2):
        """Calcula distancia Levenshtein entre dos palabras"""
        if len(s1) < len(s2):
            return self._distancia_levenshtein(s2, s1)
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def corregir_ortografia(self, texto):
        """Usa autocorrect con reglas personalizadas"""
        try:
            spell = Speller(lang='es')
            palabras = texto.split()
            corregidas = []
            
            for palabra in palabras:
                if self._debe_preservar(palabra):
                    corregidas.append(palabra)
                else:
                    # Solo corregir si la palabra no existe en español
                    correccion = spell(palabra)
                    # Si la corrección es muy diferente, preservar original
                    if self._es_correccion_valida(palabra, correccion):
                        corregidas.append(correccion)
                    else:
                        corregidas.append(palabra)
                        
            return ' '.join(corregidas)
            
        except Exception as e:
            logger.error(f"Error con autocorrect: {str(e)}")
            return texto

    def _es_correccion_valida(self, original, correccion):
        """Determina si una corrección es válida"""
        # No cambiar si la corrección es muy diferente
        if abs(len(original) - len(correccion)) > 2:
            return False
            
        # No cambiar si solo difiere en una letra (posible nombre propio)
        if len(original) > 3 and self._distancia_levenshtein(original, correccion) <= 1:
            return False
            
        return True

    def _distancia_levenshtein(self, s1, s2):
        """Calcula distancia Levenshtein entre dos palabras"""
        if len(s1) < len(s2):
            return self._distancia_levenshtein(s2, s1)
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]

    def es_saludo(self, mensaje):
        """Detecta si el mensaje es un saludo"""
        saludos = ['hola', 'buenos días', 'buenas tardes', 'buenas noches', 'saludos', 'hi', 'hello']
        return any(saludo in mensaje.lower() for saludo in saludos)

    def es_despedida(self, mensaje):
        """Detecta si el mensaje es una despedida"""
        despedidas = ['adiós', 'adios', 'hasta luego', 'nos vemos', 'gracias', 'bye', 'goodbye']
        return any(despedida in mensaje.lower() for despedida in despedidas)

    def procesar_saludo(self, mensaje):
        """Procesa mensajes de saludo"""
        saludos = [
            "¡Hola! 👋 ¿En qué puedo ayudarte hoy?",
            "¡Buen día! 🌟 Estoy aquí para asistirte",
            "¡Hola! 😊 ¿Cómo puedo ayudarte?"
        ]
        return random.choice(saludos)

    def procesar_despedida(self, mensaje):
        """Procesa mensajes de despedida"""
        despedidas = [
            "¡Hasta luego! 👋 Fue un placer ayudarte",
            "¡Que tengas un excelente día! 🌟",
            "¡Nos vemos! 😊 Estoy aquí cuando me necesites"
        ]
        return random.choice(despedidas)

    def es_consulta_bd(self, mensaje):
        """
        SOLO para logging o análisis, NO para decidir procesamiento
        Siempre retorna False para evitar consultas directas a BD
        """
        mensaje_lower = mensaje.lower()
        
        palabras_bd = [
            'productos', 'stock', 'inventario', 'existencias', 'precio', 'costos',
            'clientes', 'pedidos', 'ventas', 'facturas', 'cotizaciones'
        ]
        
        es_consulta = any(palabra in mensaje_lower for palabra in palabras_bd)
        if es_consulta:
            logger.info(f"Consulta de BD detectada pero no procesada: {mensaje}")
        
        return False

    def procesar_consulta_bd(self, mensaje):
        """
        Método deshabilitado - las consultas BD solo las manejan los módulos
        """
        logger.warning(f"Intento de consulta BD directa bloqueada: {mensaje}")
        return "Las consultas directas a base de datos están restringidas. Por favor, formula tu pregunta de manera más específica."

    def responder_pregunta_empresa(self, mensaje):
        """
        Responde preguntas sobre la empresa SIN consultar BD
        """
        mensaje_lower = mensaje.lower()
        
        # Preguntas frecuentes sobre la empresa (respuestas predefinidas)
        if any(palabra in mensaje_lower for palabra in ['qué es', 'que es', 'quienes son', 'quién es']):
            return EMPRESA_INFO
        
        if 'servicios' in mensaje_lower:
            return "Ofrecemos servicios de almacenamiento, logística, distribución y custodia de mercancías."
        
        if 'ubicaciones' in mensaje_lower or 'dónde' in mensaje_lower:
            return "Tenemos presencia en múltiples plazas. ¿Te gustaría conocer nuestras ubicaciones específicas?"
        
        if 'contacto' in mensaje_lower or 'teléfono' in mensaje_lower or 'email' in mensaje_lower:
            return "Puedes contactarnos al teléfono: 555-123-4567 o email: contacto@argo.com.mx"
        
        if 'horario' in mensaje_lower:
            return "Nuestro horario de atención es de lunes a viernes de 9:00 AM a 6:00 PM."
        
        return None

    def usar_deepseek_openrouter(self, mensaje_usuario):
        """
        Usa DeepSeek a través de OpenRouter con detección inteligente de intenciones
        """
        try:
            # Corregir ortografía del mensaje
            mensaje_corregido = self.corregir_ortografia(mensaje_usuario)
            
            prompt = f"""
            Eres ALMAssist, asistente especializado de ARGO Almacenadora. 

            CONTEXTO DE LA EMPRESA:
            {EMPRESA_INFO}

            INSTRUCCIONES ESPECIALES:
            1. ANALIZA si la pregunta está relacionada con UBICACIONES, SUCURSALES o ALMACENES
            2. Si detectas que pregunta por ubicaciones, responde SOLO con: "UBICACIONES: [tipo_consulta]|[ubicacion_extraida]"
            3. Para otras consultas, responde normalmente

            TIPOS DE CONSULTA DE UBICACIONES:
            - "GENERAL": Si pregunta por todas las ubicaciones, ej: "¿Dónde tienen almacenes?" → "UBICACIONES: GENERAL|"
            - "ESPECIFICA": Si menciona una ubicación concreta, ej: "almacenes en Querétaro" → "UBICACIONES: ESPECIFICA|Querétaro"  
            - "DETALLES": Si pide detalles específicos como direcciones, teléfonos, horarios → "UBICACIONES: DETALLES|"
            - "REFERENCIA": Si usa números como "1", "2", "primera", "segunda" → "UBICACIONES: REFERENCIA|1"

            FORMATO DE RESPUESTA PARA UBICACIONES:
            Si es sobre ubicaciones, responde EXACTAMENTE: "UBICACIONES: [GENERAL|ESPECIFICA|DETALLES|REFERENCIA]|[ubicacion_o_referencia]"

            EJEMPLOS COMPLETOS:
            - "¿Dónde están sus almacenes?" → "UBICACIONES: GENERAL|"
            - "Tienen sucursal en Guadalajara?" → "UBICACIONES: ESPECIFICA|Guadalajara"  
            - "Dirección y teléfono de Monterrey" → "UBICACIONES: DETALLES|Monterrey"
            - "Quiero la primera ubicación" → "UBICACIONES: REFERENCIA|primera"
            - "Muéstrame la número 2" → "UBICACIONES: REFERENCIA|2"
            - "Información de la 3" → "UBICACIONES: REFERENCIA|3"
            - "La ubicación 5" → "UBICACIONES: REFERENCIA|5"
            - "Quiero saber sobre servicios" → (respuesta normal)

            UBICACIONES DISPONIBLES (para referencia):
            📍 BAJIO, 📍 CÓRDOBA, 📍 GOLFO, 📍 MÉXICO, 📍 NORESTE, 📍 OCCIDENTE, 📍 PENINSULA, 📍 PUEBLA

            Pregunta del usuario: "{mensaje_corregido}"

            Responde:
            """

            headers = {
                'Authorization': f'Bearer {OPENROUTER_API_KEY}',
                'Content-Type': 'application/json',
                'HTTP-Referer': OPENROUTER_APP_URL,
                'X-Title': OPENROUTER_APP_NAME
            }
            
            payload = {
                'model': 'deepseek/deepseek-chat-v3.1:free',
                'messages': [{'role': 'user', 'content': prompt}],
                'temperature': 0.1,
                'max_tokens': 100
            }
            
            response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=20)
            response.raise_for_status()
            
            resultado = response.json()
            respuesta = resultado['choices'][0]['message']['content'].strip()
            
            # Verificar si DeepSeek detectó que es sobre ubicaciones
            if respuesta.startswith("UBICACIONES:"):
                partes = respuesta.split("|")
                tipo_consulta = partes[0].split(":")[1].strip()
                ubicacion_extraida = partes[1].strip() if len(partes) > 1 else None
                
                logger.info(f"DeepSeek detectó: tipo={tipo_consulta}, ubicación={ubicacion_extraida}")
                
                # Redirigir al módulo de ubicaciones con toda la información
                from modules.ubicaciones_module import UbicacionesModule
                ubicaciones_module = UbicacionesModule(self.db_manager, self.context_manager)
                
                # Pasar tanto el tipo como la ubicación extraída
                respuesta_real = ubicaciones_module.procesar_con_tipo(
                    mensaje_corregido, 
                    tipo_consulta, 
                    user_id="default",
                    ubicacion_extraida=ubicacion_extraida  # ← Nuevo parámetro
                )
                return respuesta_real
            
            # Si no es sobre ubicaciones, retornar la respuesta normal de DeepSeek
            return respuesta
                
        except requests.exceptions.Timeout:
            logger.error("Timeout al conectar con OpenRouter")
            return "Lo siento, el servicio de inteligencia artificial está tardando en responder. Por favor, intenta nuevamente."
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de conexión con OpenRouter: {str(e)}")
            return "Lo siento, hay problemas de conexión con el servicio de inteligencia artificial."
        except Exception as e:
            logger.error(f"Error inesperado al usar DeepSeek: {str(e)}")
            return "Lo siento, ocurrió un error inesperado al procesar tu solicitud."
        
    def procesar_mensaje(self, mensaje_usuario, user_id="default"):
        """Procesa el mensaje con el sistema modular"""
        logger.info(f"Procesando: {mensaje_usuario}")
        
        # ✅ PRIMERO: Verificar si es un saludo o despedida
        if self.es_saludo(mensaje_usuario):
            return self.procesar_saludo(mensaje_usuario)
        if self.es_despedida(mensaje_usuario):
            return self.procesar_despedida(mensaje_usuario)
        
        # ✅ SEGUNDO: Usar DeepSeek para clasificación inteligente
        respuesta_deepseek = self.usar_deepseek_openrouter(mensaje_usuario)
        
        # Si DeepSeek ya procesó la solicitud (ya sea ubicaciones o respuesta normal), retornarla
        if respuesta_deepseek and not respuesta_deepseek.startswith("UBICACIONES:"):
            return respuesta_deepseek
        
        # ✅ TERCERO: Intentar con los módulos especializados (para casos donde DeepSeek no detectó pero debería)
        for modulo in self.modulos:
            if modulo.puede_manejar(mensaje_usuario):
                logger.info(f"Módulo {modulo.__class__.__name__} maneja el mensaje")
                return modulo.procesar(mensaje_usuario, user_id)
        
        # ✅ CUARTO: Verificar si es una pregunta sobre la empresa (sin BD)
        respuesta_empresa = self.responder_pregunta_empresa(mensaje_usuario)
        if respuesta_empresa:
            return respuesta_empresa
        
        # Respuesta de emergencia
        return "Lo siento, no pude procesar tu solicitud. ¿Podrías reformular tu pregunta?"