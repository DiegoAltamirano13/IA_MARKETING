# data/servicios_data.py
# Información de horarios
HORARIOS_ATENCION = {
    'titulo': 'Horarios de Atención ARGO',
    'atencion_clientes': {
        'dias': 'Lunes a viernes',
        'horario': '9:00 a 18:00 hrs',
        'sabados': 'Sábados: 9:00 a 13:00 hrs'
    },
    'cargas_descargas': {
        'dias': 'Lunes a viernes',
        'horario': '9:00 a 16:00 hrs',
        'sabados': 'Sábados: 9:00 a 12:00 hrs'
    }
}

# Información de mercancías no susceptibles
MERCANCIAS_NO_SUSCEPTIBLES = {
    'titulo': 'Mercancías No Susceptibles de Almacenaje en Depósito Fiscal',
    'introduccion': 'En México, las mercancías que NO pueden destinarse al régimen de Depósito Fiscal están listadas por la autoridad en el Anexo 18 de las RGCE (fundamento del art. 123 de la Ley Aduanera).',
    'lista_no_permitidas': [
        'Armas y municiones',
        'Explosivos',
        'Materiales radioactivos/radiactivos, nucleares y contaminantes',
        'Precursores químicos y químicos esenciales',
        'Piedras y metales preciosos (diamantes, rubíes, zafiros, esmeraldas, perlas y joyería con metales/piedras preciosas)',
        'Relojes',
        'Artículos de jade, coral, marfil y ámbar',
        'Cigarros (Sector 9 del Anexo 10)',
        'Mercancías del Anexo 29 (listado específico de control)',
        'Azúcar de caña (partida 17.01 de la TIGIE)',
        'Textiles y calzado (capítulos 50 al 64 de la TIGIE)',
        'Juguetes de las partidas 95.03 y 95.04 cuando los introduzcan residentes en el extranjero',
        'Vehículos (con excepciones muy puntuales para ciertas fracciones/partidas)'
    ],
    'nota_textiles': 'En el caso de los textiles y calzado es posible almacenar en ARGO pero como mercancía nacional o nacionalizada, es decir, una vez pagados los impuestos.',
    'fundamento': 'Ley Aduanera, art. 123: faculta a la autoridad para señalar por reglas las mercancías no permitidas en Depósito Fiscal. Anexo 18 de las RGCE: contiene el listado detallado.'
}

# Actualizar PALABRAS_CLAVE para incluir nuevas categorías
PALABRAS_CLAVE = {
    'almacenamiento': ['almacenar', 'guardar', 'depósito', 'bodega', 'almacén', 'inventario', 'resguardo'],
    'logistica': ['logística', 'transporte', 'distribución', 'entregas', 'traslado', 'terrestre'],
    'aduanas': ['aduanal', 'importación', 'exportación', 'pedimento', 'fiscal', 'impuestos', 'aduanera'],
    'custodia': ['custodia', 'vigilancia', 'seguridad', 'protección', 'créditos', 'prendarios'],
    'acondicionamiento': ['acondicionamiento', 'etiquetas', 'marbetes', 'armado', 'pedidos', 'paquetes', 
                         'paletizado', 'emplayado', 'empacado', 'consolidación', 'desconsolidación'],
    'habilitacion': ['habilitación', 'facultades', 'instalaciones', 'clientes', 'extensivas'],
    'horarios': ['horario', 'horarios', 'atención', 'atencion', 'horas', 'abierto', 'cerrado', 
                'cargas', 'descargas', 'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado'],
    'restricciones': ['prohibido', 'no permitido', 'no almacenar', 'mercancía peligrosa', 'peligrosa',
                     'restricción', 'restringido', 'armas', 'explosivos', 'radioactivo', 'nuclear',
                     'químicos', 'preciosos', 'joyería', 'relojes', 'cigarros', 'textiles', 'calzado',
                     'vehículos', 'no susceptible', 'depósito fiscal']
}

# Lista expandida de palabras relacionadas con calzado y textiles
PALABRAS_CALZADO = [
    'zapato', 'zapatos', 'calzado', 'tenis', 'sneakers', 'deportivos', 
    'botas', 'botines', 'sandalia', 'sandalias', 'tacones', 'zapatilla',
    'zapatillas', 'plataforma', 'mocasín', 'mocasines', 'chancla', 'chanclas',
    'alpargata', 'alpargatas', 'huarache', 'huaraches', 'zapato deportivo',
    'calzado deportivo', 'zapato formal', 'calzado infantil'
]
PALABRAS_TEXTILES = [
    'textil', 'textiles', 'tela', 'telas', 'tejido', 'tejidos', 'prenda',
    'prendas', 'ropa', 'vestimenta', 'indumentaria', 'moda', 'confección',
    'costura', 'hilado', 'hilo', 'algodón', 'poliester', 'nylon', 'seda',
    'lana', 'lino', 'jeans', 'mezclilla', 'pantalón', 'pantalones', 'camisa',
    'camisas', 'blusa', 'blusas', 'vestido', 'vestidos', 'falda', 'faldas',
    'suéter', 'suéteres', 'chaqueta', 'chaquetas', 'abrigo', 'abrigos'
]

# Palabras clave para detección de servicios
PALABRAS_CLAVE = {
    'almacenamiento': ['almacenar', 'guardar', 'depósito', 'bodega', 'almacén', 'inventario', 'resguardo'],
    'logistica': ['logística', 'transporte', 'distribución', 'entregas', 'traslado', 'terrestre'],
    'aduanas': ['aduanal', 'importación', 'exportación', 'pedimento', 'fiscal', 'impuestos', 'aduanera'],
    'custodia': ['custodia', 'vigilancia', 'seguridad', 'protección', 'créditos', 'prendarios'],
    'acondicionamiento': ['acondicionamiento', 'etiquetas', 'marbetes', 'armado', 'pedidos', 'paquetes', 
                         'paletizado', 'emplayado', 'empacado', 'consolidación', 'desconsolidación'],
    'habilitacion': ['habilitación', 'facultades', 'instalaciones', 'clientes', 'extensivas']
}

# Información detallada de cada servicio
SERVICIOS_INFO = {
    'almacenamiento': {
        'nombre': 'Servicios de Almacenamiento ARGO',
        'descripcion_general': 'Ofrecemos diferentes tipos de almacenamiento:',
        'tipos': {
            'depósito fiscal': 'Almacenaje directo de aduana a nuestros almacenes, difiriendo el pago de impuestos por mercancías importadas y pagando según se retire la mercancía de nuestras instalaciones.',
            'almacenaje nacional': 'Administración y control de inventarios para el óptimo resguardo de mercancías nacionales o nacionalizadas, procurando la total coordinación y eficiencia en cada proyecto.',
            'general': 'Almacenamiento general para mercancías diversas',
            'controlado': 'Almacenamiento con control de temperatura y humedad',
            'peligroso': 'Almacenamiento para materiales peligrosos',
            'valor': 'Almacenamiento de alto valor y máxima seguridad'
        },
        'pregunta_final': '¿Qué tipo de mercancía necesitas almacenar o sobre qué servicio te gustaría más información?'
    },
    
    'logistica': {
        'nombre': 'Servicios de Logística ARGO',
        'descripcion_general': 'Ofrecemos soluciones integrales de transporte y distribución:',
        'tipos': {
            'Transporte y Distribución': 'Área especializada en logística del transporte terrestre, que ofrece alternativas de costo-servicio de acuerdo al traslado de mercancías.',
            'Distribución Nacional': 'Coordinación completa de la cadena de suministro para distribución en territorio nacional.',
            'Logística Internacional': 'Manejo de transporte y coordinación para operaciones de importación y exportación.'
        },
        'pregunta_final': '¿Para qué tipo de mercancía o trayecto necesitas servicio de logística?'
    },
    
    'aduanas': {
        'nombre': 'Servicios Aduanales ARGO',
        'descripcion_general': 'Contamos con expertise en procedimientos de importación/exportación bajo el marco de la Ley Aduanera:',
        'tipos': {
            'Depósito Fiscal': 'Almacenaje directo de aduana a nuestros almacenes, difiriendo el pago de impuestos por mercancías importadas',
            'Gestión de Pedimentos': 'Manejo completo de documentación aduanal',
            'Asesoría en Comercio Exterior': 'Consultoría especializada en normativa aduanera'
        },
        'pregunta_final': '¿Necesitas apoyo con algún procedimiento de importación o exportación específico?'
    },
    
    'custodia': {
        'nombre': 'Servicios de Custodia ARGO',
        'descripcion_general': 'Nuestros servicios cumplen con la Ley General de Títulos y Operaciones de Crédito:',
        'tipos': {
            'Custodia Física': 'Resguardo seguro de mercancías con sistemas de vigilancia avanzados',
            'Créditos Prendarios': 'Expedición de Certificados de Depósito para garantía crediticia',
            'Seguridad Integral': 'Monitoreo 24/7 y protocolos de seguridad certificados'
        },
        'pregunta_final': '¿Qué tipo de custodia o protección necesitas para tus mercancías?'
    },
    
    'acondicionamiento': {
        'nombre': 'Servicios de Acondicionamiento ARGO',
        'descripcion_general': 'Ofrecemos servicios de valor agregado para tu mercancía:',
        'tipos': {
            'Etiquetado y Marbetes': 'Colocación de etiquetas y marbetes personalizados',
            'Armado de Pedidos': 'Preparación y empaque de pedidos según especificaciones',
            'Paletizado y Emplayado': 'Preparación de mercancía para transporte seguro',
            'Consolidación': 'Agrupación de mercancías para optimización de espacio',
            'Desconsolidación': 'Separación y clasificación de mercancías consolidadas'
        },
        'pregunta_final': '¿Qué tipo de acondicionamiento necesitas para tus productos?'
    },
    
    'habilitacion': {
        'nombre': 'Habilitación Fiscal y Nacional ARGO',
        'descripcion_general': 'Hacemos extensivas nuestras facultades como Almacén General de Depósito:',
        'tipos': {
            'Habilitación Fiscal': 'Convierte tus instalaciones en Almacén Fiscal para recibir mercancías importadas directo de aduana, con diferimiento del pago de impuestos hasta por 24 meses',
            'Habilitación Nacional': 'Facultad para expedir Certificados de Depósito para la obtención de Créditos Prendarios'
        },
        'pregunta_final': '¿Te interesa conocer más sobre cómo habilitar tus instalaciones con ARGO?'
    }
}

# Respuesta general para cuando no se detecta un servicio específico
RESPUESTA_GENERAL = {
    'titulo': 'Servicios ARGO - Soluciones Integrales de Logística',
    'descripcion': 'Ofrecemos servicios especializados en:',
    'servicios': [
        '**Almacenamiento**: Depósito Fiscal, Almacenaje Nacional, controlado y de alto valor',
        '**Logística**: Transporte, distribución y gestión de cadena de suministro',
        '**Servicios Aduanales**: Expertise en importación/exportación y depósito fiscal',
        '**Custodia**: Seguridad avanzada y créditos prendarios',
        '**Acondicionamiento**: Etiquetado, armado de pedidos y preparación de mercancía',
        '**Habilitación**: Fiscal y nacional para tus propias instalaciones'
    ],
    'pregunta_final': '¿En qué servicio estás interesado o sobre cuál te gustaría más información?'
}