"""Dinero, usuarios por negocio, fuentes elegidas y monedas."""
import datetime as dt

from sqlalchemy import insert, select, update

from conftest import entrar
from servidor import db, dinero, monedas, worker
from servidor.config import Config


def test_fees_se_generan_solos_sin_duplicar(app):
    m = app.motor
    cu = [c for c in db.cuentas_de(m, 'tpa') if not c['propia']][0]
    with m.begin() as c:
        c.execute(update(db.cuentas).where(db.cuentas.c.id == cu['id']).values(plan_fee=750, alta=dt.date(2026, 9, 10)))
    dinero.generar_fees(m, 'tpa', dt.date(2026, 11, 17))
    dinero.generar_fees(m, 'tpa', dt.date(2026, 11, 17))
    fees = [x for x in dinero.cobros_de(m, 'tpa') if x['cuenta_id'] == cu['id'] and x['concepto'] == 'fee']
    assert sorted(x['periodo'] for x in fees) == ['2026-09', '2026-10', '2026-11']
    assert fees[0]['vence'].day == 10


def test_cobro_pagado_entra_en_finanzas(app, admin):
    r = admin.patch('/api/plastia/cobros/%d' % app.cobro_id, json={'pagado': '2026-11-10'}, headers={'X-CSRF': admin.csrf})
    assert r.status_code == 200
    f = admin.get('/api/plastia/finanzas?desde=2026-11-01&hasta=2026-11-30').get_json()
    assert f['ingresos']['Setups'] == 750 and f['gastos']['Herramientas'] == 97


def test_reparto_tpa_pauta_de_luis_y_transferencia_de_mateo(admin):
    cfg = {'socios': [['Mateo', 50], ['Luis', 50]], 'pagador_pauta': 'Luis'}
    movs = [{'tipo': 'transferencia', 'socio': 'Mateo', 'socio_destino': 'Luis', 'monto_usd': 300, 'fecha': '2026-11-05', 'concepto': ''}]
    r = dinero.reparto(cfg, movs, 1000, 2000)
    assert r['saldo'] == 200 and r['otro'] == 'Mateo'  # Mateo debía 500 y pasó 300
    luis = next(s for s in r['socios'] if s['nombre'] == 'Luis')
    assert luis['puso'] == 700 and luis['ganancia'] == 1000
    malo = {'tipo': 'transferencia', 'fecha': '2026-11-05', 'monto': 10, 'socio': 'Mateo', 'socio_destino': 'Pedro'}
    assert admin.post('/api/tpa/movimientos', json=malo, headers={'X-CSRF': admin.csrf}).status_code == 400
    bueno = dict(malo, socio_destino='Luis')
    assert admin.post('/api/tpa/movimientos', json=bueno, headers={'X-CSRF': admin.csrf}).status_code == 201


def test_resumen_inicio_tiene_la_forma_de_la_pantalla(admin):
    for n in ('plastia', 'tpa'):
        r = admin.get('/api/%s/resumen' % n).get_json()
        for k in ('cuentas', 'setups', 'proy', 'gastos', 'meses', 'hoy', 'conteoHoy', 'alertas', 'tareas'):
            assert k in r, (n, k)
        assert len(r['meses']) == 5 and any('Stripe' in g[0] for g in r['gastos'])
    assert 'pautaMov' in admin.get('/api/tpa/resumen').get_json()


def test_admin_de_un_solo_negocio(app):
    with app.motor.begin() as c:
        c.execute(insert(db.usuarios).values(email='luis@x.com', nombre='Luis', rol='admin', negocios=['tpa'], cuentas=[], menus=[], activo=True))
    luis = entrar(app, 'luis@x.com')
    assert luis.get('/api/sesion').get_json()['negocios'] == ['tpa']
    assert luis.get('/api/plastia/panel').status_code == 403
    assert luis.get('/api/tpa/finanzas').status_code == 200
    nuevo = {'email': 'z@x.com', 'rol': 'vendedor', 'negocios': ['plastia']}
    assert luis.post('/api/usuarios', json=nuevo, headers={'X-CSRF': luis.csrf}).status_code == 400
    emails = [u['email'] for u in luis.get('/api/usuarios').get_json()['usuarios']]
    assert 'closer@agencia.com' not in emails and 'admin@agencia.com' in emails


def test_admins_negocios_del_entorno(app):
    app.cfg.ADMINS = ['toprealestatefl@gmail.com']
    app.cfg.ADMINS_NEGOCIOS = {'toprealestatefl@gmail.com': ['tpa']}
    luis = entrar(app, 'toprealestatefl@gmail.com')
    assert luis.get('/api/sesion').get_json()['negocios'] == ['tpa']


def test_no_te_sacas_el_acceso(app, admin):
    with app.motor.connect() as c:
        yo = c.execute(select(db.usuarios.c.id).where(db.usuarios.c.email == 'admin@agencia.com')).first().id
    assert admin.patch('/api/usuarios/%d' % yo, json={'activo': False}, headers={'X-CSRF': admin.csrf}).status_code == 400


def test_portal_cuenta_ve_como_operador(app):
    with app.motor.begin() as c:
        c.execute(insert(db.usuarios).values(email='clinica@x.com', nombre='Clinica', rol='cuenta', negocios=['plastia'],
                                             cuentas=[app.clinica['id']], menus=[], activo=True))
    cli = entrar(app, 'clinica@x.com')
    assert cli.get('/api/plastia/agenda').status_code == 200
    assert cli.get('/api/plastia/finanzas').status_code == 403


def test_items_tablero(admin):
    r = admin.post('/api/plastia/items', json={'tipo': 'video', 'titulo': 'Testimonio', 'datos': {'costo': 40}}, headers={'X-CSRF': admin.csrf})
    assert r.status_code == 201
    url = '/api/plastia/items/%d' % r.get_json()['id']
    assert admin.patch(url, json={'columna': 'inventada'}, headers={'X-CSRF': admin.csrf}).status_code == 400
    assert admin.patch(url, json={'columna': 'editando'}, headers={'X-CSRF': admin.csrf}).status_code == 200
    d = admin.get('/api/plastia/items?tipo=video').get_json()
    assert d['items'][0]['columna'] == 'editando' and d['columnas'][0] == 'guiones'


def test_cuenta_guarda_fuentes_elegidas(app, admin):
    url = '/api/plastia/cuentas/%d' % app.clinica['id']
    cuerpo = {'calendarios': [{'id': 'cal1', 'nombre': 'Valoracion', 'tipo': 'calificacion'}],
              'campanas': [{'id': '123', 'nombre': 'Plastia'}], 'moneda': 'cop', 'alta': '2026-10-01'}
    assert admin.patch(url, json=cuerpo, headers={'X-CSRF': admin.csrf}).status_code == 200
    c = next(c for c in admin.get('/api/plastia/cuentas').get_json() if c['id'] == app.clinica['id'])
    assert c['moneda'] == 'COP' and c['campanas'][0]['id'] == '123' and c['alta'] == '2026-10-01'
    malo = {'calendarios': [{'id': 'x', 'tipo': 'otro'}]}
    assert admin.patch(url, json=malo, headers={'X-CSRF': admin.csrf}).status_code == 400


def test_worker_filtra_campanas_y_pasa_a_usd(tmp_path):
    class MetaFalsa:
        def moneda(self, act):
            return 'COP'

        def insights(self, act, desde, hasta):
            fila = {'fecha': '2026-11-15', 'adset_name': '', 'impresiones': 1, 'clics': 1, 'leads': 1}
            return [dict(fila, ad_id='a1', ad_name='TPA', campaign_id='c1', campaign_name='TPA', gasto=400000.0),
                    dict(fila, ad_id='a2', ad_name='Otra cosa', campaign_id='c2', campaign_name='Curso', gasto=999.0)]
    cfg = Config(DATABASE_URL='sqlite:///' + str(tmp_path / 'w.db'), SECRET_KEY='x', CRM_TOKENS={})
    cuentas = [{'id': 1, 'nombre': 'Realtor', 'grupo': '', 'propia': False, 'crm_location_id': '', 'meta_cuentas': ['act_1'],
                'youtube_cuentas': [], 'campanas': [{'id': 'c1', 'nombre': 'TPA'}]}]
    datos, _, _ = worker.armar(cfg, 'tpa', cuentas, dt.date(2026, 11, 17), meta=MetaFalsa(), tasas={'USD': 1, 'COP': 4000})
    assert datos['gasto'] == [['2026-11-15', 0, 100.0, 1, 1, 1]]


def test_tasa_manual_manda(app):
    t = monedas.tasas(app.motor, {'COP': 3900})
    assert t['COP'] == 3900 and monedas.a_usd(7800, 'COP', t) == 2


def test_migracion_agrega_columnas(tmp_path):
    import sqlite3
    ruta = tmp_path / 'vieja.db'
    con = sqlite3.connect(ruta)
    con.execute('CREATE TABLE cuentas (id INTEGER PRIMARY KEY, negocio VARCHAR(30) NOT NULL, nombre VARCHAR(200) NOT NULL)')
    con.commit()
    con.close()
    db.conectar('sqlite:///' + str(ruta))
    cols = {r[1] for r in sqlite3.connect(ruta).execute('PRAGMA table_info(cuentas)')}
    assert {'moneda', 'calendarios', 'campanas', 'plan_fee'} <= cols
