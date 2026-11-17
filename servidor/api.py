"""API de datos por negocio: Panel de campañas, Trazabilidad y alta de cuentas."""
import datetime as dt
from zoneinfo import ZoneInfo

from flask import Blueprint, abort, current_app, jsonify, request
from sqlalchemy import insert, select, update

from . import agenda, db, indicadores, metricas, ventas
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


# ---- Agenda (fase 2): calendario, ficha con resultado de la llamada y seguimientos ----

def _agenda_base(negocio):
    u = usuario_actual()
    cfg = NEGOCIOS[negocio]
    clave = request.args.get('embudo') or next(iter(cfg['embudos']))
    if clave not in cfg['embudos']:
        abort(400)
    cuentas = [c for c in cuentas_visibles(u, negocio) if not c['propia']]
    pedidas = request.args.get('cuentas')
    if pedidas:
        ids = {int(x) for x in pedidas.split(',') if x.strip().isdigit()}
        cuentas = [c for c in cuentas if c['id'] in ids]
    citas, datos = agenda.todas(current_app.motor, negocio, cuentas, cfg['embudos'][clave]['paso'])
    hoy = dt.date.fromisoformat(datos['hoy']) if datos and datos.get('demo') else _hoy()
    return u, cfg, clave, cuentas, citas, datos, hoy


@bp.get('/<negocio>/agenda')
@requiere('admin', 'vendedor', 'operador')
@datos_de_cuentas
def agenda_ver(negocio):
    u, cfg, clave, cuentas, citas, datos, hoy = _agenda_base(negocio)
    try:
        if request.args.get('desde'):
            desde = dt.date.fromisoformat(request.args['desde'])
            hasta = dt.date.fromisoformat(request.args.get('hasta') or request.args['desde'])
        else:
            desde = hoy - dt.timedelta(days=hoy.weekday())
            hasta = desde + dt.timedelta(days=6)
    except ValueError:
        abort(400)
    if hasta < desde or (hasta - desde).days > 45:
        abort(400)
    metas = dict(indicadores.para_panel(current_app.motor, negocio, 'clientes', clave)['metas'])
    metas['pct_cierre'] = indicadores.valores(current_app.motor, negocio)['emb_%s_pct_cierre' % clave]
    r = agenda.indicadores(citas, desde, hasta, hoy, metas)
    d0, d1 = desde.isoformat(), hasta.isoformat()
    r.update({'citas': [c for c in citas if d0 <= c['fecha'] <= d1], 'desde': d0, 'hasta': d1, 'hoy': hoy.isoformat(),
              'embudo': cfg['embudos'][clave]['nombre'], 'demo': bool(datos and datos.get('demo')), 'sin_datos': datos is None,
              'puede_editar': u['rol'] in ('admin', 'vendedor'),
              'cuentas_disponibles': [{'id': c['id'], 'nombre': c['nombre'], 'grupo': c['grupo']} for c in cuentas]})
    return jsonify(r)


@bp.get('/<negocio>/seguimientos')
@requiere('admin', 'vendedor')
@datos_de_cuentas
def seguimientos_ver(negocio):
    u, cfg, clave, cuentas, citas, datos, hoy = _agenda_base(negocio)
    r = agenda.seguimientos(citas, hoy)
    r.update({'hoy': hoy.isoformat(), 'embudo': cfg['embudos'][clave]['nombre'], 'demo': bool(datos and datos.get('demo')),
              'puede_editar': True})
    return jsonify(r)


def _texto(v, largo):
    if v is None:
        return None
    if not isinstance(v, str):
        abort(400)
    return v.strip()[:largo]


@bp.post('/<negocio>/citas/<cita_id>/resultado')
@requiere('admin', 'vendedor')
@datos_de_cuentas
def resultado_guardar(negocio, cita_id):
    u, cfg, clave, cuentas, citas, datos, hoy = _agenda_base(negocio)
    cita = next((c for c in citas if c['id'] == cita_id), None)
    if not cita:
        abort(404)  # no existe o es de una cuenta que no ve
    cuerpo = request.get_json(silent=True)
    if not isinstance(cuerpo, dict):
        abort(400)
    nuevo = {}
    if 'asistencia' in cuerpo:
        if cuerpo['asistencia'] not in agenda.ASISTENCIAS + (None,):
            abort(400)
        nuevo['asistencia'] = cuerpo['asistencia']
    if 'califica' in cuerpo:
        if cuerpo['califica'] not in (True, False, None):
            abort(400)
        nuevo['califica'] = cuerpo['califica']
    if 'resultado' in cuerpo:
        if cuerpo['resultado'] not in agenda.RESULTADOS + (None,):
            abort(400)
        nuevo['resultado'] = cuerpo['resultado']
    if 'servicio' in cuerpo:
        nuevo['servicio'] = _texto(cuerpo['servicio'], 200)
    if 'notas' in cuerpo:
        nuevo['notas'] = _texto(cuerpo['notas'], 4000)
    if 'monto' in cuerpo:
        nuevo['monto'] = _numero(cuerpo['monto'], 1e8)
    if 'proximo' in cuerpo:
        try:
            nuevo['proximo'] = dt.date.fromisoformat(cuerpo['proximo']) if cuerpo['proximo'] else None
        except (TypeError, ValueError):
            abort(400)
    if not nuevo:
        abort(400)
    t = db.resultados
    m = current_app.motor
    with m.begin() as c:
        antes = c.execute(select(t).where(t.c.negocio == negocio, t.c.cita_id == cita_id)).first()
        if antes:
            c.execute(update(t).where(t.c.negocio == negocio, t.c.cita_id == cita_id)
                      .values(quien=u['email'], actualizado=db.ahora(), **nuevo))
        else:
            c.execute(insert(t).values(negocio=negocio, cita_id=cita_id, cuenta_id=cita['cuenta_id'], quien=u['email'], **nuevo))
    db.auditar(m, u['email'], 'resultado_cita', f'{negocio}:{cita_id}', dict(antes._mapping) if antes else None, nuevo)
    citas, _ = agenda.todas(m, negocio, cuentas, cfg['embudos'][clave]['paso'])
    return jsonify(next(c for c in citas if c['id'] == cita_id))


# ---- Fase 3: registro de ventas (bitácora) y contactos ----

def _mes_o_rango():
    hoy = _hoy()
    try:
        if request.args.get('desde'):
            desde = dt.date.fromisoformat(request.args['desde'])
            hasta = dt.date.fromisoformat(request.args.get('hasta') or request.args['desde'])
        else:
            desde = hoy.replace(day=1)
            hasta = (desde + dt.timedelta(days=32)).replace(day=1) - dt.timedelta(days=1)
    except ValueError:
        abort(400)
    if hasta < desde or (hasta - desde).days > 400:
        abort(400)
    return desde, hasta


@bp.get('/<negocio>/ventas')
@requiere('admin', 'vendedor', 'operador')
@datos_de_cuentas
def ventas_ver(negocio):
    cuentas = [c for c in cuentas_visibles(usuario_actual(), negocio) if not c['propia']]
    desde, hasta = _mes_o_rango()
    ids = {c['id'] for c in cuentas}
    m = current_app.motor
    datos = db.leer(m, 'datos:' + negocio)
    r = ventas.calcular(negocio, ventas.listar(m, negocio, ids, desde, hasta), cuentas,
                        ventas.pauta_por_cuenta(datos, ids, desde, hasta))
    da, ha = desde - (hasta - desde) - dt.timedelta(days=1), desde - dt.timedelta(days=1)
    r['anterior'] = ventas.calcular(negocio, ventas.listar(m, negocio, ids, da, ha), cuentas,
                                    ventas.pauta_por_cuenta(datos, ids, da, ha))['resumen']
    cfg = NEGOCIOS[negocio]
    r.update({'hoy': _hoy().isoformat(), 'desde': desde.isoformat(), 'hasta': hasta.isoformat(), 'comision_pct': cfg.get('comision_pct', 0),
              'closer_pct': cfg.get('closer_pct', 0), 'puede_borrar': usuario_actual()['rol'] == 'admin',
              'cuentas_disponibles': [{'id': c['id'], 'nombre': c['nombre']} for c in cuentas]})
    return jsonify(r)


def _venta_limpia(cuerpo, ids, parcial=False):
    if not isinstance(cuerpo, dict):
        abort(400)
    d = {}
    if 'cuenta_id' in cuerpo or not parcial:
        if cuerpo.get('cuenta_id') not in ids:
            abort(400)
        d['cuenta_id'] = cuerpo['cuenta_id']
    if 'fecha' in cuerpo or not parcial:
        try:
            d['fecha'] = dt.date.fromisoformat(cuerpo.get('fecha') or '')
        except (TypeError, ValueError):
            abort(400)
    if 'monto' in cuerpo or not parcial:
        d['monto'] = _numero(cuerpo.get('monto'), 1e8)
        if d['monto'] is None:
            abort(400)
    if 'costo' in cuerpo:
        d['costo'] = _numero(cuerpo['costo'], 1e8)
    for k, largo in (('contacto', 200), ('servicio', 200), ('notas', 2000), ('cita_id', 80), ('vendedor', 200)):
        if k in cuerpo:
            d[k] = _texto(cuerpo[k], largo)
    if 'comision_cobrada' in cuerpo:
        if not isinstance(cuerpo['comision_cobrada'], bool):
            abort(400)
        d['comision_cobrada'] = cuerpo['comision_cobrada']
    if not d:
        abort(400)
    return d


@bp.post('/<negocio>/ventas')
@requiere('admin', 'vendedor', 'operador')
@datos_de_cuentas
def ventas_crear(negocio):
    u = usuario_actual()
    ids = {c['id'] for c in cuentas_visibles(u, negocio) if not c['propia']}
    d = _venta_limpia(request.get_json(silent=True), ids)
    if u['rol'] == 'vendedor':
        d['vendedor'] = u['email']  # el closer registra a su nombre
    if u['rol'] != 'admin':
        d.pop('comision_cobrada', None)  # lo marca solo el admin
    with current_app.motor.begin() as c:
        nuevo = c.execute(insert(db.ventas).values(negocio=negocio, quien=u['email'], **d)).inserted_primary_key[0]
    db.auditar(current_app.motor, u['email'], 'crear_venta', f'{negocio}:{nuevo}', None, d)
    return jsonify(id=nuevo), 201


@bp.patch('/<negocio>/ventas/<int:venta_id>')
@requiere('admin', 'vendedor', 'operador')
@datos_de_cuentas
def ventas_editar(negocio, venta_id):
    u = usuario_actual()
    ids = {c['id'] for c in cuentas_visibles(u, negocio) if not c['propia']}
    t = db.ventas
    with current_app.motor.connect() as c:
        antes = c.execute(select(t).where(t.c.id == venta_id, t.c.negocio == negocio, t.c.activo.is_(True))).first()
    if not antes or antes.cuenta_id not in ids:
        abort(404)
    if u['rol'] != 'admin' and antes.quien != u['email']:
        abort(403)  # cada uno corrige lo suyo; el admin, todo
    cuerpo = request.get_json(silent=True)
    if isinstance(cuerpo, dict) and cuerpo.get('borrar') is True:
        if u['rol'] != 'admin':
            abort(403)
        d = {'activo': False}  # nunca se borra: se desactiva
    else:
        d = _venta_limpia(cuerpo, ids, parcial=True)
        if u['rol'] != 'admin':
            d.pop('comision_cobrada', None)
            d.pop('vendedor', None)
    with current_app.motor.begin() as c:
        c.execute(update(t).where(t.c.id == venta_id).values(**d))
    db.auditar(current_app.motor, u['email'], 'editar_venta', f'{negocio}:{venta_id}', dict(antes._mapping), d)
    return jsonify(ok=True)


@bp.get('/<negocio>/contactos')
@requiere('admin', 'vendedor', 'operador')
@datos_de_cuentas
def contactos_ver(negocio):
    u, cfg, clave, cuentas, citas, datos, hoy = _agenda_base(negocio)
    q = (request.args.get('q') or '').strip().lower()
    ids = {c['id'] for c in cuentas}
    m = current_app.motor
    vs = ventas.listar(m, negocio, ids, dt.date(2000, 1, 1), dt.date(2100, 1, 1))
    personas = {}
    for c in citas:
        k = (c['cuenta_id'], c.get('contacto_id') or c['nombre'])
        p = personas.setdefault(k, {'clave': '%s:%s' % k, 'nombre': c['nombre'], 'cuenta': c['cuenta'], 'cuenta_id': c['cuenta_id'],
                                    'telefono': c['telefono'], 'email': c['email'], 'citas': [], 'ventas': []})
        p['citas'].append(c)
    for v in vs:
        p = next((p for p in personas.values() if p['cuenta_id'] == v['cuenta_id'] and p['nombre'].lower() == (v['contacto'] or '').lower()), None)
        if p is None:
            k = (v['cuenta_id'], 'venta-%d' % v['id'])
            nombres = {c['id']: c['nombre'] for c in cuentas}
            p = personas.setdefault(k, {'clave': '%s:%s' % k, 'nombre': v['contacto'] or 'Sin nombre', 'cuenta': nombres.get(v['cuenta_id'], ''),
                                        'cuenta_id': v['cuenta_id'], 'telefono': '', 'email': '', 'citas': [], 'ventas': []})
        p['ventas'].append(ventas._publico(v))
    lista = list(personas.values())
    if q:
        lista = [p for p in lista if q in p['nombre'].lower() or q in (p['telefono'] or '').lower() or q in (p['email'] or '').lower()]
    for p in lista:
        p['citas'].sort(key=lambda c: (c['fecha'], c['minuto']), reverse=True)
        p['ultima'] = max([c['fecha'] for c in p['citas']] + [v['fecha'] for v in p['ventas']] or [''])
    lista.sort(key=lambda p: p['ultima'], reverse=True)
    return jsonify({'contactos': lista[:200], 'total': len(lista), 'demo': bool(datos and datos.get('demo'))})
