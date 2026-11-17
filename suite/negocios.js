// Negocios de la suite: cada uno es como una subcuenta con su propio vocabulario, menús, modelo de cobro y socios.
// Los datos de ejemplo (DEMO) son ficticios: sirven para ver la forma de cada menú hasta conectar CRM, Meta y Finanzas.
var NEGOCIOS = {
  plastia: {
    id: 'plastia',
    nombre: 'Plastia Partners',
    corto: 'Plastia',
    sigla: 'PP',
    modelo: 'comision',
    modeloTxt: 'Setup + 25% del margen de cirugías',
    ico: '#8FD6C1',
    logo: '<img src="logo-plastia.svg?v=2" alt="Plastia Partners" width="148" height="52">',
    socios: [{ nombre: 'Mateo', pct: 100 }],
    voc: { cuenta: 'Clínica', cuentas: 'Clínicas', contacto: 'Paciente', contactos: 'Pacientes', vendedor: 'Closer', vendedores: 'Closers', servicio: 'Cirugía', servicios: 'Cirugías', citaPrincipal: 'Valoración', calificacion: 'Llamada de evaluación', compromiso: 'Anticipo' },
    cobro: { setup: 750, pctAgencia: 25, pctCloser: 25 },
    menus: [
      { grupo: null, items: [['resumen', 'Inicio', 'casa']] },
      { grupo: 'Motor Agencia', items: [['ag-ventas', 'Ventas Plastia', 'tendencia'], ['ag-campanas', 'Campañas Plastia', 'megafono'], ['finanzas', 'Finanzas', 'billetera'], ['tareas', 'Tareas', 'check']] },
      { grupo: 'Motor Contenido', items: [['guiones', 'Guiones', 'guion'], ['tablero-edicion', 'Tablero de edición', 'tablero'], ['storyboards', 'Storyboards', 'video'], ['estilos', 'Estilos de edición', 'paleta']] },
      { grupo: 'Motor Clínicas', items: [['panel', 'Panel de campañas', 'megafono'], ['trazabilidad', 'Trazabilidad', 'ruta'], ['calendario', 'Calendario de citas', 'calendario'], ['conversaciones', 'Conversaciones', 'chat'], ['pacientes', 'Pacientes', 'personas'], ['seguimientos', 'Seguimientos', 'reloj'], ['rendimiento', 'Rendimiento de closers', 'trofeo'], ['semanal', 'Reportes semanales', 'informe'], ['bitacora', 'Bitácora de cirugías', 'libro']] },
      { grupo: 'Administración', items: [['recursos', 'Ficha de clínicas', 'ficha'], ['indicadores', 'Indicadores', 'diana'], ['usuarios', 'Usuarios', 'usuario']] }
    ]
  },
  tpa: {
    id: 'tpa',
    nombre: 'Top Producer Acquisition',
    corto: 'TPA',
    sigla: 'TPA',
    modelo: 'fee',
    modeloTxt: 'Setup US$4,000 + fee mensual US$750',
    ico: '#E01010',
    // Logo propuesto (TPA no tenía): ícono rojo con barras que suben + palabra en Space Grotesk
    logo: '<svg viewBox="0 0 186 52" width="186" height="52" role="img" aria-label="Top Producer Acquisition"><defs><linearGradient id="tpa-caja" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FF1919"/><stop offset="1" stop-color="#B90000"/></linearGradient></defs>' +
      '<rect x="3" y="3" width="46" height="46" rx="11" fill="url(#tpa-caja)" stroke="#FFFFFF" stroke-opacity=".22"/>' +
      '<g fill="#FFFFFF"><rect x="13" y="29" width="6" height="10" rx="1.5"/><rect x="23" y="23" width="6" height="16" rx="1.5"/><rect x="33" y="16" width="6" height="23" rx="1.5" fill="#FFDC46"/></g>' +
      '<path d="M12 22l9-7 5 4 9-8" fill="none" stroke="#FFFFFF" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>' +
      '<text x="60" y="25" font-family="Space Grotesk, sans-serif" font-weight="700" font-size="15.5" fill="#F3F3F3" letter-spacing=".2">TOP PRODUCER</text>' +
      '<text x="61" y="41" font-family="Space Grotesk, sans-serif" font-weight="600" font-size="8.6" fill="#FF4040" letter-spacing="3.05">ACQUISITION</text></svg>',
    socios: [{ nombre: 'Mateo', pct: 50 }, { nombre: 'Luis', pct: 50 }],
    voc: { cuenta: 'Cliente', cuentas: 'Clientes', contacto: 'Lead', contactos: 'Leads', vendedor: 'Setter', vendedores: 'Setters', servicio: 'Servicio', servicios: 'Servicios', citaPrincipal: 'Cita principal', calificacion: 'Llamada de calificación', compromiso: 'Compromiso' },
    cobro: { setup: 4000, fee: 750 },
    menus: [
      { grupo: null, items: [['resumen', 'Inicio', 'casa']] },
      { grupo: 'Motor Agencia', items: [['ag-ventas', 'Ventas TPA', 'tendencia'], ['ag-campanas', 'Campañas TPA', 'megafono'], ['finanzas', 'Finanzas', 'billetera'], ['tareas', 'Tareas', 'check']] },
      { grupo: 'Motor Contenido', items: [['guiones', 'Guiones', 'guion'], ['tablero-edicion', 'Tablero de edición', 'tablero'], ['storyboards', 'Storyboards', 'video'], ['estilos', 'Estilos de edición', 'paleta']] },
      { grupo: 'Motor Clientes', items: [['panel', 'Panel de campañas', 'megafono'], ['trazabilidad', 'Trazabilidad', 'ruta'], ['calendario', 'Calendario de citas', 'calendario'], ['conversaciones', 'Conversaciones', 'chat'], ['pacientes', 'Leads', 'personas'], ['seguimientos', 'Seguimientos', 'reloj'], ['semanal', 'Reportes semanales', 'informe'], ['bitacora', 'Cierres de clientes', 'libro'], ['cobros', 'Suscripciones', 'tarjeta']] },
      { grupo: 'Administración', items: [['recursos', 'Ficha de clientes', 'ficha'], ['indicadores', 'Indicadores', 'diana'], ['usuarios', 'Usuarios', 'usuario']] }
    ]
  }
};

// Para qué sirve cada menú (del SOP), adaptado por negocio. Se muestra mientras el menú no está construido.
var MENU_INFO = {
  'ag-ventas': ['F1', 'El embudo comercial propio: llamadas de venta agendadas, asistidas, % asistencia, propuestas, cierres, tasa de cierre y ciclo de venta. Sale del calendario de ventas de la subcuenta propia en Go High Level.'],
  'ag-campanas': ['F1', 'Las campañas propias (Meta y YouTube) con la misma estructura que el Panel de campañas: gasto, leads, costo por lead, llamadas agendadas, costo por llamada, asistidas, cierres y CAC propio.'],
  'finanzas': ['F4', 'Balance de ingresos y egresos, reparto entre socios y lo que falta cobrar. Seis tarjetas, dona de ganancia por categoría, ingresos y gastos con su categoría.'],
  'tareas': ['F5', 'Tablero tipo Trello del equipo: listas, tarjetas arrastrables, responsable, fecha, checklist y repetición. Las de hoy aparecen en el Inicio.'],
  'panel': ['F1', 'Semáforo de cuentas, 4 KPI clave contra la meta, embudo con cada % al lado de su número, métricas secundarias, costo por cita y tendencia, tabla por cuenta.'],
  'trazabilidad': ['F1', 'Qué anuncios traen citas y ventas reales, con veredicto escalar / mantener / revisar / pausar. Switch a contactos cerrados con su anuncio de origen.'],
  'calendario': ['F2', 'La agenda real del CRM (día / semana / mes), indicadores de la agenda y la ficha de cada cita con el resultado de la llamada.'],
  'conversaciones': ['F5', 'Los chats del CRM dentro de la suite: lista, chat y contacto en tres columnas.'],
  'pacientes': ['F3', 'El contacto final como eje: citas, servicios, pagos y origen del anuncio.'],
  'seguimientos': ['F2', 'Leads en seguimiento en columnas por fecha del próximo contacto: vencidos, hoy, mañana, esta semana, más adelante.'],
  'rendimiento': ['F4', 'Comisión de cada closer (25% de la ganancia de Plastia por cirugía), KPI contra metas, tabla de posiciones y alertas.'],
  'semanal': ['F6', 'El reporte de los lunes por embudo: cuello de botella, qué cambió, plan de la semana, ángulos de anuncios que funcionaron.'],
  'bitacora': ['F3', 'Cada venta que cobra la cuenta con sus costos. Es la base del cálculo de comisión (Plastia) o la prueba de retorno del cliente (TPA).'],
  'cobros': ['F4', 'Suscripciones: fee por cliente, fecha de corte, estado del mes (pagado / pendiente / vencido), días de mora y link de pago.'],
  'recursos': ['F3', 'Todo lo que hace falta para vender por la cuenta y calcular lo que se le cobra: condiciones comerciales, servicios, precios, objeciones.'],
  'indicadores': ['F1', 'Metas contra las que se juzga todo: costos objetivo por embudo, tasas meta y proyección por mes.'],
  'guiones': ['F8', 'En la reunión semanal se eligen los ángulos que funcionaron, las cuentas, cuántos videos y el estilo; Claude genera los guiones y llegan como tarjetas «Para revisar» al Tablero de edición.'],
  'tablero-edicion': ['F8', 'El flujo de cada video: Guiones → Por editar → Storyboard → En corrección → Editando → Editados, con costo estimado por tarjeta.'],
  'storyboards': ['F8', 'Revisar el borrador de cada video antes de editarlo: línea de tiempo por escenas, notas por escena, aprobar o mandar a corregir.'],
  'estilos': ['F8', 'Catálogo de estilos de edición (preset, guía escrita y preview) y criterios generales.'],
  'usuarios': ['F0', 'Alta de usuarios, rol, cuentas asignadas, menús visibles, «Ver como» y pestaña de seguridad.']
};

// ---- Datos de ejemplo (ficticios) ----
var DEMO = {
  plastia: {
    // Cirugías vendidas en el mes: venta, costos de la cirugía (quirófano, insumos, honorarios) y pauta asignada
    cuentas: [
      { n: 'Clínica Aurora', cirugias: [[8200, 3100, 640], [6400, 2500, 520], [9800, 3900, 700]], cobrado: 1180 },
      { n: 'Centro Bellavista', cirugias: [[7100, 2900, 610], [5600, 2300, 480]], cobrado: 690 },
      { n: 'Dr. Ejemplo Ruiz', cirugias: [[11200, 4600, 820]], cobrado: 0 },
      { n: 'Clínica Mirador', cirugias: [[4900, 2100, 450], [5200, 2200, 460]], cobrado: 380 },
      { n: 'Estética Norte', cirugias: [[6100, 2600, 560]], cobrado: 0 }
    ],
    setups: [750],
    proy: { cash: 9800, setups: 3, comisiones: 10500, flujo: 6800, cuentas: 6, pautaPropia: 1200, pautaCuentas: 8000 },
    gastos: [['Pauta propia (Meta)', 640], ['Herramientas', 310], ['Comisión de Stripe', 96]],
    pautaPropia: 640,
    meses: [['Jul 26', 3200, 7000], ['Ago 26', 5400, 7600], ['Sep 26', 6900, 8200], ['Oct 26', 8100, 9000], ['Nov 26', 0, 9800]],
    hoy: [['09:30', 'Valoración', 'Valoración - Paciente A.', 'Clínica Aurora', 'Asistió'], ['11:00', 'Evaluación', 'Llamada - Paciente B.', 'Centro Bellavista', 'Sin marcar'], ['15:00', 'Valoración', 'Valoración - Paciente C.', 'Clínica Mirador', 'Sin marcar'], ['17:30', 'Evaluación', 'Llamada - Paciente D.', 'Estética Norte', 'Canceló']],
    conteoHoy: [[2, 'valoraciones'], [2, 'llamadas de evaluación']],
    alertas: [
      ['falta', 'Cash collected atrasado', 'Vas por debajo del ritmo de la proyección del mes.', 'Ver finanzas', 'finanzas'],
      ['cerca', 'Comisiones por cobrar', '2 clínicas con comisiones generadas sin cobrar.', 'Cobrar', 'bitacora'],
      ['cerca', 'Comisiones de closers por pagar', 'Pagos pendientes del período.', 'Registrar pago', 'rendimiento'],
      ['falta', 'Citas sin marcar', '5 citas de los últimos 7 días siguen sin estado.', 'Ver calendario', 'calendario']
    ],
    tareas: [['Revisar costos de cirugía de Clínica Mirador', 'Hoy'], ['Onboarding del closer nuevo', 'Vencida']]
  },
  tpa: {
    cuentas: [
      { n: 'Cliente Alfa', alta: 'ago', estado: 'pagado', roi: 6.1, citas: 34 },
      { n: 'Cliente Beta', alta: 'sep', estado: 'pagado', roi: 4.3, citas: 28 },
      { n: 'Cliente Gamma', alta: 'sep', estado: 'vencido', roi: 1.2, citas: 9, mora: 12 },
      { n: 'Cliente Delta', alta: 'oct', estado: 'pagado', roi: 3.4, citas: 21 },
      { n: 'Cliente Épsilon', alta: 'oct', estado: 'pendiente', roi: 2.6, citas: 17 },
      { n: 'Cliente Zeta', alta: 'nov', estado: 'pagado', roi: 0, citas: 6 }
    ],
    setups: [4000],
    bajas: 0,
    proy: { cash: 11000, setups: 2, mrr: 5250, flujo: 7400, cuentas: 7, pautaPropia: 1800, pautaCuentas: 9000 },
    gastos: [['Pauta propia (Meta y YouTube)', 1150], ['Herramientas (GHL, IA)', 420], ['Comisión de Stripe', 260]],
    pautaPropia: 1150,
    meses: [['Jul 26', 5600, 8000], ['Ago 26', 9100, 9000], ['Sep 26', 10400, 10000], ['Oct 26', 11200, 10500], ['Nov 26', 0, 11000]],
    hoy: [['10:00', 'Venta TPA', 'Llamada de venta - Prospecto A.', 'Agencia', 'Asistió'], ['12:30', 'Cita cliente', 'Cita principal - Lead B.', 'Cliente Alfa', 'Sin marcar'], ['16:00', 'Venta TPA', 'Llamada de venta - Prospecto C.', 'Agencia', 'Sin marcar']],
    conteoHoy: [[2, 'llamadas de venta TPA'], [1, 'citas de clientes']],
    alertas: [
      ['falta', 'Fee vencido', 'Cliente Gamma: 12 días de mora.', 'Ver suscripciones', 'cobros'],
      ['falta', 'Salud del cliente', 'Cliente Gamma: costo por cita fuera de meta 2 semanas seguidas.', 'Ver panel', 'panel'],
      ['cerca', 'Fee pendiente', 'Cliente Épsilon: corte esta semana.', 'Ver suscripciones', 'cobros'],
      ['cerca', 'Ganancia sin repartir', 'Reparto 50/50 con Luis pendiente del período.', 'Ver reparto', 'finanzas']
    ],
    tareas: [['Grabar creativos nuevos con Luis', 'Hoy']],
    // Pauta propia: se carga a la tarjeta de Luis; Mateo le transfiere su 50%
    pautaMov: [['02 nov', 'Meta Ads', 'Realtors · VSL', 210], ['05 nov', 'YouTube Ads', 'Realtors · video largo', 160], ['08 nov', 'Meta Ads', 'Realtors · VSL', 240], ['11 nov', 'YouTube Ads', 'Realtors · video largo', 180], ['14 nov', 'Meta Ads', 'Retargeting', 190], ['16 nov', 'Meta Ads', 'Realtors · VSL', 170]],
    pagadorPauta: 'Luis',
    transferencias: [['06 nov', 'Mateo', 'Luis', 250, 'Mi parte, semana 1'], ['13 nov', 'Mateo', 'Luis', 200, 'Mi parte, semana 2']]
  }
};

// Cálculos del modelo de cobro
function calcPlastia(d, cfg) {
  var pct = cfg.cobro.pctAgencia / 100, pctCl = cfg.cobro.pctCloser / 100;
  var filas = d.cuentas.map(function (c) {
    var venta = 0, costos = 0, pauta = 0, n = c.cirugias.length;
    c.cirugias.forEach(function (x) { venta += x[0]; costos += x[1]; pauta += x[2]; });
    var margen = Math.max(0, venta - costos - pauta), com = margen * pct;
    return { n: c.n, venta: venta, costos: costos, pauta: pauta, margen: margen, comision: com, closer: com * pctCl, cobrado: c.cobrado, cirugias: n };
  });
  var t = { venta: 0, costos: 0, pauta: 0, margen: 0, comision: 0, closer: 0, cobrado: 0, cirugias: 0 };
  filas.forEach(function (f) { Object.keys(t).forEach(function (k) { t[k] += f[k]; }); });
  var setup = d.setups.reduce(function (a, b) { return a + b; }, 0);
  return { filas: filas, t: t, setup: setup };
}
function calcTpa(d, cfg) {
  var activos = d.cuentas.length, mrr = activos * cfg.cobro.fee;
  var vencido = d.cuentas.filter(function (c) { return c.estado === 'vencido'; }).length * cfg.cobro.fee;
  var pendiente = d.cuentas.filter(function (c) { return c.estado === 'pendiente'; }).length * cfg.cobro.fee;
  var pagado = mrr - vencido - pendiente;
  var setup = d.setups.reduce(function (a, b) { return a + b; }, 0);
  return { activos: activos, mrr: mrr, vencido: vencido, pendiente: pendiente, pagado: pagado, setup: setup };
}
