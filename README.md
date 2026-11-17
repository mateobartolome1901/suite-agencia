# Suite de Agencia multi-negocio

Software interno para operar varios negocios desde un solo lugar, como subcuentas: un **selector de negocio** en el menú lateral cambia los menús, el vocabulario, el modelo de cobro, los socios y los colores.

| Negocio | Modelo de cobro | Socios | Colores |
|---|---|---|---|
| **Plastia Partners** | Setup US$750 + 25% de (venta de cirugías − costos de la cirugía − pauta). El closer se lleva el 25% de ese 25%. | Solo Mateo | Verde petróleo, menta, coral para lo especial |
| **Top Producer Acquisition** | Setup US$4,000 + fee mensual US$750. Clientes: realtors. | Mateo y Luis, 50/50 en pauta y ganancias | Negro, rojo, dorado para lo especial |

Basada en el SOP «Plantilla de la Suite de Agencia» y en el kit visual de la suite original (`referencias/`).

## Estado: completa (lista para revisar)

Todos los menús de los dos negocios funcionan con el servidor:

- **Motor Agencia:** Ventas (embudo propio, clientes nuevos, CAC, MRR), Campañas propias, Finanzas (ingresos, gastos, flujo, por cobrar; TPA: pauta propia que paga Luis y transferencias de Mateo, 50/50), Cobros / Suscripciones (fees que se generan solos cada mes desde el alta, setups, mora), Tareas.
- **Motor Contenido:** Guiones, Tablero de edición (arrastrar tarjetas), Storyboards, Estilos de edición.
- **Motor Clínicas / Clientes:** Panel de campañas, Trazabilidad, Calendario (día / semana / mes, ficha con resultado de la llamada), Conversaciones (chats de GHL, responder por SMS), Pacientes / Leads, Seguimientos, Rendimiento de closers, Reportes semanales, Bitácora de cirugías / Cierres de clientes.
- **Administración:** Ficha de cuentas (subcuenta de GHL, cuentas de Meta, **qué calendarios y qué campañas cuentan**, moneda, plan de cobro, ficha comercial), Indicadores (metas, proyección del mes, cotización del dólar a mano), Usuarios (roles, negocios, cuentas; Luis solo TPA).
- **Inicio** con datos reales: facturación, cash, flujo, por cobrar, proyección, ranking, alertas, tareas y agenda de hoy.
- **Monedas:** Plastia agencia cobra en USD (setup US$750); las clínicas venden en pesos colombianos: la bitácora calcula la comisión en pesos y muestra siempre el equivalente en USD (cotización del día automática y gratis, o a mano en Indicadores). TPA, todo en USD.
- **Seguridad:** login con Google solo para emails cargados, roles, CSRF, auditoría de cada cambio, cada admin ve solo sus negocios.
- **Hosting gratis:** un solo proceso (web + worker) con base SQLite: ver `DESPLIEGUE.md` (Oracle Cloud Always Free + HTTPS con Caddy).

Pendiente que necesita algo de afuera: tokens de GHL y Meta (van en `.env`), el login de Google (al publicar) y la IA (análisis de llamadas y guiones automáticos: necesita una clave de la API de Claude, que es paga).

## Estructura

```
servidor/           Flask: login, API, métricas, worker y conectores (ghl, meta, youtube)
tests/              pytest
render.yaml         Render: web + worker + Postgres
.env.ejemplo        variables de entorno (copiar a .env en local; en Render van en Environment)
suite/
  index.html        página única
  app.js            menú, selector de negocio, Inicio y Finanzas
  negocios.js       configuración de cada negocio (menús, vocabulario, cobro, socios, logo) y datos de ejemplo
  comun.js          animaciones, secciones plegables y sonidos (del kit original)
  marca.css         CSS original de la suite (fuente; no se usa directo)
  app.css           estructura de la página
  temas/*.css       un CSS por negocio, generado: solo cambian los colores
  tools/temas.py    genera temas/ a partir de marca.css + app.css
  sonidos/          clics de Kenney «Interface Sounds» (CC0)
referencias/        kit visual de la suite original: capturas, clips, CSS, DESIGN.md
```

## Correr en local

```bash
pip install -r requirements.txt
python -m servidor.local
```

Abrir http://localhost:8765 y entrar con `admin@local.test` (login de desarrollo, solo en local). Sin tokens, el worker publica datos de ejemplo. Tests:

```bash
python -m pytest -q tests
```
 Después de tocar `marca.css` o `app.css`, regenerar los temas:

```bash
python suite/tools/temas.py
```

## Reglas

- Lo visual es idéntico a la suite original; por negocio cambian **solo los colores** (`tools/temas.py`).
- Toda ruta nueva de la API necesita su caso en `tests/test_permisos.py` (el test falla si falta).
- Nunca poner tokens, claves ni datos de clientes en el repo: van en variables de entorno de Render.
