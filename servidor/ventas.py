"""Registro de ventas (fase 3): bitácora de cirugías (Plastia) o cierres de clientes (TPA).

Plastia cobra comisión: 25% de (venta − costos de la cirugía − pauta). La pauta del período de cada cuenta se reparte
entre sus ventas según el margen de cada una; si la pauta supera el margen, la comisión es 0 (nunca negativa).
El closer se lleva el 25% de la comisión de las ventas que cerró. TPA cobra fee fijo: acá se mide el retorno de
cada cliente (lo que vendió ÷ la pauta).
"""
from sqlalchemy import select

from . import db
from .config import NEGOCIOS


def listar(motor, negocio, ids, desde, hasta):
    t = db.ventas
    with motor.connect() as c:
        filas = c.execute(select(t).where(t.c.negocio == negocio, t.c.activo.is_(True), t.c.cuenta_id.in_(list(ids) or [-1]),
                                          t.c.fecha >= desde, t.c.fecha <= hasta).order_by(t.c.fecha.desc(), t.c.id.desc())).all()
    return [dict(f._mapping) for f in filas]


def pauta_por_cuenta(datos, ids, desde, hasta):
    if not datos:
        return {}
    d0, d1, anuncios, out = desde.isoformat(), hasta.isoformat(), datos['anuncios'], {}
    for f, ia, g, *_ in datos['gasto']:
        cid = anuncios[ia]['cuenta_id']
        if d0 <= f <= d1 and cid in ids:
            out[cid] = out.get(cid, 0) + g
    return out


def calcular(negocio, ventas, cuentas, pauta):
    cfg = NEGOCIOS[negocio]
    pct = cfg.get('comision_pct', 0) / 100
    pct_closer = cfg.get('closer_pct', 0) / 100
    nombres = {c['id']: c['nombre'] for c in cuentas}
    por_cuenta = {}
    for v in ventas:
        por_cuenta.setdefault(v['cuenta_id'], []).append(v)
    filas, resumen = [], {'ventas': 0, 'monto': 0.0, 'costos': 0.0, 'pauta': 0.0, 'margen': 0.0, 'comision': 0.0,
                          'closer': 0.0, 'comision_cobrada': 0.0}
    salida = []
    for cid in sorted(set(por_cuenta) | set(pauta), key=lambda i: nombres.get(i, '')):
        if cid not in nombres:
            continue
        vs = por_cuenta.get(cid, [])
        monto = sum(v['monto'] or 0 for v in vs)
        costos = sum(v['costo'] or 0 for v in vs)
        p = pauta.get(cid, 0.0)
        bruto = monto - costos
        margen = bruto - p
        comision = max(0.0, margen) * pct
        for v in vs:
            neto_v = (v['monto'] or 0) - (v['costo'] or 0)
            pauta_v = p * neto_v / bruto if bruto > 0 else 0.0
            com_v = max(0.0, neto_v - pauta_v) * pct if margen > 0 else 0.0
            closer_v = com_v * pct_closer if v.get('vendedor') else 0.0
            salida.append({**_publico(v), 'cuenta': nombres[cid], 'pauta': round(pauta_v, 2), 'comision': round(com_v, 2),
                           'closer': round(closer_v, 2)})
        closer = sum(x['closer'] for x in salida if x['cuenta_id'] == cid)
        cobrada = sum(x['comision'] for x in salida if x['cuenta_id'] == cid and x['comision_cobrada'])
        filas.append({'id': cid, 'nombre': nombres[cid], 'ventas': len(vs), 'monto': monto, 'costos': costos, 'pauta': p,
                      'margen': margen, 'comision': comision, 'closer': closer, 'retorno': monto / p if p else None})
        resumen['ventas'] += len(vs)
        for k, val in (('monto', monto), ('costos', costos), ('pauta', p), ('margen', margen), ('comision', comision),
                       ('closer', closer), ('comision_cobrada', cobrada)):
            resumen[k] += val
    resumen['neto'] = resumen['comision'] - resumen['closer']
    resumen['por_cobrar'] = max(0.0, resumen['comision'] - resumen['comision_cobrada'])
    resumen['retorno'] = resumen['monto'] / resumen['pauta'] if resumen['pauta'] else None
    salida.sort(key=lambda x: (x['fecha'], x['id']), reverse=True)
    vendedores = {}
    for x in salida:
        if x.get('vendedor'):
            r = vendedores.setdefault(x['vendedor'], {'vendedor': x['vendedor'], 'ventas': 0, 'monto': 0.0, 'closer': 0.0})
            r['ventas'] += 1; r['monto'] += x['monto'] or 0; r['closer'] += x['closer']
    return {'ventas': salida, 'cuentas': filas, 'resumen': resumen,
            'vendedores': sorted(vendedores.values(), key=lambda r: -r['closer'])}


def _publico(v):
    return {'id': v['id'], 'cuenta_id': v['cuenta_id'], 'fecha': v['fecha'].isoformat(), 'contacto': v['contacto'] or '',
            'servicio': v['servicio'] or '', 'monto': v['monto'], 'costo': v['costo'], 'vendedor': v['vendedor'] or '',
            'notas': v['notas'] or '', 'cita_id': v['cita_id'], 'comision_cobrada': bool(v['comision_cobrada']),
            'quien': v['quien']}
