"""Configuración: todo secreto sale de variables de entorno (nunca del repo).

Lo que no es secreto (negocios, embudos, nombres de calendarios, objetivos por defecto) vive en NEGOCIOS.
"""
import json
import os


def _json_env(nombre, defecto):
    crudo = os.environ.get(nombre)
    if not crudo:
        return defecto
    try:
        return json.loads(crudo)
    except ValueError:
        raise RuntimeError(f'La variable {nombre} no es JSON válido')


class Config:
    def __init__(self, **extra):
        e = os.environ
        self.SERVICIO = e.get('SERVICIO', 'suite')
        self.DEV = e.get('DEV_LOGIN') == '1'
        self.SECRET_KEY = e.get('SECRET_KEY') or ('dev-solo-local' if self.DEV else None)
        self.DATABASE_URL = e.get('DATABASE_URL', 'sqlite:///suite-local.db')
        if self.DATABASE_URL.startswith('postgres://'):  # Render entrega postgres://; SQLAlchemy quiere postgresql+psycopg://
            self.DATABASE_URL = 'postgresql+psycopg://' + self.DATABASE_URL[len('postgres://'):]
        elif self.DATABASE_URL.startswith('postgresql://'):
            self.DATABASE_URL = 'postgresql+psycopg://' + self.DATABASE_URL[len('postgresql://'):]
        self.ADMINS = [x.strip().lower() for x in e.get('ADMINS', '').split(',') if x.strip()]
        # Negocios de cada admin (los que no están acá ven todos): {"luis@...": ["tpa"]}
        self.ADMINS_NEGOCIOS = {k.lower(): v for k, v in _json_env('ADMINS_NEGOCIOS', {}).items()}
        # El worker corre dentro del servidor web (hosting de un solo proceso, gratis)
        self.WORKER_EN_WEB = e.get('WORKER_EN_WEB') == '1'
        self.DOMINIO_ADMIN = e.get('DOMINIO_ADMIN', '')
        self.GOOGLE_CLIENT_ID = e.get('GOOGLE_CLIENT_ID', '')
        self.GOOGLE_CLIENT_SECRET = e.get('GOOGLE_CLIENT_SECRET', '')
        # CRM: un token por subcuenta (location id -> token). Lectura y escritura por separado.
        self.CRM_TOKENS = {k: v for k, v in _json_env('CRM_TOKENS', {}).items() if not k.startswith('PEGAR')}
        # Forma simple (una línea por dato): GHL_<NOMBRE>_ID=... y GHL_<NOMBRE>_TOKEN=...
        for k, v in e.items():
            if k.startswith('GHL_') and k.endswith('_ID') and v.strip():
                token = e.get(k[:-3] + '_TOKEN', '').strip()
                if token:
                    self.CRM_TOKENS[v.strip()] = token
        self.CRM_TOKENS_ESCRITURA = _json_env('CRM_TOKENS_ESCRITURA', {})
        self.META_ACCESS_TOKEN = e.get('META_ACCESS_TOKEN', '').strip()
        # Un token por portfolio comercial: META_ACCESS_TOKEN y además META_ACCESS_TOKEN_2, _3, …
        self.META_TOKENS = [t for t in [self.META_ACCESS_TOKEN] + [e[k].strip() for k in sorted(e)
                            if k.startswith('META_ACCESS_TOKEN_')] if t and not t.startswith('PEGAR')]
        self.META_API_VERSION = e.get('META_API_VERSION', 'v21.0')
        # YouTube = Google Ads API (campañas de video)
        self.GOOGLE_ADS_DEVELOPER_TOKEN = e.get('GOOGLE_ADS_DEVELOPER_TOKEN', '')
        self.GOOGLE_ADS_REFRESH_TOKEN = e.get('GOOGLE_ADS_REFRESH_TOKEN', '')
        self.GOOGLE_ADS_LOGIN_CUSTOMER_ID = e.get('GOOGLE_ADS_LOGIN_CUSTOMER_ID', '')
        self.GOOGLE_ADS_API_VERSION = e.get('GOOGLE_ADS_API_VERSION', 'v21')
        self.ZONA_HORARIA = e.get('ZONA_HORARIA', 'America/New_York')
        self.DIAS = int(e.get('DIAS', '90'))
        self.DIAS_PROXIMOS = int(e.get('DIAS_PROXIMOS', '14'))
        # Sin credenciales (ni Meta ni GHL), el worker publica datos de ejemplo para poder ver la suite
        self.DATOS_DEMO = e.get('DATOS_DEMO', '1' if not (self.META_TOKENS or self.CRM_TOKENS) else '0') == '1'
        self.TESTING = False
        for k, v in extra.items():
            setattr(self, k, v)
        if not self.SECRET_KEY:
            raise RuntimeError('Falta SECRET_KEY')


# objetivo_costo_cita = valor de fábrica: el admin lo cambia en Indicadores (tabla indicadores).
# Embudos por negocio. El primer paso con cita es el que se mide en el Panel de campañas.
# calendarios: se reconocen por nombre (sin mayúsculas ni acentos). Ajustar a los nombres reales de GHL.
NEGOCIOS = {
    'plastia': {
        'nombre': 'Plastia Partners',
        'corto': 'Plastia', 'cuentas': 'Clínicas', 'vendedor': 'Closer', 'moneda': 'USD',
        'comision_pct': 25, 'closer_pct': 25, 'moneda_cuentas': 'COP',  # las clínicas venden en pesos colombianos
        'plan': {'setup': 750, 'fee': 0},  # 25% de (venta − costos − pauta); el closer, 25% de eso
        'embudos': {
            'valoracion': {
                'nombre': 'Valoración pagada',
                'paso': 'calificacion',  # llamada de evaluación con el closer
                'claves': ['costo_lead', 'costo_cita', 'pct_asistencia', 'costo_asistente'],
                'objetivo_costo_cita': 60,
            },
        },
        'agencia': {'nombre': 'Ventas Plastia', 'paso': 'calificacion', 'objetivo_costo_cita': 90,
                    'descripcion': 'llamadas con dueños de clínicas'},
        'calendarios': {
            'calificacion': ['evaluacion', 'llamada', 'orientacion'],
            'principal': ['valoracion', 'consulta'],
            'entrada': [],
            'excluir': ['prueba', 'test', 'copy of'],
        },
    },
    'tpa': {
        'nombre': 'Top Producer Acquisition',
        'corto': 'TPA', 'cuentas': 'Clientes', 'vendedor': 'Setter', 'moneda': 'USD', 'moneda_cuentas': 'USD',
        'plan': {'setup': 4000, 'fee': 750}, 'socios': [['Mateo', 50], ['Luis', 50]], 'pagador_pauta': 'Luis',
        'embudos': {
            'citas': {
                'nombre': 'Citas de realtors',
                'paso': 'principal',  # el agente de IA o el setter agenda la cita con el realtor
                'claves': ['costo_lead', 'costo_cita', 'pct_asistencia', 'costo_asistente'],
                'objetivo_costo_cita': 45,
            },
        },
        'agencia': {'nombre': 'Ventas TPA', 'paso': 'calificacion', 'objetivo_costo_cita': 120,
                    'descripcion': 'llamadas con realtors'},
        'calendarios': {
            'calificacion': ['discovery', 'estrategica', 'strategy', 'llamada de venta'],
            'principal': ['listing', 'buyer', 'consultation', 'showing', 'cita'],
            'entrada': [],
            'excluir': ['prueba', 'test', 'copy of'],
        },
    },
}

ROLES = ('admin', 'vendedor', 'operador', 'cuenta')
