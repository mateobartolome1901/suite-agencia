"""Go High Level (API v2, LeadConnector): calendarios, citas y anuncio de origen de cada contacto. Solo lectura.

Un token por subcuenta (CRM_TOKENS = {"<location_id>": "<token>"}), con permisos mínimos de lectura:
calendars.readonly, calendars/events.readonly, contacts.readonly.
"""
import datetime as dt
import time
import unicodedata

import requests

BASE = 'https://services.leadconnectorhq.com'

# appointmentStatus de GHL -> estado de la suite
ESTADOS = {'showed': 'asistio', 'noshow': 'no_asistio', 'cancelled': 'cancelada', 'invalid': 'cancelada',
           'confirmed': 'confirmada', 'new': 'confirmada', 'booked': 'confirmada'}


class ErrorCRM(Exception):
    pass


def normalizar(txt):
    txt = unicodedata.normalize('NFKD', txt or '').encode('ascii', 'ignore').decode()
    return txt.lower().strip()


def tipo_calendario(nombre, reglas):
    """Clasifica un calendario por su nombre: excluir, calificacion, principal, entrada (o None si no se reconoce)."""
    n = normalizar(nombre)
    if any(p in n for p in reglas.get('excluir', [])):
        return None
    for tipo in ('calificacion', 'principal', 'entrada'):
        if any(p in n for p in reglas.get(tipo, [])):
            return tipo
    return None


class GHL:
    def __init__(self, token, sesion=None, pausa=0.12):
        self.token = token
        self.s = sesion or requests.Session()
        self.pausa = pausa  # GHL limita a ~100 pedidos cada 10 s por subcuenta

    def _get(self, ruta, version, **params):
        for intento in range(4):
            r = self.s.get(BASE + ruta, params=params, timeout=30,
                           headers={'Authorization': 'Bearer ' + self.token, 'Version': version, 'Accept': 'application/json'})
            if r.status_code == 429:
                time.sleep(2 * (intento + 1))
                continue
            if r.status_code >= 400:
                raise ErrorCRM(f'GHL {ruta}: {r.status_code} {r.text[:200]}')
            time.sleep(self.pausa)
            return r.json()
        raise ErrorCRM(f'GHL {ruta}: demasiados pedidos')

    def calendarios(self, location_id):
        return self._get('/calendars/', '2021-04-15', locationId=location_id).get('calendars', [])

    def citas(self, location_id, calendario_id, desde, hasta):
        ms = lambda d: int(dt.datetime.combine(d, dt.time()).timestamp() * 1000)
        return self._get('/calendars/events', '2021-04-15', locationId=location_id, calendarId=calendario_id,
                         startTime=ms(desde), endTime=ms(hasta + dt.timedelta(days=1))).get('events', [])

    def contacto(self, contacto_id):
        return self._get('/contacts/' + contacto_id, '2021-07-28').get('contact', {})


def origen_anuncio(contacto):
    """ID del anuncio (o campaña + nombre) mirando la primera y la última atribución: al agendar, GHL pisa la última
    con «calendar», así que la primera suele ser la buena."""
    for clave in ('attributionSource', 'lastAttributionSource'):
        a = contacto.get(clave) or {}
        ad_id = a.get('utmAdId') or a.get('adId') or a.get('ad_id') or a.get('fbAdId')
        if ad_id:
            return {'id': str(ad_id)}
        campana = a.get('campaign') or a.get('utmCampaign')
        nombre = a.get('utmContent') or a.get('adName')
        if campana and nombre:
            return {'campana': campana, 'nombre': nombre}
    return None


def _fecha(valor, zona):
    """GHL devuelve ISO con zona o epoch en ms. Devuelve (fecha, minuto del día) en la zona del negocio."""
    from zoneinfo import ZoneInfo
    if isinstance(valor, (int, float)) or (isinstance(valor, str) and valor.isdigit()):
        momento = dt.datetime.fromtimestamp(int(valor) / 1000, tz=dt.timezone.utc)
    else:
        momento = dt.datetime.fromisoformat(str(valor).replace('Z', '+00:00'))
        if momento.tzinfo is None:
            momento = momento.replace(tzinfo=ZoneInfo(zona))
    local = momento.astimezone(ZoneInfo(zona))
    return local.date().isoformat(), local.hour * 60 + local.minute


def leer_cuenta(cliente, cuenta, reglas, desde, hasta, zona, cache_origen=None):
    """Devuelve citas en formato crudo: [{fecha, minuto, creada, tipo, estado, contacto_id, origen, id, titulo}]."""
    cache_origen = {} if cache_origen is None else cache_origen
    salida = []
    for cal in cliente.calendarios(cuenta['crm_location_id']):
        if cal.get('isActive') is False:
            continue
        tipo = tipo_calendario(cal.get('name', ''), reglas)
        if not tipo:
            continue
        for ev in cliente.citas(cuenta['crm_location_id'], cal['id'], desde, hasta):
            if ev.get('deleted') or not ev.get('startTime'):
                continue
            fecha, minuto = _fecha(ev['startTime'], zona)
            creada, _ = _fecha(ev.get('dateAdded') or ev['startTime'], zona)
            cid = ev.get('contactId')
            if cid and cid not in cache_origen:
                try:
                    cache_origen[cid] = origen_anuncio(cliente.contacto(cid))
                except ErrorCRM:
                    cache_origen[cid] = None
            salida.append({'id': ev.get('id'), 'fecha': fecha, 'minuto': minuto, 'creada': creada, 'tipo': tipo,
                           'estado': ESTADOS.get((ev.get('appointmentStatus') or '').lower(), 'confirmada'),
                           'contacto_id': cid, 'origen': cache_origen.get(cid), 'titulo': ev.get('title', '')})
    return salida
