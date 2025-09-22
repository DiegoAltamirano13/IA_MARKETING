import logging
import re
from data.ubicaciones_data import UBICACIONES, CIUDADES_UBICACIONES, PLAZAS

logger = logging.getLogger(__name__)

class UbicacionesModule:
    def __init__(self, db_manager, context_manager):
        self.context_manager = context_manager
        self.ubicaciones = UBICACIONES
        self.ciudades_ubicaciones = CIUDADES_UBICACIONES
        self.plazas = PLAZAS

    def puede_manejar(self, mensaje):
        """Determina si el mensaje es sobre ubicaciones"""
        mensaje_lower = mensaje.lower()
        palabras_clave = [
            'ubicacion', 'ubicación', 'ubicaciones', 'donde', 'dónde',
            'sucursal', 'sucursales', 'almacén', 'almacen', 'bodega',
            'direccion', 'dirección', 'maps', 'mapa', 'google maps',
            'córdoba', 'veracruz', 'puebla', 'méxico', 'cdmx',
            'querétaro', 'guadalajara', 'mérida', 'monterrey',
            'plaza', 'centro', 'corporativo'
        ]
        return any(palabra in mensaje_lower for palabra in palabras_clave)

    def procesar(self, mensaje, user_id):
        """Procesa mensajes sobre ubicaciones"""
        mensaje_lower = mensaje.lower()
        
        # Guardar contexto
        self.context_manager.guardar_contexto(user_id, "tema_consulta", "ubicaciones")
        
        # Detectar tipo de consulta
        if any(palabra in mensaje_lower for palabra in ['todos', 'todas', 'listado', 'lista', 'cuales', 'cuáles']):
            return self._procesar_consulta_general()
        
        elif any(palabra in mensaje_lower for palabra in ['cerca', 'cercano', 'cercana', 'próximo', 'proximo']):
            return self._procesar_ubicacion_cercana(mensaje, user_id)
        
        elif any(palabra in mensaje_lower for palabra in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', 
                                                         'primera', 'segunda', 'tercera', 'cuarta', 'quinta']):
            return self._procesar_por_referencia(mensaje)
        
        else:
            # Buscar por ciudad o ubicación específica
            return self._procesar_ubicacion_especifica(mensaje)

    def procesar_con_tipo(self, mensaje, tipo_consulta, user_id="default", ubicacion_extraida=None):
        """Procesa con tipo de consulta específico"""
        if tipo_consulta == "GENERAL":
            return self._procesar_consulta_general()
        elif tipo_consulta == "ESPECIFICA" and ubicacion_extraida:
            return self._buscar_ubicacion_por_nombre(ubicacion_extraida)
        elif tipo_consulta == "DETALLES" and ubicacion_extraida:
            return self._mostrar_detalles_completos(ubicacion_extraida)
        elif tipo_consulta == "REFERENCIA" and ubicacion_extraida:
            return self._procesar_por_referencia(ubicacion_extraida)
        else:
            return self.procesar(mensaje, user_id)

    def _procesar_consulta_general(self):
        """Muestra todas las ubicaciones disponibles"""
        respuesta = "📍 *UBICACIONES ARGO ALMACENADORA*\n\n"
        respuesta += "Tenemos presencia en las siguientes plazas:\n\n"
        
        for plaza in self.plazas:
            respuesta += f"🏢 *{plaza}*\n"
            ubicaciones_plaza = [u for u in self.ubicaciones.values() if u['plaza'] == plaza]
            for ubicacion in ubicaciones_plaza:
                respuesta += f"• {ubicacion['nombre']}\n"
            respuesta += "\n"
        
        respuesta += "¿Te interesa alguna ubicación en específico? Puedo darte todos los detalles."
        return respuesta

    def _procesar_ubicacion_cercana(self, mensaje, user_id):
        """Pregunta por la ubicación del usuario para recomendar la más cercana"""
        # Guardar contexto para seguimiento
        self.context_manager.guardar_contexto(user_id, "esperando_ubicacion", "true")
        
        return "Para recomendarte la ubicación más cercana, ¿podrías decirme en qué ciudad o estado te encuentras?"

    def _procesar_por_referencia(self, mensaje):
        """Procesa consultas por número de referencia"""
        mensaje_lower = mensaje.lower()
        
        # Mapeo de números a ubicaciones
        ubicaciones_lista = list(self.ubicaciones.keys())
        mapeo_numeros = {
            '1': 0, 'primera': 0, 'primero': 0,
            '2': 1, 'segunda': 1, 'segundo': 1,
            '3': 2, 'tercera': 2, 'tercero': 2,
            '4': 3, 'cuarta': 3, 'cuarto': 3,
            '5': 4, 'quinta': 4, 'quinto': 4,
            '6': 5, 'sexta': 5, 'sexto': 5,
            '7': 6, 'séptima': 6, 'septima': 6, 'séptimo': 6, 'septimo': 6,
            '8': 7, 'octava': 7, 'octavo': 7,
            '9': 8, 'novena': 8, 'noveno': 8,
            '10': 9, 'décima': 9, 'decima': 9, 'décimo': 9, 'decimo': 9
        }
        
        for palabra, indice in mapeo_numeros.items():
            if palabra in mensaje_lower:
                if indice < len(ubicaciones_lista):
                    ubicacion_key = ubicaciones_lista[indice]
                    return self._mostrar_detalles_completos(ubicacion_key)
                else:
                    return f"Solo tenemos {len(ubicaciones_lista)} ubicaciones disponibles."
        
        return "No entendí la referencia. ¿Podrías ser más específico?"

    def _procesar_ubicacion_especifica(self, mensaje):
        """Busca ubicación por nombre o ciudad"""
        mensaje_lower = mensaje.lower()
        
        # Buscar por nombre de ubicación
        for ubicacion_key, datos in self.ubicaciones.items():
            if ubicacion_key.lower() in mensaje_lower or datos['nombre'].lower() in mensaje_lower:
                return self._mostrar_detalles_completos(ubicacion_key)
        
        # Buscar por ciudad
        for ciudad, ubicaciones in self.ciudades_ubicaciones.items():
            if ciudad in mensaje_lower:
                if len(ubicaciones) == 1:
                    return self._mostrar_detalles_completos(ubicaciones[0])
                else:
                    return self._mostrar_ubicaciones_ciudad(ciudad, ubicaciones)
        
        # Si no encuentra, ofrecer ayuda
        return self._ofrecer_ayuda_ubicaciones()

    def _buscar_ubicacion_por_nombre(self, nombre_ubicacion):
        """Busca ubicación por nombre aproximado"""
        nombre_lower = nombre_ubicacion.lower()
        
        # Búsqueda exacta
        for ubicacion_key in self.ubicaciones.keys():
            if ubicacion_key.lower() == nombre_lower:
                return self._mostrar_detalles_completos(ubicacion_key)
        
        # Búsqueda parcial
        for ubicacion_key, datos in self.ubicaciones.items():
            if (nombre_lower in ubicacion_key.lower() or 
                nombre_lower in datos['nombre'].lower() or
                nombre_lower in datos['ciudad'].lower()):
                return self._mostrar_detalles_completos(ubicacion_key)
        
        return f"No encontré la ubicación '{nombre_ubicacion}'. ¿Podrías intentar con otro nombre?"

    def _mostrar_detalles_completos(self, ubicacion_key):
        """Muestra todos los detalles de una ubicación"""
        if ubicacion_key not in self.ubicaciones:
            return "Ubicación no encontrada."
        
        ubicacion = self.ubicaciones[ubicacion_key]
        
        respuesta = f"📍 *{ubicacion['nombre']}*\n\n"
        respuesta += f"🏢 *Plaza:* {ubicacion['plaza']}\n"
        respuesta += f"📮 *Dirección:* {ubicacion['direccion']}\n"
        respuesta += f"📦 *C.P.:* {ubicacion['cp']}\n"
        respuesta += f"🏙️ *Ciudad:* {ubicacion['ciudad']}\n"
        respuesta += f"🗺️ *Google Maps:* {ubicacion['maps']}\n\n"
        respuesta += "¿Necesitas información de otra ubicación?"
        
        return respuesta

    def _mostrar_ubicaciones_ciudad(self, ciudad, ubicaciones):
        """Muestra todas las ubicaciones de una ciudad"""
        respuesta = f"📍 *UBICACIONES EN {ciudad.upper()}*\n\n"
        
        for ubicacion_key in ubicaciones:
            ubicacion = self.ubicaciones[ubicacion_key]
            respuesta += f"🏢 *{ubicacion['nombre']}*\n"
            respuesta += f"📮 {ubicacion['direccion']}\n"
            respuesta += f"🗺️ {ubicacion['maps']}\n\n"
        
        respuesta += "¿Te interesa alguna en específico?"
        return respuesta

    def _ofrecer_ayuda_ubicaciones(self):
        """Ofrece ayuda para encontrar ubicaciones"""
        respuesta = "📍 *UBICACIONES ARGO*\n\n"
        respuesta += "Puedo ayudarte a encontrar nuestras ubicaciones. Puedes preguntar por:\n\n"
        respuesta += "• 'Ubicaciones en [ciudad]' (ej: Ubicaciones en Veracruz)\n"
        respuesta += "• 'Almacén [nombre]' (ej: Almacén Ulúa)\n"
        respuesta += "• 'Todas las ubicaciones'\n"
        respuesta += "• 'Ubicación más cercana'\n\n"
        respuesta += "¿En qué te puedo ayudar?"
        
        return respuesta

    def procesar_ubicacion_usuario(self, ciudad, user_id):
        """Procesa la ubicación proporcionada por el usuario"""
        ciudad_lower = ciudad.lower()
        
        # Buscar ubicaciones en esa ciudad
        ubicaciones_encontradas = []
        
        for ciudad_map, ubicaciones in self.ciudades_ubicaciones.items():
            if ciudad_lower in ciudad_map:
                ubicaciones_encontradas.extend(ubicaciones)
        
        # También buscar en las ciudades de las ubicaciones
        for ubicacion_key, datos in self.ubicaciones.items():
            if ciudad_lower in datos['ciudad'].lower():
                ubicaciones_encontradas.append(ubicacion_key)
        
        if ubicaciones_encontradas:
            if len(ubicaciones_encontradas) == 1:
                return self._mostrar_detalles_completos(ubicaciones_encontradas[0])
            else:
                return self._mostrar_ubicaciones_ciudad(ciudad, ubicaciones_encontradas)
        else:
            return f"No tenemos ubicaciones en {ciudad}. Te recomiendo consultar nuestras ubicaciones disponibles."