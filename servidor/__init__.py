"""Suite de agencia multi-negocio: servidor web (Flask). Arranque: create_app()."""
import datetime as dt
import os

from flask import Flask, abort, jsonify, redirect, request, send_from_directory

from . import db
from .config import NEGOCIOS, Config
from .seguridad import cabeceras

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(RAIZ, 'suite')


def create_app(cfg=None):
    cfg = cfg or Config()
    app = Flask(__name__, static_folder=None)
    app.cfg = cfg
    app.negocios = NEGOCIOS
    app.secret_key = cfg.SECRET_KEY
    app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax', SESSION_COOKIE_SECURE=not cfg.DEV,
                      PERMANENT_SESSION_LIFETIME=dt.timedelta(hours=12))
    app.motor = db.conectar(cfg.DATABASE_URL)
    if os.environ.get('DETRAS_DE_PROXY') == '1':  # Caddy o Render adelante: respetar https y el dominio real
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    from .auth import bp as auth_bp
    from .api import bp as api_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)
    app.after_request(cabeceras)
    if cfg.WORKER_EN_WEB and not cfg.TESTING:
        from .worker import en_segundo_plano
        en_segundo_plano(cfg, app.motor)

    @app.errorhandler(401)
    @app.errorhandler(403)
    @app.errorhandler(404)
    @app.errorhandler(429)
    @app.errorhandler(500)
    def error(e):
        codigo = getattr(e, 'code', 500)
        if request.path.startswith('/api/'):
            return jsonify(error=codigo), codigo
        if codigo == 401:
            return redirect('/ingresar')
        return (f'Error {codigo}', codigo)

    @app.get('/')
    def inicio():
        return send_from_directory(WEB, 'index.html')

    @app.get('/ingresar')
    def ingresar():
        return send_from_directory(WEB, 'ingresar.html')

    @app.get('/<path:ruta>')
    def estaticos(ruta):
        # solo archivos de la carpeta web; nada de rutas con ..
        if '..' in ruta or ruta.startswith(('servidor', 'tests', '.')):
            abort(404)
        if not os.path.isfile(os.path.join(WEB, ruta)):
            abort(404)
        return send_from_directory(WEB, ruta)

    return app
