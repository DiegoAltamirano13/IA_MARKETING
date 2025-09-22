import requests
import re
import logging
import random
from autocorrect import Speller
from config import OPENROUTER_API_URL, OPENROUTER_API_KEY, OPENROUTER_APP_NAME, OPENROUTER_APP_URL, CONTEXTO_GENERAL, EMPRESA_INFO
from database import DatabaseManager, SecurityError

# ✅ Importar los nuevos módulos
from modules.ubicaciones_module import UbicacionesModule
from modules.servicios_module import ServiciosModule
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
            UbicacionesModule(self.db_manager, self.context_manager),
            ServiciosModule(self.db_manager, self.context_manager)  # ← Nuevo módulo
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
        Usa DeepSeek a través de OpenRouter con el contexto completo de ARGO
        """
        try:
            mensaje_corregido = self.corregir_ortografia(mensaje_usuario)
            
            # Obtener contexto de la conversación
            contexto_conversacion = self.context_manager.obtener_contexto(user_id="default")
            
            prompt = f"""
                Eres ALMAssist, asistente especializado de ARGO Almacenadora, actuando como ejecutivo comercial de prospección y atención a clientes.

                OBJETIVO PRINCIPAL:
                Proporcionar información clara, precisa y profesional sobre servicios especializados de almacenaje y logística como Almacén General de Depósito, captando solicitudes de información, quejas o requerimientos de clientes activos.

                CONTEXTO DE LA EMPRESA:
                {CONTEXTO_GENERAL}

                MARCO LEGAL DE REFERENCIA:
                • Ley General de Organizaciones y Actividades Auxiliares del Crédito
                • Ley General de Títulos y Operaciones de Crédito  
                • Ley Aduanera

                UBICACIONES DISPONIBLES (SOLO estas):
                - CENTRAL CÓRDOBA: Corporativo Córdoba, Almacén Peñuela, Almacén Atoyaquillo
                - PLAZA GOLFO: Almacén Ulúa, Almacén Acacias  
                - PLAZA PUEBLA: Almacén Cuautlancingo
                - PLAZA MÉXICO: Almacén Tabla Honda, Almacén Ceylan, Almacén Pantaco
                - PLAZA BAJÍO: Almacén Querétaro
                - PLAZA OCCIDENTE: Almacén Guadalajara
                - PLAZA PENÍNSULA: Almacén Mérida
                - PLAZA NORESTE: Almacén Monterrey

                INSTRUCCIONES ESPECÍFICAS:
                1. TONO: Formal, cordial y empático (ejecutivo comercial). Sin lenguaje emotivo ni promocional.
                2. Para UBICACIONES: Responder EXACTAMENTE "UBICACIONES: [TIPO]|[VALOR]"
                - TIPOS: GENERAL, ESPECIFICA, DETALLES, REFERENCIA, CERCANA
                3. Si preguntan por ubicación cercana: "UBICACIONES: CERCANA|"
                4. Si mencionan ciudad/estado: "UBICACIONES: ESPECIFICA|[CIUDAD]"
                5. Para SERVICIOS: "SERVICIOS: [TIPO]|[DETALLE]"
                6. Para HORARIOS: "HORARIOS: |"
                7. Para RESTRICCIONES: "RESTRICCIONES: |"
                8. Para CONTACTO HUMANO: "CONTACTO: EJECUTIVO|"
                9. Si no tienes información suficiente: Ofrecer contacto de ejecutivo humano inmediatamente.
                10. Las respuestas deben estar respaldadas por el marco legal mencionado cuando sea pertinente.

                EJEMPLOS DE RESPUESTAS:
                - "¿Dónde tienen almacenes?" → "UBICACIONES: GENERAL|"
                - "Almacenes en Veracruz" → "UBICACIONES: ESPECIFICA|Veracruz"
                - "Quiero la más cercana" → "UBICACIONES: CERCANA|"
                - "Almacén Ulúa" → "UBICACIONES: ESPECIFICA|Ulúa"
                - "¿Qué servicios ofrecen?" → "SERVICIOS: GENERAL|"
                - "Necesito hablar con alguien" → "CONTACTO: EJECUTIVO|"
                - "No entiendo" → "Le comento que..."
                - "¿A qué hora abren?" → "HORARIOS: | "
                - "¿Qué no se puede almacenar?" → "RESTRICCIONES: |"

                Pregunta: "{mensaje_corregido}"

                Responde SOLO con el formato especificado, manteniendo el tono formal de ejecutivo comercial y refiriendo al marco legal cuando corresponda:
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
            # AÑADIR ESTA SECCIÓN PARA DETECTAR SERVICIOS
            elif respuesta.startswith("SERVICIOS:"):
                partes = respuesta.split("|")
                tipo_servicio = partes[0].split(":")[1].strip()
                servicio_especifico = partes[1].strip() if len(partes) > 1 else None
                
                logger.info(f"DeepSeek detectó: tipo_servicio={tipo_servicio}, servicio_especifico={servicio_especifico}")
                
                # Redirigir al módulo de servicios
                from modules.servicios_module import ServiciosModule
                servicios_module = ServiciosModule(self.db_manager, self.context_manager)
                
                # Pasar tanto el tipo como el servicio específico
                respuesta_real = servicios_module.procesar_con_tipo(
                    mensaje_corregido,
                    tipo_servicio,
                    user_id="default",
                    servicio_especifico=servicio_especifico
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
        
        # Verificar si es el primer mensaje del usuario
        historial = self.context_manager.obtener_historial(user_id)
        es_primer_mensaje = len(historial) == 0
        
        if es_primer_mensaje:
            # Saludo inicial con menú de opciones
            respuesta = (
                "¡Hola! Soy el Asistente IA de ARGO Almacenadora, ¿en qué puedo apoyarte?\n\n"
                "Por favor selecciona una opción:\n"
                "1. Información sobre infraestructura, servicios y ubicaciones\n"
                "2. Cotización de servicios\n"
                #"3. Información de mi operación (soy cliente activo)\n"
                #"4. Proveedores\n"
                #"5. Vacantes\n"
                "3. Otro"
            )
            # Guardar en contexto que ya mostramos el menú inicial
            self.context_manager.guardar_contexto(user_id, "mostrado_menu_inicial", True)
            # Guardar respuesta en contexto
            self.context_manager.agregar_mensaje(user_id, "assistant", respuesta)
            return respuesta
        
        # Verificar si estamos esperando ubicación del usuario
        contexto = self.context_manager.obtener_contexto(user_id)
        
        # Asegurarse de que contexto es un diccionario
        if isinstance(contexto, dict) and contexto.get('esperando_ubicacion') == 'true':
            # Limpiar el contexto
            self.context_manager.guardar_contexto(user_id, "esperando_ubicacion", "false")
            # Procesar la ubicación proporcionada
            ubicaciones_module = UbicacionesModule(self.db_manager, self.context_manager)
            respuesta = ubicaciones_module.procesar_ubicacion_usuario(mensaje_usuario, user_id)
            # Guardar respuesta en contexto y retornar
            self.context_manager.agregar_mensaje(user_id, "assistant", respuesta)
            return respuesta
        
        # Si contexto no es un diccionario, inicializarlo como tal
        if not isinstance(contexto, dict):
            contexto = {}
            self.context_manager.guardar_contexto(user_id, contexto)
        
        # Guardar mensaje en contexto
        self.context_manager.agregar_mensaje(user_id, "user", mensaje_usuario)
        
        # 1. Saludos y despedidas
        if self.es_saludo(mensaje_usuario):
            respuesta = self.procesar_saludo(mensaje_usuario)
        elif self.es_despedida(mensaje_usuario):
            respuesta = self.procesar_despedida(mensaje_usuario)
        else:
            # 2. Procesar selección de menú si es una opción numérica
            if mensaje_usuario.strip() in ['1', '2', '3', '4', '5', '6']:
                respuesta = self._procesar_opcion_menu(mensaje_usuario, user_id)
            else:
                # 3. Intentar con OpenRouter para clasificación
                try:
                    respuesta_deepseek = self.usar_deepseek_openrouter(mensaje_usuario)
                    
                    # Verificar si es una respuesta especializada
                    if respuesta_deepseek and respuesta_deepseek.startswith(("UBICACIONES:", "SERVICIOS:", "HORARIOS:", "RESTRICCIONES:", "COTIZACION:", "ATENCION_CLIENTE:")):
                        respuesta = self._procesar_respuesta_especializada(respuesta_deepseek, mensaje_usuario, user_id)
                    else:
                        # Si no es una respuesta especializada, usar la respuesta de DeepSeek directamente
                        respuesta = respuesta_deepseek
                        
                except Exception as e:
                    logger.error(f"Error con OpenRouter: {str(e)}")
                    # 4. Fallback a módulos especializados
                    respuesta = self._procesar_con_modulos(mensaje_usuario, user_id)
        
        # Guardar respuesta en contexto
        self.context_manager.agregar_mensaje(user_id, "assistant", respuesta)
        
        return respuesta

    def _procesar_opcion_menu(self, opcion, user_id):
        """Procesa la selección de opciones del menú inicial"""
        opciones = {
            '1': self._procesar_opcion_informacion,
            '2': self._procesar_opcion_cotizacion,
            '3': self._redirigir_a_comercial,
            '4': self._redirigir_a_comercial,
            '5': self._redirigir_a_comercial,
            '6': self._procesar_opcion_otro
        }
        
        if opcion in opciones:
            return opciones[opcion](user_id)
        else:
            return "Opción no válida. Por favor selecciona una opción del 1 al 6."

    def _procesar_opcion_informacion(self, user_id):
        """Procesa la opción 1: Información sobre infraestructura, servicios y ubicaciones"""
        return (
            "**INFORMACIÓN SOBRE INFRAESTRUCTURA, SERVICIOS Y UBICACIONES**\n\n"
            "En ARGO Almacenadora contamos con:\n\n"
            "🏭 **Infraestructura:**\n"
            "• Almacenes modernos y seguros\n"
            "• Sistemas de vigilancia 24/7\n"
            "• Control de clima y humedad\n"
            "• Estructuras anti-sísmicas\n\n"
            "📦 **Servicios:**\n"
            "• Almacenamiento general y especializado\n"
            "• Logística y distribución\n"
            "• Servicios aduanales\n"
            "• Custodia de mercancías\n\n"
            "📍 **Ubicaciones:**\n"
            "• Central Córdoba\n"
            "• Plaza Golfo\n"
            "• Plaza Puebla\n"
            "• Plaza México\n"
            "• Plaza Bajío\n"
            "• Plaza Occidente\n"
            "• Plaza Península\n"
            "• Plaza Noreste\n\n"
            "¿Sobre qué aspecto específico te gustaría conocer más?"
        )

    def _procesar_opcion_cotizacion(self, user_id):
        """Procesa la opción 2: Cotización de servicios"""
        # Guardar en contexto que el usuario quiere cotización
        self.context_manager.guardar_contexto(user_id, "solicitando_cotizacion", True)
        
        return (
            "**COTIZACIÓN DE SERVICIOS**\n\n"
            "Para proporcionarte una cotización precisa, necesito conocer:\n\n"
            "1. **Tipo de mercancía:** ¿Qué producto deseas almacenar?\n"
            "2. **Volumen aproximado:** ¿Cuánto espacio necesitas? (m³ o pallets)\n"
            "3. **Tiempo de almacenaje:** ¿Por cuánto tiempo?\n"
            "4. **Ubicación preferida:** ¿En qué plaza te interesa?\n\n"
            "Por favor, proporciona estos detalles o un ejecutivo se pondrá en contacto contigo."
        )

    def _redirigir_a_comercial(self, user_id):
        """Redirige las opciones 3-5 a un ejecutivo comercial"""
        return (
            "**CONEXIÓN CON EJECUTIVO**\n\n"
            "Para atender tu solicitud de manera personalizada, te conectaremos con uno de nuestros ejecutivos especializados.\n\n"
            "📞 **Contacto directo:**\n"
            "• Teléfono: 555-123-4567\n"
            "• Email: ejecutivos@argo.com.mx\n"
            "• Horario: Lunes a Viernes 9:00 AM - 6:00 PM\n\n"
            "Un ejecutivo se pondrá en contacto contigo a la brevedad para brindarte la atención personalizada que necesitas."
        )

    def _procesar_opcion_otro(self, user_id):
        """Procesa la opción 6: Otro"""
        return (
            "**OTRAS CONSULTAS**\n\n"
            "Para cualquier otra consulta no cubierta en las opciones anteriores, "
            "por favor describe tu necesidad específica y te ayudaré en lo posible.\n\n"
            "También puedes contactarnos directamente:\n"
            "📞 Teléfono: 555-123-4567\n"
            "📧 Email: contacto@argo.com.mx\n"
            "🌐 Web: www.argo.com.mx\n\n"
            "¿En qué más puedo ayudarte?"
        )
            
    def _procesar_respuesta_especializada(self, respuesta_etiquetada, mensaje_original, user_id):
        """Procesa respuestas etiquetadas de OpenRouter"""
        # Primero, limpiar la respuesta de cualquier contenido adicional después del pipe
        if "|" in respuesta_etiquetada:
            # Tomar solo la parte antes del pipe y el pipe mismo, ignorando lo que viene después
            respuesta_limpia = respuesta_etiquetada.split("|")[0] + "|"
        else:
            respuesta_limpia = respuesta_etiquetada
        
        # Ahora procesar con la respuesta limpia
        if respuesta_limpia.startswith("UBICACIONES:"):
            partes = respuesta_limpia.split("|")
            tipo_consulta = partes[0].split(":")[1].strip()
            ubicacion_extraida = partes[1].strip() if len(partes) > 1 else None
            
            ubicaciones_module = UbicacionesModule(self.db_manager, self.context_manager)
            return ubicaciones_module.procesar_con_tipo(
                mensaje_original, tipo_consulta, user_id, ubicacion_extraida
            )
        
        elif respuesta_limpia.startswith("SERVICIOS:"):
            partes = respuesta_limpia.split("|")
            tipo_servicio = partes[0].split(":")[1].strip()
            detalle_servicio = partes[1].strip() if len(partes) > 1 else None
            
            servicios_module = ServiciosModule(self.db_manager, self.context_manager)
            return servicios_module.procesar_con_tipo(mensaje_original, tipo_servicio, user_id, detalle_servicio)
        
        elif respuesta_limpia.startswith("HORARIOS:"):
            # Procesamiento para horarios
            servicios_module = ServiciosModule(self.db_manager, self.context_manager)
            return servicios_module._procesar_horarios(mensaje_original, user_id)
        
        elif respuesta_limpia.startswith("RESTRICCIONES:"):
            # Procesamiento para restricciones
            servicios_module = ServiciosModule(self.db_manager, self.context_manager)
            return servicios_module._procesar_restricciones(mensaje_original, user_id)
        
        elif respuesta_limpia.startswith("COTIZACION:"):
            # Lógica para cotizaciones
            return self._procesar_cotizacion(respuesta_limpia, user_id)
        
        elif respuesta_limpia.startswith("ATENCION_CLIENTE:"):
            # Lógica para atención a clientes
            return self._procesar_atencion_cliente(respuesta_limpia, user_id)
        
        return "Un ejecutivo se pondrá en contacto para atender su solicitud."

    def _procesar_con_modulos(self, mensaje, user_id):
        """Procesa el mensaje con los módulos especializados"""
        for modulo in self.modulos:
            if modulo.puede_manejar(mensaje):
                logger.info(f"Módulo {modulo.__class__.__name__} maneja el mensaje")
                return modulo.procesar(mensaje, user_id)
        
        # Último recurso: respuesta genérica
        return "¿Podría proporcionar más detalles sobre su consulta? Un ejecutivo se pondrá en contacto si es necesario."