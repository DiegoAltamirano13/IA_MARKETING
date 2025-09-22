import json
import time
import logging
from datetime import datetime, timedelta

class ContextManager:
    def __init__(self):
        self.conversaciones = {}  # user_id -> {contexto, historial, timestamp}
        
    def obtener_contexto(self, user_id):
        """Obtiene el contexto de un usuario"""
        if user_id not in self.conversaciones:
            return {}
        return self.conversaciones[user_id].get('contexto', {})
    
    def obtener_historial(self, user_id):
        """Obtiene el historial de mensajes del usuario"""
        if user_id not in self.conversaciones:
            return []
        return self.conversaciones[user_id].get('historial', [])
    
    def agregar_mensaje(self, user_id, rol, mensaje):
        """Agrega un mensaje al historial de conversación"""
        if user_id not in self.conversaciones:
            self.conversaciones[user_id] = {
                'historial': [],
                'contexto': {},
                'timestamp': time.time()
            }
        
        self.conversaciones[user_id]['historial'].append({
            'rol': rol,
            'mensaje': mensaje,
            'timestamp': datetime.now().isoformat()
        })
        
        # Limpiar conversaciones antiguas (más de 24 horas)
        self._limpiar_conversaciones_antiguas()
    
    def guardar_contexto(self, user_id, clave, valor):
        """Guarda información contextual específica"""
        if user_id not in self.conversaciones:
            self.conversaciones[user_id] = {
                'historial': [],
                'contexto': {},
                'timestamp': time.time()
            }
        
        self.conversaciones[user_id]['contexto'][clave] = {
            'valor': valor,
            'timestamp': datetime.now().isoformat()
        }
    
    def _limpiar_conversaciones_antiguas(self):
        """Elimina conversaciones con más de 24 horas de antigüedad"""
        ahora = time.time()
        user_ids_a_eliminar = []
        
        for user_id, datos in self.conversaciones.items():
            if ahora - datos['timestamp'] > 86400:  # 24 horas
                user_ids_a_eliminar.append(user_id)
        
        for user_id in user_ids_a_eliminar:
            del self.conversaciones[user_id]
    
    def obtener_historial_completo(self, user_id):
        """Obtiene el historial completo de mensajes"""
        return self.obtener_historial(user_id)
    
    def limpiar_contexto_usuario(self, user_id):
        """Limpia el contexto de un usuario específico"""
        if user_id in self.conversaciones:
            del self.conversaciones[user_id]