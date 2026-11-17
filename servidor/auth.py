"""Login con Google (solo entran emails cargados y activos) y login de desarrollo local (DEV_LOGIN=1)."""
import secrets
import urllib.parse

import requests
from flask import Blueprint, abort, current_app, jsonify, redirect, request, session

from .seguridad import iniciar_sesion, limitar, requiere, usuario_actual

bp = Blueprint('auth', __name__)
GOOGLE_AUTH = 'https://accounts.google.com/o/oauth2/v2/auth'
GOOGLE_TOKEN = 'https://oauth2.googleapis.com/token'
GOOGLE_USERINFO = 'https://openidconnect.googleapis.com/v1/userinfo'


def _redireccion():
    return request.url_root.rstrip('/') + '/auth/google/vuelta'


@bp.get('/auth/google')
def google():
    cfg = current_app.cfg
    if not cfg.GOOGLE_CLIENT_ID:
        abort(404)
    limitar('login', 20)
    estado = secrets.token_urlsafe(24)
    session['oauth_estado'] = estado
    q = {'client_id': cfg.GOOGLE_CLIENT_ID, 'redirect_uri': _redireccion(), 'response_type': 'code',
         'scope': 'openid email profile', 'state': estado, 'prompt': 'select_account'}
    return redirect(GOOGLE_AUTH + '?' + urllib.parse.urlencode(q))


@bp.get('/auth/google/vuelta')
def google_vuelta():
    cfg = current_app.cfg
    limitar('login', 20)
    estado = session.pop('oauth_estado', None)
    if not estado or not secrets.compare_digest(estado, request.args.get('state', '')):
        abort(403)
    r = requests.post(GOOGLE_TOKEN, timeout=20, data={
        'code': request.args.get('code', ''), 'client_id': cfg.GOOGLE_CLIENT_ID, 'client_secret': cfg.GOOGLE_CLIENT_SECRET,
        'redirect_uri': _redireccion(), 'grant_type': 'authorization_code'})
    if r.status_code != 200:
        abort(403)
    info = requests.get(GOOGLE_USERINFO, timeout=20, headers={'Authorization': 'Bearer ' + r.json()['access_token']}).json()
    if not info.get('email_verified') or not iniciar_sesion(info.get('email', '')):
        current_app.logger.warning('Login rechazado: %s', info.get('email'))
        return redirect('/ingresar?error=sin-acceso')
    return redirect('/')


@bp.post('/auth/dev')
def dev():
    """Solo en local (DEV_LOGIN=1): entrar con un email cargado, sin Google."""
    if not current_app.cfg.DEV:
        abort(404)
    if not iniciar_sesion(request.form.get('email', '')):
        return redirect('/ingresar?error=sin-acceso')
    return redirect('/')


@bp.post('/auth/salir')
@requiere()
def salir():
    session.clear()
    return jsonify(ok=True)


@bp.get('/api/sesion')
@requiere()
def sesion():
    u = usuario_actual()
    negocios = list(current_app.negocios) if u['rol'] == 'admin' else [n for n in (u.get('negocios') or []) if n in current_app.negocios]
    return jsonify(email=u['email'], nombre=u['nombre'], rol=u['rol'], negocios=negocios, csrf=session.get('csrf'))


@bp.get('/api/login-opciones')
def opciones():
    cfg = current_app.cfg
    return jsonify(google=bool(cfg.GOOGLE_CLIENT_ID), dev=cfg.DEV)
