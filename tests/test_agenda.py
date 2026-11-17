"""Agenda: calendario con datos personales filtrados por cuenta, resultado de la llamada y seguimientos."""
from servidor import db


def _post(cli, cita, cuerpo):
    return cli.post('/api/plastia/citas/%s/resultado' % cita, json=cuerpo, headers={'X-CSRF': cli.csrf})


def test_agenda_trae_semana_y_datos_personales(admin):
    r = admin.get('/api/plastia/agenda').get_json()
    assert r['desde'] == '2026-11-16' and r['hasta'] == '2026-11-22'
    assert r['citas'] and all(c['nombre'] and r['desde'] <= c['fecha'] <= r['hasta'] for c in r['citas'])
    assert set(r['kpi']) == {'agendadas', 'asistio', 'pct_asistencia', 'califica', 'avanza', 'pct_cierre'}


def test_vendedor_solo_ve_citas_de_sus_cuentas(app, closer):
    r = closer.get('/api/plastia/agenda?desde=2026-10-20&hasta=2026-11-20').get_json()
    assert r['citas'] and {c['cuenta_id'] for c in r['citas']} == {app.clinica['id']}


def test_rango_invalido(admin):
    assert admin.get('/api/plastia/agenda?desde=2026-11-20&hasta=2026-11-01').status_code == 400
    assert admin.get('/api/plastia/agenda?desde=2026-01-01&hasta=2026-11-01').status_code == 400
    assert admin.get('/api/plastia/agenda?desde=ayer').status_code == 400


def test_resultado_y_asistencia_manda_sobre_crm(app, admin):
    r = _post(admin, app.cita_id, {'asistencia': 'no_asistio', 'califica': False, 'notas': 'No contestó'})
    assert r.status_code == 200
    c = r.get_json()
    assert c['estado'] == 'no_asistio' and c['resultado']['notas'] == 'No contestó'
    r = _post(admin, app.cita_id, {'asistencia': None})  # quitar la marca vuelve al estado de GHL
    assert r.get_json()['estado'] == r.get_json()['estado_crm']
    assert r.get_json()['resultado']['notas'] == 'No contestó'  # lo demás queda


def test_seguimiento_aparece_en_su_columna(app, admin):
    _post(admin, app.cita_id, {'asistencia': 'asistio', 'resultado': 'seguimiento', 'monto': 1500, 'proximo': '2026-11-15'})
    r = admin.get('/api/plastia/seguimientos').get_json()
    assert r['activos'] == 1 and r['vencidos'] == 1 and r['monto'] == 1500
    assert r['columnas']['vencidos'][0]['id'] == app.cita_id
    _post(admin, app.cita_id, {'proximo': '2026-11-18'})  # «Mañana»
    r = admin.get('/api/plastia/seguimientos').get_json()
    assert r['vencidos'] == 0 and len(r['columnas']['manana']) == 1


def test_validaciones_resultado(app, admin):
    assert _post(admin, app.cita_id, {'asistencia': 'quizas'}).status_code == 400
    assert _post(admin, app.cita_id, {'resultado': 'otro'}).status_code == 400
    assert _post(admin, app.cita_id, {'proximo': '15/11/2026'}).status_code == 400
    assert _post(admin, app.cita_id, {'monto': -1}).status_code == 400
    assert _post(admin, app.cita_id, {'califica': 'si'}).status_code == 400
    assert _post(admin, app.cita_id, {}).status_code == 400
    assert _post(admin, 'no-existe', {'asistencia': 'asistio'}).status_code == 404


def test_vendedor_no_marca_citas_ajenas(app, closer):
    d = db.leer(app.motor, 'datos:plastia')
    i = next(i for i, x in enumerate(d['citas']) if x[3] != app.clinica['id'] and x[4] == 'calificacion')
    assert _post(closer, 'demo-%d' % i, {'asistencia': 'asistio'}).status_code == 404


def test_resultado_queda_en_auditoria(app, admin):
    from sqlalchemy import select
    _post(admin, app.cita_id, {'resultado': 'avanza'})
    with app.motor.connect() as c:
        filas = c.execute(select(db.auditoria).where(db.auditoria.c.accion == 'resultado_cita')).all()
    assert len(filas) == 1 and filas[0].objeto == 'plastia:' + app.cita_id
