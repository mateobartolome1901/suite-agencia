"""Worker: cada 15 minutos lee el CRM y los anuncios de cada negocio y publica datos:<negocio> (agregado, sin datos
personales) y privado:<negocio> (nombre y link de cada cita, que solo sirve el servidor a quien tenga permiso).

Uso:  python -m servidor.worker            (bucle)
      python -m servidor.worker --una-vez  (una lectura y termina)
"""
import datetime as dt
import logging
import sys
import time
from zoneinfo import ZoneInfo

from . import db, demo
from .config import NEGOCIOS, Config
from .conectores import ghl as ghl_mod
from .conectores.meta import ErrorMeta, Meta
from .conectores.youtube import ErrorYouTube, YouTube

log = logging.getLogger('worker')
CADA = 15 * 60


def hoy_negocio(cfg):
    return dt.datetime.now(ZoneInfo(cfg.ZONA_HORARIA)).date()


def armar(cfg, negocio, cuentas, hoy, meta=None, youtube=None, crear_ghl=None):
    """Arma (datos, privado, avisos) para un negocio. Un error en una cuenta no corta las demás: queda en avisos."""
    desde, hasta = hoy - dt.timedelta(days=cfg.DIAS), hoy + dt.timedelta(days=cfg.DIAS_PROXIMOS)
    reglas = NEGOCIOS[negocio]['calendarios']
    anuncios, por_id, por_nombre = [], {}, {}
    gasto, citas, privado, avisos = [], [], [], []

    def anuncio(cuenta_id, ad_id, nombre, campana, conjunto, plataforma):
        if ad_id and ad_id in por_id:
            return por_id[ad_id]
        k = (cuenta_id, campana, nombre)
        if not ad_id and k in por_nombre:
            return por_nombre[k]
        anuncios.append({'id': ad_id or '', 'nombre': nombre, 'campana': campana, 'conjunto': conjunto,
                         'cuenta_id': cuenta_id, 'plataforma': plataforma})
        i = len(anuncios) - 1
        if ad_id:
            por_id[ad_id] = i
        por_nombre.setdefault(k, i)
        return i

    for c in cuentas:
        fuentes = [('meta', act, meta) for act in (c.get('meta_cuentas') or [])]
        fuentes += [('youtube', yt, youtube) for yt in (c.get('youtube_cuentas') or [])]
        for plataforma, cuenta_ads, cliente in fuentes:
            if cliente is None:
                avisos.append(f'{c["nombre"]}: falta configurar el acceso a {plataforma}')
                continue
            try:
                for f in cliente.insights(cuenta_ads, desde, hoy):
                    i = anuncio(c['id'], f['ad_id'], f['ad_name'], f['campaign_name'], f['adset_name'], plataforma)
                    gasto.append([f['fecha'], i, round(f['gasto'], 2), f['impresiones'], f['clics'], f['leads']])
            except (ErrorMeta, ErrorYouTube) as e:
                avisos.append(f'{c["nombre"]}: {e}')
        loc = c.get('crm_location_id')
        if not loc:
            avisos.append(f'{c["nombre"]}: falta la subcuenta de GHL')
            continue
        token = cfg.CRM_TOKENS.get(loc)
        if not token or crear_ghl is None:
            avisos.append(f'{c["nombre"]}: falta el token de GHL de la subcuenta')
            continue
        try:
            for x in ghl_mod.leer_cuenta(crear_ghl(token), c, reglas, desde, hasta, cfg.ZONA_HORARIA):
                o = x['origen']
                if not o:
                    ia = -1
                elif 'id' in o:
                    ia = por_id.get(o['id'], -1)
                    if ia < 0:  # anuncio que no gastó en el período (o de otra cuenta publicitaria)
                        ia = anuncio(c['id'], o['id'], 'Anuncio ' + o['id'], '—', '', 'meta')
                else:
                    ia = anuncio(c['id'], '', o['nombre'], o['campana'], '', 'meta')
                citas.append([x['fecha'], x['minuto'], x['creada'], c['id'], x['tipo'], x['estado'], ia])
                privado.append([x['id'], x['titulo'], x['contacto_id'], loc])
        except ghl_mod.ErrorCRM as e:
            avisos.append(f'{c["nombre"]}: {e}')

    datos = {'negocio': negocio, 'hoy': hoy.isoformat(), 'actualizado': db.ahora().isoformat() + 'Z',
             'cuentas': [{'id': c['id'], 'nombre': c['nombre'], 'grupo': c.get('grupo'), 'propia': c.get('propia', False)} for c in cuentas],
             'anuncios': anuncios, 'gasto': gasto, 'citas': citas, 'demo': False}
    return datos, {'citas': privado}, avisos


def una_lectura(cfg, motor):
    hoy = hoy_negocio(cfg)
    meta = Meta(cfg.META_ACCESS_TOKEN, cfg.META_API_VERSION) if cfg.META_ACCESS_TOKEN else None
    yt = YouTube(cfg)
    yt = yt if yt.disponible() else None
    for negocio in NEGOCIOS:
        if cfg.DATOS_DEMO:
            demo.sembrar_cuentas(motor, negocio)
            datos, privado, avisos = demo.datos(negocio, db.cuentas_de(motor, negocio), hoy), {'citas': []}, []
        else:
            datos, privado, avisos = armar(cfg, negocio, db.cuentas_de(motor, negocio), hoy, meta, yt, ghl_mod.GHL)
        db.publicar(motor, 'datos:' + negocio, datos)
        db.publicar(motor, 'privado:' + negocio, privado)
        db.publicar(motor, 'estado:' + negocio, {'actualizado': datos['actualizado'], 'avisos': avisos})
        log.info('%s: %d anuncios, %d filas de gasto, %d citas, %d avisos', negocio, len(datos['anuncios']), len(datos['gasto']), len(datos['citas']), len(avisos))


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)s %(message)s')
    cfg = Config()
    motor = db.conectar(cfg.DATABASE_URL)
    while True:
        try:
            una_lectura(cfg, motor)
        except Exception:  # el bucle no se cae por un error: lo registra y sigue en la próxima vuelta
            log.exception('Falló la lectura')
        if '--una-vez' in sys.argv:
            return
        time.sleep(CADA)


if __name__ == '__main__':
    main()
