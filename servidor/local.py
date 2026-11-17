"""Correr la suite en local: python -m servidor.local

Lee .env si existe, activa el login de desarrollo, hace una lectura del worker (datos de ejemplo si no hay tokens)
y levanta el servidor en http://localhost:8765. Nunca usar en producción.
"""
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def cargar_env():
    ruta = os.path.join(RAIZ, '.env')
    if not os.path.exists(ruta):
        return
    for linea in open(ruta, encoding='utf-8'):
        linea = linea.split(' #')[0].strip()
        if linea and not linea.startswith('#') and '=' in linea:
            k, v = linea.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())


def main():
    cargar_env()
    os.environ.setdefault('DEV_LOGIN', '1')
    os.environ.setdefault('ADMINS', 'admin@local.test')
    os.environ.setdefault('DATABASE_URL', 'sqlite:///' + os.path.join(RAIZ, 'suite-local.db'))
    from . import create_app, worker
    app = create_app()
    worker.una_lectura(app.cfg, app.motor)
    app.run(port=int(os.environ.get('PUERTO', '8765')), debug=False)


if __name__ == '__main__':
    main()
