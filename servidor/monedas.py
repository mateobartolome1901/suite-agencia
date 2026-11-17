"""Monedas: cotización contra el dólar (gratis, open.er-api.com, una vez por día) y conversión.

Todo lo de la agencia se muestra en USD. Las cuentas que venden en otra moneda (las clínicas de Plastia, en pesos
colombianos) cargan sus ventas en su moneda; la suite muestra siempre el equivalente en USD al lado.
Si el admin carga una cotización a mano en Indicadores (tasa_COP, por ejemplo), manda esa.
"""
import requests

from . import db

URL = 'https://open.er-api.com/v6/latest/USD'
RESPALDO = {'USD': 1.0, 'COP': 4000.0, 'MXN': 18.0}  # solo si nunca se pudo leer la cotización


def actualizar(motor, sesion=None):
    """Lee la cotización del día y la guarda en datos_panel['tasas']. Devuelve el dict o None si falló."""
    try:
        r = (sesion or requests).get(URL, timeout=20)
        d = r.json()
        if d.get('result') != 'success':
            return None
        tasas = {k: float(v) for k, v in d['rates'].items()}
        db.publicar(motor, 'tasas', {'tasas': tasas, 'fecha': d.get('time_last_update_utc', '')})
        return tasas
    except (requests.RequestException, ValueError, KeyError):
        return None


def tasas(motor, manuales=None):
    """Unidades de cada moneda por 1 USD. Las manuales (Indicadores) mandan sobre las leídas."""
    guardadas = (db.leer(motor, 'tasas') or {}).get('tasas') or {}
    t = {**RESPALDO, **guardadas}
    for k, v in (manuales or {}).items():
        if v:
            t[k] = float(v)
    t['USD'] = 1.0
    return t


def fecha(motor):
    return (db.leer(motor, 'tasas') or {}).get('fecha')


def a_usd(monto, moneda, t):
    if monto is None:
        return None
    return monto / t.get((moneda or 'USD').upper(), 1.0)


def desde_usd(monto, moneda, t):
    if monto is None:
        return None
    return monto * t.get((moneda or 'USD').upper(), 1.0)
