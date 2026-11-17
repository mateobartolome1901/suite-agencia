"""Indicadores: el admin carga las metas y el Panel de campañas las usa (con config.py como respaldo)."""
from sqlalchemy import select

from servidor import db


def _put(cli, cuerpo, negocio='plastia'):
    return cli.put('/api/%s/indicadores' % negocio, json=cuerpo, headers={'X-CSRF': cli.csrf})


def test_sin_cargar_usa_valor_de_fabrica(admin):
    r = admin.get('/api/plastia/panel?dias=30').get_json()
    assert r['objetivo'] == 60 and abs(r['objetivo_rojo'] - 78) < 0.01


def test_guardar_y_el_panel_lo_usa(admin):
    r = _put(admin, {'valores': {'emb_valoracion_costo_cita': 40, 'emb_valoracion_costo_rojo': 80, 'emb_valoracion_pct_asistencia': '65'}})
    assert r.status_code == 200
    assert r.get_json()['valores']['emb_valoracion_costo_cita'] == 40
    p = admin.get('/api/plastia/panel?dias=30').get_json()
    assert p['objetivo'] == 40 and p['objetivo_rojo'] == 80 and p['metas']['pct_asistencia'] == 65
    t = admin.get('/api/plastia/trazabilidad?dias=30').get_json()
    assert t['metas']['pct_asistencia'] == 65


def test_vaciar_vuelve_al_valor_de_fabrica(admin):
    _put(admin, {'valores': {'emb_valoracion_costo_cita': 40}})
    _put(admin, {'valores': {'emb_valoracion_costo_cita': None}})
    assert admin.get('/api/plastia/panel?dias=30').get_json()['objetivo'] == 60


def test_agencia_usa_su_objetivo(admin):
    _put(admin, {'valores': {'ag_costo_cita': 70}})
    assert admin.get('/api/plastia/panel?ambito=agencia&dias=30').get_json()['objetivo'] == 70


def test_objetivo_por_cuenta(app, admin):
    cid = app.clinica['id']
    assert _put(admin, {'cuentas': {str(cid): 25}}).status_code == 200
    fila = [f for f in admin.get('/api/plastia/panel?dias=30').get_json()['cuentas'] if f['id'] == cid][0]
    assert fila['objetivo'] == 25
    _put(admin, {'cuentas': {str(cid): ''}})
    fila = [f for f in admin.get('/api/plastia/panel?dias=30').get_json()['cuentas'] if f['id'] == cid][0]
    assert fila['objetivo'] == 60


def test_validaciones(admin):
    assert _put(admin, {'valores': {'clave_inventada': 1}}).status_code == 400
    assert _put(admin, {'valores': {'emb_valoracion_pct_asistencia': 120}}).status_code == 400
    assert _put(admin, {'valores': {'emb_valoracion_costo_cita': -5}}).status_code == 400
    assert _put(admin, {'valores': {'emb_valoracion_costo_cita': 'abc'}}).status_code == 400
    assert _put(admin, {'valores': {'emb_valoracion_costo_cita': True}}).status_code == 400
    assert _put(admin, ['no', 'es', 'objeto']).status_code == 400


def test_no_toca_cuentas_de_otro_negocio(app, admin):
    tpa = db.cuentas_de(app.motor, 'tpa')[0]['id']
    assert _put(admin, {'cuentas': {str(tpa): 10}}).status_code == 400


def test_negocios_separados(admin):
    _put(admin, {'valores': {'ag_costo_cita': 11}})
    assert admin.get('/api/tpa/indicadores').get_json()['valores'].get('ag_costo_cita') is None


def test_sin_csrf_403(admin):
    assert admin.put('/api/plastia/indicadores', json={'valores': {}}).status_code == 403


def test_queda_en_auditoria_y_ultimo_cambio(app, admin):
    _put(admin, {'valores': {'ag_cac': 300}})
    with app.motor.connect() as c:
        filas = c.execute(select(db.auditoria).where(db.auditoria.c.accion == 'editar_indicadores')).all()
    assert len(filas) == 1 and filas[0].quien == 'admin@agencia.com' and filas[0].objeto == 'plastia'
    assert admin.get('/api/plastia/indicadores').get_json()['ultimo']['quien'] == 'admin@agencia.com'
