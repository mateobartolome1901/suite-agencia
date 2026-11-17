"""Sesión, roles, CSRF, filtro por cuenta y límite de pedidos.

Regla central: toda ruta que devuelve datos de cuentas a un no admin tiene que pasar por cuentas_visibles(). Si una
ruta marcada con @datos_de_cuentas responde sin haberlo hecho, el servidor corta con 500 y lo registra.
"""
import functools
import secrets
import time

from flask import abort, current_app, g, request, session
from sqlalchemy import select, update

from . import db

DURACION_SESION = 12 * 3600


def usuario_actual():
    if 'u' in g:
        return g.u
    g.u = None
    email = session.get('email')
    if not email or time.time() - session.get('desde', 0) > DURACION_SESION:
        return None
    with current_app.motor.connect() as c:
        fila = c.execute(select(db.usuarios).where(db.usuarios.c.email == email)).first()
    if fila and fila.activo:  # cada pedido vuelve a verificar que siga activo
        g.u = dict(fila._mapping)
        if g.u['rol'] == 'cuenta':  # portal del cliente: mismos permisos que el operador de la cuenta
            g.u['rol'] = 'operador'
    return g.u


def iniciar_sesion(email):
    email = email.strip().lower()
    motor = current_app.motor
    cfg = current_app.cfg
    with motor.begin() as c:
        fila = c.execute(select(db.usuarios).where(db.usuarios.c.email == email)).first()
        if not fila and email in cfg.ADMINS:  # los ADMINS del entorno se crean solos la primera vez
            c.execute(db.usuarios.insert().values(email=email, nombre=email.split('@')[0], rol='admin',
                                                  negocios=cfg.ADMINS_NEGOCIOS.get(email) or list(current_app.negocios),
                                                  cuentas=[], menus=[], activo=True))
            fila = c.execute(select(db.usuarios).where(db.usuarios.c.email == email)).first()
        if not fila or not fila.activo:
            return False
        if fila.rol == 'admin' and cfg.DOMINIO_ADMIN and not email.endswith('@' + cfg.DOMINIO_ADMIN) and email not in cfg.ADMINS:
            return False
        c.execute(update(db.usuarios).where(db.usuarios.c.id == fila.id).values(ultimo_ingreso=db.ahora()))
    session.clear()
    session.permanent = True
    session['email'] = email
    session['desde'] = time.time()
    session['csrf'] = secrets.token_urlsafe(24)
    return True


def requiere(*roles):
    """Login obligatorio (401) y, si se indican roles, uno de ellos (403)."""
    def deco(f):
        @functools.wraps(f)
        def envuelta(*a, **k):
            u = usuario_actual()
            if not u:
                abort(401)
            if roles and u['rol'] not in roles:
                abort(403)
            if request.method not in ('GET', 'HEAD', 'OPTIONS'):
                enviado = request.headers.get('X-CSRF', '')
                if not enviado or not secrets.compare_digest(enviado, session.get('csrf', '')):
                    abort(403)
            negocio = k.get('negocio')
            if negocio is not None:
                if negocio not in current_app.negocios:
                    abort(404)
                if negocio not in (u.get('negocios') or []):  # también el admin: Luis solo ve TPA
                    abort(403)
            return f(*a, **k)
        return envuelta
    return deco


def cuentas_visibles(u, negocio):
    """Ids de cuentas del negocio que el usuario puede ver. Marca que la ruta aplicó el filtro."""
    g.filtro_cuentas = True
    todas = db.cuentas_de(current_app.motor, negocio)
    if u['rol'] == 'admin':
        return todas
    permitidas = set(u.get('cuentas') or [])
    # los no admin nunca ven la subcuenta propia del negocio (ventas y campañas de la agencia)
    return [c for c in todas if c['id'] in permitidas and not c['propia']]


def datos_de_cuentas(f):
    @functools.wraps(f)
    def envuelta(*a, **k):
        g.filtro_cuentas = False
        resp = f(*a, **k)
        u = usuario_actual()
        if u and u['rol'] != 'admin' and not g.get('filtro_cuentas'):
            current_app.logger.error('Ruta %s respondió datos de cuentas sin filtrar', request.path)
            abort(500)
        return resp
    return envuelta


_pedidos = {}


def limitar(clave, maximo, ventana=60):
    """Límite simple por IP en memoria (por proceso)."""
    if current_app.cfg.TESTING:
        return
    ahora = time.time()
    k = (clave, request.remote_addr)
    lista = [t for t in _pedidos.get(k, []) if ahora - t < ventana]
    if len(lista) >= maximo:
        abort(429)
    lista.append(ahora)
    _pedidos[k] = lista


def cabeceras(resp):
    resp.headers['X-Content-Type-Options'] = 'nosniff'
    resp.headers['Referrer-Policy'] = 'same-origin'
    resp.headers['X-Frame-Options'] = 'DENY'
    resp.headers['Content-Security-Policy'] = (
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; "
        "form-action 'self' https://accounts.google.com")
    if not current_app.cfg.DEV:
        resp.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    if request.path.startswith('/api/'):
        resp.headers['Cache-Control'] = 'no-store'
    return resp
