"""Conectores con respuestas simuladas (sin llamar a GHL ni a Meta de verdad)."""
import datetime as dt

from servidor import worker
from servidor.config import NEGOCIOS, Config
from servidor.conectores import ghl
from servidor.conectores.meta import Meta, leads_de

HOY = dt.date(2026, 11, 17)


class Resp:
    def __init__(self, cuerpo, codigo=200):
        self.cuerpo, self.status_code, self.text = cuerpo, codigo, str(cuerpo)

    def json(self):
        return self.cuerpo


class SesionFalsa:
    def __init__(self, respuestas):
        self.respuestas, self.pedidos = respuestas, []

    def get(self, url, params=None, headers=None, timeout=None):
        self.pedidos.append((url, params, headers))
        for clave, cuerpo in self.respuestas.items():
            if clave in url:
                return Resp(cuerpo() if callable(cuerpo) else cuerpo)
        return Resp({}, 404)


def test_tipo_de_calendario_por_nombre():
    reglas = NEGOCIOS['plastia']['calendarios']
    assert ghl.tipo_calendario('Llamada de Evaluación', reglas) == 'calificacion'
    assert ghl.tipo_calendario('Valoración presencial', reglas) == 'principal'
    assert ghl.tipo_calendario('Copy of Valoración', reglas) is None
    assert ghl.tipo_calendario('Otro calendario', reglas) is None


def test_origen_usa_primera_atribucion_si_la_ultima_es_calendar():
    c = {'attributionSource': {'utmAdId': '123'}, 'lastAttributionSource': {'medium': 'calendar'}}
    assert ghl.origen_anuncio(c) == {'id': '123'}
    c = {'lastAttributionSource': {'campaign': 'C1', 'utmContent': 'Video 1'}}
    assert ghl.origen_anuncio(c) == {'campana': 'C1', 'nombre': 'Video 1'}
    assert ghl.origen_anuncio({}) is None


def test_leads_de_meta_no_suma_acciones_solapadas():
    acciones = [{'action_type': 'lead', 'value': '7'}, {'action_type': 'onsite_conversion.lead_grouped', 'value': '7'}]
    assert leads_de(acciones) == 7
    assert leads_de(None) == 0


def test_meta_pagina_resultados():
    pagina2 = {'data': [{'date_start': '2026-11-16', 'ad_id': '2', 'ad_name': 'B', 'spend': '5', 'impressions': '50', 'clicks': '1', 'actions': []}]}
    pagina1 = {'data': [{'date_start': '2026-11-16', 'ad_id': '1', 'ad_name': 'A', 'adset_name': 'X', 'campaign_name': 'C',
                         'spend': '10.5', 'impressions': '100', 'clicks': '3', 'actions': [{'action_type': 'lead', 'value': '2'}]}],
               'paging': {'next': 'https://graph.facebook.com/next-page'}}
    s = SesionFalsa({'next-page': pagina2, 'insights': pagina1})
    filas = Meta('tok', sesion=s).insights('123', dt.date(2026, 11, 10), HOY)
    assert [f['ad_id'] for f in filas] == ['1', '2']
    assert filas[0]['gasto'] == 10.5 and filas[0]['leads'] == 2
    assert s.pedidos[0][0].endswith('/act_123/insights')


def test_worker_arma_datos_desde_ghl_y_meta():
    cfg = Config(SECRET_KEY='x', CRM_TOKENS={'loc1': 'tok'}, DIAS=30, DIAS_PROXIMOS=7, ZONA_HORARIA='America/New_York')
    respuestas = {
        '/calendars/events': {'events': [
            {'id': 'e1', 'startTime': '2026-11-16T15:00:00Z', 'dateAdded': '2026-11-15T12:00:00Z', 'appointmentStatus': 'showed', 'contactId': 'k1', 'title': 'Llamada'},
            {'id': 'e2', 'startTime': '2026-11-16T16:00:00Z', 'dateAdded': '2026-11-15T12:00:00Z', 'appointmentStatus': 'noshow', 'contactId': 'k2', 'title': 'Llamada'},
        ]},
        '/calendars/': {'calendars': [{'id': 'cal1', 'name': 'Llamada de evaluación'}, {'id': 'cal2', 'name': 'Prueba interna'}]},
        '/contacts/k1': {'contact': {'attributionSource': {'utmAdId': 'ad1'}}},
        '/contacts/k2': {'contact': {}},
    }

    class MetaFalsa:
        def insights(self, act, desde, hasta):
            return [{'fecha': '2026-11-15', 'ad_id': 'ad1', 'ad_name': 'Video', 'adset_name': '', 'campaign_name': 'C', 'gasto': 40.0, 'impresiones': 400, 'clics': 4, 'leads': 3}]

    cuentas = [{'id': 7, 'nombre': 'Clínica', 'grupo': 'Activas', 'propia': False, 'crm_location_id': 'loc1', 'meta_cuentas': ['act_9'], 'youtube_cuentas': ['111']}]
    datos, privado, avisos = worker.armar(cfg, 'plastia', cuentas, HOY, meta=MetaFalsa(), youtube=None,
                                          crear_ghl=lambda t: ghl.GHL(t, sesion=SesionFalsa(respuestas), pausa=0))
    assert datos['gasto'] == [['2026-11-15', 0, 40.0, 400, 4, 3]]
    assert sorted(c[5] for c in datos['citas']) == ['asistio', 'no_asistio']
    con_anuncio = [c for c in datos['citas'] if c[6] == 0]
    assert len(con_anuncio) == 1 and con_anuncio[0][0] == '2026-11-16' and con_anuncio[0][1] == 10 * 60  # 15:00 UTC = 10:00 NY
    assert any('youtube' in a for a in avisos)  # avisa que falta configurar YouTube, no se cae
    assert 'k1' not in str(datos)  # los ids de contacto solo van en privado
    assert privado['citas'][0][2] in ('k1', 'k2')


def test_tokens_ghl_en_forma_simple(monkeypatch):
    from servidor.config import Config
    monkeypatch.setenv('GHL_PLASTIA_ID', 'loc123')
    monkeypatch.setenv('GHL_PLASTIA_TOKEN', 'pit-abc')
    monkeypatch.setenv('GHL_VACIA_ID', '')
    cfg = Config(SECRET_KEY='x')
    assert cfg.CRM_TOKENS.get('loc123') == 'pit-abc' and '' not in cfg.CRM_TOKENS


def test_varios_tokens_de_meta_cada_cuenta_usa_el_suyo(monkeypatch):
    monkeypatch.setenv('META_ACCESS_TOKEN', 'tok-a')
    monkeypatch.setenv('META_ACCESS_TOKEN_2', 'tok-b')
    assert Config(SECRET_KEY='x').META_TOKENS == ['tok-a', 'tok-b']

    class SesionPorToken(SesionFalsa):
        def get(self, url, params=None, headers=None, timeout=None):
            self.pedidos.append((url, params, headers))
            # act_2 solo la ve el segundo token
            if url.endswith('/act_2') and params.get('access_token') != 'tok-b':
                return Resp({'error': 'sin acceso'}, 400)
            return Resp({'id': 'act_2', 'currency': 'COP'})
    s = SesionPorToken({})
    m = Meta(['tok-a', 'tok-b'], sesion=s)
    assert m.moneda('2') == 'COP'
    assert s.pedidos[-1][1]['access_token'] == 'tok-b'


def test_origen_desde_utm_en_campos_personalizados_y_contactos_de_prueba():
    campos = {'f1': 'UTM campaign', 'f2': 'UTM content (anuncio)', 'f3': 'Ciudad'}
    k = {'attributionSource': {'sessionSource': 'CRM Workflows', 'medium': 'Manual'},
         'customFields': [{'id': 'f1', 'value': 'PLASTIA | FRÍO'}, {'id': 'f2', 'value': 'V1B | La factura'},
                          {'id': 'f3', 'value': 'Córdoba'}]}
    assert ghl.origen_anuncio(k, campos) == {'campana': 'PLASTIA | FRÍO', 'nombre': 'V1B | La factura'}
    assert ghl.origen_anuncio(k) is None  # sin los nombres de los campos no se adivina
    assert ghl.es_prueba({'tags': ['lead agencia', 'Prueba']}) and not ghl.es_prueba({'tags': ['calificado']})


def test_utm_content_numerico_es_id_de_anuncio():
    k = {'attributionSource': {'utmCampaign': '120246286994160680', 'utmContent': '120246518685750680'}}
    assert ghl.origen_anuncio(k) == {'id': '120246518685750680'}
