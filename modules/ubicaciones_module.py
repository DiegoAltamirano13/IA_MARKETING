import re
import logging
import unicodedata
from .base_module import BaseModule
from utils.formatters import formatear_lista

logger = logging.getLogger(__name__)

def normalizar_texto(texto):
    """Normaliza texto quitando acentos y convirtiendo a minúsculas"""
    if not texto:
        return ""
    
    # Normaliza a forma NFKD y quita los caracteres diacríticos (acentos)
    texto_normalizado = unicodedata.normalize('NFKD', texto)
    texto_sin_acentos = ''.join([c for c in texto_normalizado if not unicodedata.combining(c)])
    
    return texto_sin_acentos.lower()

class UbicacionesModule(BaseModule):
    def puede_manejar(self, mensaje):
        mensaje_lower = mensaje.lower()
         # Lista MUY completa de palabras clave y variantes
        palabras_clave_ubicaciones = [
            # Palabras básicas
            'ubicación', 'ubicacion', 'ubicaciones', 'dirección', 'direccion', 
            'direcciones', 'localización', 'localizacion', 'localizaciones',
            'lugar', 'lugares', 'sitio', 'sitios', 'sede', 'sedes',
            'plaza', 'plazas', 'almacén', 'almacen', 'almacenes', 'bodega', 'bodegas',
            'depósito', 'deposito', 'depósitos', 'depositos', 'centro', 'centros',
            'sucursal', 'sucursales', 'instalación', 'instalacion', 'instalaciones',
            
            # Verbos de búsqueda
            'encontrar', 'encontrará', 'buscar', 'encontré', 'hallar', 'localizar',
            'ver', 'mostrar', 'listar', 'conocer', 'saber', 'consultar',
            
            # Preguntas de ubicación
            'dónde', 'donde', 'dónde está', 'donde esta', 'dónde están', 'donde estan',
            'dónde queda', 'donde queda', 'dónde quedan', 'donde quedan',
            'dónde se encuentra', 'donde se encuentra', 'dónde se encuentran', 'donde se encuentran',
            'dónde hay', 'donde hay', 'dónde puedo encontrar', 'donde puedo encontrar',
            'en qué lugar', 'en que lugar', 'en qué lugares', 'en que lugares',
            'cuál es la dirección', 'cual es la direccion', 'cuáles son las direcciones',
            'cuales son las direcciones', 'cómo llegar', 'como llegar',
            'qué dirección', 'que direccion', 'qué direcciones', 'que direcciones',
            
            # Preposiciones y artículos comunes
            'la ubicación', 'las ubicaciones', 'el almacén', 'los almacenes',
            'mi ubicación', 'nuestra ubicación', 'sus ubicaciones',
            
            # Términos geográficos
            'ciudad', 'ciudades', 'estado', 'estados', 'municipio', 'municipios',
            'zona', 'zonas', 'región', 'region', 'regiones', 'área', 'area', 'áreas',
            'locación', 'locacion', 'locaciones',
            
            # Términos de negocio/logística
            'punto', 'puntos', 'punto de entrega', 'puntos de entrega',
            'centro de distribución', 'centros de distribución',
            'logística', 'logistica', 'distribución', 'distribucion',
            'entrega', 'entregas', 'recepción', 'recepcion'
        ]
        
         # Referencias a posiciones (primera, segunda, etc.)
        referencias_posiciones = [
            'primera', 'segunda', 'tercera', 'cuarta', 'quinta', 'última',
            'primero', 'segundo', 'tercero', 'cuarto', 'quinto',
            '1ra', '2da', '3ra', '4ta', '5ta', 'número', 'num', 'nro'
        ]

        # Verificar palabras clave de ubicaciones
        tiene_palabra_ubicacion = any(palabra in mensaje_lower for palabra in palabras_clave_ubicaciones)
        
        # Verificar si es una referencia a posición (ej: "la primera")
        tiene_referencia_posicion = any(ref in mensaje_lower for ref in referencias_posiciones)
        
        # También detectar patrones como "de la primera", "la número 1", etc.
        patrones_referencia = [
            r'(?:la|el)\s+(primera|segunda|tercera|cuarta|quinta|última)',
            r'(?:número|num|nro)\s*\d+',
            r'la\s+\d+'
        ]
        
        tiene_patron_referencia = any(re.search(patron, mensaje_lower) for patron in patrones_referencia)
        
        return tiene_palabra_ubicacion or tiene_referencia_posicion or tiene_patron_referencia
    
    def procesar_con_tipo(self, mensaje, tipo_consulta, user_id="default", ubicacion_extraida=None):
        """
        Procesa el mensaje sabiendo previamente el tipo de consulta y ubicación
        """
        logger.info(f"Procesando consulta: tipo={tipo_consulta}, ubicación_extraida={ubicacion_extraida}")
        
        if tipo_consulta == "ESPECIFICA":
            # Usar la ubicación extraída por DeepSeek si está disponible
            if ubicacion_extraida and ubicacion_extraida != "":
                logger.info(f"Usando ubicación extraída por DeepSeek: {ubicacion_extraida}")
                return self._obtener_detalles_ubicacion_especifica(ubicacion_extraida)
            
            # Si no hay ubicación extraída, buscar en el mensaje
            ubicacion_especifica = self._buscar_ubicacion_en_mensaje(mensaje)
            if ubicacion_especifica:
                logger.info(f"Ubicación encontrada en mensaje: {ubicacion_especifica}")
                return self._obtener_detalles_ubicacion_especifica(ubicacion_especifica)
            else:
                # Si no encuentra la ubicación, preguntar al usuario
                return "¿En qué ciudad o plaza específica te interesa conocer nuestras instalaciones?"
        
        elif tipo_consulta == "DETALLES":
            # Usar la ubicación extraída por DeepSeek si está disponible
            if ubicacion_extraida and ubicacion_extraida != "":
                return self._obtener_detalles_ubicacion_especifica(ubicacion_extraida)
            
            # Buscar ubicación para detalles específicos
            ubicacion_especifica = self._buscar_ubicacion_en_mensaje(mensaje)
            if ubicacion_especifica:
                return self._obtener_detalles_ubicacion_especifica(ubicacion_especifica)
            else:
                # Mostrar todas las ubicaciones con detalles
                return self._obtener_ubicaciones_detalladas()
        
        elif tipo_consulta == "REFERENCIA":
            # Manejar referencias numéricas como "1", "2", "primera", "segunda"
            if ubicacion_extraida and ubicacion_extraida != "":
                logger.info(f"Procesando referencia: {ubicacion_extraida}")
                return self._procesar_referencia_ubicacion(user_id, ubicacion_extraida)
            else:
                # Si no hay referencia específica, mostrar todas las ubicaciones
                return self._obtener_ubicaciones_generales(user_id)
        
        elif tipo_consulta == "GENERAL":
            # Mostrar todas las ubicaciones generales
            return self._obtener_ubicaciones_generales(user_id)
        
        else:
            # Por defecto, usar el procesamiento normal
            return self.procesar(mensaje, user_id)
        
    def procesar(self, mensaje, user_id="default"):
        mensaje_lower = mensaje.lower()
        
        # PRIMERO: Verificar si es una solicitud de DETALLES específicos
        if self._es_solicitud_detalles(mensaje):
            logger.info("Detectada solicitud de detalles específicos")
            return self._obtener_ubicaciones_detalladas()
        
        # SEGUNDO: Verificar si menciona una ubicación específica
        ubicacion_especifica = self._buscar_ubicacion_en_mensaje(mensaje)
        if ubicacion_especifica:
            logger.info(f"Detectada ubicación específica: {ubicacion_especifica}")
            return self._obtener_detalles_ubicacion_especifica(ubicacion_especifica)
        
        # TERCERO: Verificar si es una referencia a ubicación previa
        referencia = self._detectar_referencia_numerica(mensaje)
        if referencia:
            logger.info(f"Detectada referencia numérica: {referencia}")
            return self._procesar_referencia_ubicacion(user_id, referencia)
        
        # CUARTO: Por defecto, mostrar TODAS las ubicaciones (consulta general)
        logger.info("Mostrando todas las ubicaciones (consulta general)")
        return self._obtener_ubicaciones_generales(user_id)
    
    def _detectar_pregunta_con_ubicacion(self, mensaje):
        """Detecta específicamente patrones como 'en [ubicación]'"""
        patrones = [
            r'en\s+([a-zA-ZáéíóúñÑ\s]+)\??$',
            r'ubicaciones\s+en\s+([a-zA-ZáéíóúñÑ\s]+)\??$',
            r'almacenes\s+en\s+([a-zA-ZáéíóúñÑ\s]+)\??$',
            r'plazas\s+en\s+([a-zA-ZáéíóúñÑ\s]+)\??$',
            r'tienes\s+.*en\s+([a-zA-ZáéíóúñÑ\s]+)\??$',
            r'hay\s+.*en\s+([a-zA-ZáéíóúñÑ\s]+)\??$'
        ]
        
        for patron in patrones:
            coincidencias = re.findall(patron, mensaje, re.IGNORECASE)
            if coincidencias:
                ubicacion = coincidencias[0].strip()
                # Validar que no sea una palabra muy corta o común
                if len(ubicacion) > 3 and ubicacion.lower() not in ['que', 'donde', 'como', 'cuando']:
                    return ubicacion
        return None

    def _detectar_referencia_numerica(self, mensaje):
        """Solo detecta referencias numéricas, no nombres de lugares"""
        patrones = [
            r'(?:la|el)\s+(primera|segunda|tercera|cuarta|quinta|última|1ra|2da|3ra|4ta|5ta)',
            r'(?:número|num|nro|#)\s*(\d+)',
            r'la\s+(\d+)(?:ª|ra|da|ta)?'
        ]
        
        for patron in patrones:
            coincidencias = re.findall(patron, mensaje, re.IGNORECASE)
            if coincidencias:
                return coincidencias[0].strip()
        return None
    
    def _detectar_referencia_ubicacion(self, mensaje):
        patrones = [
            r'(?:la|el|las|los)\s+(primera|segunda|tercera|cuarta|quinta|última|1ra|2da|3ra|4ta|5ta)',
            r'(?:número|num|nro|#)\s*(\d+)',
            r'en\s+([a-zA-ZáéíóúñÑ\s]+)',
            r'de\s+([a-zA-ZáéíóúñÑ\s]+)',
            r'(\b(?:primera|segunda|tercera|cuarta|quinta|última)\b)'
        ]
        
        for patron in patrones:
            coincidencias = re.findall(patron, mensaje, re.IGNORECASE)
            if coincidencias:
                return coincidencias[0].strip()
        return None
    
    def _procesar_referencia_ubicacion(self, user_id, referencia):
        logger.info(f"Procesando referencia: '{referencia}' para user: {user_id}")
        
        # Convertir referencias textuales a numéricas
        mapeo_referencias = {
            'primera': '1', 'primero': '1', '1ra': '1',
            'segunda': '2', 'segundo': '2', '2da': '2', 
            'tercera': '3', 'tercero': '3', '3ra': '3',
            'cuarta': '4', 'cuarto': '4', '4ta': '4',
            'quinta': '5', 'quinto': '5', '5ta': '5',
            'última': 'ultima', 'ultima': 'ultima'
        }
        
        # Normalizar la referencia
        referencia_normalizada = referencia.lower().strip()
        if referencia_normalizada in mapeo_referencias:
            referencia_normalizada = mapeo_referencias[referencia_normalizada]
        
        # OBTENER las ubicaciones del contexto
        ubicaciones = self.context_manager.obtener_ubicaciones(user_id)
        logger.info(f"Ubicaciones en contexto: {ubicaciones}")
        
        if not ubicaciones:
            logger.warning("No hay ubicaciones en contexto")
            return "No tengo ubicaciones en contexto. ¿Podrías pedirme que muestre las ubicaciones primero?"
        
        # Buscar por número de referencia
        if referencia_normalizada.isdigit():
            indice = int(referencia_normalizada) - 1
            if 0 <= indice < len(ubicaciones):
                ubicacion = ubicaciones[indice]
                logger.info(f"Ubicación encontrada para referencia '{referencia}': {ubicacion}")
                return self._obtener_detalles_ubicacion_especifica(ubicacion)
        
        # Buscar por texto "última"
        elif referencia_normalizada == 'ultima' and ubicaciones:
            ubicacion = ubicaciones[-1]
            logger.info(f"Última ubicación encontrada: {ubicacion}")
            return self._obtener_detalles_ubicacion_especifica(ubicacion)
        
        # Si no encuentra, mostrar sugerencias
        primeras_tres = ubicaciones[:3]
        sugerencias = ", ".join(primeras_tres)
        return f"No encontré la ubicación '{referencia}'. Las ubicaciones disponibles incluyen: {sugerencias}... ¿Te refieres a alguna de estas?"
        
    def _es_solicitud_detalles(self, mensaje):
        mensaje_lower = mensaje.lower()
        palabras_detalles = [
            'detalles', 'específico', 'especifico', 'dirección', 'direccion', 
            'teléfono', 'telefono', 'horario', 'contacto', 'información', 'informacion'
        ]
        return any(palabra in mensaje_lower for palabra in palabras_detalles)
    
    def _buscar_ubicacion_en_mensaje(self, mensaje):
        """Busca nombres de ubicaciones en el mensaje normalizando texto"""
        try:
            # Obtener todas las ubicaciones posibles de la BD
            query = """
            SELECT DISTINCT 
                CASE 
                    WHEN INSTR(B.V_RAZON_SOCIAL, '(') > 0 AND INSTR(B.V_RAZON_SOCIAL, ')') > 0
                        THEN SUBSTR(B.V_RAZON_SOCIAL, 1, INSTR(B.V_RAZON_SOCIAL, '(') - 1) || 
                        SUBSTR(B.V_RAZON_SOCIAL, INSTR(B.V_RAZON_SOCIAL, ')') + 1)
                    ELSE B.V_RAZON_SOCIAL 
                END AS V_RAZON_SOCIAL,
                A.V_DIRECCION
            FROM almacen a 
            INNER JOIN PLAZA B ON A.IID_PLAZA = B.IID_PLAZA
            WHERE A.S_STATUS = 1 AND A.IID_PLAZA <> 2
            """
            
            columnas, resultados = self.db_manager.ejecutar_consulta_segura(query)
            
            if not resultados:
                return None
            
            # Normalizar el mensaje para búsqueda sin acentos
            mensaje_normalizado = normalizar_texto(mensaje)
            
            # Buscar en nombres de plazas (normalizados)
            for fila in resultados:
                plaza = fila[0]
                if plaza:
                    plaza_normalizada = normalizar_texto(plaza)
                    if plaza_normalizada in mensaje_normalizado:
                        return plaza
            
            # Buscar en direcciones (normalizadas)
            for fila in resultados:
                direccion = fila[1]
                if direccion:
                    direccion_normalizada = normalizar_texto(direccion)
                    if direccion_normalizada in mensaje_normalizado:
                        return fila[0]  # Devolver la plaza correspondiente
            
            return None
            
        except Exception as e:
            logger.error(f"Error buscando ubicación en mensaje: {str(e)}")
            return None
    
    def _obtener_ubicaciones_generales(self, user_id):
        query = """
        SELECT DISTINCT 
            CASE 
                WHEN INSTR(B.V_RAZON_SOCIAL, '(') > 0 AND INSTR(B.V_RAZON_SOCIAL, ')') > 0
                    THEN SUBSTR(B.V_RAZON_SOCIAL, 1, INSTR(B.V_RAZON_SOCIAL, '(') - 1) || 
                    SUBSTR(B.V_RAZON_SOCIAL, INSTR(B.V_RAZON_SOCIAL, ')') + 1)
                ELSE B.V_RAZON_SOCIAL 
            END AS V_RAZON_SOCIAL
        FROM almacen a 
        INNER JOIN PLAZA B ON A.IID_PLAZA = B.IID_PLAZA
        WHERE A.S_STATUS = 1 AND A.IID_PLAZA <> 2
        ORDER BY V_RAZON_SOCIAL
        """
        
        columnas, resultados = self.db_manager.ejecutar_consulta_segura(query)
        
        if not resultados:
            return "No se encontraron ubicaciones en la base de datos."
        
        ubicaciones = [fila[0] for fila in resultados]
        self.context_manager.guardar_ubicaciones(user_id, ubicaciones)
        
        ubicaciones_formateadas = formatear_lista(ubicaciones, "location")
        
        respuesta = "📍 **Tenemos almacenes en las siguientes plazas:**\n\n"
        respuesta += f"{ubicaciones_formateadas}\n\n"
        respuesta += "¿Te gustaría conocer las direcciones específicas de alguna plaza en particular?"
        
        return respuesta
    
    def _obtener_ubicaciones_detalladas(self):
        query = """
        SELECT DISTINCT 
            CASE 
                WHEN INSTR(B.V_RAZON_SOCIAL, '(') > 0 AND INSTR(B.V_RAZON_SOCIAL, ')') > 0
                    THEN SUBSTR(B.V_RAZON_SOCIAL, 1, INSTR(B.V_RAZON_SOCIAL, '(') - 1) || 
                    SUBSTR(B.V_RAZON_SOCIAL, INSTR(B.V_RAZON_SOCIAL, ')') + 1)
                ELSE B.V_RAZON_SOCIAL 
            END AS V_RAZON_SOCIAL,
            A.V_DIRECCION,
            '+52 271-111-2222' as V_TELEFONO,
            '9am - 7pm ' as V_HORARIO
        FROM almacen a 
        INNER JOIN PLAZA B ON A.IID_PLAZA = B.IID_PLAZA
        WHERE A.S_STATUS = 1 AND A.IID_PLAZA <> 2
        ORDER BY V_RAZON_SOCIAL, V_DIRECCION
        """
        
        columnas, resultados = self.db_manager.ejecutar_consulta_segura(query)
        
        if not resultados:
            return "No se encontraron ubicaciones específicas en la base de datos."
        
        # Agrupar por estado/plaza
        ubicaciones_por_plaza = {}
        for fila in resultados:
            plaza = fila[0]
            direccion = fila[1]
            telefono = fila[2] or "No disponible"
            horario = fila[3] or "No disponible"
            
            if plaza not in ubicaciones_por_plaza:
                ubicaciones_por_plaza[plaza] = []
            
            ubicaciones_por_plaza[plaza].append({
                'direccion': direccion,
                'telefono': telefono,
                'horario': horario
            })
        
        respuesta = "📍 **Ubicaciones específicas de nuestras instalaciones:**\n\n"
        
        for plaza, ubicaciones in ubicaciones_por_plaza.items():
            respuesta += f"🏢 **{plaza}:**\n"
            for i, ubicacion in enumerate(ubicaciones, 1):
                respuesta += f"   {i}. {ubicacion['direccion']}\n"
                if ubicacion['telefono'] != "No disponible":
                    respuesta += f"     📞 Teléfono: {ubicacion['telefono']}\n"
                if ubicacion['horario'] != "No disponible":
                    respuesta += f"     ⏰ Horario: {ubicacion['horario']}\n"
                respuesta += "\n"
        
        return respuesta
    
    def _obtener_detalles_ubicacion_especifica(self, ubicacion):
        try:
            # Normalizar la ubicación para búsqueda sin acentos
            ubicacion_normalizada = normalizar_texto(ubicacion)
            
            query = """
            SELECT 
                CASE 
                    WHEN INSTR(B.V_RAZON_SOCIAL, '(') > 0 AND INSTR(B.V_RAZON_SOCIAL, ')') > 0
                        THEN SUBSTR(B.V_RAZON_SOCIAL, 1, INSTR(B.V_RAZON_SOCIAL, '(') - 1) || 
                        SUBSTR(B.V_RAZON_SOCIAL, INSTR(B.V_RAZON_SOCIAL, ')') + 1)
                    ELSE B.V_RAZON_SOCIAL 
                END AS V_RAZON_SOCIAL,
                A.V_DIRECCION,
                '+52 271-111-2222' as V_TELEFONO,
                '9am - 7pm ' as V_HORARIO
            FROM almacen a 
            INNER JOIN PLAZA B ON A.IID_PLAZA = B.IID_PLAZA
            WHERE A.S_STATUS = 1 
            AND (LOWER(B.V_RAZON_SOCIAL) LIKE '%' || LOWER(:1) || '%' 
                OR LOWER(A.V_DIRECCION) LIKE '%' || LOWER(:2) || '%')
            ORDER BY V_RAZON_SOCIAL, V_DIRECCION
            """
            
            # Buscar primero con texto original, luego con normalizado
            columnas, resultados = self.db_manager.ejecutar_consulta_segura(
                query, [ubicacion, ubicacion]
            )
            
            # Si no hay resultados, buscar con texto normalizado
            if not resultados:
                columnas, resultados = self.db_manager.ejecutar_consulta_segura(
                    query, [ubicacion_normalizada, ubicacion_normalizada]
                )

            if not resultados:
                return f"❌ No se encontraron almacenes en la ubicación '{ubicacion}'. ¿Te gustaría ver todas nuestras ubicaciones disponibles?"
            
            respuesta = f"📍 **Almacenes en {ubicacion.upper()}:**\n\n"
            
            for fila in resultados:
                plaza = fila[0]
                direccion = fila[1]
                telefono = fila[2] or "No disponible"
                horario = fila[3] or "No disponible"
                
                respuesta += f"🏢 **{plaza}**\n"
                respuesta += f"   📍 {direccion}\n"
                if telefono != "No disponible":
                    respuesta += f"   📞 {telefono}\n"
                if horario != "No disponible":
                    respuesta += f"   ⏰ {horario}\n"
                respuesta += "\n"
            
            return respuesta
            
        except Exception as e:
            logger.error(f"Error obteniendo detalles de ubicación '{ubicacion}': {str(e)}")
            return f"❌ Error al obtener información de la ubicación '{ubicacion}'."
        
    def obtener_todas_las_ubicaciones(self):
        """Método público para obtener todas las ubicaciones sin formato de respuesta"""
        try:
            query = """
            SELECT DISTINCT 
                CASE 
                    WHEN INSTR(B.V_RAZON_SOCIAL, '(') > 0 AND INSTR(B.V_RAZON_SOCIAL, ')') > 0
                        THEN SUBSTR(B.V_RAZON_SOCIAL, 1, INSTR(B.V_RAZON_SOCIAL, '(') - 1) || 
                        SUBSTR(B.V_RAZON_SOCIAL, INSTR(B.V_RAZON_SOCIAL, ')') + 1)
                    ELSE B.V_RAZON_SOCIAL 
                END AS V_RAZON_SOCIAL
            FROM almacen a 
            INNER JOIN PLAZA B ON A.IID_PLAZA = B.IID_PLAZA
            WHERE A.S_STATUS = 1 AND A.IID_PLAZA <> 2
            ORDER BY V_RAZON_SOCIAL
            """
            
            columnas, resultados = self.db_manager.ejecutar_consulta_segura(query)
            
            if resultados:
                return [fila[0] for fila in resultados]
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error obteniendo todas las ubicaciones: {str(e)}")
            return []