"""Métricas del Panel de campañas y de Trazabilidad, calculadas sobre datos.json (lo que publica el worker).

Formato de datos (compacto, sin datos personales):
  cuentas:  [{id, nombre, grupo, propia, objetivo}]
  anuncios: [{id, nombre, campana, conjunto, cuenta_id, plataforma}]
  gasto:    [[fecha, i_anuncio, gasto, impresiones, clics, leads]]
  citas:    [[fecha_cita, minuto, fecha_creada, cuenta_id, tipo, estado, i_anuncio]]   (i_anuncio = -1 si no trae anuncio)
Estados: asistio, no_asistio, cancelada, confirmada (pendiente o sin marcar), reprogramada.
"""
import datetime as dt

# Glosario único: el diseño nunca cambia un nombre ni una definición.
GLOSARIO = {
    'Gasto': 'Inversión en anuncios (Meta y YouTube) en el período.',
    'Leads': 'Leads que reporta la plataforma de anuncios en el período.',
    'Citas creadas': 'Citas del primer paso del embudo creadas en el período por contactos que vienen de un anuncio.',
    'Costo por lead': 'Gasto ÷ leads.',
    'Costo por cita': 'Gasto ÷ citas creadas.',
    '% de agendamiento': 'Citas creadas ÷ leads.',
    'Citas pasadas': 'Citas con fecha en el período que ya pasaron y tienen estado (asistió, no se presentó o canceló). Son la base de las tasas.',
    '% de asistencia': 'Asistieron ÷ citas pasadas.',
    'Costo por asistencia': 'Gasto ÷ citas que asistieron.',
    'Sin marcar': 'Citas que ya pasaron y siguen sin estado en el CRM.',
    'Veredicto': 'Escalar: costo por cita ≤ 80% del objetivo con 3 citas o más. Mantener: hasta el objetivo. '
                 'Revisar: hasta el doble del objetivo. Pausar: más del doble, o sin citas habiendo gastado 1,5 veces el objetivo.',
    'Semáforo': 'Por costo por cita creada contra el objetivo de Indicadores: bien hasta el objetivo, atención hasta 30% arriba, crítico más arriba.',
    'Comparación': 'Contra el período anterior del mismo largo. Si el rango llega al futuro, compara solo lo que ya pasó.',
}

PASADO = ('asistio', 'no_asistio', 'cancelada')


def _f(s):
    return dt.date.fromisoformat(s)


def _div(a, b):
    return a / b if b else None


def _dias(desde, hasta):
    d = desde
    while d <= hasta:
        yield d
        d += dt.timedelta(days=1)


def _cambio(actual, anterior):
    if actual is None or not anterior:
        return None
    return (actual - anterior) / anterior * 100


def _base(datos, cuentas_ids, desde, hasta, paso, hoy):
    """Números base del período para un conjunto de cuentas."""
    ids = set(cuentas_ids)
    anuncios = datos['anuncios']
    gasto = leads = impresiones = clics = 0.0
    por_dia = {d.isoformat(): {'gasto': 0.0, 'leads': 0, 'citas': 0, 'asistio': 0, 'pasadas': 0} for d in _dias(desde, hasta)}
    d0, d1 = desde.isoformat(), hasta.isoformat()
    for f, ia, g, imp, cl, ld in datos['gasto']:
        if d0 <= f <= d1 and anuncios[ia]['cuenta_id'] in ids:
            gasto += g; leads += ld; impresiones += imp; clics += cl
            por_dia[f]['gasto'] += g; por_dia[f]['leads'] += ld
    creadas = asistio = no_asistio = canceladas = sin_marcar = 0
    hoy_s = hoy.isoformat()
    for fc, minuto, fcr, cid, tipo, est, ia in datos['citas']:
        if cid not in ids or tipo != paso:
            continue
        if ia >= 0 and d0 <= fcr <= d1:
            creadas += 1
            por_dia[fcr]['citas'] += 1
        if d0 <= fc <= d1 and fc <= hoy_s:
            if est == 'asistio':
                asistio += 1; por_dia[fc]['asistio'] += 1; por_dia[fc]['pasadas'] += 1
            elif est == 'no_asistio':
                no_asistio += 1; por_dia[fc]['pasadas'] += 1
            elif est == 'cancelada':
                canceladas += 1; por_dia[fc]['pasadas'] += 1
            elif est == 'confirmada' and fc < hoy_s:
                sin_marcar += 1
    pasadas = asistio + no_asistio + canceladas
    return {
        'gasto': gasto, 'leads': int(leads), 'impresiones': int(impresiones), 'clics': int(clics),
        'citas': creadas, 'asistio': asistio, 'no_asistio': no_asistio, 'canceladas': canceladas, 'pasadas': pasadas,
        'sin_marcar': sin_marcar,
        'costo_lead': _div(gasto, leads), 'costo_cita': _div(gasto, creadas),
        'pct_asistencia': _div(asistio * 100, pasadas), 'costo_asistente': _div(gasto, asistio),
        'pct_agenda': _div(creadas * 100, leads),
        'por_dia': por_dia,
    }


def _periodo_anterior(desde, hasta, hoy):
    """Mismo largo antes de 'desde'. Si el rango llega al futuro, compara solo hasta hoy."""
    fin = min(hasta, hoy)
    largo = (fin - desde).days + 1
    return desde - dt.timedelta(days=largo), desde - dt.timedelta(days=1), fin


def _serie(por_dia, clave):
    dias = sorted(por_dia)
    if clave in ('gasto', 'leads', 'citas', 'asistio'):
        return [round(por_dia[d][clave], 2) for d in dias]
    if clave == 'costo_lead':
        return [_div(por_dia[d]['gasto'], por_dia[d]['leads']) for d in dias]
    if clave == 'costo_cita':
        return [_div(por_dia[d]['gasto'], por_dia[d]['citas']) for d in dias]
    if clave == 'pct_asistencia':
        return [_div(por_dia[d]['asistio'] * 100, por_dia[d]['pasadas']) for d in dias]
    if clave == 'costo_asistente':
        return [_div(por_dia[d]['gasto'], por_dia[d]['asistio']) for d in dias]
    return []


def semaforo(costo_cita, gasto, objetivo):
    if not gasto:
        return 'sin_datos'
    if costo_cita is None:
        return 'critico'  # gastó y no trajo citas
    if costo_cita <= objetivo:
        return 'bien'
    if costo_cita <= objetivo * 1.3:
        return 'atencion'
    return 'critico'


def veredicto(gasto, citas, objetivo):
    if citas == 0:
        return 'pausar' if gasto >= objetivo * 1.5 else 'sin_datos'
    cpc = gasto / citas
    if cpc <= objetivo * 0.8 and citas >= 3:
        return 'escalar'
    if cpc <= objetivo:
        return 'mantener'
    if cpc <= objetivo * 2:
        return 'revisar'
    return 'pausar'


def panel(datos, cuentas, desde, hasta, paso, objetivo_defecto, hoy):
    """cuentas: lista de dicts {id, nombre, objetivo_costo_cita} ya filtrada por permisos."""
    ids = [c['id'] for c in cuentas]
    act = _base(datos, ids, desde, hasta, paso, hoy)
    a0, a1, fin = _periodo_anterior(desde, hasta, hoy)
    act_cmp = _base(datos, ids, desde, fin, paso, hoy) if fin < hasta else act
    ant = _base(datos, ids, a0, a1, paso, hoy)

    def kpi(clave):
        return {'valor': act[clave], 'anterior': ant[clave], 'cambio': _cambio(act_cmp[clave], ant[clave]),
                'serie': _serie(act['por_dia'], clave)}

    filas, semaf = [], {'critico': [], 'atencion': [], 'bien': [], 'sin_datos': []}
    proximos_fin = (hoy + dt.timedelta(days=7)).isoformat()
    for c in cuentas:
        objetivo = c.get('objetivo_costo_cita') or objetivo_defecto
        b = _base(datos, [c['id']], desde, hasta, paso, hoy)
        bc = _base(datos, [c['id']], desde, fin, paso, hoy) if fin < hasta else b
        ba = _base(datos, [c['id']], a0, a1, paso, hoy)
        prox = sum(1 for fc, _m, _cr, cid, tipo, est, _a in datos['citas']
                   if cid == c['id'] and tipo == paso and hoy.isoformat() <= fc <= proximos_fin and est != 'cancelada')
        est = semaforo(b['costo_cita'], b['gasto'], objetivo)
        semaf[est].append(c['nombre'])
        if not b['gasto'] and not b['leads'] and not b['citas']:
            nota = 'Sin actividad en el período'
        elif est == 'bien':
            nota = 'Costo por cita en verde'
        elif b['pct_agenda'] is not None and b['pct_agenda'] < 15:
            nota = 'Agenda solo el %d%% de los leads' % round(b['pct_agenda'])
        elif est == 'critico':
            nota = 'Costo por cita arriba del objetivo'
        else:
            nota = 'Costo por cita cerca del objetivo'
        filas.append({'id': c['id'], 'nombre': c['nombre'], 'estado': est, 'nota': nota, 'objetivo': objetivo,
                      'gasto': b['gasto'], 'leads': b['leads'], 'citas': b['citas'], 'pct_agenda': b['pct_agenda'],
                      'costo_cita': b['costo_cita'], 'cambio_costo_cita': _cambio(bc['costo_cita'], ba['costo_cita']),
                      'asistio': b['asistio'], 'pasadas': b['pasadas'], 'pct_asistencia': b['pct_asistencia'],
                      'sin_marcar': b['sin_marcar'], 'proximos_7': prox})
    orden = {'critico': 0, 'atencion': 1, 'bien': 2, 'sin_datos': 3}
    filas.sort(key=lambda f: (orden[f['estado']], -(f['gasto'] or 0)))
    traz = trazabilidad(datos, cuentas, desde, hasta, paso, objetivo_defecto)
    cuenta_veredicto = {'pausar': 0, 'revisar': 0, 'escalar': 0}
    for a in traz['anuncios']:
        if a['veredicto'] in cuenta_veredicto:
            cuenta_veredicto[a['veredicto']] += 1
    alertas = [{'nivel': 'falta', 'cuenta': f['nombre'], 'texto': f['nota']} for f in filas if f['estado'] == 'critico']
    alertas += [{'nivel': 'cerca', 'cuenta': f['nombre'], 'texto': '%d citas pasadas sin marcar' % f['sin_marcar']}
                for f in filas if f['sin_marcar'] >= 3]
    hoy_s = hoy.isoformat()
    citas_hoy = sum(1 for fc, _m, _cr, cid, tipo, est, _a in datos['citas'] if cid in set(ids) and tipo == paso and fc == hoy_s and est != 'cancelada')
    prox7 = sum(f['proximos_7'] for f in filas)
    return {
        'kpi': {k: kpi(k) for k in ('costo_lead', 'costo_cita', 'pct_asistencia', 'costo_asistente', 'gasto', 'leads', 'citas', 'asistio')},
        'secundarias': {'no_asistio': act['no_asistio'], 'no_asistio_ant': ant['no_asistio'], 'canceladas': act['canceladas'],
                        'canceladas_ant': ant['canceladas'], 'pasadas': act['pasadas'], 'pct_agenda': act['pct_agenda'],
                        'impresiones': act['impresiones'], 'clics': act['clics']},
        'agenda': {'hoy': citas_hoy, 'proximos_7': prox7, 'sin_marcar': act['sin_marcar']},
        'semaforo': semaf,
        'veredictos': cuenta_veredicto,
        'cuentas': filas,
        'tendencia': [{'dia': d, 'leads': v['leads'], 'citas': v['citas']} for d, v in sorted(act['por_dia'].items())],
        'alertas': alertas,
        'objetivo': objetivo_defecto,
        'anterior': {'desde': a0.isoformat(), 'hasta': a1.isoformat()},
    }


def trazabilidad(datos, cuentas, desde, hasta, paso, objetivo_defecto):
    """Por anuncio: gasto, leads, citas creadas y veredicto. Las copias con el mismo nombre en una campaña se suman."""
    por_id = {c['id']: c for c in cuentas}
    d0, d1 = desde.isoformat(), hasta.isoformat()
    anuncios = datos['anuncios']
    grupos = {}

    def clave(ia):
        a = anuncios[ia]
        return (a['cuenta_id'], a['campana'], a['nombre'])

    for f, ia, g, _imp, _cl, ld in datos['gasto']:
        if d0 <= f <= d1 and anuncios[ia]['cuenta_id'] in por_id:
            r = grupos.setdefault(clave(ia), {'gasto': 0.0, 'leads': 0, 'citas': 0, 'plataforma': anuncios[ia]['plataforma']})
            r['gasto'] += g; r['leads'] += ld
    sin_anuncio = 0
    for _fc, _m, fcr, cid, tipo, _est, ia in datos['citas']:
        if cid not in por_id or tipo != paso or not (d0 <= fcr <= d1):
            continue
        if ia < 0:
            sin_anuncio += 1
            continue
        r = grupos.setdefault(clave(ia), {'gasto': 0.0, 'leads': 0, 'citas': 0, 'plataforma': anuncios[ia]['plataforma']})
        r['citas'] += 1
    filas = []
    for (cid, campana, nombre), r in grupos.items():
        objetivo = por_id[cid].get('objetivo_costo_cita') or objetivo_defecto
        filas.append({'anuncio': nombre, 'campana': campana, 'cuenta': por_id[cid]['nombre'], 'plataforma': r['plataforma'],
                      'gasto': r['gasto'], 'leads': r['leads'], 'citas': r['citas'],
                      'pct_agenda': _div(r['citas'] * 100, r['leads']), 'costo_lead': _div(r['gasto'], r['leads']),
                      'costo_cita': _div(r['gasto'], r['citas']), 'veredicto': veredicto(r['gasto'], r['citas'], objetivo)})
    filas.sort(key=lambda f: -f['gasto'])
    con_citas = [f for f in filas if f['citas']]
    mejor = min(con_citas, key=lambda f: f['costo_cita']) if con_citas else None
    cara = max(con_citas, key=lambda f: f['costo_cita']) if len(con_citas) > 1 else None
    # Con varias cuentas, solo lo accionable; con una sola, todos sus anuncios
    if len(cuentas) > 1:
        filas = [f for f in filas if f['veredicto'] in ('pausar', 'revisar', 'escalar')]
    return {'anuncios': filas, 'mejor': mejor, 'mas_cara': cara, 'sin_anuncio': sin_anuncio, 'una_cuenta': len(cuentas) == 1}
