"""Dinero (todo en USD para la agencia; lo que viene en otra moneda se convierte con la cotización del día).

- Cobros: setups, fees mensuales (se generan solos según el plan de cada cuenta) y otros.
- Movimientos: ingresos, gastos y transferencias entre socios.
- Finanzas del período, reparto entre socios (TPA: la pauta propia la paga Luis y Mateo le transfiere su mitad).
- Resumen para el Inicio (misma forma que los datos de ejemplo de negocios.js, así la pantalla no cambia).
"""
import datetime as dt

from sqlalchemy import insert, select

from . import agenda, db, indicadores, metricas, monedas, ventas
from .config import NEGOCIOS

MESES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']


def mes_de(d):
    return d.strftime('%Y-%m')


def rango_mes(d):
    ini = d.replace(day=1)
    fin = (ini + dt.timedelta(days=32)).replace(day=1) - dt.timedelta(days=1)
    return ini, fin


def tasas_de(motor, negocio):
    v = indicadores.valores(motor, negocio)
    return monedas.tasas(motor, {'COP': v.get('tasa_cop')})


# ---------- Cobros ----------

def generar_fees(motor, negocio, hoy):
    """Un cobro de fee por mes por cuenta con plan_fee, desde su alta hasta el mes actual (sin duplicar)."""
    t = db.cobros
    with motor.begin() as c:
        cuentas = c.execute(select(db.cuentas).where(db.cuentas.c.negocio == negocio, db.cuentas.c.activo.is_(True),
                                                     db.cuentas.c.propia.is_(False))).all()
        hay = {(f.cuenta_id, f.periodo) for f in c.execute(select(t.c.cuenta_id, t.c.periodo).where(
            t.c.negocio == negocio, t.c.concepto == 'fee'))}
        for cu in cuentas:
            if not cu.plan_fee or not cu.alta:
                continue
            d = cu.alta.replace(day=1)
            fin = min(hoy, cu.baja) if cu.baja else hoy
            while d <= fin:
                per = mes_de(d)
                if (cu.id, per) not in hay:
                    dia = min(cu.alta.day, 28)
                    c.execute(insert(t).values(negocio=negocio, cuenta_id=cu.id, concepto='fee', periodo=per, monto=cu.plan_fee,
                                               moneda='USD', vence=d.replace(day=dia), quien='automático', activo=True))
                d = (d + dt.timedelta(days=32)).replace(day=1)


def cobros_de(motor, negocio, desde=None, hasta=None):
    t = db.cobros
    q = select(t).where(t.c.negocio == negocio, t.c.activo.is_(True))
    if desde:
        q = q.where(t.c.vence >= desde)
    if hasta:
        q = q.where(t.c.vence <= hasta)
    with motor.connect() as c:
        return [dict(f._mapping) for f in c.execute(q.order_by(t.c.vence.desc(), t.c.id.desc()))]


def estado_cobro(x, hoy):
    if x['pagado']:
        return 'pagado'
    if x['vence'] and x['vence'] < hoy:
        return 'vencido'
    return 'pendiente'


def cobro_publico(x, hoy, nombres, t):
    est = estado_cobro(x, hoy)
    return {'id': x['id'], 'cuenta_id': x['cuenta_id'], 'cuenta': nombres.get(x['cuenta_id'], '—'), 'concepto': x['concepto'],
            'periodo': x['periodo'], 'monto': x['monto'], 'moneda': x['moneda'] or 'USD',
            'monto_usd': monedas.a_usd(x['monto'], x['moneda'], t), 'vence': x['vence'].isoformat() if x['vence'] else None,
            'pagado': x['pagado'].isoformat() if x['pagado'] else None, 'estado': est, 'nota': x['nota'] or '',
            'mora': (hoy - x['vence']).days if est == 'vencido' else 0}


# ---------- Movimientos ----------

def movimientos_de(motor, negocio, desde, hasta):
    t = db.movimientos
    with motor.connect() as c:
        return [dict(f._mapping) for f in c.execute(select(t).where(
            t.c.negocio == negocio, t.c.activo.is_(True), t.c.fecha >= desde, t.c.fecha <= hasta).order_by(t.c.fecha.desc(), t.c.id.desc()))]


def mov_publico(x, t):
    return {'id': x['id'], 'fecha': x['fecha'].isoformat(), 'tipo': x['tipo'], 'categoria': x['categoria'] or '',
            'concepto': x['concepto'] or '', 'monto': x['monto'], 'moneda': x['moneda'] or 'USD',
            'monto_usd': monedas.a_usd(x['monto'], x['moneda'], t), 'cuenta_id': x['cuenta_id'], 'socio': x['socio'] or '',
            'socio_destino': x['socio_destino'] or ''}


def pauta_propia(motor, negocio, desde, hasta):
    """Gasto de las campañas propias (cuenta propia del negocio), en USD, por día y campaña."""
    datos = agenda.datos_con_marcas(motor, negocio)
    if not datos:
        return 0.0, []
    propias = {c['id'] for c in datos.get('cuentas', []) if c.get('propia')}
    d0, d1 = desde.isoformat(), hasta.isoformat()
    por, total = {}, 0.0
    for f, ia, g, *_ in datos['gasto']:
        a = datos['anuncios'][ia]
        if a['cuenta_id'] in propias and d0 <= f <= d1:
            k = (f, a['plataforma'], a['campana'])
            por[k] = por.get(k, 0) + g
            total += g
    filas = [[k[0], 'YouTube Ads' if k[1] == 'youtube' else 'Meta Ads', k[2], round(v, 2)] for k, v in sorted(por.items())]
    return total, filas


# ---------- Finanzas del período ----------

def finanzas(motor, negocio, desde, hasta, hoy):
    cfg = NEGOCIOS[negocio]
    t = tasas_de(motor, negocio)
    generar_fees(motor, negocio, hoy)
    cuentas = db.cuentas_de(motor, negocio, solo_activas=False)
    nombres = {c['id']: c['nombre'] for c in cuentas}
    cobros = [cobro_publico(x, hoy, nombres, t) for x in cobros_de(motor, negocio)]
    pagados = [x for x in cobros if x['pagado'] and desde.isoformat() <= x['pagado'] <= hasta.isoformat()]
    movs = [mov_publico(x, t) for x in movimientos_de(motor, negocio, desde, hasta)]
    ingresos, gastos = {}, {}
    for x in pagados:
        k = {'setup': 'Setups', 'fee': 'Fees mensuales', 'comision': 'Comisiones', 'otro': 'Otros cobros'}.get(x['concepto'], 'Otros cobros')
        ingresos[k] = ingresos.get(k, 0) + x['monto_usd']
    # comisiones de Plastia cobradas (marcadas en la bitácora)
    clientes = [c for c in cuentas if not c['propia']]
    ids = {c['id'] for c in clientes}
    datos = agenda.datos_con_marcas(motor, negocio)
    vs = ventas.calcular(negocio, ventas.listar(motor, negocio, ids, desde, hasta), clientes,
                         ventas.pauta_por_cuenta(datos, ids, desde, hasta), t)
    if vs['resumen']['comision_cobrada']:
        ingresos['Comisiones'] = ingresos.get('Comisiones', 0) + vs['resumen']['comision_cobrada']
    for m in movs:
        if m['tipo'] == 'ingreso':
            ingresos[m['categoria'] or 'Otros ingresos'] = ingresos.get(m['categoria'] or 'Otros ingresos', 0) + m['monto_usd']
        elif m['tipo'] == 'gasto':
            gastos[m['categoria'] or 'Otros gastos'] = gastos.get(m['categoria'] or 'Otros gastos', 0) + m['monto_usd']
    pp, pauta_filas = pauta_propia(motor, negocio, desde, hasta)
    if pp:
        gastos['Pauta propia'] = gastos.get('Pauta propia', 0) + pp
    total_i, total_g = sum(ingresos.values()), sum(gastos.values())
    pendientes = [x for x in cobros if x['estado'] != 'pagado']
    r = {'desde': desde.isoformat(), 'hasta': hasta.isoformat(), 'ingresos': ingresos, 'gastos': gastos,
         'total_ingresos': total_i, 'total_gastos': total_g, 'flujo': total_i - total_g,
         'por_cobrar': sum(x['monto_usd'] for x in pendientes), 'vencido': sum(x['monto_usd'] for x in pendientes if x['estado'] == 'vencido'),
         'movimientos': [m for m in movs], 'cobros_pagados': pagados, 'pauta_propia': pp, 'pauta_filas': pauta_filas,
         'comisiones': vs['resumen'], 'tasas': {'COP': t.get('COP')}, 'tasas_fecha': monedas.fecha(motor)}
    socios = cfg.get('socios')
    if socios:
        r['socios'] = reparto(cfg, movs, pp, r['flujo'])
    return r


def reparto(cfg, movs, pauta, flujo):
    """Socios 50/50: la pauta propia la paga uno con su tarjeta; el otro le transfiere su parte."""
    socios, pagador = cfg['socios'], cfg.get('pagador_pauta')
    parte = {s: pauta * p / 100 for s, p in socios}
    puso = {s: 0.0 for s, _ in socios}
    if pagador:
        puso[pagador] += pauta
    trans = [m for m in movs if m['tipo'] == 'transferencia']
    for m in trans:
        if m['socio'] in puso:
            puso[m['socio']] += m['monto_usd']
        if m['socio_destino'] in puso:
            puso[m['socio_destino']] -= m['monto_usd']
    otros = [s for s, _ in socios if s != pagador]
    otro = otros[0] if otros else None
    return {'socios': [{'nombre': s, 'pct': p, 'parte': parte[s], 'puso': puso[s], 'ganancia': flujo * p / 100} for s, p in socios],
            'pagador': pagador, 'otro': otro, 'transferido': sum(m['monto_usd'] for m in trans),
            'saldo': max(0.0, parte.get(otro, 0) - puso.get(otro, 0)) if otro else 0.0,
            'transferencias': [[m['fecha'], m['socio'], m['socio_destino'], m['monto_usd'], m['concepto']] for m in trans]}


# ---------- Inicio (misma forma que DEMO en negocios.js) ----------

def resumen_inicio(motor, negocio, hoy):
    cfg = NEGOCIOS[negocio]
    desde, hasta = rango_mes(hoy)
    f = finanzas(motor, negocio, desde, hasta, hoy)
    t = tasas_de(motor, negocio)
    v = indicadores.valores(motor, negocio)
    cuentas = db.cuentas_de(motor, negocio)
    clientes = [c for c in cuentas if not c['propia']]
    ids = {c['id'] for c in clientes}
    datos = agenda.datos_con_marcas(motor, negocio)
    vs = ventas.calcular(negocio, ventas.listar(motor, negocio, ids, desde, hasta), clientes, ventas.pauta_por_cuenta(datos, ids, desde, hasta), t)
    cobros = [cobro_publico(x, hoy, {c['id']: c['nombre'] for c in cuentas}, t) for x in cobros_de(motor, negocio)]
    setups = [x['monto_usd'] for x in cobros if x['concepto'] == 'setup' and x['pagado'] and x['pagado'] >= desde.isoformat()]
    stripe = sum(m['monto_usd'] for m in f['movimientos'] if m['tipo'] == 'gasto' and 'stripe' in (m['categoria'] + m['concepto']).lower())
    gastos = [[k, round(val, 2)] for k, val in f['gastos'].items() if 'stripe' not in k.lower()] + [['Comisión de Stripe', round(stripe, 2)]]
    # cash por mes: los 4 meses anteriores + este
    meses = []
    for i in range(4, -1, -1):
        d = (hoy.replace(day=1) - dt.timedelta(days=1)) if i else hoy
        ref = hoy.replace(day=1)
        for _ in range(i):
            ref = (ref - dt.timedelta(days=1)).replace(day=1)
        a, b = rango_mes(ref)
        cash = f['total_ingresos'] if i == 0 else finanzas(motor, negocio, a, b, hoy)['total_ingresos']
        meses.append([MESES[ref.month - 1] + ' ' + str(ref.year)[2:], round(cash, 2), v.get('proy_cash') or 0])
    proy = {'cash': v.get('proy_cash') or 0, 'setups': v.get('proy_setups') or 0, 'comisiones': v.get('proy_comisiones') or 0,
            'mrr': v.get('proy_mrr') or 0, 'flujo': v.get('proy_flujo') or 0, 'cuentas': v.get('proy_cuentas') or 0,
            'pautaPropia': v.get('proy_pauta_propia') or 0, 'pautaCuentas': v.get('proy_pauta_cuentas') or 0}
    # agenda de hoy (todas las cuentas, todos los pasos)
    hoy_s = hoy.isoformat()
    citas_hoy, conteo = [], {}
    for clave, e in cfg['embudos'].items():
        cs, _ = agenda.todas(motor, negocio, clientes, e['paso'])
        for c in cs:
            if c['fecha'] == hoy_s:
                citas_hoy.append(['%02d:%02d' % divmod(c['minuto'], 60), e['nombre'], c['nombre'], c['cuenta'],
                                  {'asistio': 'Asistió', 'no_asistio': 'No asistió', 'cancelada': 'Canceló'}.get(c['estado'], 'Sin marcar')])
                conteo[e['nombre']] = conteo.get(e['nombre'], 0) + 1
    citas_hoy.sort()
    # tareas de hoy y vencidas
    with motor.connect() as c:
        filas = c.execute(select(db.items).where(db.items.c.negocio == negocio, db.items.c.tipo == 'tarea', db.items.c.activo.is_(True),
                                                 db.items.c.columna != 'hecho', db.items.c.vence <= hoy)).all()
    tareas = [[x.titulo, 'Vencida' if x.vence < hoy else 'Hoy'] for x in filas]
    alertas = []
    venc = [x for x in cobros if x['estado'] == 'vencido']
    if venc:
        alertas.append(['falta', 'Cobros vencidos', '%d cobros vencidos por %s.' % (len(venc), _us(sum(x['monto_usd'] for x in venc))),
                        'Ver cobros', 'cobros' if negocio == 'tpa' else 'finanzas'])
    if vs['resumen']['por_cobrar'] > 0:
        alertas.append(['cerca', 'Comisiones por cobrar', '%s de comisiones generadas sin cobrar.' % _us(vs['resumen']['por_cobrar']), 'Cobrar', 'bitacora'])
    if datos and f.get('socios') and f['socios']['saldo'] > 1:
        s = f['socios']
        alertas.append(['cerca', 'Pauta entre socios', '%s le debe %s a %s de la pauta propia.' % (s['otro'], _us(s['saldo']), s['pagador']), 'Ver reparto', 'finanzas'])
    sin_marcar = 0
    if datos:
        for clave, e in cfg['embudos'].items():
            cs, _ = agenda.todas(motor, negocio, clientes, e['paso'])
            sin_marcar += sum(1 for c in cs if (hoy - dt.timedelta(days=7)).isoformat() <= c['fecha'] < hoy_s and c['estado'] == 'confirmada')
    if sin_marcar:
        alertas.append(['falta', 'Citas sin marcar', '%d citas de los últimos 7 días siguen sin estado.' % sin_marcar, 'Ver calendario', 'calendario'])
    base = {'setups': setups, 'proy': proy, 'gastos': gastos, 'pautaPropia': round(f['pauta_propia'], 2), 'meses': meses,
            'hoy': citas_hoy, 'conteoHoy': [[n, k.lower()] for k, n in conteo.items()] or [[0, 'citas']],
            'alertas': alertas, 'tareas': tareas, 'real': True, 'tasas': f['tasas']}
    if cfg.get('comision_pct'):
        por = {}
        for x in vs['ventas']:
            por.setdefault(x['cuenta'], {'n': x['cuenta'], 'cirugias': [], 'cobrado': 0})
            por[x['cuenta']]['cirugias'].append([x['monto_usd'], x['costo_usd'] or 0, x['pauta_usd']])
            if x['comision_cobrada']:
                por[x['cuenta']]['cobrado'] += x['comision_usd']
        base['cuentas'] = list(por.values())
    else:
        filas_v = {f_['id']: f_ for f_ in vs['cuentas']}
        citas_mes = {}
        for clave, e in cfg['embudos'].items():
            cs, _ = agenda.todas(motor, negocio, clientes, e['paso'])
            for c in cs:
                if desde.isoformat() <= c['fecha'] <= hasta.isoformat():
                    citas_mes[c['cuenta_id']] = citas_mes.get(c['cuenta_id'], 0) + 1
        estado = {}
        for x in cobros:
            if x['concepto'] == 'fee' and x['periodo'] == mes_de(hoy):
                estado[x['cuenta_id']] = (x['estado'], x['mora'])
        activos = [c for c in clientes if c.get('plan_fee') and (not c.get('baja') or c['baja'] > hoy)]
        base['cuentas'] = [{'n': c['nombre'], 'alta': MESES[c['alta'].month - 1].lower() if c.get('alta') else '—',
                            'estado': estado.get(c['id'], ('pendiente', 0))[0], 'mora': estado.get(c['id'], ('', 0))[1],
                            'roi': (filas_v.get(c['id']) or {}).get('retorno') or 0, 'citas': citas_mes.get(c['id'], 0),
                            'fee': c['plan_fee']} for c in activos]
        base['bajas'] = sum(1 for c in clientes if c.get('baja') and desde <= c['baja'] <= hasta)
        s = f.get('socios') or {}
        base['pautaMov'] = [[x[0][8:] + ' ' + MESES[int(x[0][5:7]) - 1].lower(), x[1], x[2], x[3]] for x in f['pauta_filas']]
        base['pagadorPauta'] = s.get('pagador') or ''
        base['transferencias'] = [[x[0][8:] + ' ' + MESES[int(x[0][5:7]) - 1].lower(), x[1], x[2], x[3], x[4]] for x in s.get('transferencias', [])]
    return base


def _us(x):
    return 'US$' + format(round(x), ',')


# ---------- Ventas de la agencia (embudo propio) ----------

def ventas_agencia(motor, negocio, desde, hasta, hoy):
    cfg = NEGOCIOS[negocio]
    propias = [c for c in db.cuentas_de(motor, negocio) if c['propia']]
    datos = agenda.datos_con_marcas(motor, negocio) or {'gasto': [], 'citas': [], 'anuncios': [], 'cuentas': []}
    p = metricas.panel(datos, propias, desde, hasta, cfg['agencia']['paso'], indicadores.para_panel(motor, negocio, 'agencia', None)['objetivo'] or cfg['agencia']['objetivo_costo_cita'], hoy)
    t = tasas_de(motor, negocio)
    cuentas = db.cuentas_de(motor, negocio, solo_activas=False)
    nombres = {c['id']: c['nombre'] for c in cuentas}
    cobros = [cobro_publico(x, hoy, nombres, t) for x in cobros_de(motor, negocio)]
    setups = [x for x in cobros if x['concepto'] == 'setup' and desde.isoformat() <= (x['vence'] or '') <= hasta.isoformat()]
    nuevos = [c for c in cuentas if not c['propia'] and c.get('alta') and desde <= c['alta'] <= hasta]
    activos = [c for c in cuentas if not c['propia'] and c['activo'] and c.get('plan_fee') and (not c.get('baja') or c['baja'] > hoy)]
    k = p['kpi']
    asistidas = k['asistio']['valor']
    cierres = len(nuevos)
    return {'desde': desde.isoformat(), 'hasta': hasta.isoformat(), 'embudo': cfg['agencia']['nombre'],
            'agendadas': p['totales']['agendadas'], 'desde_anuncios': k['citas']['valor'], 'asistidas': asistidas, 'pct_asistencia': k['pct_asistencia']['valor'],
            'gasto': k['gasto']['valor'], 'leads': k['leads']['valor'], 'costo_cita': k['costo_cita']['valor'],
            'cierres': cierres, 'tasa_cierre': cierres / asistidas * 100 if asistidas else None,
            'cac': k['gasto']['valor'] / cierres if cierres else None,
            'setups_cobrados': sum(x['monto_usd'] for x in setups if x['pagado']), 'setups_pendientes': sum(x['monto_usd'] for x in setups if not x['pagado']),
            'mrr': sum(c['plan_fee'] or 0 for c in activos), 'activos': len(activos),
            'nuevos': [{'id': c['id'], 'nombre': c['nombre'], 'alta': c['alta'].isoformat(), 'setup': c.get('plan_setup'), 'fee': c.get('plan_fee')} for c in nuevos],
            'agenda': p['agenda'], 'demo': bool(datos.get('demo'))}
