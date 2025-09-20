from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class BaseModule(ABC):
    def __init__(self, db_manager, context_manager):
        self.db_manager = db_manager
        self.context_manager = context_manager
    
    @abstractmethod
    def puede_manejar(self, mensaje):
        """Determina si este módulo puede manejar el mensaje"""
        pass
    
    @abstractmethod
    def procesar(self, mensaje, user_id):
        """Procesa el mensaje y devuelve una respuesta"""
        pass
    
    def get_name(self):
        """Retorna el nombre del módulo"""
        return self.__class__.__name__