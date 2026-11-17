"""Base de datos (SQLAlchemy Core, sin ORM). SQLite en local, Postgres en Render."""
import datetime as dt
import json

from sqlalchemy import (JSON, Boolean, Column, Date, DateTime, Float, Integer, MetaData, String, Table, Text, create_engine,
                        insert, select, update)

meta = MetaData()


def ahora():
    """UTC sin zona (como lo guarda la base)."""
    return dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)


usuarios = Table(
    'usuarios', meta,
    Column('id', Integer, primary_key=True),
    Column('email', String(200), unique=True, nullable=False),
    Column('nombre', String(200), default=''),
    Column('rol', String(20), nullable=False),            # admin, vendedor, operador, cuenta
    Column('negocios', JSON, default=list),                # ['plastia', 'tpa']
    Column('cuentas', JSON, default=list),                 # ids de cuentas que ve (no admin)
    Column('menus', JSON, default=list),                   # menús visibles (vacío = defecto del rol)
    Column('activo', Boolean, default=True),               # nunca se borran: se desactivan
    Column('creado', DateTime, default=ahora),
    Column('ultimo_ingreso', DateTime),
)

# Cuentas = clientes de cada negocio (clínicas, realtors) y la subcuenta propia del negocio (propia=True)
cuentas = Table(
    'cuentas', meta,
    Column('id', Integer, primary_key=True),
    Column('negocio', String(30), nullable=False),
    Column('nombre', String(200), nullable=False),
    Column('grupo', String(60), default='Activas'),
    Column('propia', Boolean, default=False),
    Column('crm_location_id', String(80), default=''),
    Column('meta_cuentas', JSON, default=list),            # ['act_123', ...]
    Column('youtube_cuentas', JSON, default=list),         # ids de cliente de Google Ads
    Column('objetivo_costo_cita', Float),                  # si es nulo, el del embudo
    Column('activo', Boolean, default=True),
)

# Lo que publica el worker: datos:<negocio> (agregado, sin datos personales), privado:<negocio> (PII), estado
datos_panel = Table(
    'datos_panel', meta,
    Column('clave', String(80), primary_key=True),
    Column('valor', Text, nullable=False),
    Column('actualizado', DateTime, default=ahora),
)

# Metas que carga el admin en Indicadores (clave -> valor, por negocio). Nulo = sin meta (o el valor de fábrica).
indicadores = Table(
    'indicadores', meta,
    Column('negocio', String(30), primary_key=True),
    Column('clave', String(80), primary_key=True),
    Column('valor', Float),
    Column('actualizado', DateTime, default=ahora),
    Column('quien', String(200)),
)

# Resultado de la llamada de cada cita (lo carga el admin o el vendedor en la ficha). Da origen a Seguimientos.
resultados = Table(
    'resultados', meta,
    Column('negocio', String(30), primary_key=True),
    Column('cita_id', String(80), primary_key=True),       # id de la cita en GHL
    Column('cuenta_id', Integer, nullable=False),
    Column('asistencia', String(20)),                      # asistio, no_asistio, cancelada (manda sobre GHL)
    Column('califica', Boolean),
    Column('resultado', String(30)),                       # avanza, pendiente, seguimiento, no_interesado, perdido, no_califica
    Column('servicio', String(200)),
    Column('monto', Float),
    Column('proximo', Date),                               # próximo seguimiento
    Column('notas', Text),
    Column('quien', String(200)),
    Column('actualizado', DateTime, default=ahora),
)

# Registro de ventas: cirugías (Plastia) o cierres de los clientes (TPA). Nunca se borran: se desactivan.
ventas = Table(
    'ventas', meta,
    Column('id', Integer, primary_key=True),
    Column('negocio', String(30), nullable=False),
    Column('cuenta_id', Integer, nullable=False),
    Column('fecha', Date, nullable=False),
    Column('contacto', String(200)),                       # nombre del paciente o lead
    Column('servicio', String(200)),                       # cirugía, tratamiento, propiedad…
    Column('monto', Float, nullable=False),                # venta
    Column('costo', Float),                                # costos de la cirugía (Plastia)
    Column('vendedor', String(200)),                       # email del closer que cerró
    Column('cita_id', String(80)),
    Column('notas', Text),
    Column('comision_cobrada', Boolean, default=False),
    Column('quien', String(200)),
    Column('creado', DateTime, default=ahora),
    Column('activo', Boolean, default=True),
)

auditoria = Table(
    'auditoria', meta,
    Column('id', Integer, primary_key=True),
    Column('cuando', DateTime, default=ahora),
    Column('quien', String(200)),
    Column('accion', String(80)),
    Column('objeto', String(200)),
    Column('antes', Text),
    Column('despues', Text),
)


def conectar(url):
    motor = create_engine(url, future=True, pool_pre_ping=True)
    meta.create_all(motor)
    return motor


def auditar(motor, quien, accion, objeto, antes=None, despues=None):
    with motor.begin() as c:
        c.execute(insert(auditoria).values(quien=quien, accion=accion, objeto=objeto,
                                           antes=json.dumps(antes, default=str) if antes is not None else None,
                                           despues=json.dumps(despues, default=str) if despues is not None else None))


def publicar(motor, clave, valor):
    texto = json.dumps(valor, separators=(',', ':'), default=str)
    with motor.begin() as c:
        hay = c.execute(select(datos_panel.c.clave).where(datos_panel.c.clave == clave)).first()
        if hay:
            c.execute(update(datos_panel).where(datos_panel.c.clave == clave).values(valor=texto, actualizado=ahora()))
        else:
            c.execute(insert(datos_panel).values(clave=clave, valor=texto, actualizado=ahora()))


def leer(motor, clave):
    with motor.connect() as c:
        fila = c.execute(select(datos_panel.c.valor).where(datos_panel.c.clave == clave)).first()
    return json.loads(fila[0]) if fila else None


def cuentas_de(motor, negocio, solo_activas=True):
    q = select(cuentas).where(cuentas.c.negocio == negocio)
    if solo_activas:
        q = q.where(cuentas.c.activo.is_(True))
    with motor.connect() as c:
        return [dict(r._mapping) for r in c.execute(q.order_by(cuentas.c.propia.desc(), cuentas.c.nombre))]
