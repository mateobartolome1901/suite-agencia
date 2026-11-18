"""API de datos por negocio: Panel de campañas, Trazabilidad y alta de cuentas."""
import datetime as dt
from zoneinfo import ZoneInfo

from flask import Blueprint, abort, current_app, jsonify, request
from sqlalchemy import insert, select, update

from . import agenda, db, dinero, indicadores, metricas, ventas
from .config import NEGOCIOS
from .conectores import ghl as ghl_mod
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
    datos = agenda.datos_con_marcas(current_app.motor, negocio)
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


CAMPOS_CUENTA = ('nombre', 'grupo', 'propia', 'crm_location_id', 'meta_cuentas', 'youtube_cuentas', 'objetivo_costo_cita', 'activo',
                 'calendarios', 'campanas', 'moneda', 'plan_setup', 'plan_fee', 'alta', 'baja', 'ficha')
TIPOS_CALENDARIO = ('calificacion', 'principal', 'entrada')


def _limpiar(cuerpo):
    datos = {k: cuerpo[k] for k in CAMPOS_CUENTA if k in cuerpo}
    for k in ('meta_cuentas', 'youtube_cuentas'):
        if k in datos and not (isinstance(datos[k], list) and all(isinstance(x, str) for x in datos[k])):
            abort(400)
    if 'nombre' in datos and not str(datos['nombre']).strip():
        abort(400)
    if 'calendarios' in datos:
        cal = datos['calendarios']
        if not isinstance(cal, list) or not all(isinstance(x, dict) and isinstance(x.get('id'), str) and x.get('tipo') in TIPOS_CALENDARIO for x in cal):
            abort(400)
        datos['calendarios'] = [{'id': x['id'], 'nombre': str(x.get('nombre', ''))[:200], 'tipo': x['tipo']} for x in cal]
    if 'campanas' in datos:
        ca = datos['campanas']
        if not isinstance(ca, list) or not all(isinstance(x, dict) and isinstance(x.get('id'), str) for x in ca):
            abort(400)
        datos['campanas'] = [{'id': x['id'], 'nombre': str(x.get('nombre', ''))[:200]} for x in ca]
    if 'moneda' in datos:
        if not isinstance(datos['moneda'], str) or len(datos['moneda']) != 3 or not datos['moneda'].isalpha():
            abort(400)
        datos['moneda'] = datos['moneda'].upper()
    for k in ('plan_setup', 'plan_fee', 'objetivo_costo_cita'):
        if k in datos:
            datos[k] = _numero(datos[k], 1e9)
    for k in ('alta', 'baja'):
        if k in datos:
            datos[k] = _fecha_o_none(datos[k])
    if 'ficha' in datos and (not isinstance(datos['ficha'], dict) or len(str(datos['ficha'])) > 50000):
        abort(400)
    for k in ('propia', 'activo'):
        if k in datos and not isinstance(datos[k], bool):
            abort(400)
    return datos


def _cuenta_publica(c, tokens):
    x = {**c, 'tiene_token': bool(c['crm_location_id'] and c['crm_location_id'] in tokens)}
    for k in ('alta', 'baja'):
        x[k] = c[k].isoformat() if c.get(k) else None
    return x


@bp.get('/<negocio>/cuentas')
@requiere('admin')
@datos_de_cuentas
def cuentas_listar(negocio):
    filas = cuentas_visibles(usuario_actual(), negocio)
    # nunca se devuelven tokens: solo si la subcuenta tiene uno cargado
    tokens = current_app.cfg.CRM_TOKENS
    return jsonify([_cuenta_publica(c, tokens) for c in filas])


@bp.post('/<negocio>/cuentas')
@requiere('admin')
def cuentas_crear(negocio):
    datos = _limpiar(request.get_json(silent=True) or {})
    if 'nombre' not in datos:
        abort(400)
    datos.setdefault('moneda', NEGOCIOS[negocio].get('moneda_cuentas', 'USD') if not datos.get('propia') else 'USD')
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

def _agenda_base(negocio, ambito=None):
    """ambito «agencia»: llamadas de venta de las cuentas propias; «clientes» (por defecto): citas de los clientes."""
    u = usuario_actual()
    cfg = NEGOCIOS[negocio]
    ambito = ambito or request.args.get('ambito') or 'clientes'
    if ambito not in ('agencia', 'clientes'):
        abort(400)
    if ambito == 'agencia':
        if u['rol'] not in ('admin', 'vendedor'):
            abort(403)  # la agenda de ventas de la agencia no es para el portal de clientes
        cuentas = [c for c in cuentas_visibles(u, negocio) if c['propia']]
        citas, datos = agenda.todas(current_app.motor, negocio, cuentas, cfg['agencia']['paso'])
        hoy = dt.date.fromisoformat(datos['hoy']) if datos and datos.get('demo') else _hoy()
        return u, cfg, None, cuentas, citas, datos, hoy
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
    if clave is None:  # agenda de ventas de la agencia
        metas = dict(indicadores.para_panel(current_app.motor, negocio, 'agencia', None)['metas'])
        metas['pct_cierre'] = indicadores.valores(current_app.motor, negocio).get('ag_pct_cierre')
    else:
        metas = dict(indicadores.para_panel(current_app.motor, negocio, 'clientes', clave)['metas'])
        metas['pct_cierre'] = indicadores.valores(current_app.motor, negocio)['emb_%s_pct_cierre' % clave]
    r = agenda.indicadores(citas, desde, hasta, hoy, metas)
    d0, d1 = desde.isoformat(), hasta.isoformat()
    r.update({'citas': [c for c in citas if d0 <= c['fecha'] <= d1], 'desde': d0, 'hasta': d1, 'hoy': hoy.isoformat(),
              'ambito': 'agencia' if clave is None else 'clientes',
              'embudo': cfg['agencia']['nombre'] if clave is None else cfg['embudos'][clave]['nombre'], 'demo': bool(datos and datos.get('demo')), 'sin_datos': datos is None,
              'puede_editar': u['rol'] in ('admin', 'vendedor'),
              'cuentas_disponibles': [{'id': c['id'], 'nombre': c['nombre'], 'grupo': c['grupo']} for c in cuentas]})
    return jsonify(r)


@bp.get('/<negocio>/seguimientos')
@requiere('admin', 'vendedor')
@datos_de_cuentas
def seguimientos_ver(negocio):
    u, cfg, clave, cuentas, citas, datos, hoy = _agenda_base(negocio)
    r = agenda.seguimientos(citas, hoy)
    r.update({'hoy': hoy.isoformat(), 'embudo': cfg['agencia']['nombre'] if clave is None else cfg['embudos'][clave]['nombre'],
              'ambito': 'agencia' if clave is None else 'clientes', 'demo': bool(datos and datos.get('demo')),
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
    ghl_msg = _marcar_en_ghl(cita, cuentas, nuevo['asistencia']) if nuevo.get('asistencia') else None
    paso = cfg['agencia']['paso'] if clave is None else cfg['embudos'][clave]['paso']
    citas, _ = agenda.todas(m, negocio, cuentas, paso)
    out = next(c for c in citas if c['id'] == cita_id)
    out['ghl'] = ghl_msg
    return jsonify(out)


GHL_ESTADO = {'asistio': 'showed', 'no_asistio': 'noshow', 'cancelada': 'cancelled', 'confirmada': 'confirmed'}


def _marcar_en_ghl(cita, cuentas, asistencia):
    """Copia el estado a la cita de GHL. Si el token no tiene permiso de escritura, queda solo en la suite."""
    cfg = current_app.cfg
    if cfg.DATOS_DEMO or str(cita.get('id', '')).startswith('cita-'):
        return {'ok': False, 'texto': 'Guardado en la suite (datos de ejemplo).'}
    loc = next((c['crm_location_id'] for c in cuentas if c['id'] == cita['cuenta_id']), None)
    token = (cfg.CRM_TOKENS_ESCRITURA.get(loc) or cfg.CRM_TOKENS.get(loc)) if loc else None
    if not token:
        return {'ok': False, 'texto': 'Guardado en la suite. Falta el token de GHL de esta subcuenta.'}
    try:
        ghl_mod.GHL(token).marcar(cita['id'], GHL_ESTADO[asistencia])
        return {'ok': True, 'texto': 'Guardado en la suite y en GHL.'}
    except ghl_mod.ErrorCRM as e:
        sin_permiso = ' 401' in str(e) or ' 403' in str(e)
        return {'ok': False, 'texto': 'Guardado en la suite. ' + (
            'Para que también cambie en GHL, el token necesita el permiso calendars/events.write.' if sin_permiso
            else 'GHL no lo aceptó: ' + str(e)[:120])}


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
    datos = agenda.datos_con_marcas(m, negocio)
    t = dinero.tasas_de(m, negocio)
    r = ventas.calcular(negocio, ventas.listar(m, negocio, ids, desde, hasta), cuentas,
                        ventas.pauta_por_cuenta(datos, ids, desde, hasta), t)
    da, ha = desde - (hasta - desde) - dt.timedelta(days=1), desde - dt.timedelta(days=1)
    r['anterior'] = ventas.calcular(negocio, ventas.listar(m, negocio, ids, da, ha), cuentas,
                                    ventas.pauta_por_cuenta(datos, ids, da, ha), t)['resumen']
    r['tasas'] = {'COP': t.get('COP')}
    cfg = NEGOCIOS[negocio]
    r.update({'hoy': _hoy().isoformat(), 'desde': desde.isoformat(), 'hasta': hasta.isoformat(), 'comision_pct': cfg.get('comision_pct', 0),
              'closer_pct': cfg.get('closer_pct', 0), 'puede_borrar': usuario_actual()['rol'] == 'admin',
              'cuentas_disponibles': [{'id': c['id'], 'nombre': c['nombre'], 'moneda': c.get('moneda') or 'USD'} for c in cuentas]})
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


# ---- Fuentes elegibles de cada cuenta (calendarios de GHL y campañas de Meta, en vivo) ----

@bp.get('/<negocio>/cuentas/<int:cuenta_id>/fuentes')
@requiere('admin')
@datos_de_cuentas
def cuentas_fuentes(negocio, cuenta_id):
    from .conectores import ghl as ghl_mod
    from .conectores.meta import ErrorMeta, Meta
    cu = next((c for c in cuentas_visibles(usuario_actual(), negocio) if c['id'] == cuenta_id), None)
    if not cu:
        abort(404)
    cfg = current_app.cfg
    r = {'calendarios': [], 'campanas': [], 'avisos': []}
    loc = cu.get('crm_location_id')
    token = cfg.CRM_TOKENS.get(loc) if loc else None
    if not loc:
        r['avisos'].append('Falta el ID de la subcuenta de GHL.')
    elif not token:
        r['avisos'].append('Falta el token de GHL de esta subcuenta (variable CRM_TOKENS).')
    else:
        try:
            r['calendarios'] = [{'id': x['id'], 'nombre': x.get('name', ''), 'activo': x.get('isActive') is not False}
                                for x in ghl_mod.GHL(token).calendarios(loc)]
        except ghl_mod.ErrorCRM as e:
            r['avisos'].append(str(e))
    if not cfg.META_TOKENS:
        r['avisos'].append('Falta el token de Meta (META_ACCESS_TOKEN).')
    else:
        m = Meta(cfg.META_TOKENS, cfg.META_API_VERSION)
        for act in cu.get('meta_cuentas') or []:
            try:
                r['campanas'] += [{**x, 'cuenta': act} for x in m.campanas(act)]
            except ErrorMeta as e:
                r['avisos'].append(str(e))
    return jsonify(r)


# ---- Dinero: cobros, movimientos, finanzas, inicio y ventas de la agencia ----

def _nombres(negocio):
    return {c['id']: c['nombre'] for c in db.cuentas_de(current_app.motor, negocio, solo_activas=False)}


def _rango_param(defecto_mes=True):
    hoy = _hoy()
    try:
        if request.args.get('desde'):
            d = dt.date.fromisoformat(request.args['desde'])
            h = dt.date.fromisoformat(request.args.get('hasta') or request.args['desde'])
        else:
            d, h = dinero.rango_mes(hoy)
    except ValueError:
        abort(400)
    if h < d or (h - d).days > 400:
        abort(400)
    return d, h, hoy


@bp.get('/<negocio>/cobros')
@requiere('admin')
@datos_de_cuentas
def cobros_ver(negocio):
    cuentas_visibles(usuario_actual(), negocio)
    hoy = _hoy()
    m = current_app.motor
    dinero.generar_fees(m, negocio, hoy)
    t = dinero.tasas_de(m, negocio)
    nombres = _nombres(negocio)
    lista = [dinero.cobro_publico(x, hoy, nombres, t) for x in dinero.cobros_de(m, negocio)]
    clientes = [c for c in db.cuentas_de(m, negocio) if not c['propia']]
    mes = dinero.mes_de(hoy)
    planes = []
    for c in clientes:
        fee = next((x for x in lista if x['cuenta_id'] == c['id'] and x['concepto'] == 'fee' and x['periodo'] == mes), None)
        planes.append({'id': c['id'], 'nombre': c['nombre'], 'setup': c.get('plan_setup'), 'fee': c.get('plan_fee'),
                       'alta': c['alta'].isoformat() if c.get('alta') else None, 'baja': c['baja'].isoformat() if c.get('baja') else None,
                       'estado_mes': fee['estado'] if fee else None, 'mora': fee['mora'] if fee else 0, 'cobro_mes': fee['id'] if fee else None})
    return jsonify({'cobros': lista, 'planes': planes, 'hoy': hoy.isoformat(),
                    'mrr': sum(p['fee'] or 0 for p in planes if p['fee'] and not p['baja']),
                    'por_cobrar': sum(x['monto_usd'] for x in lista if x['estado'] != 'pagado'),
                    'vencido': sum(x['monto_usd'] for x in lista if x['estado'] == 'vencido'),
                    'cobrado_mes': sum(x['monto_usd'] for x in lista if x['pagado'] and x['pagado'][:7] == mes)})


def _fecha_o_none(v):
    if v in (None, ''):
        return None
    try:
        return dt.date.fromisoformat(v)
    except (TypeError, ValueError):
        abort(400)


@bp.post('/<negocio>/cobros')
@requiere('admin')
@datos_de_cuentas
def cobros_crear(negocio):
    ids = {c['id'] for c in cuentas_visibles(usuario_actual(), negocio)}
    b = request.get_json(silent=True)
    if not isinstance(b, dict) or b.get('cuenta_id') not in ids or b.get('concepto') not in ('setup', 'fee', 'comision', 'otro'):
        abort(400)
    monto = _numero(b.get('monto'), 1e9)
    if monto is None:
        abort(400)
    d = {'cuenta_id': b['cuenta_id'], 'concepto': b['concepto'], 'monto': monto, 'moneda': (b.get('moneda') or 'USD')[:3].upper(),
         'vence': _fecha_o_none(b.get('vence')) or _hoy(), 'pagado': _fecha_o_none(b.get('pagado')), 'nota': _texto(b.get('nota'), 200),
         'periodo': (b.get('periodo') or None)}
    with current_app.motor.begin() as c:
        nuevo = c.execute(insert(db.cobros).values(negocio=negocio, quien=usuario_actual()['email'], activo=True, **d)).inserted_primary_key[0]
    db.auditar(current_app.motor, usuario_actual()['email'], 'crear_cobro', f'{negocio}:{nuevo}', None, d)
    return jsonify(id=nuevo), 201


@bp.patch('/<negocio>/cobros/<int:cobro_id>')
@requiere('admin')
@datos_de_cuentas
def cobros_editar(negocio, cobro_id):
    ids = {c['id'] for c in cuentas_visibles(usuario_actual(), negocio)}
    t = db.cobros
    with current_app.motor.connect() as c:
        antes = c.execute(select(t).where(t.c.id == cobro_id, t.c.negocio == negocio, t.c.activo.is_(True))).first()
    if not antes or antes.cuenta_id not in ids:
        abort(404)
    b = request.get_json(silent=True)
    if not isinstance(b, dict):
        abort(400)
    d = {}
    if b.get('borrar') is True:
        d['activo'] = False
    if 'pagado' in b:
        d['pagado'] = _fecha_o_none(b['pagado'])
    if 'monto' in b:
        d['monto'] = _numero(b['monto'], 1e9)
        if d['monto'] is None:
            abort(400)
    if 'vence' in b:
        d['vence'] = _fecha_o_none(b['vence'])
    if 'nota' in b:
        d['nota'] = _texto(b['nota'], 200)
    if not d:
        abort(400)
    with current_app.motor.begin() as c:
        c.execute(update(t).where(t.c.id == cobro_id).values(**d))
    db.auditar(current_app.motor, usuario_actual()['email'], 'editar_cobro', f'{negocio}:{cobro_id}', dict(antes._mapping), d)
    return jsonify(ok=True)


@bp.get('/<negocio>/movimientos')
@requiere('admin')
def movimientos_ver(negocio):
    d, h, hoy = _rango_param()
    m = current_app.motor
    t = dinero.tasas_de(m, negocio)
    return jsonify([dinero.mov_publico(x, t) for x in dinero.movimientos_de(m, negocio, d, h)])


@bp.post('/<negocio>/movimientos')
@requiere('admin')
def movimientos_crear(negocio):
    b = request.get_json(silent=True)
    if not isinstance(b, dict) or b.get('tipo') not in ('ingreso', 'gasto', 'transferencia'):
        abort(400)
    monto = _numero(b.get('monto'), 1e10)
    fecha = _fecha_o_none(b.get('fecha'))
    if monto is None or not fecha:
        abort(400)
    socios = [s for s, _ in NEGOCIOS[negocio].get('socios') or []]
    if b['tipo'] == 'transferencia' and (b.get('socio') not in socios or b.get('socio_destino') not in socios or b['socio'] == b['socio_destino']):
        abort(400)
    d = {'tipo': b['tipo'], 'fecha': fecha, 'monto': monto, 'moneda': (b.get('moneda') or 'USD')[:3].upper(),
         'categoria': _texto(b.get('categoria'), 60), 'concepto': _texto(b.get('concepto'), 200),
         'socio': _texto(b.get('socio'), 60), 'socio_destino': _texto(b.get('socio_destino'), 60)}
    with current_app.motor.begin() as c:
        nuevo = c.execute(insert(db.movimientos).values(negocio=negocio, quien=usuario_actual()['email'], activo=True, **d)).inserted_primary_key[0]
    db.auditar(current_app.motor, usuario_actual()['email'], 'crear_movimiento', f'{negocio}:{nuevo}', None, d)
    return jsonify(id=nuevo), 201


@bp.patch('/<negocio>/movimientos/<int:mov_id>')
@requiere('admin')
def movimientos_editar(negocio, mov_id):
    t = db.movimientos
    with current_app.motor.connect() as c:
        antes = c.execute(select(t).where(t.c.id == mov_id, t.c.negocio == negocio, t.c.activo.is_(True))).first()
    if not antes:
        abort(404)
    b = request.get_json(silent=True)
    if not isinstance(b, dict) or b.get('borrar') is not True:
        abort(400)  # se corrige borrando y cargando de nuevo
    with current_app.motor.begin() as c:
        c.execute(update(t).where(t.c.id == mov_id).values(activo=False))
    db.auditar(current_app.motor, usuario_actual()['email'], 'borrar_movimiento', f'{negocio}:{mov_id}', dict(antes._mapping), None)
    return jsonify(ok=True)


@bp.get('/<negocio>/finanzas')
@requiere('admin')
@datos_de_cuentas
def finanzas_ver(negocio):
    cuentas_visibles(usuario_actual(), negocio)
    d, h, hoy = _rango_param()
    r = dinero.finanzas(current_app.motor, negocio, d, h, hoy)
    r['categorias'] = CATEGORIAS
    return jsonify(r)


CATEGORIAS = {'ingreso': ['Setups', 'Fees mensuales', 'Comisiones', 'Otros ingresos'],
              'gasto': ['Pauta propia', 'Herramientas', 'Comisión de Stripe', 'Equipo', 'Comisiones de closers', 'Impuestos', 'Otros gastos']}


@bp.get('/<negocio>/resumen')
@requiere('admin')
@datos_de_cuentas
def resumen_ver(negocio):
    cuentas_visibles(usuario_actual(), negocio)
    return jsonify(dinero.resumen_inicio(current_app.motor, negocio, _hoy()))


@bp.get('/<negocio>/ventas-agencia')
@requiere('admin')
@datos_de_cuentas
def ventas_agencia_ver(negocio):
    cuentas_visibles(usuario_actual(), negocio)
    d, h, hoy = _rango_param()
    return jsonify(dinero.ventas_agencia(current_app.motor, negocio, d, h, hoy))


# ---- Tableros y listas: tareas, tablero de edición, guiones, storyboards, estilos ----

TIPOS_ITEM = {
    'tarea': ['por_hacer', 'haciendo', 'esperando', 'hecho'],
    'video': ['guiones', 'por_editar', 'storyboard', 'correccion', 'editando', 'editados'],
    'guion': ['borrador', 'para_revisar', 'aprobado', 'descartado'],
    'storyboard': ['pendiente', 'nuevo', 'corregido', 'terminado'],
    'estilo': ['activo', 'archivado'],
}


def _item_publico(x):
    return {'id': x['id'], 'tipo': x['tipo'], 'columna': x['columna'], 'titulo': x['titulo'], 'datos': x['datos'] or {},
            'responsable': x['responsable'] or '', 'vence': x['vence'].isoformat() if x['vence'] else None, 'orden': x['orden'] or 0,
            'quien': x['quien'], 'actualizado': x['actualizado'].isoformat() if x['actualizado'] else None}


@bp.get('/<negocio>/items')
@requiere('admin', 'vendedor')
def items_ver(negocio):
    tipo = request.args.get('tipo')
    if tipo not in TIPOS_ITEM:
        abort(400)
    t = db.items
    with current_app.motor.connect() as c:
        filas = c.execute(select(t).where(t.c.negocio == negocio, t.c.tipo == tipo, t.c.activo.is_(True)).order_by(t.c.orden, t.c.id)).all()
    return jsonify({'columnas': TIPOS_ITEM[tipo], 'items': [_item_publico(dict(f._mapping)) for f in filas]})


def _item_limpio(b, tipo, parcial):
    if not isinstance(b, dict):
        abort(400)
    d = {}
    if 'titulo' in b or not parcial:
        d['titulo'] = _texto(b.get('titulo') or '', 300)
        if not d['titulo']:
            abort(400)
    if 'columna' in b or not parcial:
        d['columna'] = b.get('columna') or TIPOS_ITEM[tipo][0]
        if d['columna'] not in TIPOS_ITEM[tipo]:
            abort(400)
    if 'datos' in b:
        if not isinstance(b['datos'], dict) or len(str(b['datos'])) > 50000:
            abort(400)
        d['datos'] = b['datos']
    if 'responsable' in b:
        d['responsable'] = _texto(b['responsable'], 200)
    if 'vence' in b:
        d['vence'] = _fecha_o_none(b['vence'])
    if 'orden' in b:
        d['orden'] = _numero(b['orden'], 1e9)
    return d


@bp.post('/<negocio>/items')
@requiere('admin', 'vendedor')
def items_crear(negocio):
    b = request.get_json(silent=True) or {}
    tipo = b.get('tipo')
    if tipo not in TIPOS_ITEM:
        abort(400)
    d = _item_limpio(b, tipo, False)
    with current_app.motor.begin() as c:
        nuevo = c.execute(insert(db.items).values(negocio=negocio, tipo=tipo, quien=usuario_actual()['email'], activo=True,
                                                  actualizado=db.ahora(), **d)).inserted_primary_key[0]
    return jsonify(id=nuevo), 201


@bp.patch('/<negocio>/items/<int:item_id>')
@requiere('admin', 'vendedor')
def items_editar(negocio, item_id):
    t = db.items
    with current_app.motor.connect() as c:
        antes = c.execute(select(t).where(t.c.id == item_id, t.c.negocio == negocio, t.c.activo.is_(True))).first()
    if not antes:
        abort(404)
    b = request.get_json(silent=True)
    d = {'activo': False} if isinstance(b, dict) and b.get('borrar') is True else _item_limpio(b, antes.tipo, True)
    with current_app.motor.begin() as c:
        c.execute(update(t).where(t.c.id == item_id).values(actualizado=db.ahora(), **d))
    return jsonify(ok=True)


# ---- Reportes semanales y rendimiento comercial ----

@bp.get('/<negocio>/semanal')
@requiere('admin', 'vendedor')
@datos_de_cuentas
def semanal_ver(negocio):
    cfg = NEGOCIOS[negocio]
    cuentas = [c for c in cuentas_visibles(usuario_actual(), negocio) if not c['propia']]
    m = current_app.motor
    datos = agenda.datos_con_marcas(m, negocio) or {'gasto': [], 'citas': [], 'anuncios': [], 'cuentas': []}
    hoy = dt.date.fromisoformat(datos['hoy']) if datos.get('demo') else _hoy()
    lunes = hoy - dt.timedelta(days=hoy.weekday() + 7)  # última semana completa
    semanas = []
    for clave, e in cfg['embudos'].items():
        ind = indicadores.para_panel(m, negocio, 'clientes', clave)
        obj = ind['objetivo'] or e['objetivo_costo_cita']
        for i in range(4):
            d0 = lunes - dt.timedelta(days=7 * i)
            p = metricas.panel(datos, cuentas, d0, d0 + dt.timedelta(days=6), e['paso'], obj, hoy, ind['factor_rojo'])
            tz = metricas.trazabilidad(datos, cuentas, d0, d0 + dt.timedelta(days=6), e['paso'], obj)
            k = p['kpi']
            mejores = sorted([a for a in tz['anuncios'] if a['citas']], key=lambda a: a['costo_cita'])[:3]
            embudo = [('leads', k['leads']['valor']), ('citas', k['citas']['valor']), ('asistieron', k['asistio']['valor'])]
            cuello = None
            if k['leads']['valor'] and (p['secundarias']['pct_agenda'] or 0) < (ind['metas'].get('pct_agenda') or 15):
                cuello = 'Agendamiento: solo %d%% de los leads agenda.' % round(p['secundarias']['pct_agenda'] or 0)
            elif k['pct_asistencia']['valor'] is not None and k['pct_asistencia']['valor'] < (ind['metas'].get('pct_asistencia') or 50):
                cuello = 'Asistencia: va el %d%% de los que agendan.' % round(k['pct_asistencia']['valor'])
            elif k['costo_cita']['valor'] and k['costo_cita']['valor'] > obj:
                cuello = 'Costo por cita arriba del objetivo (%s).' % round(k['costo_cita']['valor'])
            semanas.append({'embudo': e['nombre'], 'desde': d0.isoformat(), 'hasta': (d0 + dt.timedelta(days=6)).isoformat(),
                            'gasto': k['gasto']['valor'], 'leads': k['leads']['valor'], 'citas': k['citas']['valor'],
                            'asistio': k['asistio']['valor'], 'costo_cita': k['costo_cita']['valor'], 'pct_asistencia': k['pct_asistencia']['valor'],
                            'cambio_costo': k['costo_cita']['cambio'], 'objetivo': obj, 'cuello': cuello,
                            'criticas': [f['nombre'] for f in p['cuentas'] if f['estado'] == 'critico'],
                            'angulos': [{'anuncio': a['anuncio'], 'cuenta': a['cuenta'], 'citas': a['citas'], 'costo_cita': a['costo_cita']} for a in mejores],
                            'embudo_numeros': embudo})
    return jsonify({'semanas': semanas, 'demo': bool(datos.get('demo'))})


@bp.get('/<negocio>/rendimiento')
@requiere('admin', 'vendedor')
@datos_de_cuentas
def rendimiento_ver(negocio):
    u = usuario_actual()
    cfg = NEGOCIOS[negocio]
    cuentas = [c for c in cuentas_visibles(u, negocio) if not c['propia']]
    d, h, hoy = _rango_param()
    m = current_app.motor
    t = dinero.tasas_de(m, negocio)
    ids = {c['id'] for c in cuentas}
    datos = agenda.datos_con_marcas(m, negocio)
    vs = ventas.calcular(negocio, ventas.listar(m, negocio, ids, d, h), cuentas, ventas.pauta_por_cuenta(datos, ids, d, h), t)
    por = {}
    for clave, e in cfg['embudos'].items():
        citas, _ = agenda.todas(m, negocio, cuentas, e['paso'])
        for c in citas:
            r = c['resultado']
            if not r or not (d.isoformat() <= c['fecha'] <= h.isoformat()):
                continue
            x = por.setdefault(r['quien'], {'vendedor': r['quien'], 'llamadas': 0, 'asistio': 0, 'califica': 0, 'avanza': 0, 'ventas': 0, 'monto': 0.0, 'comision': 0.0})
            x['llamadas'] += 1
            x['asistio'] += c['estado'] == 'asistio'
            x['califica'] += bool(r['califica'])
            x['avanza'] += r['resultado'] == 'avanza'
    for v in vs['vendedores']:
        x = por.setdefault(v['vendedor'], {'vendedor': v['vendedor'], 'llamadas': 0, 'asistio': 0, 'califica': 0, 'avanza': 0, 'ventas': 0, 'monto': 0.0, 'comision': 0.0})
        x['ventas'], x['monto'], x['comision'] = v['ventas'], v['monto'], v['closer']
    filas = sorted(por.values(), key=lambda x: (-x['comision'], -x['avanza']))
    for x in filas:
        x['pct_asistencia'] = x['asistio'] / x['llamadas'] * 100 if x['llamadas'] else None
        x['pct_cierre'] = x['avanza'] / x['asistio'] * 100 if x['asistio'] else None
    if u['rol'] != 'admin':
        filas = [x for x in filas if x['vendedor'] == u['email']]
    metas = indicadores.valores(m, negocio)
    clave = next(iter(cfg['embudos']))
    return jsonify({'desde': d.isoformat(), 'hasta': h.isoformat(), 'filas': filas, 'closer_pct': cfg.get('closer_pct', 0),
                    'metas': {'pct_asistencia': metas.get('emb_%s_pct_asistencia' % clave), 'pct_cierre': metas.get('emb_%s_pct_cierre' % clave)}})


# ---- Conversaciones (GHL) ----

def _ghl_de_cuenta(negocio, cuenta_id):
    from .conectores import ghl as ghl_mod
    cu = next((c for c in cuentas_visibles(usuario_actual(), negocio) if c['id'] == cuenta_id), None)
    if not cu:
        abort(404)
    loc = cu.get('crm_location_id')
    token = current_app.cfg.CRM_TOKENS_ESCRITURA.get(loc) or current_app.cfg.CRM_TOKENS.get(loc) if loc else None
    return cu, loc, (ghl_mod.GHL(token) if token else None), ghl_mod


@bp.get('/<negocio>/conversaciones')
@requiere('admin', 'vendedor')
@datos_de_cuentas
def conversaciones_ver(negocio):
    cuentas = cuentas_visibles(usuario_actual(), negocio)
    try:
        cid = int(request.args.get('cuenta_id') or (cuentas[0]['id'] if cuentas else 0))
    except ValueError:
        abort(400)
    if not cuentas:
        return jsonify({'cuentas': [], 'conversaciones': [], 'aviso': 'No tenés cuentas asignadas.'})
    cu, loc, cli, ghl_mod = _ghl_de_cuenta(negocio, cid)
    base = {'cuentas': [{'id': c['id'], 'nombre': c['nombre']} for c in cuentas], 'cuenta_id': cid, 'conversaciones': []}
    if not cli:
        base['aviso'] = 'Falta el token de GHL de esta subcuenta: cuando esté, acá aparecen los chats.'
        return jsonify(base)
    try:
        base['conversaciones'] = [{'id': x.get('id'), 'contacto_id': x.get('contactId'), 'nombre': x.get('fullName') or x.get('contactName') or x.get('email') or x.get('phone') or 'Sin nombre',
                                   'ultimo': x.get('lastMessageBody') or '', 'fecha': x.get('lastMessageDate'), 'no_leidos': x.get('unreadCount') or 0,
                                   'tipo': x.get('lastMessageType') or ''} for x in cli.conversaciones(loc)]
    except ghl_mod.ErrorCRM as e:
        base['aviso'] = str(e)
    return jsonify(base)


@bp.get('/<negocio>/conversaciones/<conv_id>')
@requiere('admin', 'vendedor')
@datos_de_cuentas
def conversaciones_mensajes(negocio, conv_id):
    try:
        cid = int(request.args.get('cuenta_id') or 0)
    except ValueError:
        abort(400)
    cu, loc, cli, ghl_mod = _ghl_de_cuenta(negocio, cid)
    if not cli:
        abort(404)
    try:
        msgs = cli.mensajes(conv_id)
    except ghl_mod.ErrorCRM as e:
        return jsonify({'mensajes': [], 'aviso': str(e)})
    return jsonify({'mensajes': [{'id': x.get('id'), 'texto': x.get('body') or '', 'saliente': x.get('direction') == 'outbound',
                                  'fecha': x.get('dateAdded'), 'tipo': x.get('messageType') or x.get('type')} for x in msgs][::-1]})


@bp.post('/<negocio>/conversaciones/<conv_id>')
@requiere('admin', 'vendedor')
@datos_de_cuentas
def conversaciones_enviar(negocio, conv_id):
    b = request.get_json(silent=True)
    if not isinstance(b, dict) or not isinstance(b.get('texto'), str) or not b['texto'].strip() or not isinstance(b.get('contacto_id'), str):
        abort(400)
    try:
        cid = int(b.get('cuenta_id') or 0)
    except (TypeError, ValueError):
        abort(400)
    cu, loc, cli, ghl_mod = _ghl_de_cuenta(negocio, cid)
    if not cli:
        abort(404)
    try:
        cli.enviar(b['contacto_id'], b['texto'].strip()[:1600], b.get('tipo') if b.get('tipo') in ('SMS', 'WhatsApp', 'Email', 'IG', 'FB') else 'SMS')
    except ghl_mod.ErrorCRM as e:
        return jsonify(error=str(e)), 502
    db.auditar(current_app.motor, usuario_actual()['email'], 'enviar_mensaje', f'{negocio}:{conv_id}', None, {'largo': len(b['texto'])})
    return jsonify(ok=True)


# ---- Usuarios (solo admin; cada admin maneja usuarios de sus negocios) ----

def _usuario_publico(x):
    return {'id': x['id'], 'email': x['email'], 'nombre': x['nombre'] or '', 'rol': x['rol'], 'negocios': x['negocios'] or [],
            'cuentas': x['cuentas'] or [], 'menus': x['menus'] or [], 'activo': bool(x['activo']),
            'ultimo_ingreso': x['ultimo_ingreso'].isoformat() if x['ultimo_ingreso'] else None}


def _usuario_limpio(b, yo, parcial):
    if not isinstance(b, dict):
        abort(400)
    d = {}
    if 'email' in b or not parcial:
        email = str(b.get('email') or '').strip().lower()
        if '@' not in email or len(email) > 200 or ' ' in email:
            abort(400)
        d['email'] = email
    if 'nombre' in b:
        d['nombre'] = _texto(b['nombre'], 200)
    if 'rol' in b or not parcial:
        if b.get('rol') not in ('admin', 'vendedor', 'operador', 'cuenta'):
            abort(400)
        d['rol'] = b['rol']
    if 'negocios' in b or not parcial:
        ns = b.get('negocios') or []
        if not isinstance(ns, list) or any(n not in (yo.get('negocios') or []) for n in ns) or (not ns and not parcial):
            abort(400)  # solo puede dar acceso a sus propios negocios
        d['negocios'] = ns
    if 'cuentas' in b:
        if not isinstance(b['cuentas'], list) or not all(isinstance(i, int) for i in b['cuentas']):
            abort(400)
        d['cuentas'] = b['cuentas']
    if 'menus' in b:
        if not isinstance(b['menus'], list) or not all(isinstance(i, str) for i in b['menus']):
            abort(400)
        d['menus'] = b['menus']
    if 'activo' in b:
        if not isinstance(b['activo'], bool):
            abort(400)
        d['activo'] = b['activo']
    return d


@bp.get('/usuarios')
@requiere('admin')
def usuarios_ver():
    yo = usuario_actual()
    mios = set(yo.get('negocios') or [])
    with current_app.motor.connect() as c:
        filas = [dict(f._mapping) for f in c.execute(select(db.usuarios).order_by(db.usuarios.c.email))]
    # cada admin ve los usuarios que comparten al menos un negocio con él
    filas = [f for f in filas if set(f['negocios'] or []) & mios or f['email'] == yo['email']]
    cuentas = {n: [{'id': c['id'], 'nombre': c['nombre'], 'propia': c['propia']} for c in db.cuentas_de(current_app.motor, n)] for n in mios}
    return jsonify({'usuarios': [_usuario_publico(f) for f in filas], 'cuentas': cuentas, 'yo': yo['email']})


@bp.post('/usuarios')
@requiere('admin')
def usuarios_crear():
    yo = usuario_actual()
    d = _usuario_limpio(request.get_json(silent=True), yo, False)
    with current_app.motor.begin() as c:
        if c.execute(select(db.usuarios.c.id).where(db.usuarios.c.email == d['email'])).first():
            abort(409)
        nuevo = c.execute(insert(db.usuarios).values(activo=True, cuentas=d.pop('cuentas', []), menus=d.pop('menus', []), **d)).inserted_primary_key[0]
    db.auditar(current_app.motor, yo['email'], 'crear_usuario', d['email'], None, d)
    return jsonify(id=nuevo), 201


@bp.patch('/usuarios/<int:usuario_id>')
@requiere('admin')
def usuarios_editar(usuario_id):
    yo = usuario_actual()
    with current_app.motor.connect() as c:
        antes = c.execute(select(db.usuarios).where(db.usuarios.c.id == usuario_id)).first()
    if not antes or not (set(antes.negocios or []) & set(yo.get('negocios') or [])):
        abort(404)
    if set(antes.negocios or []) - set(yo.get('negocios') or []) and antes.rol == 'admin':
        abort(403)  # Luis no puede tocar a un admin con negocios que él no tiene
    d = _usuario_limpio(request.get_json(silent=True), yo, True)
    if antes.email == yo['email'] and (d.get('activo') is False or d.get('rol', 'admin') != 'admin'):
        abort(400)  # no te podés sacar el acceso a vos mismo
    if 'negocios' in d:  # conserva los negocios que este admin no maneja
        d['negocios'] = sorted(set(d['negocios']) | (set(antes.negocios or []) - set(yo.get('negocios') or [])))
    with current_app.motor.begin() as c:
        c.execute(update(db.usuarios).where(db.usuarios.c.id == usuario_id).values(**d))
    db.auditar(current_app.motor, yo['email'], 'editar_usuario', antes.email, _usuario_publico(dict(antes._mapping)), d)
    return jsonify(ok=True)
