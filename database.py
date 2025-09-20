import oracledb
import logging
import re
import os
from config import ORACLE_USER, ORACLE_PASSWORD

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.connection = None
        self.conexion_activa = False
        # Configuración de conexión
        self.host = "10.10.2.197"
        self.port = 1526
        self.service_name = "ORACBA"
        
    def connect(self):
        """Establece conexión con la base de datos Oracle usando oracledb"""
        try:
            # Inicializar el cliente Oracle explícitamente (modo thick)
            try:
                oracledb.init_oracle_client()
                logger.info("Cliente Oracle inicializado correctamente")
            except Exception as e:
                logger.warning(f"Cliente Oracle ya inicializado: {str(e)}")
            
            # Conexión usando DSN (modo thick con cliente)
            dsn = oracledb.makedsn(self.host, self.port, service_name=self.service_name)
            
            self.connection = oracledb.connect(
                user=ORACLE_USER,
                password=ORACLE_PASSWORD,
                dsn=dsn
            )
            
            logger.info("Conexión a Oracle establecida correctamente (modo thick)")
            self.conexion_activa = True
            return True
            
        except Exception as e:
            logger.error(f"Error conectando a Oracle: {str(e)}")
            # Intentar modo thin como fallback
            try:
                self.connection = oracledb.connect(
                    user=ORACLE_USER,
                    password=ORACLE_PASSWORD,
                    host=self.host,
                    port=self.port,
                    service_name=self.service_name,
                    thick_mode=False
                )
                logger.info("Conexión a Oracle establecida correctamente (modo thin)")
                self.conexion_activa = True
                return True
            except Exception as thin_error:
                logger.error(f"Error en modo thin también: {str(thin_error)}")
                self.conexion_activa = False
                return False
            
    def disconnect(self):
        try:
            if self.connection:
                self.connection.close()
                self.connection = None
                print("Conexión cerrada correctamente")
        except Exception as e:
            print(f"Error al desconectar: {e}")
            # No lanzar excepción para no interrumpir el flujo
    
    def verificar_conexion(self):
        """Verifica si la conexión está activa"""
        if not self.conexion_activa:
            return self.connect()
        
        try:
            # Verificar conexión ejecutando una consulta simple
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM DUAL")
                cursor.fetchone()
            return True
        except:
            # Reconectar si falla la verificación
            self.disconnect()
            return self.connect()
    
    def es_consulta_segura(self, consulta):
        """
        Verifica que la consulta sea segura (solo SELECT)
        Bloquea cualquier operación de modificación de manera más estricta
        """
        # Normalizar la consulta (remover comentarios y espacios múltiples)
        consulta_limpia = re.sub(r'--.*?\n|/\*.*?\*/', '', consulta, flags=re.DOTALL)
        consulta_normalizada = ' '.join(consulta_limpia.strip().split()).upper()
        
        # Lista de palabras clave peligrosas (más completa)
        palabras_peligrosas = [
            'INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE',
            'TRUNCATE', 'MERGE', 'EXECUTE', 'EXEC', 'GRANT', 'REVOKE',
            'COMMIT', 'ROLLBACK', 'SAVEPOINT', 'LOCK', 'UNLOCK', 'PURGE',
            'DECLARE', 'BEGIN', 'CALL', 'ANALYZE', 'AUDIT', 'COMMENT',
            'EXPLAIN', 'FLASHBACK', 'NOAUDIT', 'RENAME', 'SET', 'SHUTDOWN',
            'UNDROP', 'WITH'
        ]
        
        # Verificar si la consulta contiene operaciones peligrosas
        for palabra in palabras_peligrosas:
            # Buscar la palabra como comando SQL independiente
            patron = rf'(^|\s|;){palabra}\s+'
            if re.search(patron, consulta_normalizada):
                logger.warning(f"Intento de operación peligrosa detectada: {palabra}")
                return False
        
        # Verificar que sea una consulta SELECT (más estricto)
        if not consulta_normalizada.startswith('SELECT'):
            logger.warning("Solo se permiten consultas SELECT")
            return False
        
        # Bloquear consultas con múltiples statements
        if ';' in consulta_normalizada and len(consulta_normalizada.split(';')) > 2:
            logger.warning("Múltiples statements detectados")
            return False
        
        # Bloquear consultas con UNION SELECT (podría ser SQL injection)
        if 'UNION' in consulta_normalizada and 'SELECT' in consulta_normalizada:
            # Permitir solo si es parte de una consulta legítima pero con validación adicional
            if not re.search(r'UNION\s+ALL\s+SELECT', consulta_normalizada):
                logger.warning("Patrón UNION SELECT detectado - posible inyección SQL")
                return False
        
        return True
    
    def ejecutar_consulta_segura(self, consulta, parametros=None):
        """
        Ejecuta una consulta SQL de manera segura (solo SELECT)
        con validaciones adicionales
        """
        # Verificar que la consulta sea segura
        if not self.es_consulta_segura(consulta):
            raise SecurityError("La consulta no es segura. Solo se permiten consultas SELECT.")
        
        # Validar parámetros para prevenir inyección
        if parametros:
            for param in parametros:
                if isinstance(param, str) and any(char in param for char in [';', '--', '/*', '*/', "'", '"']):
                    logger.warning("Parámetros con caracteres potencialmente peligrosos")
                    raise SecurityError("Parámetros no válidos")
        
        # Limitar el tamaño de la consulta
        if len(consulta) > 10000:  # 10KB máximo
            logger.warning("Consulta demasiado larga")
            raise SecurityError("Consulta demasiado larga")
        
        # Verificar conexión
        if not self.verificar_conexion():
            raise ConnectionError("No se pudo establecer conexión con la base de datos")
        
        try:
            with self.connection.cursor() as cursor:
                # Establecer timeout para la consulta
                cursor.callTimeout = 30000  # 30 segundos
                
                if parametros:
                    # Validar tipos de parámetros
                    valid_params = []
                    for param in parametros:
                        if isinstance(param, (str, int, float, type(None))):
                            valid_params.append(param)
                        else:
                            valid_params.append(str(param))
                    
                    cursor.execute(consulta, valid_params)
                else:
                    cursor.execute(consulta)
                
                # Limitar número de resultados (máximo 1000 filas)
                if cursor.description:
                    columnas = [col[0] for col in cursor.description]
                    resultados = cursor.fetchmany(1000)  # Máximo 1000 filas
                    return columnas, resultados
                else:
                    return None, cursor.rowcount
                    
        except oracledb.DatabaseError as e:
            error_msg = str(e)
            logger.error(f"Error de base de datos: {error_msg}")
            
            # Detectar errores específicos de Oracle
            if 'ORA-00942' in error_msg:  # tabla o vista no existe
                raise ValueError("La tabla o vista no existe")
            elif 'ORA-00936' in error_msg:  # expresión missing
                raise ValueError("Consulta mal formada")
            else:
                raise
        
        except Exception as e:
            logger.error(f"Error ejecutando consulta: {str(e)}")
            raise
    
    def obtener_estructura_tablas(self):
        """Obtiene la estructura de las tablas disponibles en la base de datos"""
        try:
            consulta = """
            SELECT table_name 
            FROM user_tables 
            WHERE table_name NOT LIKE 'BIN$%'  -- Excluir tablas en papelera
            ORDER BY table_name
            """
            columnas, resultados = self.ejecutar_consulta_segura(consulta)
            return [fila[0] for fila in resultados] if resultados else []
        except Exception as e:
            logger.error(f"Error obteniendo estructura de tablas: {str(e)}")
            return []
    
    def obtener_columnas_tabla(self, tabla_nombre):
        """Obtiene las columnas de una tabla específica de manera segura"""
        try:
            # Validar nombre de tabla (solo letras, números y _)
            if not re.match(r'^[A-Za-z0-9_]+$', tabla_nombre):
                raise ValueError("Nombre de tabla no válido")
                
            consulta = """
            SELECT column_name, data_type, data_length, nullable
            FROM user_tab_columns 
            WHERE table_name = :1 
            ORDER BY column_id
            """
            columnas, resultados = self.ejecutar_consulta_segura(consulta, [tabla_nombre.upper()])
            return resultados if resultados else []
        except Exception as e:
            logger.error(f"Error obteniendo columnas de la tabla {tabla_nombre}: {str(e)}")
            return []
    
    def obtener_datos_tabla(self, tabla_nombre, limite=10, where_clause=""):
        """Obtiene datos de una tabla específica con límite"""
        try:
            # Validar nombre de tabla
            if not re.match(r'^[A-Za-z0-9_]+$', tabla_nombre):
                raise ValueError("Nombre de tabla no válido")
            
            # Construir consulta de forma segura
            where_safe = ""
            if where_clause and re.match(r'^[A-Za-z0-9_=\s<>]+$', where_clause):
                where_safe = f"WHERE {where_clause}"
                
            consulta = f"SELECT * FROM {tabla_nombre} {where_safe} AND ROWNUM <= :1"
            columnas, resultados = self.ejecutar_consulta_segura(consulta, [limite])
            return columnas, resultados
        except Exception as e:
            logger.error(f"Error obteniendo datos de la tabla {tabla_nombre}: {str(e)}")
            return [], []
    
    def obtener_conteo_clientes(self):
        """Método específico para obtener el conteo de clientes"""
        try:
            # Buscar tabla de clientes
            tablas = self.obtener_estructura_tablas()
            tabla_clientes = next((t for t in tablas if 'CLIENTE' in t.upper() or 'CUSTOMER' in t.upper()), None)
            
            if tabla_clientes:
                consulta = f"SELECT COUNT(*) FROM {tabla_clientes}"
                columnas, resultados = self.ejecutar_consulta_segura(consulta)
                return resultados[0][0] if resultados else 0
            return 0
        except Exception as e:
            logger.error(f"Error obteniendo conteo de clientes: {str(e)}")
            return 0
    
    def obtener_metadata_base(self):
        """Obtiene metadata básica de la base de datos"""
        try:
            consultas = {
                'usuarios': "SELECT COUNT(*) FROM all_users",
                'tablas': "SELECT COUNT(*) FROM user_tables",
                'vistas': "SELECT COUNT(*) FROM user_views"
            }
            
            metadata = {}
            for key, consulta in consultas.items():
                try:
                    _, resultados = self.ejecutar_consulta_segura(consulta)
                    metadata[key] = resultados[0][0] if resultados else 0
                except:
                    metadata[key] = 'N/A'
            
            return metadata
        except Exception as e:
            logger.error(f"Error obteniendo metadata: {str(e)}")
            return {}

class SecurityError(Exception):
    """Excepción personalizada para errores de seguridad"""
    pass


# Ejemplo de uso
if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    # Crear instancia y conectar
    db_manager = DatabaseManager()
    if db_manager.connect():
        print("✅ Conexión exitosa!")
        
        # Probar algunas consultas
        tablas = db_manager.obtener_estructura_tablas()
        print(f"Tablas disponibles: {tablas[:5]}...")  # Mostrar primeras 5
        
        if tablas:
            # Mostrar columnas de la primera tabla
            columnas = db_manager.obtener_columnas_tabla(tablas[0])
            print(f"Columnas de {tablas[0]}: {columnas}")
            
            # Mostrar algunos datos
            cols, datos = db_manager.obtener_datos_tabla(tablas[0], 3)
            print(f"Datos de muestra: {datos}")
        
        db_manager.disconnect()
    else:
        print("❌ Error de conexión")