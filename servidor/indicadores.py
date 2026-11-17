"""Indicadores: las metas contra las que se juzga todo (costos objetivo, tasas meta), por negocio.

El esquema (qué metas hay, en qué sección, con qué unidad) sale de NEGOCIOS en config.py. Los valores los carga el
admin desde el menú Indicadores y se guardan en la tabla `indicadores`. Si una meta nunca se cargó, vale la de
config.py (valor de fábrica); si el admin la deja vacía, queda «sin meta» (salvo las que tienen valor de fábrica,
que vuelven a él).
"""
from sqlalchemy import delete, desc, insert, select

from . import db
from .config import NEGOCIOS

FACTOR_ROJO = 1.3  # sin «rojo arriba de» cargado: rojo 30% arriba del objetivo


def _campo(clave, nombre, unidad, ayuda, defecto=None):
    return {'clave': clave, 'nombre': nombre, 'unidad': unidad, 'ayuda': ayuda, 'defecto': defecto}


def esquema(negocio):
    cfg = NEGOCIOS[negocio]
    mon = cfg.get('moneda', 'USD')
    ag = cfg['agencia']
    secciones = [{
        'id': 'agencia',
        'titulo': 'Campañas de ' + cfg.get('corto', cfg['nombre']),
        'sub': 'Motor Agencia: %s. En %s.' % (ag.get('descripcion', 'llamadas de venta con clientes nuevos'), mon),
        'grupos': [{'nombre': None, 'campos': [
            _campo('ag_costo_cita', ag.get('nombre_cita', 'Costo por llamada agendada'), mon, 'gasto en ads ÷ llamadas agendadas', ag['objetivo_costo_cita']),
            _campo('ag_pct_asistencia', '% asistencia a la llamada', '%', 'asistidas ÷ agendadas'),
            _campo('ag_pct_cierre', '% cierre', '%', 'clientes cerrados ÷ llamadas asistidas'),
            _campo('ag_cac', 'Costo por cliente cerrado (CAC)', mon, 'gasto en ads ÷ clientes cerrados'),
        ]}],
    }, {
        'id': 'clientes',
        'titulo': 'Campañas de ' + cfg.get('cuentas', 'clientes').lower(),
        'sub': 'Semáforo del Panel de campañas y veredicto de Trazabilidad. En %s, como el gasto de Meta.' % mon,
        'grupos': [{'nombre': e['nombre'], 'campos': [
            _campo('emb_%s_costo_cita' % k, 'Costo por cita creada · verde hasta', mon, 'Panel de campañas: semáforo', e['objetivo_costo_cita']),
            _campo('emb_%s_costo_rojo' % k, 'Costo por cita creada · rojo arriba de', mon, 'entre los dos queda en ámbar · vacío: 30% arriba'),
            _campo('emb_%s_pct_agenda' % k, '% de agendamiento', '%', 'citas creadas ÷ leads'),
        ]} for k, e in cfg['embudos'].items()],
    }, {
        'id': 'agenda',
        'titulo': 'Agenda · tasas meta',
        'sub': 'Lo que controla el %s. El calendario marca si cada tasa cumple.' % cfg.get('vendedor', 'vendedor').lower(),
        'grupos': [{'nombre': e['nombre'], 'campos': [
            _campo('emb_%s_pct_asistencia' % k, '% de asistencia', '%', 'asistieron ÷ citas pasadas'),
            _campo('emb_%s_pct_cierre' % k, '% de cierre', '%', 'cerrados ÷ asistieron'),
        ]} for k, e in cfg['embudos'].items()],
    }]
    return secciones


def campos(negocio):
    return {c['clave']: c for s in esquema(negocio) for g in s['grupos'] for c in g['campos']}


def guardados(motor, negocio):
    """Solo lo que cargó el admin: {clave: valor o None}."""
    with motor.connect() as c:
        filas = c.execute(select(db.indicadores.c.clave, db.indicadores.c.valor).where(db.indicadores.c.negocio == negocio)).all()
    return {f.clave: f.valor for f in filas}


def valores(motor, negocio):
    """Valor efectivo de cada meta: lo cargado o, si no hay, el de fábrica. None = sin meta."""
    g = guardados(motor, negocio)
    out = {}
    for clave, campo in campos(negocio).items():
        v = g.get(clave)
        out[clave] = v if v is not None else campo['defecto']
    return out


def guardar(motor, negocio, nuevos, quien):
    """nuevos: {clave: float o None}, ya validado."""
    t = db.indicadores
    with motor.begin() as c:
        for clave, valor in nuevos.items():
            c.execute(delete(t).where(t.c.negocio == negocio, t.c.clave == clave))
            c.execute(insert(t).values(negocio=negocio, clave=clave, valor=valor, quien=quien, actualizado=db.ahora()))


def ultimo_cambio(motor, negocio):
    a = db.auditoria
    with motor.connect() as c:
        f = c.execute(select(a.c.quien, a.c.cuando).where(a.c.accion == 'editar_indicadores', a.c.objeto == negocio)
                      .order_by(desc(a.c.id)).limit(1)).first()
    return {'quien': f.quien, 'cuando': f.cuando.isoformat()} if f else None


def para_panel(motor, negocio, ambito, embudo):
    """Objetivo, factor del rojo y tasas meta que usa el Panel de campañas."""
    v = valores(motor, negocio)
    if ambito == 'agencia':
        obj = v['ag_costo_cita']
        return {'objetivo': obj, 'factor_rojo': FACTOR_ROJO,
                'metas': {'pct_asistencia': v['ag_pct_asistencia'], 'pct_agenda': None}}
    obj = v['emb_%s_costo_cita' % embudo]
    rojo = v['emb_%s_costo_rojo' % embudo]
    factor = rojo / obj if (rojo and obj and rojo > obj) else FACTOR_ROJO
    return {'objetivo': obj, 'factor_rojo': factor,
            'metas': {'pct_asistencia': v['emb_%s_pct_asistencia' % embudo], 'pct_agenda': v['emb_%s_pct_agenda' % embudo]}}
