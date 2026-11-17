import datetime as dt
import os
import sys

import pytest
from sqlalchemy import insert

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from servidor import create_app, db, demo  # noqa: E402
from servidor.config import Config  # noqa: E402

HOY = dt.date(2026, 11, 17)


@pytest.fixture
def app(tmp_path):
    cfg = Config(DATABASE_URL='sqlite:///' + str(tmp_path / 'p.db'), SECRET_KEY='prueba', DEV=True, TESTING=True,
                 ADMINS=['admin@agencia.com'], DOMINIO_ADMIN='', DATOS_DEMO=True, CRM_TOKENS={'loc1': 'x'})
    a = create_app(cfg)
    m = a.motor
    for n in ('plastia', 'tpa'):
        demo.sembrar_cuentas(m, n)
        cuentas = db.cuentas_de(m, n)
        d = demo.datos(n, cuentas, HOY)
        db.publicar(m, 'datos:' + n, d)
        db.publicar(m, 'privado:' + n, demo.privado(d))
    plastia = db.cuentas_de(m, 'plastia')
    clinica = [c for c in plastia if not c['propia']][0]
    with m.begin() as c:
        c.execute(insert(db.usuarios).values(email='admin@agencia.com', nombre='Admin', rol='admin', negocios=['plastia', 'tpa'], cuentas=[], menus=[], activo=True))
        c.execute(insert(db.usuarios).values(email='closer@agencia.com', nombre='Closer', rol='vendedor', negocios=['plastia'], cuentas=[clinica['id']], menus=[], activo=True))
        c.execute(insert(db.usuarios).values(email='doctor@clinica.com', nombre='Doctor', rol='operador', negocios=['plastia'], cuentas=[clinica['id']], menus=[], activo=True))
        c.execute(insert(db.usuarios).values(email='baja@agencia.com', nombre='Baja', rol='admin', negocios=['plastia'], cuentas=[], menus=[], activo=False))
    a.clinica = clinica
    d = db.leer(m, 'datos:plastia')
    i = next(i for i, x in enumerate(d['citas']) if x[3] == clinica['id'] and x[4] == 'calificacion')
    a.cita_id = 'demo-%d' % i
    with m.begin() as c:  # una venta cargada por el admin (el vendedor no la puede editar: no es suya)
        a.venta_id = c.execute(insert(db.ventas).values(negocio='plastia', cuenta_id=clinica['id'], fecha=dt.date(2026, 11, 5), contacto='Ana Ejemplo',
                                                        servicio='Rinoplastia', monto=5000, costo=1500, vendedor='closer@agencia.com',
                                                        quien='admin@agencia.com', activo=True)).inserted_primary_key[0]
    return a


def entrar(app, email):
    cli = app.test_client()
    cli.post('/auth/dev', data={'email': email})
    r = cli.get('/api/sesion')
    cli.csrf = r.get_json()['csrf'] if r.status_code == 200 else ''
    return cli


@pytest.fixture
def admin(app):
    return entrar(app, 'admin@agencia.com')


@pytest.fixture
def closer(app):
    return entrar(app, 'closer@agencia.com')


@pytest.fixture
def operador(app):
    return entrar(app, 'doctor@clinica.com')
