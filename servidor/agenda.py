"""Agenda (fase 2): citas del CRM con sus datos personales, resultado de la llamada y seguimientos.

Las citas salen de lo que publica el worker: datos:<negocio> (sin datos personales) y privado:<negocio> (nombre,
teléfono, email; alineado por índice con datos['citas']). El resultado de cada llamada lo cargan el admin o el vendedor
en la ficha y se guarda en la tabla `resultados`. Si marcan la asistencia, manda sobre el estado de GHL.
"""
import datetime as dt

from sqlalchemy import select

from . import db
from .metricas import _periodo_anterior

ASISTENCIAS = ('confirmada', 'asistio', 'no_asistio', 'cancelada')  # los mismos estados que GHL
RESULTADOS = ('avanza', 'pendiente', 'seguimiento', 'no_interesado', 'perdido', 'no_califica')
EN_SEGUIMIENTO = ('pendiente', 'seguimiento')
PASADO = ('asistio', 'no_asistio', 'cancelada')


def _fecha(s):
    return dt.date.fromisoformat(s)


def resultados_de(motor, negocio):
    with motor.connect() as c:
        filas = c.execute(select(db.resultados).where(db.resultados.c.negocio == negocio)).all()
    return {f.cita_id: dict(f._mapping) for f in filas}


def _res_publico(r):
    if not r:
        return None
    return {'asistencia': r['asistencia'], 'califica': r['califica'], 'resultado': r['resultado'], 'servicio': r['servicio'] or '',
            'monto': r['monto'], 'proximo': r['proximo'].isoformat() if r['proximo'] else None, 'notas': r['notas'] or '',
            'quien': r['quien'], 'actualizado': r['actualizado'].isoformat() if r['actualizado'] else None}


def datos_con_marcas(motor, negocio):
    """Los datos del worker con el estado de cada cita tal como quedó marcado en la suite (manda sobre GHL).
    Todas las pantallas leen de acá, así Campañas, Ventas, Agenda e Inicio cuentan lo mismo."""
    datos = db.leer(motor, 'datos:' + negocio)
    if not datos:
        return datos
    priv = (db.leer(motor, 'privado:' + negocio) or {}).get('citas') or []
    marcas = {k: r['asistencia'] for k, r in resultados_de(motor, negocio).items() if r.get('asistencia')}
    if not marcas:
        return datos
    citas = []
    for i, c in enumerate(datos['citas']):
        p = priv[i] if i < len(priv) else None
        cita_id = p[0] if p and p[0] else 'cita-%d' % i
        m = marcas.get(cita_id)
        citas.append(c[:5] + [m] + c[6:] if m else c)
    return {**datos, 'citas': citas}


def todas(motor, negocio, cuentas, paso):
    """Todas las citas del paso para las cuentas dadas (ya filtradas por permisos), con datos personales y resultado."""
    datos = db.leer(motor, 'datos:' + negocio)
    if not datos:
        return [], None
    priv = (db.leer(motor, 'privado:' + negocio) or {}).get('citas') or []
    res = resultados_de(motor, negocio)
    nombres = {c['id']: c['nombre'] for c in cuentas}
    anuncios = datos['anuncios']
    salida = []
    for i, (fc, minuto, creada, cid, tipo, estado, ia) in enumerate(datos['citas']):
        if cid not in nombres or tipo != paso:
            continue
        p = priv[i] if i < len(priv) else None
        cita_id = (p[0] if p and p[0] else 'cita-%d' % i)
        r = res.get(cita_id)
        efectivo = (r and r['asistencia']) or estado
        a = anuncios[ia] if 0 <= ia < len(anuncios) else None
        salida.append({
            'id': cita_id, 'contacto_id': p[2] if p else None, 'fecha': fc, 'minuto': minuto, 'creada': creada, 'cuenta_id': cid, 'cuenta': nombres[cid],
            'estado': efectivo, 'estado_crm': estado,
            'nombre': (p[4] if p and len(p) > 4 and p[4] else (p[1] if p else '')) or 'Sin nombre',
            'telefono': p[5] if p and len(p) > 5 else '', 'email': p[6] if p and len(p) > 6 else '',
            'anuncio': ('%s · %s' % (a['nombre'], a['campana'])) if a else None,
            'resultado': _res_publico(r),
        })
    return salida, datos


def _cuenta_periodo(citas, desde, hasta):
    d0, d1 = desde.isoformat(), hasta.isoformat()
    x = [c for c in citas if d0 <= c['fecha'] <= d1]
    agendadas = len(x)
    asistio = sum(1 for c in x if c['estado'] == 'asistio')
    pasadas = sum(1 for c in x if c['estado'] in PASADO)
    califica = sum(1 for c in x if c['resultado'] and c['resultado']['califica'])
    avanza = sum(1 for c in x if c['resultado'] and c['resultado']['resultado'] == 'avanza')
    return {'agendadas': agendadas, 'asistio': asistio, 'pasadas': pasadas, 'califica': califica, 'avanza': avanza,
            'no_asistio': sum(1 for c in x if c['estado'] == 'no_asistio'),
            'canceladas': sum(1 for c in x if c['estado'] == 'cancelada'),
            'reprogramadas': sum(1 for c in x if c['estado'] == 'reprogramada'),
            'pct_asistencia': asistio / pasadas * 100 if pasadas else None,
            'pct_cierre': avanza / asistio * 100 if asistio else None}


def _cambio(a, b):
    if a is None or not b:
        return None
    return (a - b) / b * 100


def indicadores(citas, desde, hasta, hoy, metas):
    act = _cuenta_periodo(citas, desde, hasta)
    a0, a1, fin = _periodo_anterior(desde, hasta, hoy)
    cmp_ = _cuenta_periodo(citas, desde, fin) if fin < hasta else act
    ant = _cuenta_periodo(citas, a0, a1)
    kpi = {k: {'valor': act[k], 'anterior': ant[k], 'cambio': _cambio(cmp_[k], ant[k])}
           for k in ('agendadas', 'asistio', 'pct_asistencia', 'califica', 'avanza', 'pct_cierre')}
    hoy_s, en7 = hoy.isoformat(), (hoy + dt.timedelta(days=7)).isoformat()
    pend = [c for c in citas if c['fecha'] >= hoy_s and c['estado'] != 'cancelada']
    seg = seguimientos(citas, hoy)
    return {'kpi': kpi, 'metas': metas,
            'secundarias': {'no_asistio': act['no_asistio'], 'canceladas': act['canceladas'], 'reprogramadas': act['reprogramadas'],
                            'pasadas': act['pasadas'], 'agendadas': act['agendadas'],
                            'pendientes_hoy': sum(1 for c in pend if c['fecha'] == hoy_s),
                            'pendientes_7': sum(1 for c in pend if c['fecha'] <= en7),
                            'sin_marcar': sum(1 for c in citas if desde.isoformat() <= c['fecha'] < hoy_s and c['estado'] == 'confirmada'),
                            'seguimientos': seg['activos'], 'vencidos': seg['vencidos']},
            'anterior': {'desde': a0.isoformat(), 'hasta': a1.isoformat()}}


def seguimientos(citas, hoy):
    """Contactos en seguimiento o pendientes de compromiso, por fecha del próximo contacto (la última cita de cada uno)."""
    por_contacto = {}
    for c in citas:
        r = c['resultado']
        if r and r['resultado'] in EN_SEGUIMIENTO:
            k = (c['cuenta_id'], c['nombre'])
            if k not in por_contacto or c['fecha'] > por_contacto[k]['fecha']:
                por_contacto[k] = c
    hoy_s = hoy.isoformat()
    manana = (hoy + dt.timedelta(days=1)).isoformat()
    fin_semana = (hoy + dt.timedelta(days=7)).isoformat()
    cols = {'vencidos': [], 'hoy': [], 'manana': [], 'semana': [], 'despues': [], 'sin_fecha': []}
    for c in sorted(por_contacto.values(), key=lambda c: c['resultado']['proximo'] or '9999'):
        p = c['resultado']['proximo']
        col = ('sin_fecha' if not p else 'vencidos' if p < hoy_s else 'hoy' if p == hoy_s else 'manana' if p == manana
               else 'semana' if p <= fin_semana else 'despues')
        cols[col].append(c)
    activos = len(por_contacto)
    return {'columnas': cols, 'activos': activos, 'vencidos': len(cols['vencidos']), 'para_hoy': len(cols['hoy']),
            'pendientes': sum(1 for c in por_contacto.values() if c['resultado']['resultado'] == 'pendiente'),
            'monto': sum(c['resultado']['monto'] or 0 for c in por_contacto.values())}
