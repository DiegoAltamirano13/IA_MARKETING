from .base_module import BaseModule

class InventarioModule(BaseModule):
    def puede_manejar(self, mensaje):
        mensaje_lower = mensaje.lower()
        palabras_clave = [
            'inventario', 'stock', 'producto', 'productos', 'existencia',
            'mercancía', 'mercancias', 'artículos', 'articulos', 'items'
        ]
        return any(palabra in mensaje_lower for palabra in palabras_clave)
    
    def procesar(self, mensaje, user_id):
        # Lógica específica para consultas de inventario
        return self._consultar_inventario(mensaje)
    
    def _consultar_inventario(self, mensaje):
        # Implementación de consultas a inventario
        pass