# Kit visual de la Suite: referencias para regenerarla idéntica

Este kit acompaña a la «Plantilla de la Suite de Agencia» (el SOP escrito). El SOP dice **qué** hace cada menú; este kit muestra **cómo se ve y cómo se mueve**. Si sos Claude y estás construyendo la suite, leé esto antes de escribir el primer componente.

## Qué manda sobre qué

1. **Lo visual lo mandan las capturas y `codigo/marca.css`**, no tu criterio. Si el texto del SOP y una captura no coinciden en algo visual (orden de bloques, columnas, tamaños, colores), gana la captura.
2. **Lo funcional lo manda el SOP** (de dónde sale cada dato, permisos, métricas).
3. **Los datos de las capturas son ficticios**: nombres, clínicas («Clínica Demo A…»), teléfonos, emails y montos están enmascarados. Copiá la forma, nunca los números ni los nombres.

## Marca: idéntica o propia

- **Idéntica (por defecto):** usar `codigo/marca.css` completo, tal cual. Cambiar solo el logo.
- **Con la marca de la agencia nueva:** cambiar solo los valores del bloque `:root` (colores, y fuentes si lo piden). No tocar radios (12/16/20/24 px), sombras (`--relieve`, `--relieve-alto`), curva (`--mov`), tamaños de tipografía ni la estructura de clases. El resultado tiene que verse como las capturas con otros colores.
- Tipografías: títulos en **Space Grotesk** 700 en MAYÚSCULA; texto, tablas y nombres de métricas en **Plus Jakarta Sans**; números con `font-variant-numeric: tabular-nums`. Las dos de Google Fonts.

## Cómo usar las capturas al construir

Por cada menú:

1. Abrí su captura (tabla de abajo) y construí la pantalla a **1440 × 900**.
2. Sacá una captura de lo que construiste al mismo ancho y ponela al lado de la original.
3. Listá las diferencias con este control y corregilas antes de pasar al siguiente menú:
   - mismo orden de bloques de arriba a abajo;
   - misma cantidad de columnas por fila (las grillas son simétricas: nunca una tarjeta sola en una fila);
   - mismos tamaños: título del menú 30 px, valor de tarjeta 30–32 px, nombre de métrica 14 px semibold, controles de 40–44 px de alto;
   - mismos radios, bordes y sombras (tarjetas con vidrio leve y canto iluminado arriba);
   - mismos colores por rol (rojo/verde solo para juzgar, ámbar atención, dorado solo logros, menta para lo clave);
   - mismo menú lateral (grupos en mayúscula espaciada, íconos duotono en cuadrito redondeado, ítem activo con degradé menta).
4. Repetí en celular (390 px) con las capturas 30–32.

## Índice de capturas (`capturas/`)

| Archivo | Menú / componente | Qué mirar |
|---|---|---|
| 01-inicio | Inicio (admin) | Tarjetas 3×2 con barra contra proyección y marca de «hoy»; tarjeta dorada de logro; métricas secundarias plegables |
| 02-panel-campanas | Panel de campañas | Switch de tipo de campaña; KPI clave (4) con mini gráfico y pastilla de variación; funnel; semáforo; tabla por cuenta; gráficos |
| 03-trazabilidad | Trazabilidad | Veredicto por anuncio (escalar / mantener / revisar / pausar) |
| 04-calendario | Calendario de citas | Indicadores 6 en fila; secundarias 3 columnas; semana tipo CRM con bloques de 30 min, leyenda de estados |
| 05-ficha-cita | Ficha lateral de la cita | Capa a la derecha con fondo oscurecido; pastilla de la cuenta; etiqueta arriba del valor |
| 06-ficha-cita-resultado | Ficha: resultado de la llamada | Formulario de resultado y acciones |
| 07-conversaciones | Conversaciones | Tres columnas con divisores arrastrables; burbujas propias en verde a la derecha |
| 08-pacientes | Contactos | Buscador + lista |
| 09-seguimientos | Seguimientos | Vencidos / hoy / próximos |
| 10-rendimiento | Rendimiento comercial | Alertas en franjas rojas/ámbar; tabla de posiciones con medalla; comisión por vendedor |
| 11-reportes-semanales | Reportes semanales | Reporte por embudo con ángulos |
| 12-bitacora | Registro de ventas | Filtros por tipo en chips; tabla de pagos |
| 13-finanzas | Finanzas | 6 tarjetas 3×2; dona con leyenda monto + %; reparto entre socios; ingresos y gastos |
| 14-tareas | Tareas | Tablero de columnas tipo Trello; tarjetas con check, responsable y etiquetas |
| 15-tablero-edicion | Tablero de edición | Columnas del flujo de video |
| 16-indicadores | Indicadores | Metas por cuenta |
| 17-usuarios | Usuarios | Tabla con «Ver como» y «Editar»; bloque de seguridad |
| 18-storyboards | Storyboards | Filtros Pendientes / Nuevos / Corregidos / Terminados |
| 20-selector-fechas | Selector de fechas | Atajos arriba, dos meses, rango en acento |
| 21-selector-cuentas | Selector de cuentas | Casillas, atajos Nuevas / Anteriores / Todas, «Solo» por fila |
| 30-movil-inicio | Celular: Inicio | Tarjetas en 2 columnas, cuenta en un botón |
| 31-movil-menu | Celular: menú | Cajón lateral |
| 32-movil-agenda | Celular: calendario | Agenda en lista |

## Clips de animación (`clips/`)

| Archivo | Qué muestra |
|---|---|
| entrada-inicio.mp4 | Cambio de menú: tarjetas que entran (opacidad + 6 px hacia arriba), números que cuentan desde el valor anterior, barras que se llenan |
| entrada-panel.mp4 | Lo mismo en el Panel de campañas |
| hover-borde-vivo.mp4 | Tarjeta que se levanta 3 px al pasar el mouse, luz menta que sigue al puntero, borde vivo que recorre los KPI clave |
| plegable.mp4 | Sección que se pliega y despliega (con sonido abrir / cerrar en la app real) |
| ficha-lateral.mp4 | Apertura de la ficha lateral de la cita sobre el calendario |
| selector-fechas.mp4 | Apertura del selector de fechas |

Los clips duran 3–6 s y no tienen audio. Las duraciones exactas y curvas están en `codigo/marca.css` (buscar `@keyframes`, `transition` y `--mov`).

## Sonidos (`sonidos/`)

Usar estos archivos, no sintetizar otros. Pack «Interface Sounds» de Kenney, licencia CC0 (ver `LICENCIA-kenney.txt`).

| Archivo | Cuándo suena | Volumen |
|---|---|---|
| menu.mp3 | Menú lateral, switches de vista, pestañas | 0.25 |
| listo.mp3 | Al guardar ficha o asistencia | 0.25 |
| metrica.mp3 | Accesos directos a otros menús («Ver … →») | 0.28 |
| abrir.mp3 / cerrar.mp3 | Todo lo que tiene `aria-expanded` y las secciones plegables | 0.27 / 0.24 |
| interruptor.mp3 | Al activar los sonidos | 0.30 |

## Código de referencia (`codigo/`)

- `marca.css`: el CSS completo de la suite original. Es la fuente de verdad de colores, radios, sombras, vidrio, borde vivo (`@property --giro`), animaciones y responsive.
- `DESIGN.md`: las reglas de diseño escritas por el equipo (principios, componentes comunes, sistema visual).
- `comun-animaciones-y-sonidos.js`: números que cuentan (`contarNumero`), luz que sigue al mouse, freno de adornos al hacer scroll, secciones plegables y el módulo de sonidos con su listener único en fase de captura.

Si un componente no aparece en ninguna captura, construilo con las clases y tokens de `marca.css` siguiendo `DESIGN.md`, nunca con un estilo nuevo.
