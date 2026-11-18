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

    def campos(self, location_id):
        """Campos personalizados de la subcuenta: {id: nombre}. Si no hay permiso, vacío (no corta la lectura)."""
        try:
            d = self._get(f'/locations/{location_id}/customFields', '2021-07-28')
        except ErrorCRM:
            return {}
        return {x['id']: x.get('name', '') for x in d.get('customFields', []) if x.get('id')}

    # ---- Conversaciones (necesita conversations.readonly / conversations/message.write) ----
    def conversaciones(self, location_id, limite=40):
        return self._get('/conversations/search', '2021-04-15', locationId=location_id, limit=limite,
                         sort='desc', sortBy='last_message_date').get('conversations', [])

    def mensajes(self, conversacion_id, limite=60):
        d = self._get(f'/conversations/{conversacion_id}/messages', '2021-04-15', limit=limite)
        return (d.get('messages') or {}).get('messages', []) if isinstance(d.get('messages'), dict) else d.get('messages', [])

    def enviar(self, contacto_id, texto, tipo='SMS'):
        r = self.s.post(BASE + '/conversations/messages', timeout=30, json={'type': tipo, 'contactId': contacto_id, 'message': texto},
                        headers={'Authorization': 'Bearer ' + self.token, 'Version': '2021-04-15', 'Accept': 'application/json'})
        if r.status_code >= 400:
            raise ErrorCRM(f'GHL enviar: {r.status_code} {r.text[:200]}')
        return r.json()


def _utm_de_campos(contacto, campos):
    """UTM guardados en campos personalizados por un workflow (formularios de Meta que entran por webhook)."""
    utm = {}
    for f in contacto.get('customFields') or []:
        n = normalizar(campos.get(f.get('id'), ''))
        v = f.get('value') if f.get('value') not in (None, '') else f.get('fieldValue')
        if not v or not isinstance(v, (str, int, float)):
            continue
        v = str(v).strip()
        if 'utm' in n and 'campaign' in n or n in ('campana', 'campaña'):
            utm.setdefault('campaign', v)
        elif 'utm' in n and 'content' in n or 'anuncio' in n and 'utm' in n:
            utm.setdefault('utmContent', v)
        elif n in ('ad id', 'utm id', 'utm ad id', 'id del anuncio'):
            utm.setdefault('adId', v)
    return utm


def es_prueba(contacto):
    """Contactos de prueba (etiqueta «prueba»/«test»): no cuentan en los números."""
    return any(normalizar(t) in ('prueba', 'test', 'testing') for t in (contacto.get('tags') or []))


def origen_anuncio(contacto, campos=None):
    """ID del anuncio (o campaña + nombre) mirando la primera y la última atribución: al agendar, GHL pisa la última
    con «calendar», así que la primera suele ser la buena. Si no hay, los UTM de los campos personalizados."""
    for clave in ('attributionSource', 'lastAttributionSource'):
        a = contacto.get(clave) or {}
        ad_id = a.get('utmAdId') or a.get('adId') or a.get('ad_id') or a.get('fbAdId')
        if ad_id:
            return {'id': str(ad_id)}
        campana = a.get('campaign') or a.get('utmCampaign')
        nombre = a.get('utmContent') or a.get('adName')
        if str(nombre or '').isdigit() and len(str(nombre)) >= 12:
            return {'id': str(nombre)}
        if campana and nombre:
            return {'campana': campana, 'nombre': nombre}
    u = _utm_de_campos(contacto, campos or {})
    if u.get('adId'):
        return {'id': u['adId']}
    if str(u.get('utmContent', '')).isdigit() and len(u['utmContent']) >= 12:
        return {'id': u['utmContent']}  # utm_content={{ad.id}}: el ID del anuncio de Meta
    if u.get('campaign') and u.get('utmContent'):
        return {'campana': u['campaign'], 'nombre': u['utmContent']}
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
    elegidos = {c['id']: c.get('tipo') for c in (cuenta.get('calendarios') or []) if c.get('id')}
    campos = cliente.campos(cuenta['crm_location_id']) if hasattr(cliente, 'campos') else {}
    for cal in cliente.calendarios(cuenta['crm_location_id']):
        if elegidos:  # elegidos a mano en la ficha de la cuenta: solo esos, con el tipo elegido
            tipo = elegidos.get(cal.get('id'))
        elif cal.get('isActive') is False:
            continue
        else:
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
                    k = cliente.contacto(cid)
                    k = k.get('contact', k) if isinstance(k, dict) else {}
                    nombre = (k.get('name') or ' '.join(x for x in (k.get('firstName'), k.get('lastName')) if x)).strip()
                    cache_origen[cid] = {'origen': origen_anuncio(k, campos), 'nombre': nombre, 'prueba': es_prueba(k),
                                         'telefono': k.get('phone') or '', 'email': k.get('email') or ''}
                except ErrorCRM:
                    cache_origen[cid] = None
            k = cache_origen.get(cid) or {}
            if k.get('prueba'):
                continue
            salida.append({'id': ev.get('id'), 'fecha': fecha, 'minuto': minuto, 'creada': creada, 'tipo': tipo,
                           'estado': ESTADOS.get((ev.get('appointmentStatus') or '').lower(), 'confirmada'),
                           'contacto_id': cid, 'origen': k.get('origen'), 'titulo': ev.get('title', ''),
                           'nombre': k.get('nombre', ''), 'telefono': k.get('telefono', ''), 'email': k.get('email', '')})
    return salida
