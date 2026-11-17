"""Cada ruta × cada rol × cuenta ajena. Si aparece una ruta /api nueva sin su caso, test_todas_las_rutas_tienen_caso falla."""
import pytest

from conftest import entrar

# ruta -> (método, quiénes pueden: rol -> código esperado)
CASOS = {
    '/api/sesion': ('GET', {'anon': 401, 'admin': 200, 'vendedor': 200, 'operador': 200}),
    '/api/login-opciones': ('GET', {'anon': 200, 'admin': 200, 'vendedor': 200, 'operador': 200}),
    '/api/<negocio>/panel': ('GET', {'anon': 401, 'admin': 200, 'vendedor': 200, 'operador': 403}),
    '/api/<negocio>/trazabilidad': ('GET', {'anon': 401, 'admin': 200, 'vendedor': 200, 'operador': 403}),
    '/api/<negocio>/cuentas': ('GET', {'anon': 401, 'admin': 200, 'vendedor': 403, 'operador': 403}),
    '/api/<negocio>/cuentas#POST': ('POST', {'anon': 401, 'admin': 201, 'vendedor': 403, 'operador': 403}),
    '/api/<negocio>/cuentas/<int:cuenta_id>': ('PATCH', {'anon': 401, 'admin': 200, 'vendedor': 403, 'operador': 403}),
    '/api/<negocio>/indicadores': ('GET', {'anon': 401, 'admin': 200, 'vendedor': 403, 'operador': 403}),
    '/api/<negocio>/agenda': ('GET', {'anon': 401, 'admin': 200, 'vendedor': 200, 'operador': 200}),
    '/api/<negocio>/seguimientos': ('GET', {'anon': 401, 'admin': 200, 'vendedor': 200, 'operador': 403}),
    '/api/<negocio>/citas/<cita_id>/resultado': ('POST', {'anon': 401, 'admin': 200, 'vendedor': 200, 'operador': 403}),
    '/api/<negocio>/ventas': ('GET', {'anon': 401, 'admin': 200, 'vendedor': 200, 'operador': 200}),
    '/api/<negocio>/ventas#POST': ('POST', {'anon': 401, 'admin': 201, 'vendedor': 201, 'operador': 201}),
    '/api/<negocio>/ventas/<int:venta_id>': ('PATCH', {'anon': 401, 'admin': 200, 'vendedor': 403, 'operador': 403}),
    '/api/<negocio>/contactos': ('GET', {'anon': 401, 'admin': 200, 'vendedor': 200, 'operador': 200}),
    '/api/<negocio>/cuentas/<int:cuenta_id>/fuentes': ('GET', {'anon': 401, 'admin': 200, 'vendedor': 403, 'operador': 403}),
    '/api/<negocio>/cobros': ('GET', {'anon': 401, 'admin': 200, 'vendedor': 403, 'operador': 403}),
    '/api/<negocio>/cobros#POST': ('POST', {'anon': 401, 'admin': 201, 'vendedor': 403, 'operador': 403}),
    '/api/<negocio>/cobros/<int:cobro_id>': ('PATCH', {'anon': 401, 'admin': 200, 'vendedor': 403, 'operador': 403}),
    '/api/<negocio>/movimientos': ('GET', {'anon': 401, 'admin': 200, 'vendedor': 403, 'operador': 403}),
    '/api/<negocio>/movimientos#POST': ('POST', {'anon': 401, 'admin': 201, 'vendedor': 403, 'operador': 403}),
    '/api/<negocio>/movimientos/<int:mov_id>': ('PATCH', {'anon': 401, 'admin': 200, 'vendedor': 403, 'operador': 403}),
    '/api/<negocio>/finanzas': ('GET', {'anon': 401, 'admin': 200, 'vendedor': 403, 'operador': 403}),
    '/api/<negocio>/resumen': ('GET', {'anon': 401, 'admin': 200, 'vendedor': 403, 'operador': 403}),
    '/api/<negocio>/ventas-agencia': ('GET', {'anon': 401, 'admin': 200, 'vendedor': 403, 'operador': 403}),
    '/api/<negocio>/items': ('GET', {'anon': 401, 'admin': 200, 'vendedor': 200, 'operador': 403}),
    '/api/<negocio>/items#POST': ('POST', {'anon': 401, 'admin': 201, 'vendedor': 201, 'operador': 403}),
    '/api/<negocio>/items/<int:item_id>': ('PATCH', {'anon': 401, 'admin': 200, 'vendedor': 200, 'operador': 403}),
    '/api/<negocio>/semanal': ('GET', {'anon': 401, 'admin': 200, 'vendedor': 200, 'operador': 403}),
    '/api/<negocio>/rendimiento': ('GET', {'anon': 401, 'admin': 200, 'vendedor': 200, 'operador': 403}),
    '/api/<negocio>/conversaciones': ('GET', {'anon': 401, 'admin': 200, 'vendedor': 200, 'operador': 403}),
    '/api/<negocio>/conversaciones/<conv_id>': ('GET', {'anon': 401, 'admin': 404, 'vendedor': 404, 'operador': 403}),
    '/api/<negocio>/conversaciones/<conv_id>#POST': ('POST', {'anon': 401, 'admin': 404, 'vendedor': 404, 'operador': 403}),
    '/api/usuarios': ('GET', {'anon': 401, 'admin': 200, 'vendedor': 403, 'operador': 403}),
    '/api/usuarios#POST': ('POST', {'anon': 401, 'admin': 201, 'vendedor': 403, 'operador': 403}),
    '/api/usuarios/<int:usuario_id>': ('PATCH', {'anon': 401, 'admin': 200, 'vendedor': 403, 'operador': 403}),
    '/api/<negocio>/indicadores#PUT': ('PUT', {'anon': 401, 'admin': 200, 'vendedor': 403, 'operador': 403}),
}
EXCLUIDAS = {'/auth/salir'}  # escritura sin datos de cuentas: probada aparte


def _url(regla, app):
    return (regla.split('#')[0].replace('<negocio>', 'plastia').replace('<int:cuenta_id>', str(app.clinica['id']))
            .replace('<cita_id>', app.cita_id).replace('<int:venta_id>', str(app.venta_id)).replace('<int:cobro_id>', str(app.cobro_id))
            .replace('<int:mov_id>', str(app.mov_id)).replace('<int:item_id>', str(app.item_id)).replace('<conv_id>', 'conv1')
            .replace('<int:usuario_id>', str(app.usuario_id)))


def test_todas_las_rutas_tienen_caso(app):
    rutas = {r.rule for r in app.url_map.iter_rules() if r.rule.startswith('/api/')}
    con_caso = {k.split('#')[0] for k in CASOS}
    assert rutas - con_caso == set(), 'Rutas sin test de permisos: %s' % (rutas - con_caso)


@pytest.mark.parametrize('regla', list(CASOS))
@pytest.mark.parametrize('rol', ['anon', 'admin', 'vendedor', 'operador'])
def test_permisos_por_rol(app, regla, rol):
    metodo, esperado = CASOS[regla]
    email = {'admin': 'admin@agencia.com', 'vendedor': 'closer@agencia.com', 'operador': 'doctor@clinica.com'}.get(rol)
    cli = entrar(app, email) if email else app.test_client()
    cli.csrf = getattr(cli, 'csrf', '')
    cuerpo = ({'asistencia': 'asistio'} if 'resultado' in regla else
              {'cuenta_id': app.clinica['id'], 'fecha': '2026-11-10', 'monto': 1000} if 'ventas' in regla else
              {'cuenta_id': app.clinica['id'], 'concepto': 'setup', 'monto': 750} if regla == '/api/<negocio>/cobros#POST' else
              {'pagado': '2026-11-10'} if 'cobro_id' in regla else
              {'tipo': 'gasto', 'fecha': '2026-11-10', 'monto': 50, 'categoria': 'Herramientas'} if regla == '/api/<negocio>/movimientos#POST' else
              {'borrar': True} if 'mov_id' in regla else
              {'tipo': 'tarea', 'titulo': 'Llamar'} if regla == '/api/<negocio>/items#POST' else
              {'columna': 'hecho'} if 'item_id' in regla else
              {'texto': 'hola', 'contacto_id': 'k1', 'cuenta_id': app.clinica['id']} if 'conv_id' in regla else
              {'email': 'nuevo@agencia.com', 'rol': 'vendedor', 'negocios': ['plastia']} if regla == '/api/usuarios#POST' else
              {'nombre': 'Closer 2'} if 'usuario_id' in regla else
              {'nombre': 'Clínica nueva'} if metodo in ('POST', 'PATCH')
              else {'valores': {}} if metodo == 'PUT' else None)
    q = ('?cuenta_id=%d' % app.clinica['id'] if regla.endswith('<conv_id>') and metodo == 'GET' else
         '?tipo=tarea' if regla == '/api/<negocio>/items' else '')
    r = cli.open(_url(regla, app) + q, method=metodo, json=cuerpo, headers={'X-CSRF': cli.csrf})
    assert r.status_code == esperado[rol], (regla, rol, r.status_code)


def test_escritura_sin_csrf_es_403(admin):
    r = admin.post('/api/plastia/cuentas', json={'nombre': 'X'})
    assert r.status_code == 403
    r = admin.post('/api/plastia/cuentas', json={'nombre': 'X'}, headers={'X-CSRF': 'otro'})
    assert r.status_code == 403


def test_usuario_inactivo_no_entra(app):
    cli = entrar(app, 'baja@agencia.com')
    assert cli.get('/api/sesion').status_code == 401


def test_email_no_cargado_no_entra(app):
    cli = entrar(app, 'intruso@gmail.com')
    assert cli.get('/api/sesion').status_code == 401


def test_vendedor_solo_ve_sus_cuentas(app, closer):
    r = closer.get('/api/plastia/panel?dias=30').get_json()
    assert [c['id'] for c in r['cuentas_disponibles']] == [app.clinica['id']]
    assert all(f['id'] == app.clinica['id'] for f in r['cuentas'])


def test_vendedor_no_amplia_con_parametro(app, closer):
    otras = ','.join(str(i) for i in range(1, 30))
    r = closer.get('/api/plastia/panel?dias=30&cuentas=' + otras).get_json()
    assert [c['id'] for c in r['cuentas_disponibles']] == [app.clinica['id']]


def test_vendedor_no_ve_negocio_ajeno(closer):
    assert closer.get('/api/tpa/panel').status_code == 403


def test_vendedor_no_ve_ambito_agencia(closer):
    assert closer.get('/api/plastia/panel?ambito=agencia').status_code == 403


def test_admin_ve_agencia_solo_cuenta_propia(admin):
    r = admin.get('/api/plastia/panel?ambito=agencia&dias=30').get_json()
    assert [c['nombre'] for c in r['cuentas_disponibles']] == ['Plastia Partners (propia)']


def test_negocio_inexistente_404(admin):
    assert admin.get('/api/otro/panel').status_code == 404


def test_cuentas_no_devuelve_tokens(admin):
    filas = admin.get('/api/plastia/cuentas').get_json()
    assert filas and all('token' not in k or k == 'tiene_token' for f in filas for k in f)


def test_alta_queda_en_auditoria(app, admin):
    from sqlalchemy import select
    from servidor import db
    admin.post('/api/plastia/cuentas', json={'nombre': 'Clínica Auditada', 'meta_cuentas': ['act_1']}, headers={'X-CSRF': admin.csrf})
    with app.motor.connect() as c:
        filas = c.execute(select(db.auditoria).where(db.auditoria.c.accion == 'crear_cuenta')).all()
    assert len(filas) == 1 and filas[0].quien == 'admin@agencia.com'


def test_alta_valida_campos(admin):
    r = admin.post('/api/plastia/cuentas', json={'nombre': 'X', 'meta_cuentas': 'act_1'}, headers={'X-CSRF': admin.csrf})
    assert r.status_code == 400


def test_cabeceras_de_seguridad(admin):
    r = admin.get('/api/sesion')
    assert r.headers['X-Content-Type-Options'] == 'nosniff'
    assert "script-src 'self'" in r.headers['Content-Security-Policy']
    assert r.headers['Cache-Control'] == 'no-store'


def test_no_sirve_codigo_del_servidor(admin):
    assert admin.get('/servidor/config.py').status_code == 404
    assert admin.get('/../servidor/config.py').status_code == 404


def test_login_dev_apagado_en_produccion(app):
    app.cfg.DEV = False
    assert app.test_client().post('/auth/dev', data={'email': 'admin@agencia.com'}).status_code == 404
