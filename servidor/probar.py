"""Prueba las conexiones del .env sin mostrar los tokens: python -m servidor.probar"""
from .local import cargar_env


def main():
    cargar_env()
    from .config import Config
    from .conectores import ghl
    from .conectores.meta import ErrorMeta, Meta
    import os
    os.environ.setdefault('SECRET_KEY', 'prueba')
    cfg = Config()
    if not cfg.CRM_TOKENS:
        print('GHL: no hay subcuentas cargadas en el .env')
    for loc, token in cfg.CRM_TOKENS.items():
        try:
            cals = ghl.GHL(token).calendarios(loc)
            print('GHL %s…: OK, %d calendarios: %s' % (loc[:5], len(cals), ', '.join(c.get('name', '') for c in cals)))
        except ghl.ErrorCRM as e:
            print('GHL %s…: FALLA (%s)' % (loc[:5], str(e)[:160]))
    if cfg.META_TOKENS:
        try:
            d = Meta(cfg.META_TOKENS, cfg.META_API_VERSION).cuentas()
            print('Meta (%d token/s): OK, cuentas publicitarias: ' % len(cfg.META_TOKENS) + ', '.join('%s (act_%s, %s)' % (x.get('name'), x.get('account_id'), x.get('currency')) for x in d))
        except ErrorMeta as e:
            print('Meta: FALLA (%s)' % str(e)[:160])
    else:
        print('Meta: todavía sin token')


if __name__ == '__main__':
    main()
