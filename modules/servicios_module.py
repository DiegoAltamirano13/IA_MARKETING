# modules/servicios_module.py

import logging
from database import DatabaseManager
from data.servicios_data import PALABRAS_CLAVE, SERVICIOS_INFO, RESPUESTA_GENERAL, HORARIOS_ATENCION, MERCANCIAS_NO_SUSCEPTIBLES

logger = logging.getLogger(__name__)

class ServiciosModule:
    def __init__(self, db_manager, context_manager):
        self.db_manager = db_manager
        self.context_manager = context_manager
        self.palabras_clave = PALABRAS_CLAVE
        self.servicios_info = SERVICIOS_INFO
        self.respuesta_general = RESPUESTA_GENERAL
        self.horarios_atencion = HORARIOS_ATENCION
        self.mercancias_no_susceptibles = MERCANCIAS_NO_SUSCEPTIBLES

    def procesar_con_tipo(self, mensaje, tipo_servicio, user_id, servicio_especifico=None):
        """
        Procesa la consulta con información pre-detecada por DeepSeek
        """
        logger.info(f"Procesando servicio: {tipo_servicio}, específico: {servicio_especifico}")
        
        # Mapear tipos de DeepSeek a nuestros servicios internos
        mapeo_tipos = {
            'ESPECIFICO': 'almacenamiento',  # Si DeepSeek dice ESPECIFICO, asumimos almacenamiento
            'GENERAL': 'almacenamiento',
            'ALMACENAMIENTO': 'almacenamiento',
            'LOGISTICA': 'logistica',
            'ADUANAS': 'aduanas',
            'CUSTODIA': 'custodia',
            'ACONDICIONAMIENTO': 'acondicionamiento',
            'HABILITACION': 'habilitacion'
        }

         # Normalizar el tipo de servicio
        tipo_normalizado = mapeo_tipos.get(tipo_servicio.upper(), tipo_servicio.lower())

        if tipo_servicio.upper() in ["ESPECIFICO", "ESPECIFICA"] and servicio_especifico:
            # Guardar en contexto el servicio específico consultado
            self.context_manager.guardar_contexto(
                user_id, 
                "ultimo_servicio_consultado", 
                servicio_especifico
            )
            return self._procesar_servicio_especifico(servicio_especifico, user_id)
            
        # Mapear los tipos detectados por DeepSeek a nuestras funciones internas
        mapeo_servicios = {
            'almacenamiento': self._procesar_servicio_generico,
            'logistica': self._procesar_servicio_generico,
            'aduanas': self._procesar_servicio_generico,
            'custodia': self._procesar_servicio_generico,
            'acondicionamiento': self._procesar_servicio_generico,
            'habilitacion': self._procesar_servicio_generico,
            'horarios': self._procesar_horarios,
            'restricciones': self._procesar_restricciones
        }

        if tipo_normalizado in self.servicios_info:
            # Guardar en contexto el servicio consultado
            self.context_manager.guardar_contexto(user_id, "ultimo_servicio_consultado", servicio_especifico if servicio_especifico else tipo_normalizado)
            return self._procesar_servicio_generico(mensaje, user_id, tipo_normalizado, servicio_especifico)
        
        # Si tenemos un tipo específico detectado, usarlo
        if tipo_normalizado in mapeo_servicios:
            if tipo_normalizado in ['horarios', 'restricciones']:
                return mapeo_servicios[tipo_normalizado](mensaje, user_id)
            else:
                return self._procesar_servicio_generico(mensaje, user_id, tipo_normalizado, servicio_especifico)
        
        # Si no, procesar normalmente
        return self.procesar(mensaje, user_id)
    
    def _procesar_servicio_especifico(self, servicio_especifico, user_id):
        """
        Procesa servicios específicos detectados por DeepSeek
        """
        servicio_especifico_lower = servicio_especifico.lower()
        
        # Listas expandidas de palabras relacionadas
        palabras_calzado = [
            'zapato', 'zapatos', 'calzado', 'tenis', 'sneakers', 'deportivos', 
            'botas', 'botines', 'sandalia', 'sandalias', 'tacones', 'zapatilla',
            'zapatillas', 'plataforma', 'mocasín', 'mocasines', 'chancla', 'chanclas',
            'alpargata', 'alpargatas', 'huarache', 'huaraches', 'zapato deportivo',
            'calzado deportivo', 'zapato formal', 'calzado infantil'
        ]
        
        palabras_textiles = [
            'textil', 'textiles', 'tela', 'telas', 'tejido', 'tejidos', 'prenda',
            'prendas', 'ropa', 'vestimenta', 'indumentaria', 'moda', 'confección',
            'costura', 'hilado', 'hilo', 'algodón', 'poliester', 'nylon', 'seda',
            'lana', 'lino', 'jeans', 'mezclilla', 'pantalón', 'pantalones', 'camisa',
            'camisas', 'blusa', 'blusas', 'vestido', 'vestidos', 'falda', 'faldas',
            'suéter', 'suéteres', 'chaqueta', 'chaquetas', 'abrigo', 'abrigos'
        ]
        
        # Verificar si es calzado
        if any(palabra in servicio_especifico_lower for palabra in palabras_calzado):
            return self._procesar_almacenamiento_textiles_calzado(servicio_especifico)
        
        # Verificar si es textil
        if any(palabra in servicio_especifico_lower for palabra in palabras_textiles):
            return self._procesar_almacenamiento_textiles_calzado(servicio_especifico)
        
        # Buscar en todos los servicios el tipo específico
        for servicio, servicio_data in self.servicios_info.items():
            for nombre_servicio, descripcion in servicio_data['tipos'].items():
                if servicio_especifico_lower in nombre_servicio.lower():
                    respuesta = f"**{nombre_servicio.upper()} - ARGO**\n\n"
                    respuesta += f"{descripcion}\n\n"
                    respuesta += servicio_data['pregunta_final']
                    
                    # Guardar contexto
                    self.context_manager.guardar_contexto(
                        user_id, 
                        f"interes_{servicio}",
                        f"usuario preguntando sobre {nombre_servicio}"
                    )
                    return respuesta
        
        # Si no se encuentra el servicio específico, dar respuesta general
        return self._respuesta_general_servicios()

    def _procesar_servicio_generico(self, mensaje, user_id, tipo_servicio, servicio_especifico=None):
        """
        Procesa cualquier servicio usando la estructura de datos externa
        """
        if tipo_servicio not in self.servicios_info:
            return self._respuesta_general_servicios()
        
        servicio_data = self.servicios_info[tipo_servicio]
        
        # Si se especificó un servicio concreto, dar información detallada
        if servicio_especifico:
            servicio_especifico_lower = servicio_especifico.lower()
            
            # Listas expandidas para mejor detección
            palabras_calzado = ['zapato', 'zapatos', 'calzado', 'tenis', 'botas', 'sandalias']
            palabras_textiles = ['textil', 'tela', 'ropa', 'prenda', 'vestimenta']
            
            # Caso especial para consultas sobre almacenamiento de textiles/calzado
            if tipo_servicio == 'almacenamiento' and (
                any(palabra in servicio_especifico_lower for palabra in palabras_calzado) or
                any(palabra in servicio_especifico_lower for palabra in palabras_textiles)
            ):
                return self._procesar_almacenamiento_textiles_calzado(servicio_especifico)
                
            for nombre_servicio, descripcion in servicio_data['tipos'].items():
                if servicio_especifico_lower in nombre_servicio.lower():
                    respuesta = f"**{nombre_servicio.upper()} - ARGO**\n\n"
                    respuesta += f"{descripcion}\n\n"
                    respuesta += servicio_data['pregunta_final']
                    
                    # Guardar contexto
                    self.context_manager.guardar_contexto(
                        user_id, 
                        f"interes_{tipo_servicio}",
                        f"usuario preguntando sobre {nombre_servicio}"
                    )
                    return respuesta
        
        # Respuesta general del servicio
        respuesta = f"**{servicio_data['nombre']}**\n\n"
        respuesta += f"{servicio_data['descripcion_general']}\n\n"
        
        for nombre_servicio, descripcion in servicio_data['tipos'].items():
            respuesta += f"• **{nombre_servicio.upper()}**: {descripcion}\n"
        
        respuesta += f"\n{servicio_data['pregunta_final']}"
        
        # Guardar contexto
        self.context_manager.guardar_contexto(
            user_id, 
            f"interes_{tipo_servicio}", 
            f"usuario preguntando sobre servicios de {tipo_servicio}"
        )
        
        return respuesta

    def _procesar_horarios(self, mensaje, user_id):
        """
        Procesa consultas sobre horarios de atención
        """
        respuesta = f"**{self.horarios_atencion['titulo']}**\n\n"
        
        respuesta += "📞 **Atención a clientes:**\n"
        respuesta += f"• {self.horarios_atencion['atencion_clientes']['dias']}: {self.horarios_atencion['atencion_clientes']['horario']}\n"
        respuesta += f"• {self.horarios_atencion['atencion_clientes']['sabados']}\n\n"
        
        respuesta += "🚚 **Cargas y descargas:**\n"
        respuesta += f"• {self.horarios_atencion['cargas_descargas']['dias']}: {self.horarios_atencion['cargas_descargas']['horario']}\n"
        respuesta += f"• {self.horarios_atencion['cargas_descargas']['sabados']}\n\n"
        
        respuesta += "¿Necesitas información adicional sobre nuestros servicios?"
        
        # Guardar contexto
        self.context_manager.guardar_contexto(
            user_id, 
            "interes_horarios", 
            "usuario preguntando sobre horarios de atención"
        )
        
        return respuesta

    def _procesar_restricciones(self, mensaje, user_id):
        """
        Procesa consultas sobre mercancías no susceptibles de almacenaje
        """
        respuesta = f"**{self.mercancias_no_susceptibles['titulo']}**\n\n"
        respuesta += f"{self.mercancias_no_susceptibles['introduccion']}\n\n"
        
        respuesta += "**Mercancías NO permitidas en Depósito Fiscal:**\n"
        for item in self.mercancias_no_susceptibles['lista_no_permitidas']:
            respuesta += f"• {item}\n"
        
        respuesta += f"\n💡 **Nota importante:** {self.mercancias_no_susceptibles['nota_textiles']}\n\n"
        respuesta += f"**Fundamento legal:** {self.mercancias_no_susceptibles['fundamento']}\n\n"
        respuesta += "Para mercancías nacionales o nacionalizadas (impuestos pagados), contamos con servicios de almacenaje nacional. ¿Te interesa conocer más?"
        
        # Guardar contexto
        self.context_manager.guardar_contexto(
            user_id, 
            "interes_restricciones", 
            "usuario preguntando sobre mercancías no susceptibles"
        )
        
        return respuesta

    def puede_manejar(self, mensaje):
        mensaje_lower = mensaje.lower()
        return any(
            any(palabra in mensaje_lower for palabra in palabras) 
            for servicio, palabras in self.palabras_clave.items()
        )

    def procesar(self, mensaje, user_id):
        mensaje_lower = mensaje.lower()
        
        # Determinar tipo de servicio basado en palabras clave
        for servicio, palabras in self.palabras_clave.items():
            if any(palabra in mensaje_lower for palabra in palabras):
                if servicio in ['horarios', 'restricciones']:
                    # Para horarios y restricciones, usar métodos específicos
                    if servicio == 'horarios':
                        return self._procesar_horarios(mensaje, user_id)
                    else:
                        return self._procesar_restricciones(mensaje, user_id)
                else:
                    # Para otros servicios, usar el método genérico
                    return self._procesar_servicio_generico(mensaje, user_id, servicio)
        
        return self._respuesta_general_servicios()

    def _respuesta_general_servicios(self):
        respuesta = f"**{self.respuesta_general['titulo']}**\n\n"
        respuesta += f"{self.respuesta_general['descripcion']}\n\n"
        
        for servicio in self.respuesta_general['servicios']:
            respuesta += f"• {servicio}\n"
        
        respuesta += f"\n{self.respuesta_general['pregunta_final']}"
        
        return respuesta

    def _procesar_almacenamiento_textiles_calzado(self, producto_especifico):
        """
        Procesa consultas específicas sobre almacenamiento de textiles y calzado
        """
        # Determinar el tipo de producto para personalizar el mensaje
        palabras_calzado = ['zapato', 'calzado', 'tenis', 'bota', 'sandalia']
        palabras_textiles = ['textil', 'tela', 'ropa', 'prenda', 'vestimenta']
        
        tipo_producto = "textiles y calzado"
        if any(palabra in producto_especifico.lower() for palabra in palabras_calzado):
            tipo_producto = "calzado"
        elif any(palabra in producto_especifico.lower() for palabra in palabras_textiles):
            tipo_producto = "textiles"
        
        respuesta = f"**ALMACENAJE DE {tipo_producto.upper()} - ARGO**\n\n"
        
        respuesta += f"Le informo que sí es posible almacenar {producto_especifico} en nuestras instalaciones. "
        respuesta += "Como Almacén General de Depósito autorizado por la SHCP, podemos recibir:\n\n"
        
        respuesta += "✅ **Mercancía nacional o nacionalizada**: Una vez pagados los impuestos de importación\n"
        respuesta += "✅ **Bajo el régimen de almacenaje nacional**: Con todos los beneficios de seguridad y custodia\n\n"
        
        respuesta += "**Importante**: Para textiles y calzado de importación, es necesario:\n"
        respuesta += "• Que los impuestos de importación estén pagados\n"
        respuesta += "• Contar con la documentación aduanal completa\n"
        respuesta += "• La mercancía debe estar nacionalizada\n\n"
        
        respuesta += "**No podemos recibir** textiles o calzado bajo régimen de Depósito Fiscal (diferimiento de impuestos) "
        respuesta += "según lo establecido en el Anexo 18 de las RGCE.\n\n"
        
        respuesta += "¿Le interesa conocer más sobre nuestros servicios de almacenaje nacional o necesita cotización?"
        
        return respuesta