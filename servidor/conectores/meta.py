"""Meta Ads (Graph API): gasto, impresiones, clics y leads por anuncio y por día.

META_ACCESS_TOKEN de un usuario del sistema del Business Manager con ads_read y read_insights, con acceso a cada
cuenta publicitaria (las propias de cada negocio y las de los clientes).
"""
import json
import time

import requests

# Acciones que cuentan como lead (formularios nativos, píxel y mensajes)
ACCIONES_LEAD = ('lead', 'onsite_conversion.lead_grouped', 'offsite_conversion.fb_pixel_lead')


class ErrorMeta(Exception):
    pass


def leads_de(acciones):
    valores = {a.get('action_type'): float(a.get('value', 0)) for a in acciones or []}
    for tipo in ACCIONES_LEAD:  # en orden de preferencia; no se suman porque se solapan
        if tipo in valores:
            return int(valores[tipo])
    return 0


class Meta:
    def __init__(self, token, version='v21.0', sesion=None):
        self.token = token
        self.base = f'https://graph.facebook.com/{version}'
        self.s = sesion or requests.Session()

    def insights(self, cuenta_act, desde, hasta):
        """Filas [{fecha, ad_id, ad_name, adset_name, campaign_name, gasto, impresiones, clics, leads}]."""
        if not cuenta_act.startswith('act_'):
            cuenta_act = 'act_' + cuenta_act
        url = f'{self.base}/{cuenta_act}/insights'
        params = {'level': 'ad', 'time_increment': 1, 'limit': 500, 'access_token': self.token,
                  'fields': 'ad_id,ad_name,adset_name,campaign_id,campaign_name,spend,impressions,clicks,actions',
                  'time_range': json.dumps({'since': desde.isoformat(), 'until': hasta.isoformat()})}
        filas = []
        while url:
            for intento in range(4):
                r = self.s.get(url, params=params, timeout=60)
                if r.status_code in (429, 500, 503) or (r.status_code == 400 and '"code":17' in r.text):
                    time.sleep(5 * (intento + 1))  # límite de uso de la API
                    continue
                break
            if r.status_code >= 400:
                raise ErrorMeta(f'Meta {cuenta_act}: {r.status_code} {r.text[:200]}')
            cuerpo = r.json()
            for x in cuerpo.get('data', []):
                filas.append({'fecha': x['date_start'], 'ad_id': x['ad_id'], 'ad_name': x.get('ad_name', ''),
                              'adset_name': x.get('adset_name', ''), 'campaign_name': x.get('campaign_name', ''),
                              'campaign_id': x.get('campaign_id', ''),
                              'gasto': float(x.get('spend', 0)), 'impresiones': int(x.get('impressions', 0)),
                              'clics': int(x.get('clicks', 0)), 'leads': leads_de(x.get('actions'))})
            url = cuerpo.get('paging', {}).get('next')
            params = None  # la URL de "next" ya trae todo
        return filas

    def _get(self, ruta, **params):
        params['access_token'] = self.token
        r = self.s.get(f'{self.base}/{ruta}', params=params, timeout=60)
        if r.status_code >= 400:
            raise ErrorMeta(f'Meta {ruta}: {r.status_code} {r.text[:200]}')
        return r.json()

    def moneda(self, cuenta_act):
        """Moneda de la cuenta publicitaria (el gasto viene en esta moneda)."""
        act = cuenta_act if cuenta_act.startswith('act_') else 'act_' + cuenta_act
        return self._get(act, fields='currency,name').get('currency', 'USD')

    def campanas(self, cuenta_act):
        """Campañas de la cuenta para elegir cuáles cuentan: [{id, nombre, estado}]."""
        act = cuenta_act if cuenta_act.startswith('act_') else 'act_' + cuenta_act
        d = self._get(act + '/campaigns', fields='id,name,effective_status', limit=200)
        return [{'id': x['id'], 'nombre': x.get('name', ''), 'estado': x.get('effective_status', '')} for x in d.get('data', [])]
