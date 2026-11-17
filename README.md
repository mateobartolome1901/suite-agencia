# Suite de Agencia multi-negocio

Software interno para operar varios negocios desde un solo lugar, como subcuentas: un **selector de negocio** en el menú lateral cambia los menús, el vocabulario, el modelo de cobro, los socios y los colores.

| Negocio | Modelo de cobro | Socios | Colores |
|---|---|---|---|
| **Plastia Partners** | Setup US$750 + 25% de (venta de cirugías − costos de la cirugía − pauta). El closer se lleva el 25% de ese 25%. | Solo Mateo | Verde petróleo, menta, coral para lo especial |
| **Top Producer Acquisition** | Setup US$4,000 + fee mensual US$750. Clientes: realtors. | Mateo y Luis, 50/50 en pauta y ganancias | Negro, rojo, dorado para lo especial |

Basada en el SOP «Plantilla de la Suite de Agencia» y en el kit visual de la suite original (`referencias/`).

## Estado

**Fase 0 (base), con datos de ejemplo:**
- Menú lateral con grupos (Motor Agencia, Motor Contenido, Motor Clínicas / Clientes, Administración) y selector de negocio.
- Inicio por modelo de cobro (comisión o fee mensual).
- Finanzas de TPA: pauta propia cargada a la tarjeta de un socio y transferencias del otro, con el saldo entre socios.
- Vista celular (cajón lateral), sonidos y animaciones del original.

El resto de los menús muestra qué va a hacer y en qué fase entra. Plan de fases: F1 datos (GHL + Meta), F2 agenda, F3 contactos y ventas, F4 dinero, F5 comunicación, F6 IA, F7 portal y seguridad, F8 contenido.

**Stack previsto (igual al original):** Python + Flask, Postgres, frontend sin framework, hosting en Render (servicios web + worker + base), integraciones con Go High Level, Meta Ads, YouTube Ads, API de Claude y Google Drive.

## Estructura

```
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
python -m http.server 8765 --directory suite
```

Abrir http://localhost:8765. Después de tocar `marca.css` o `app.css`, regenerar los temas:

```bash
python suite/tools/temas.py
```

## Reglas

- Lo visual es idéntico a la suite original; por negocio cambian **solo los colores** (`tools/temas.py`).
- Nunca poner tokens, claves ni datos de clientes en el repo: van en variables de entorno de Render.
