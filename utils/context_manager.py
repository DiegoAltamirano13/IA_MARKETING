from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class ContextManager:
    def __init__(self):
        self.contexto_ubicaciones = {}
        self.contexto_tiempo = {}
        self.tiempo_expiracion = timedelta(minutes=10)
    
    def guardar_ubicaciones(self, user_id, ubicaciones):
        self.contexto_ubicaciones[user_id] = ubicaciones
        self.contexto_tiempo[user_id] = datetime.now()
        logger.info(f"Contexto guardado para usuario {user_id}: {len(ubicaciones)} ubicaciones")
    
    def obtener_ubicaciones(self, user_id):
        self._limpiar_contexto_antiguo(user_id)
        ubicaciones = self.contexto_ubicaciones.get(user_id, [])  # ⬅️ PRIMERO obtén las ubicaciones
        logger.info(f"Ubicaciones recuperadas para {user_id}: {ubicaciones}")  # ⬅️ LUEGO las usas
        return ubicaciones
    
    def obtener_ubicacion_por_referencia(self, user_id, referencia):
        ubicaciones = self.obtener_ubicaciones(user_id)
        logger.info(f"Buscando referencia '{referencia}' para user {user_id}")

        if not ubicaciones:
            return None
        
        # Mapeo de referencias a números
        numeros = {
            'primera': 1, 'primero': 1, '1ra': 1, '1ro': 1, '1': 1,
            'segunda': 2, 'segundo': 2, '2da': 2, '2do': 2, '2': 2,
            'tercera': 3, 'tercero': 3, '3ra': 3, '3ro': 3, '3': 3,
            'cuarta': 4, 'cuarto': 4, '4ta': 4, '4to': 4, '4': 4,
            'quinta': 5, 'quinto': 5, '5ta': 5, '5to': 5, '5': 5,
            'última': -1, 'ultima': -1, 'último': -1, 'ultimo': -1
        }
        
        if referencia.lower() in numeros:
            indice = numeros[referencia.lower()]
            if indice == -1:  # Última
                return ubicaciones[-1] if ubicaciones else None
            elif 1 <= indice <= len(ubicaciones):
                return ubicaciones[indice - 1]
        
        # Búsqueda por nombre aproximado
        referencia_limpia = referencia.lower().strip()
        for ubicacion in ubicaciones:
            if referencia_limpia in ubicacion.lower():
                return ubicacion
        
        return None
    
    def _limpiar_contexto_antiguo(self, user_id):
        ahora = datetime.now()
        if user_id in self.contexto_tiempo:
            tiempo_transcurrido = ahora - self.contexto_tiempo[user_id]
            if tiempo_transcurrido > self.tiempo_expiracion:
                if user_id in self.contexto_ubicaciones:
                    del self.contexto_ubicaciones[user_id]
                if user_id in self.contexto_tiempo:
                    del self.contexto_tiempo[user_id]
                logger.info(f"Contexto limpiado para usuario {user_id}")