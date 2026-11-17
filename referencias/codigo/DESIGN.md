# Diseño del Panel GDS — marca fija

Guía para cualquier cambio del panel (artifact "Semáforo GDS" y versión servidor). La marca sale de nuestra landing ([growthdentalsystem.com/vsl---agendamiento-page](https://growthdentalsystem.com/vsl---agendamiento-page)): fondo verde casi negro, menta y títulos en mayúscula.

**Todo el estilo vive en [`web/marca.css`](web/marca.css).** Los archivos del panel no llevan colores sueltos: usan sus variables (`var(--menta)`, `var(--tarjeta)`…). Para ajustar la marca se toca solo ese archivo.

## Principios

1. **Minimalista y legible en dos segundos.** Fondo oscuro, pocas tarjetas, nada de decoración que no sea un dato. Un % nunca va en una tarjeta propia: va al lado de su número base (ej. Reprogramadas 5 · 12%).
2. **Lo clave va aparte y brilla.** Arriba de cada menú, en su propia fila, solo los KPI que mueven la aguja (CPL, costo por llamada, CAC, % asistencia, tasa de cierre…): borde y valor en menta, brillo suave y mini gráfico. Debajo, los números base en tarjetas más chicas.
3. **Rojo y verde solo para juzgar.** Verde = bien, rojo = mal (variación contra el período anterior, semáforo, no asistencia). Ámbar = atención o falta marcar la cita. El menta es marca, no estado.
4. **Los datos mandan sobre el estilo.** Nombres fijos de las métricas en `GLOSARIO` (`web/comun.js`); el diseño nunca cambia un nombre o una definición.

## Colores (`web/marca.css`)

| Variable | Valor | Uso |
|---|---|---|
| `--fondo` | `#0E1612` | Fondo de la página: verde oscuro, no negro; encima van las luces de `.app` |
| `--hundido` | `#121C17` | Ventanas desplegables, campos |
| `--tarjeta` / `--tarjeta-2` | `#17231D` / `#1D2B24` | Tarjetas y paneles / elementos dentro de ellos |
| `--activo` | `#25362E` | Fila elegida, hover |
| `--linea` / `--borde` / `--borde-fuerte` | `#22302A` / `#2A3B33` / `#3A4F44` | Divisores y bordes |
| `--oro`, `--oro-claro`, `--oro-oscuro` (+ `-fondo`, `-borde`) | | Solo logros y empujones (recuadro de wins, barra del bono) |
| `--r-chico` / `--r` / `--r-tarjeta` / `--r-grande` | 12 / 16 / 20 / 24 px | Radios: campos y botones / paneles chicos / tarjetas / bloques grandes |
| `--relieve` / `--relieve-alto` / `--brillo-sup` | | Volumen de tarjetas y cajas (luz arriba, sombra abajo) y su versión al pasar el mouse |
| `--texto` → `--texto-4` | `#EDF2EF` → `#80908A` | Texto principal a secundario (todos ≥ 4.5:1 sobre las tarjetas) |
| `--acento` | `#4A7A63` | Botones y opción elegida (el botón de la landing) |
| `--menta` | `#8FC4AA` | Métricas clave, mini gráficos, foco del teclado |
| `--menta-claro` / `--menta-hielo` | `#D7ECE2` / `#EAF5EF` | Enlaces / valor de las métricas clave |
| `--verde`, `--rojo`, `--ambar` (+ `-texto`, `-fondo`, `-borde`) | | Estados y variaciones |
| `--cat-*` | | Tipo de cita: virtual (menta), limpieza, carillas, implantes, ortodoncia, alineadores |

## Sistema visual (v4): con volumen, sin perder lo simple

Objetivo del doc «Indicaciones Software GDS v.2»: que no se vea plano, sino robusto y «touchy», manteniendo lo minimalista.

- **Fondo:** verde oscuro con luces (degradados radiales fijos en `.app`); el menú lateral (`.lateral`) es translúcido con desenfoque. Ítem activo del menú con degradé menta (`--nav-activo`).
- **Relieve:** tarjetas (`.kpi`) y cajas con fondo de tarjeta (clase `.caja` en la plantilla) llevan `--relieve`. Bordes más redondeados (tarjetas 20 px, paneles 16–18, campos 12).
- **Hover:** la tarjeta se levanta 3 px, el borde se aclara y una luz menta sigue al mouse (`.kpi::before` con `--mx`/`--my`, lo pone `comun.js`). Los botones se hunden al tocar.
- **Animaciones** (todas se apagan con «reducir movimiento»):
  - Números que cuentan: al aparecer o cambiar, el valor sube desde el anterior con el mismo formato (`contarNumero` en `comun.js`; aplica a `.kpi-valor`, `.sec-valor`, `.rend-monto`, `.juego-monto`, `.wins-monto`, `.ini-anillo-pct`, `.rend-mini strong`, `.ini-ranking-total` y cualquier `[data-contar]`).
  - Barras que se llenan al aparecer y un destello que las recorre cada tanto (`.rend-barra`, `.juego-barra`, `.juego-pista`, `.wins-barra`).
  - Tarjetas que entran suaves al cambiar de menú; la que cumple la meta (`.kpi--logro`) hace un destello verde.
- **Recuadro dorado de wins (`.wins`):** borde y luz dorados que laten, brillo que lo cruza, `.wins-label`, `.wins-monto`, `.wins-txt` y `.wins-barra`. Solo para premios y empujones (bono, récord, «te faltan N para…»); el dorado no es un estado. Ya lo usa el próximo objetivo de Mi rendimiento.

### Vidrio, borde vivo y sonidos (v5)

- **Vidrio leve:** tarjetas (`.kpi`), cajas (`.caja`), `.sec` y `.rend-card` son traslúcidas (`--vidrio`, borde `--vidrio-borde`) con el canto iluminado arriba y sombra abajo (`--canto`, dentro de `--relieve`). Las tarjetas además desenfocan lo que tienen detrás. Separa lo tangible del fondo sin decorar.
- **Borde vivo:** una luz menta recorre el borde, lenta y constante (9 s), en los bloques importantes: KPI clave, proyección del Inicio, hero de Mi rendimiento y cualquier `.borde-vivo` (ej. semáforo del Panel de campañas). Cada tarjeta de la grilla arranca en otro punto. Se apaga con «reducir movimiento».
- **Sonidos** (`SONIDO` en `comun.js`, sintetizados con Web Audio, sin archivos): menú = tic agudo (menú lateral, switches, pestañas); métrica = «ping» de vidrio (tarjetas, ítems de métricas, wins); desplegable = barrido que sube al abrir y baja al cerrar (todo lo que tiene `aria-expanded`, `.sec-cab` y títulos plegables). Botón «Sonidos» en el menú lateral (se guarda en el navegador, `gds_sonido`). Un elemento con `data-sin-sonido` no suena.

### Panel de campañas (v5)

- Arriba el semáforo; después **KPI clave** (los 4 de la tabla de abajo, `.grilla` de 4, con barra contra el objetivo de Indicadores: costo por cita de limpieza y costo por llamada o lead de alto ticket con `contraTope`, tasas con `contraMeta`), **Funnel** con los números base (gasto, leads o llamadas, citas o asistidas, valoraciones y cierres; cada % al lado de su número) y **Métricas secundarias** en `.sec` (no presentados, cancelaciones, costo por asistencia, contactados, anticipos, landing).
- Costo por cita y tendencia, y Trazabilidad y alertas, en `.bloques`. Campañas Growth usa la misma estructura.

### Componentes comunes (usar en todos los menús)

- **Grilla simétrica:** `class="grilla" style="{{grillaEstilo(n)}}"` → n columnas iguales en escritorio (hasta 6; con más, la mitad: 8 → 4 + 4); en tablet y celular 2 columnas y la última, si queda sola, ocupa la fila. Reemplaza los `repeat(auto-fit, minmax(…))` que dejan tarjetas huérfanas.
- **Bloques lado a lado:** `.bloques` (dos columnas iguales; una en pantallas chicas) para agrupar secciones y bajar el scroll (ej. ranking al lado de clínicas activas).
- **Métricas secundarias:** debajo de las clave, un solo bloque de ancho completo en lista plegable: `<section class="sec" data-sec="<clave única>">` con `button.sec-cab` (título + `.sec-n` + `.sec-flecha`) y `ul.sec-lista` de `li.sec-item` (`.sec-nombre`, `.sec-valor` con su `.kpi-pct`, `.sec-sub`, `.sec-delta`). Usa los mismos objetos que `tarjeta()`. Abierto por defecto; el estado se guarda en el navegador. Ejemplo: Calendario.
- **Desplegables (`<select>`):** todos llevan la marca sin tocar cada menú: borde menta al pasar el mouse, foco con anillo menta y, en Chrome, la lista propia (fondo hundido, opciones redondeadas, elegida en menta con ✓) vía `appearance: base-select`. En otros navegadores queda el desplegable del sistema en oscuro. El calendario de los campos de fecha va en menta.

## Tipografía

- **Títulos:** Space Grotesk 700 en **mayúscula** (`.titulo-1` para el título del menú, `.titulo-2` para cada sección).
- **Texto, nombres de métricas y tablas:** Plus Jakarta Sans. Números en cifras tabulares.
- **Valores de las tarjetas:** Space Grotesk 700, 30 px (24 px en los números base; su % al lado en menta, 15 px).
- **Nombre de cada métrica:** 14 px, semibold, en `--texto-2` (en menta si es clave). Sin mayúsculas: son largos y se leen mejor así.

## Filtros (iguales en todos los menús)

- **Fecha:** un solo botón con calendario (`selectorRango` en `comun.js`): atajos arriba (últimos 7/14/30 días, este mes, mes pasado, este año si hay datos, y los propios del menú, como «Todas las fechas» en Seguimientos), el atajo activo en acento, y dos meses para elegir inicio y fin. Lo usan Panel, Trazabilidad, Calendario, Seguimientos (por día de la cita), Rendimiento, Bitácora, Finanzas e Inicio (al lado de Mes / Año; un rango que no es un mes entero pasa a «personalizado» y la proyección se toma en proporción a los días).
- **Clínicas:** desplegable propio con casillas; arriba los atajos Nuevas / Anteriores / Todas (el admin ve la lista por grupo, del campo «Grupo» de la Ficha de clientes, con «Marcar todas» en cada grupo), buscador desde 9 clínicas y «Solo» en cada fila para quedarse con una (`selectorClinicas`). La selección es la misma en todos los menús, también Inicio y Finanzas. Nunca un `<select>` del navegador para filtrar (los `<select>` quedan para campos de formularios).
- **Cerrar:** todo desplegable va dentro de un contenedor `data-pop="<clave>"` (ver `POPOVERS` en `comun.js`); tocar afuera o Escape lo cierra.

## Tarjeta de indicador

Una sola tarjeta para todos los menús, del mismo alto y con el mismo texto (clases `.kpi` y `.kpi--clave` en `marca.css`; la arma `tarjeta()` en `comun.js`):

- Arriba: nombre de la métrica y, a la derecha, la variación contra el período anterior (pastilla verde o roja).
- Valor (Space Grotesk, 32 px, números tabulares) y debajo el contexto ("vs 484 ant.").
- El % de la métrica va en una pastilla menta al lado del número (`k.pct`); en el contexto se aclara qué es ("cancelación · vs 4 ant.").
- KPI clave (`.kpi--clave`): solo cambia el brillo menta y el borde (y, en algunos menús, el ancho). Mismo alto y mismo texto que el resto.

### Menú lateral y bloques

- Menú lateral: Inicio (general) y tres grupos desplegables: Motor Agencia (solo admin), Motor Clínicas y Administración. El estado abierto/cerrado se guarda en el navegador.
- Orden de Motor Clínicas: Panel de campañas, Trazabilidad, Calendario, Seguimientos, Rendimiento comercial, Bitácora. Trazabilidad tiene switch Anuncios | Pacientes cerrados (este, solo admin, menú «traz-cerrados»: base de cerrados con anuncio de origen, ranking por anuncio/campaña/conjunto/fuente y CSV), como Bitácora Doctor | Growth. Administración: Ficha de clientes, Indicadores, Usuarios. El closer no ve Administración: su «Ficha de clientes» va al final de Motor Clínicas.
- Toda sección con título (`h2.titulo-2` dentro de un `<section>`) se pliega al tocar el título; lo hace `window.dcPostRender` en `comun.js` y se guarda en el navegador.

### Métricas clave por menú

| Menú / embudo | Clave |
|---|---|
| Limpieza | Costo por lead, Costo por cita, % de asistencia, Costo por paciente que asistió |
| Carillas · landing e Implantes | Costo por llamada, % asistencia orientación, Tasa de cierre efectiva, CAC (costo por venta) |
| Carillas · formulario | Costo por lead, % asistencia orientación, Tasa de cierre efectiva, CAC (costo por venta) |
| Calendario · Orientación virtual | Agendadas, asistidas, % asistencia, calificadas, valoraciones agendadas, tasa de cierre efectiva |
| Calendario · Citas de limpieza | Agendadas, asistidas, % asistencia, upsells, % upsells |
| Calendario · Valoraciones (high ticket) | Agendadas, asistidas, % asistencia, tratamientos cerrados, tasa de cierre efectiva |
| Resumen › Agenda | Citas / orientaciones de hoy |

Se cambian en `funnel.js` (`claves`), `comun.js` (`CAL_GRUPOS`, calendario) y `resumen.js`. En el calendario, «Personalizar» muestra los dos grupos del tipo de cita (KPI clave y universales): cada usuario oculta o reordena dentro de cada grupo, y se guarda por tipo de cita en su navegador. Universales: no asistieron, reprogramadas, canceladas, citas pasadas (por fecha y hora), pendientes, sin marcar y seguimientos activos (orientaciones y valoraciones); en orientaciones además anticipos pagados y pendientes. En el calendario, si el rango llega al futuro, la variación compara solo lo que ya pasó (hasta hoy) contra el mismo tramo del período anterior.

## Estilo juego (barras de cumplimiento en todos los menús)

- Que cada usuario entre, vea sus números y quiera ganar más: toda tarjeta con meta o con algo contra qué medirse lleva una barra que se llena (`.juego-barra`, con `verMeta` / `metaBarra` / `metaEst` en la tarjeta) debajo de su pastilla de meta; al cumplir la barra pasa a verde y la tarjeta brilla (`.kpi--logro`, lo agrega `tarjeta()` cuando `metaEst` es «cumple»).
- De dónde sale la barra: metas de Indicadores (`contraMeta`: Calendario, Mi rendimiento), período anterior (`contraAnterior`: Bitácora del doctor, «¡Superaste el mes anterior!»), proyección (Finanzas: cash y profit), seguimientos al día y comisión de la semana cobrada (Bitácora Growth).
- Mi rendimiento (closer): arriba `.juego-hero` con lo ganado en grande, el próximo objetivo (bono) en una pista que se llena con lo que vale llegar («te faltan N anticipos: son $X + el bono») y un anillo con los KPI cumplidos (`anillo()` en `comun.js`).
- Las barras se llenan con animación al aparecer (se desactiva con «reducir movimiento»).

## Reglas al agregar algo

- Colores siempre con variables de `marca.css`. Si hace falta uno nuevo, se agrega ahí con nombre y uso.
- Nada de etiquetas chicas encima de los títulos, texto con degradé, bordes laterales de color en tarjetas ni emojis como íconos (íconos SVG de trazo, como los del menú).
- Botones y controles: mínimo 40–44 px de alto; opción elegida con fondo `--acento` y texto blanco.
- Revisar en 1440 px y 390 px antes de publicar. El artifact se arma con `tools/pagina_estatica.py`, que embebe `marca.css` y el logo (`web/logo-growth.png`).

## Calendario

- Arriba: grupo de citas (Virtuales · Presenciales); en presenciales, chips Todas · Limpiezas · Valoraciones con su cantidad, y en valoraciones el tratamiento; closer (solo admin; filtra por las clínicas que tiene asignadas en Usuarios). El período va en el selector de fechas del encabezado.
- Después, el bloque «Indicadores de la agenda» (plegable). Debajo, el calendario con Día / Semana / Mes.
- Semana como en GHL: grilla por hora (`.cal-semana`), cada cita en su hora como bloque de 30 minutos; las que se pisan se reparten el ancho; línea roja en la hora actual.
- Mes: cada cita se abre con un clic; el número del día y «+N más» llevan al día. Al entrar a un día se muestra «Volver a la semana / al mes».
- Ficha: la clínica va en una pastilla menta arriba del nombre (`.ficha-clinica`); los datos del lead, con la etiqueta arriba del valor (`.ficha-datos`). Para admin y closer la pastilla es un botón («Ver ficha ›») que abre la ficha comercial de la clínica en una capa encima del panel del lead (`.fc-capa`, mismo ancho), con flecha arriba a la izquierda para volver (Escape también vuelve) y solo lo que se usa para vender: datos rápidos, clínica y doctor, precios, tratamiento, quién califica, casos, objeciones, logística y material (`FICHA_VENTA` en recursos.js). El admin tiene «Editar la ficha completa» (va a Ficha de clientes). En «Precios y paquetes» va primero la lista de precios de la tabla de tratamientos. El botón «Abrir chat» abre el contacto en GHL con su conversación.

## Ficha de clientes

- Menú `#recursos` (antes «Data / Recursos»), en Administración. Admin: tabla «Clínicas» (como Data Clientes del CRM GDS, con % de comisión, precio de limpieza y cantidad de tratamientos de alto ticket cargados; la columna Ficha es el % de campos cargados) y debajo la ficha de la clínica elegida, con «Editar ficha». Closer: botones con sus clínicas y la ficha sin «Datos de la agencia» ni «Comisión y descuentos».
- «Comisión y descuentos» (solo admin): % de GDS en grande (`.com-pct`) y la tabla de tratamientos (`.com-tabla`): categoría de la bitácora + nombre o paquete, precio, laboratorio y materiales, especialista, «Descuentos» (chips `.com-chip`; al editar, desplegable con casillas `.com-desc-btn` / `.com-desc-menu` que se abre dentro de la celda) y la comisión por tratamiento antes de la pauta. Sin tabla, al editar arranca con limpieza y el tratamiento de la clínica con los descuentos de la Plantilla de Acuerdo (limpieza: pauta; alto ticket: pauta + laboratorio). Nunca se restan gastos fijos.
- Cálculo (Finanzas → Pacientes cerrados y «Comisión por semana»): cada pago de la bitácora busca su fila por categoría (si hay varias, la que tiene el nombre en el detalle). Se resta laboratorio (lo que cargó el doctor o, en el primer pago, el costo de la ficha), especialista (en el primer pago) y la pauta de Meta de esa semana (lunes a domingo) del funnel, limpiezas o alto ticket, repartida entre los pagos de la semana según su neto. Si la pauta supera lo facturado, la comisión es 0. La pauta sale de datos.json (últimos 90 días). Las limpiezas asistidas entran solas (etiqueta «Automático»); comisión en MXN y ≈ USD debajo. Arriba de la tabla, tres bloques: generada, pagada por Stripe y por cobrar; casilla por fila para elegir varios pacientes y una barra fija para marcarlos pagados con el pago de Stripe que los cubre.
- Ficha: cabecera (`.rec-cabeza`), datos rápidos para la llamada (`.rec-rapido`: tratamiento, precio base, anticipo, MSI, doctor) y una sección plegable por bloque con los campos en grilla (`.rec-campos`). Solo se muestran los campos con dato; al editar aparecen todos.
- Los campos salen de `gds/recursos.py` (mismas claves que la Ficha Clientes del onboarding).

## Rendimiento comercial

- Menú `#rendimiento` (antes `#comisiones`, que redirige). Período propio (Este mes / Mes pasado / Últimos 30 días o rango) y el filtro de clínicas de siempre; el admin además elige closer.
- Closer («Mi rendimiento»): «Tu comisión» (total del período ancho y con brillo, por valoraciones, por tratamientos, bono con barra de avance del mes y pendiente de cobrar), «Tus KPI» (tarjetas con la pastilla cumple / cerca / falta y una línea con lo que falta mejorar), detalle de comisiones y pagos por mes.
- Admin: resumen del equipo, alertas (`.rend-alerta`, rojo = no cumple, ámbar = atención), tabla de posiciones (`.rend-pos`, el 1.º en menta), KPI por clínica (celdas coloreadas por estado) y una tarjeta por closer con «Registrar pago».
- Las tasas se colorean solo para juzgar contra la meta de Indicadores; sin meta quedan en gris.

## Inicio y Finanzas

- Mismo período en los dos (Mes / Año con flechas y el filtro de fechas, en la cabecera). Todo en USD; MXN chico al lado cuando ayuda.
- Inicio: primero las métricas financieras; el % de la proyección cumplido va chico, en un anillo al costado (`.ini-anillo`, abajo y horizontal en pantallas chicas; color por estado: menta o verde va bien, ámbar cerca, rojo atrasado) con una marca blanca donde habría que estar hoy según los días que pasaron. La tabla «Cumplimiento por línea» va después de Clínicas. Las tarjetas con proyección llevan la misma barra chica (`.ini-barra`) y «N% de US$X proyectado». Ranking de clínicas con medallas (`.rend-pos`) y barras. Alertas con botón al menú que las resuelve (`.rend-alerta`). Agenda de hoy en lista (`.ini-hoy-cita`, clic abre la ficha).
- Finanzas (balance de ingresos y egresos; los pacientes cerrados y la cotización van en la Bitácora Growth): 6 tarjetas en `.grilla` de 3 (Facturación · Cash collected neto · Gastos · Flujo de caja neto · Comisión por socio · Comisiones por cobrar en USD con MXN y cotización chicos y `.kpi-ir` a cobros), secundarias en `.sec`, y en `.bloques` la dona de ganancia por categoría (`.fin-dona`) junto al reparto entre socios. Ingresos y Gastos con su botón de registrar en la cabecera (`.fin-boton`), barras por categoría que filtran el listado (`.fin-cat--filtro`) y el estado del reparto en pastilla (`.fin-rep`: ámbar pendiente, verde repartido, oro a reservas).
- Dona: colores fijos por categoría, nunca por tamaño: alto ticket `#2E9E6B`, limpiezas `#3B82C4`, fees semanales `#B38A26`, incorporación `#8B6CC8`, comisiones sin desglose `#C2603E`, otros `#6B7A72` (validados para daltonismo sobre `--tarjeta`). Siempre con leyenda con monto y %; al pasar por un arco o su fila, el centro muestra esa categoría. Un `<svg>` por arco (dc-lite no recorre `sc-for` dentro de un `<svg>`).

