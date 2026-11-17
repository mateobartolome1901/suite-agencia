"""API de datos por negocio: Panel de campañas, Trazabilidad y alta de cuentas."""
import datetime as dt
from zoneinfo import ZoneInfo

from flask import Blueprint, abort, current_app, jsonify, request
from sqlalchemy import insert, select, update

from . import db, indicadores, metricas
from .config import NEGOCIOS
from .seguridad import cuentas_visibles, datos_de_cuentas, requiere, usuario_actual

bp = Blueprint('api', __name__, url_prefix='/api')


def _hoy():
    return dt.datetime.now(ZoneInfo(current_app.cfg.ZONA_HORARIA)).date()


def _contexto(negocio):
    """Período, cuentas (ya filtradas por permisos), paso del embudo y objetivo según los parámetros."""
    u = usuario_actual()
    ambito = request.args.get('ambito', 'clientes')
    if ambito not in ('clientes', 'agencia'):
        abort(400)
    if ambito == 'agencia' and u['rol'] != 'admin':
        abort(403)
    visibles = cuentas_visibles(u, negocio)
    visibles = [c for c in visibles if bool(c['propia']) == (ambito == 'agencia')]
    pedidas = request.args.get('cuentas')
    if pedidas:
        ids = {int(x) for x in pedidas.split(',') if x.strip().isdigit()}
        visibles = [c for c in visibles if c['id'] in ids]  # nunca se amplía más allá de lo permitido
    datos = db.leer(current_app.motor, 'datos:' + negocio)
    hoy = dt.date.fromisoformat(datos['hoy']) if datos and datos.get('demo') else _hoy()
    try:
        if request.args.get('desde'):
            desde = dt.date.fromisoformat(request.args['desde'])
            hasta = dt.date.fromisoformat(request.args.get('hasta') or hoy.isoformat())
        else:
            dias = min(max(int(request.args.get('dias', 7)), 1), 90)
            hasta, desde = hoy, hoy - dt.timedelta(days=dias - 1)
    except ValueError:
        abort(400)
    if hasta < desde or (hasta - desde).days > 120:
        abort(400)
    cfg = NEGOCIOS[negocio]
    clave = None
    if ambito == 'agencia':
        paso, nombre, fabrica = cfg['agencia']['paso'], cfg['agencia']['nombre'], cfg['agencia']['objetivo_costo_cita']
    else:
        clave = request.args.get('embudo') or next(iter(cfg['embudos']))
        if clave not in cfg['embudos']:
            abort(400)
        e = cfg['embudos'][clave]
        paso, nombre, fabrica = e['paso'], e['nombre'], e['objetivo_costo_cita']
    # metas de Indicadores (lo que cargó el admin; si no cargó nada, el valor de fábrica de config.py)
    ind = indicadores.para_panel(current_app.motor, negocio, ambito, clave)
    return {'u': u, 'ambito': ambito, 'cuentas': visibles, 'datos': datos, 'hoy': hoy, 'desde': desde, 'hasta': hasta,
            'paso': paso, 'objetivo': ind['objetivo'] or fabrica, 'factor_rojo': ind['factor_rojo'], 'metas': ind['metas'],
            'embudo': nombre}


def _vacio():
    return {'gasto': [], 'citas': [], 'anuncios': [], 'cuentas': []}


def _cabecera(ctx, negocio):
    estado = db.leer(current_app.motor, 'estado:' + negocio) or {}
    return {'desde': ctx['desde'].isoformat(), 'hasta': ctx['hasta'].isoformat(), 'hoy': ctx['hoy'].isoformat(),
            'embudo': ctx['embudo'], 'ambito': ctx['ambito'],
            'cuentas_disponibles': [{'id': c['id'], 'nombre': c['nombre'], 'grupo': c['grupo']} for c in ctx['cuentas']],
            'actualizado': estado.get('actualizado'), 'demo': bool(ctx['datos'] and ctx['datos'].get('demo')),
            'avisos': estado.get('avisos', []) if ctx['u']['rol'] == 'admin' else [],
            'sin_datos': ctx['datos'] is None, 'glosario': metricas.GLOSARIO, 'metas': ctx['metas']}


@bp.get('/<negocio>/panel')
@requiere('admin', 'vendedor')
@datos_de_cuentas
def panel(negocio):
    ctx = _contexto(negocio)
    datos = ctx['datos'] or _vacio()
    r = metricas.panel(datos, ctx['cuentas'], ctx['desde'], ctx['hasta'], ctx['paso'], ctx['objetivo'], ctx['hoy'], ctx['factor_rojo'])
    r.update(_cabecera(ctx, negocio))
    return jsonify(r)


@bp.get('/<negocio>/trazabilidad')
@requiere('admin', 'vendedor')
@datos_de_cuentas
def trazabilidad(negocio):
    ctx = _contexto(negocio)
    datos = ctx['datos'] or _vacio()
    r = metricas.trazabilidad(datos, ctx['cuentas'], ctx['desde'], ctx['hasta'], ctx['paso'], ctx['objetivo'])
    r.update(_cabecera(ctx, negocio))
    return jsonify(r)


CAMPOS_CUENTA = ('nombre', 'grupo', 'propia', 'crm_location_id', 'meta_cuentas', 'youtube_cuentas', 'objetivo_costo_cita', 'activo')


def _limpiar(cuerpo):
    datos = {k: cuerpo[k] for k in CAMPOS_CUENTA if k in cuerpo}
    for k in ('meta_cuentas', 'youtube_cuentas'):
        if k in datos and not (isinstance(datos[k], list) and all(isinstance(x, str) for x in datos[k])):
            abort(400)
    if 'nombre' in datos and not str(datos['nombre']).strip():
        abort(400)
    return datos


@bp.get('/<negocio>/cuentas')
@requiere('admin')
@datos_de_cuentas
def cuentas_listar(negocio):
    filas = cuentas_visibles(usuario_actual(), negocio)
    # nunca se devuelven tokens: solo si la subcuenta tiene uno cargado
    tokens = current_app.cfg.CRM_TOKENS
    return jsonify([{**c, 'tiene_token': bool(c['crm_location_id'] and c['crm_location_id'] in tokens)} for c in filas])


@bp.post('/<negocio>/cuentas')
@requiere('admin')
def cuentas_crear(negocio):
    datos = _limpiar(request.get_json(silent=True) or {})
    if 'nombre' not in datos:
        abort(400)
    with current_app.motor.begin() as c:
        nuevo = c.execute(insert(db.cuentas).values(negocio=negocio, **datos)).inserted_primary_key[0]
    db.auditar(current_app.motor, usuario_actual()['email'], 'crear_cuenta', f'{negocio}:{nuevo}', None, datos)
    return jsonify(id=nuevo), 201


@bp.patch('/<negocio>/cuentas/<int:cuenta_id>')
@requiere('admin')
def cuentas_editar(negocio, cuenta_id):
    datos = _limpiar(request.get_json(silent=True) or {})
    with current_app.motor.begin() as c:
        antes = c.execute(select(db.cuentas).where(db.cuentas.c.id == cuenta_id, db.cuentas.c.negocio == negocio)).first()
        if not antes:
            abort(404)
        c.execute(update(db.cuentas).where(db.cuentas.c.id == cuenta_id).values(**datos))
    db.auditar(current_app.motor, usuario_actual()['email'], 'editar_cuenta', f'{negocio}:{cuenta_id}', dict(antes._mapping), datos)
    return jsonify(ok=True)


# ---- Indicadores (solo admin): metas por negocio y objetivo opcional por cuenta ----

def _indicadores_respuesta(negocio):
    m = current_app.motor
    cuentas = [{'id': c['id'], 'nombre': c['nombre'], 'grupo': c['grupo'], 'propia': bool(c['propia']),
                'objetivo_costo_cita': c['objetivo_costo_cita']} for c in cuentas_visibles(usuario_actual(), negocio)]
    return {'secciones': indicadores.esquema(negocio), 'valores': indicadores.guardados(m, negocio),
            'cuentas': cuentas, 'ultimo': indicadores.ultimo_cambio(m, negocio)}


@bp.get('/<negocio>/indicadores')
@requiere('admin')
@datos_de_cuentas
def indicadores_ver(negocio):
    return jsonify(_indicadores_respuesta(negocio))


def _numero(v, maximo):
    """None o '' = sin meta; si no, número entre 0 y maximo."""
    if v is None or v == '':
        return None
    if isinstance(v, bool) or not isinstance(v, (int, float, str)):
        abort(400)
    try:
        v = float(str(v).replace(',', '.'))
    except ValueError:
        abort(400)
    if not (0 <= v <= maximo):
        abort(400)
    return v


@bp.put('/<negocio>/indicadores')
@requiere('admin')
@datos_de_cuentas
def indicadores_guardar(negocio):
    cuerpo = request.get_json(silent=True)
    if not isinstance(cuerpo, dict):
        abort(400)
    campos = indicadores.campos(negocio)
    nuevos_v = cuerpo.get('valores') or {}
    nuevos_c = cuerpo.get('cuentas') or {}
    if not isinstance(nuevos_v, dict) or not isinstance(nuevos_c, dict):
        abort(400)
    limpios = {}
    for k, v in nuevos_v.items():
        if k not in campos:
            abort(400)
        limpios[k] = _numero(v, 100 if campos[k]['unidad'] == '%' else 1e7)
    ids = {c['id']: c for c in cuentas_visibles(usuario_actual(), negocio)}
    por_cuenta = {}
    for k, v in nuevos_c.items():
        if not str(k).isdigit() or int(k) not in ids:
            abort(400)
        por_cuenta[int(k)] = _numero(v, 1e7)
    m = current_app.motor
    previos = indicadores.guardados(m, negocio)
    antes = {'valores': {k: previos.get(k) for k in limpios},
             'cuentas': {i: ids[i]['objetivo_costo_cita'] for i in por_cuenta}}
    indicadores.guardar(m, negocio, limpios, usuario_actual()['email'])
    if por_cuenta:
        with m.begin() as c:
            for i, v in por_cuenta.items():
                c.execute(update(db.cuentas).where(db.cuentas.c.id == i, db.cuentas.c.negocio == negocio)
                          .values(objetivo_costo_cita=v))
    db.auditar(m, usuario_actual()['email'], 'editar_indicadores', negocio, antes, {'valores': limpios, 'cuentas': por_cuenta})
    return jsonify(_indicadores_respuesta(negocio))
