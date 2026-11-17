"""Datos de ejemplo (ficticios) para ver la suite antes de conectar GHL, Meta y YouTube.

Se usan solo con DATOS_DEMO=1 (por defecto cuando no hay META_ACCESS_TOKEN). Nombres y montos inventados.
"""
import datetime as dt
import random

from sqlalchemy import insert

from . import db
from .config import NEGOCIOS

CUENTAS_DEMO = {
    'plastia': ['Plastia Partners (propia)', 'Clínica Aurora', 'Centro Bellavista', 'Dr. Ejemplo Ruiz', 'Clínica Mirador', 'Estética Norte'],
    'tpa': ['TPA (propia)', 'Realtor Alfa', 'Realtor Beta', 'Realtor Gamma', 'Realtor Delta', 'Realtor Épsilon', 'Realtor Zeta'],
}
ANGULOS = {
    'plastia': ['Valoración pagada · VSL', 'Antes y después', 'Testimonio paciente', 'Doctor explica', 'Financiación'],
    'tpa': ['Listings gratis · VSL', 'Home valuation', 'Guía del comprador', 'Caso de éxito', 'Retargeting'],
    'propia': ['Masterclass', 'Caso de cliente', 'Video largo YouTube', 'Retargeting llamada'],
}


def sembrar_cuentas(motor, negocio):
    if db.cuentas_de(motor, negocio, solo_activas=False):
        return
    with motor.begin() as c:
        for i, nombre in enumerate(CUENTAS_DEMO[negocio]):
            plan = NEGOCIOS[negocio].get('plan') or {}
            c.execute(insert(db.cuentas).values(negocio=negocio, nombre=nombre, propia=(i == 0),
                                                grupo='Propia' if i == 0 else ('Nuevas' if i > 3 else 'Activas'),
                                                crm_location_id='', meta_cuentas=[], youtube_cuentas=[], activo=True,
                                                moneda='USD' if i == 0 else NEGOCIOS[negocio].get('moneda_cuentas', 'USD'),
                                                plan_setup=None if i == 0 else plan.get('setup'), plan_fee=None if i == 0 else (plan.get('fee') or None),
                                                alta=None if i == 0 else dt.date(2026, 7 + min(i, 4), 3 + i)))


def datos(negocio, cuentas, hoy, dias=90, proximos=14):
    rnd = random.Random(negocio + hoy.isoformat()[:7])  # estable dentro del mes
    cfg = NEGOCIOS[negocio]
    anuncios, gasto, citas = [], [], []
    inicio = hoy - dt.timedelta(days=dias)
    for c in cuentas:
        propia = c.get('propia')
        paso = cfg['agencia']['paso'] if propia else next(iter(cfg['embudos'].values()))['paso']
        calidad = rnd.uniform(0.55, 1.7)  # <1 cuenta buena, >1 cuenta cara
        if not propia and rnd.random() < 0.15:
            continue  # una cuenta sin actividad, como en la vida real
        angulos = ANGULOS['propia' if propia else negocio]
        mis = []
        for j in range(rnd.randint(3, 5)):
            plataforma = 'youtube' if (j == 2 and (propia or negocio == 'tpa')) else 'meta'
            anuncios.append({'id': f'demo-{c["id"]}-{j}', 'nombre': f'{angulos[j % len(angulos)]} · v{j + 1}',
                             'campana': ('YouTube · ' if plataforma == 'youtube' else 'Meta · ') + ('Venta propia' if propia else 'Captación'),
                             'conjunto': 'Público amplio', 'cuenta_id': c['id'], 'plataforma': plataforma})
            mis.append((len(anuncios) - 1, rnd.uniform(0.5, 1.8) * calidad))
        for d in range(dias + 1):
            dia = inicio + dt.timedelta(days=d)
            for ia, factor in mis:
                g = round(rnd.uniform(8, 40) * (1.4 if propia else 1), 2)
                cpl = rnd.uniform(6, 14) * factor * (2.5 if propia else {'plastia': 2.4, 'tpa': 1.5}.get(negocio, 1))
                leads = int(g / cpl + rnd.random())
                gasto.append([dia.isoformat(), ia, g, int(g * rnd.uniform(60, 110)), int(g * rnd.uniform(1.2, 2.4)), leads])
                # cuentas y anuncios caros agendan menos: la tasa baja con el factor
                n_citas = sum(1 for _ in range(leads) if rnd.random() < min(0.4, 0.26 / factor))
                for _ in range(n_citas):
                    _cita(rnd, citas, dia, c['id'], paso, ia, hoy, proximos)
        for _ in range(rnd.randint(3, 9)):  # citas que no traen anuncio de origen
            _cita(rnd, citas, inicio + dt.timedelta(days=rnd.randint(0, dias)), c['id'], paso, -1, hoy, proximos)
    return {'negocio': negocio, 'hoy': hoy.isoformat(), 'actualizado': db.ahora().isoformat() + 'Z',
            'cuentas': [{'id': c['id'], 'nombre': c['nombre'], 'grupo': c.get('grupo'), 'propia': c.get('propia', False)} for c in cuentas],
            'anuncios': anuncios, 'gasto': gasto, 'citas': citas, 'demo': True}


def _cita(rnd, citas, creada, cuenta_id, paso, ia, hoy, proximos):
    fecha = creada + dt.timedelta(days=rnd.choice([0, 1, 1, 2, 2, 3, 4, 6]))
    if fecha > hoy + dt.timedelta(days=proximos):
        return
    if fecha < hoy:
        r = rnd.random()
        estado = 'asistio' if r < 0.55 else 'no_asistio' if r < 0.78 else 'cancelada' if r < 0.9 else 'confirmada'
    else:
        estado = 'confirmada'
    citas.append([fecha.isoformat(), rnd.choice(range(9 * 60, 19 * 60, 30)), creada.isoformat(), cuenta_id, paso, estado, ia])


NOMBRES = ['Valeria', 'Martín', 'Camila', 'Mateo', 'Sofía', 'Lucas', 'Elena', 'Diego', 'Paula', 'Andrés', 'Laura', 'Tomás',
           'Mariana', 'Gabriel', 'Lucía', 'Hugo', 'Carla', 'Iván']
APELLIDOS = ['Ejemplo', 'Demo', 'Prueba', 'Muestra', 'Ficticio', 'Modelo']


def privado(datos):
    """Nombres, teléfonos y emails inventados, alineados con datos['citas'] (mismo índice)."""
    rnd = random.Random('privado' + datos['negocio'])
    filas = []
    for i, _c in enumerate(datos['citas']):
        n, a = rnd.choice(NOMBRES), rnd.choice(APELLIDOS)
        filas.append(['demo-%d' % i, 'Cita', 'demo-contacto-%d' % i, '', '%s %s %s.' % (n, a, chr(65 + i % 26)),
                      '+1 555 01%02d' % (i % 100), '%s.%s@ejemplo.test' % (n.lower(), i)])
    return {'citas': filas}
