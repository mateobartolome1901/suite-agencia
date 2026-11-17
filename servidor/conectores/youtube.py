"""YouTube Ads = campañas de video de Google Ads (API REST de Google Ads, consulta GAQL).

Requiere: GOOGLE_ADS_DEVELOPER_TOKEN (se pide en el Centro de API de una cuenta de administrador de Google Ads),
GOOGLE_ADS_REFRESH_TOKEN (OAuth de la cuenta de Google con acceso), GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET y, si las
cuentas cuelgan de un administrador, GOOGLE_ADS_LOGIN_CUSTOMER_ID. La versión de la API va en GOOGLE_ADS_API_VERSION:
Google retira versiones viejas cada año, así que hay que revisarla al conectar.
"""
import requests

CONSULTA = (
    "SELECT segments.date, ad_group_ad.ad.id, ad_group_ad.ad.name, ad_group.name, campaign.name, "
    "metrics.cost_micros, metrics.impressions, metrics.clicks, metrics.conversions "
    "FROM ad_group_ad WHERE segments.date BETWEEN '{desde}' AND '{hasta}' "
    "AND campaign.advertising_channel_type = 'VIDEO'"
)


class ErrorYouTube(Exception):
    pass


class YouTube:
    def __init__(self, cfg, sesion=None):
        self.cfg = cfg
        self.s = sesion or requests.Session()
        self._token = None

    def disponible(self):
        c = self.cfg
        return bool(c.GOOGLE_ADS_DEVELOPER_TOKEN and c.GOOGLE_ADS_REFRESH_TOKEN and c.GOOGLE_CLIENT_ID and c.GOOGLE_CLIENT_SECRET)

    def _acceso(self):
        if not self._token:
            r = self.s.post('https://oauth2.googleapis.com/token', timeout=30, data={
                'client_id': self.cfg.GOOGLE_CLIENT_ID, 'client_secret': self.cfg.GOOGLE_CLIENT_SECRET,
                'refresh_token': self.cfg.GOOGLE_ADS_REFRESH_TOKEN, 'grant_type': 'refresh_token'})
            if r.status_code >= 400:
                raise ErrorYouTube('No se pudo renovar el acceso a Google Ads: ' + r.text[:200])
            self._token = r.json()['access_token']
        return self._token

    def insights(self, cliente_id, desde, hasta):
        """Mismo formato que Meta.insights: [{fecha, ad_id, ad_name, adset_name, campaign_name, gasto, impresiones, clics, leads}]."""
        cid = cliente_id.replace('-', '')
        url = f'https://googleads.googleapis.com/{self.cfg.GOOGLE_ADS_API_VERSION}/customers/{cid}/googleAds:searchStream'
        cab = {'Authorization': 'Bearer ' + self._acceso(), 'developer-token': self.cfg.GOOGLE_ADS_DEVELOPER_TOKEN}
        if self.cfg.GOOGLE_ADS_LOGIN_CUSTOMER_ID:
            cab['login-customer-id'] = self.cfg.GOOGLE_ADS_LOGIN_CUSTOMER_ID.replace('-', '')
        r = self.s.post(url, headers=cab, timeout=60, json={'query': CONSULTA.format(desde=desde.isoformat(), hasta=hasta.isoformat())})
        if r.status_code >= 400:
            raise ErrorYouTube(f'Google Ads {cid}: {r.status_code} {r.text[:200]}')
        filas = []
        for lote in r.json():
            for x in lote.get('results', []):
                ad = x.get('adGroupAd', {}).get('ad', {})
                m = x.get('metrics', {})
                filas.append({'fecha': x['segments']['date'], 'ad_id': 'yt-' + str(ad.get('id')),
                              'ad_name': ad.get('name') or 'Video ' + str(ad.get('id')),
                              'adset_name': x.get('adGroup', {}).get('name', ''), 'campaign_name': x.get('campaign', {}).get('name', ''),
                              'gasto': int(m.get('costMicros', 0)) / 1_000_000, 'impresiones': int(m.get('impressions', 0)),
                              'clics': int(m.get('clicks', 0)), 'leads': int(float(m.get('conversions', 0)))})
        return filas
