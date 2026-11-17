"""Registro de ventas: comisión de Plastia (25% de venta − costos − pauta, closer 25% de eso), permisos y contactos."""
import datetime as dt

from servidor import ventas


def _venta(id_, cuenta, monto, costo, vendedor='closer@x.com', cobrada=False):
    return {'id': id_, 'cuenta_id': cuenta, 'fecha': dt.date(2026, 11, 5), 'contacto': 'X', 'servicio': 'S', 'monto': monto,
            'costo': costo, 'vendedor': vendedor, 'notas': '', 'cita_id': None, 'comision_cobrada': cobrada, 'quien': 'a'}


def test_comision_plastia():
    r = ventas.calcular('plastia', [_venta(1, 1, 10000, 3000), _venta(2, 1, 5000, 2000, vendedor='')],
                        [{'id': 1, 'nombre': 'C'}], {1: 2000})
    s = r['resumen']
    assert s['margen'] == 8000 and s['comision'] == 2000  # 25% de (15000 − 5000 − 2000)
    # la pauta se reparte según el margen de cada venta: 7000/10000 y 3000/10000
    v1 = next(v for v in r['ventas'] if v['id'] == 1)
    assert v1['pauta'] == 1400 and v1['comision'] == 1400 and v1['closer'] == 350
    assert next(v for v in r['ventas'] if v['id'] == 2)['closer'] == 0  # sin closer
    assert s['neto'] == 2000 - 350


def test_pauta_mayor_que_margen_no_da_negativo():
    r = ventas.calcular('plastia', [_venta(1, 1, 1000, 500)], [{'id': 1, 'nombre': 'C'}], {1: 2000})
    assert r['resumen']['comision'] == 0 and r['ventas'][0]['comision'] == 0


def test_tpa_sin_comision_con_retorno():
    r = ventas.calcular('tpa', [_venta(1, 1, 9000, None)], [{'id': 1, 'nombre': 'R'}], {1: 1500})
    assert r['resumen']['comision'] == 0 and r['cuentas'][0]['retorno'] == 6


def _post(cli, cuerpo):
    return cli.post('/api/plastia/ventas', json=cuerpo, headers={'X-CSRF': cli.csrf})


def test_alta_y_lista(app, admin):
    r = _post(admin, {'cuenta_id': app.clinica['id'], 'fecha': '2026-11-12', 'monto': 8000, 'costo': 2000, 'contacto': 'Beto Prueba', 'servicio': 'Lipo'})
    assert r.status_code == 201
    d = admin.get('/api/plastia/ventas?desde=2026-11-01&hasta=2026-11-30').get_json()
    fila = next(c for c in d['cuentas'] if c['id'] == app.clinica['id'])
    assert fila['moneda'] == 'COP' and fila['monto'] == 13000  # la clínica vende en pesos
    assert d['resumen']['ventas'] == 2 and abs(d['resumen']['monto'] - 13000 / d['tasas']['COP']) < 0.01  # totales en USD


def test_validaciones(app, admin):
    assert _post(admin, {'cuenta_id': app.clinica['id'], 'fecha': '2026-11-12'}).status_code == 400  # sin monto
    assert _post(admin, {'cuenta_id': app.clinica['id'], 'fecha': 'ayer', 'monto': 1}).status_code == 400
    assert _post(admin, {'cuenta_id': 99999, 'fecha': '2026-11-12', 'monto': 1}).status_code == 400
    assert _post(admin, {'cuenta_id': app.clinica['id'], 'fecha': '2026-11-12', 'monto': -5}).status_code == 400


def test_vendedor_registra_a_su_nombre_y_no_marca_cobrada(app, closer):
    r = _post(closer, {'cuenta_id': app.clinica['id'], 'fecha': '2026-11-12', 'monto': 100, 'vendedor': 'otro@x.com', 'comision_cobrada': True})
    assert r.status_code == 201
    v = next(v for v in closer.get('/api/plastia/ventas').get_json()['ventas'] if v['id'] == r.get_json()['id'])
    assert v['vendedor'] == 'closer@agencia.com' and v['comision_cobrada'] is False
    # y puede corregir lo suyo
    assert closer.patch('/api/plastia/ventas/%d' % v['id'], json={'monto': 200}, headers={'X-CSRF': closer.csrf}).status_code == 200


def test_vendedor_no_carga_en_cuenta_ajena(app, closer):
    from servidor import db
    otra = [c for c in db.cuentas_de(app.motor, 'plastia') if c['id'] != app.clinica['id'] and not c['propia']][0]
    assert _post(closer, {'cuenta_id': otra['id'], 'fecha': '2026-11-12', 'monto': 1}).status_code == 400


def test_borrar_solo_admin_y_es_desactivar(app, admin):
    r = admin.patch('/api/plastia/ventas/%d' % app.venta_id, json={'borrar': True}, headers={'X-CSRF': admin.csrf})
    assert r.status_code == 200
    assert admin.get('/api/plastia/ventas').get_json()['resumen']['ventas'] == 0


def test_contactos_busca_y_junta_ventas(app, admin):
    d = admin.get('/api/plastia/contactos?q=ana ejemplo').get_json()
    con_venta = [p for p in d['contactos'] if p['ventas']]
    assert con_venta and con_venta[0]['ventas'][0]['servicio'] == 'Rinoplastia'
    assert all('ana ejemplo' in p['nombre'].lower() for p in d['contactos'])
    todos = admin.get('/api/plastia/contactos').get_json()
    assert todos['total'] > 5 and all(p['citas'] or p['ventas'] for p in todos['contactos'])


def test_contactos_vendedor_solo_sus_cuentas(app, closer):
    d = closer.get('/api/plastia/contactos').get_json()
    assert d['contactos'] and {p['cuenta_id'] for p in d['contactos']} == {app.clinica['id']}
