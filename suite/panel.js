// Panel de campañas, Campañas propias y Trazabilidad: leen /api/<negocio>/panel y /trazabilidad (datos del worker).
// Usa las piezas comunes de app.js (window.SUITE) y las clases de marca.css.
(function () {
  var P = { dias: 7, ambito: null, cuentas: null, filtro: 'todas', glosario: false };
  var ultimo = null; // { menu, negocio } que se está mostrando, para no pintar respuestas viejas

  function S() { return window.SUITE; }
  function n0(x) { return x == null ? '—' : Math.round(x).toLocaleString('en-US'); }
  function plata(x) { return x == null ? '—' : '$' + (x < 100 && x % 1 ? x.toFixed(1) : Math.round(x).toLocaleString('en-US')); }
  function pctTxt(x) { return x == null ? '—' : Math.round(x) + '%'; }
  function fechaCorta(s) { var m = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']; var p = s.split('-'); return +p[2] + ' ' + m[+p[1] - 1]; }
  // Variación: en costos bajar es bueno; en el resto, subir
  function vari(cambio, menosEsMejor) {
    if (cambio == null || !isFinite(cambio)) return null;
    var bueno = menosEsMejor ? cambio <= 0 : cambio >= 0;
    return [(cambio > 0 ? '+' : '−') + Math.abs(cambio).toFixed(1) + '%', bueno ? 'bien' : 'mal'];
  }
  function spark(serie) {
    var v = serie.map(function (x) { return x == null ? null : +x; }), hay = v.filter(function (x) { return x != null; });
    if (hay.length < 2) return '';
    var max = Math.max.apply(null, hay), min = Math.min.apply(null, hay), rango = max - min || 1, paso = 100 / (v.length - 1), pts = [];
    v.forEach(function (x, i) { if (x != null) pts.push((i * paso).toFixed(1) + ' ' + (30 - (x - min) / rango * 26).toFixed(1)); });
    var linea = 'M' + pts.join(' L');
    return '<svg class="kpi-spark" viewBox="0 0 100 34" preserveAspectRatio="none" aria-hidden="true"><path class="kpi-area" d="' + linea + ' L' + pts[pts.length - 1].split(' ')[0] + ' 34 L' + pts[0].split(' ')[0] + ' 34Z"/><path class="kpi-linea" d="' + linea + '"/></svg>';
  }

  // Tarjeta KPI del panel (misma tarjeta que el resto: nombre + variación, valor, contexto, meta, mini gráfico)
  function kpi(o) {
    var esc = S().esc, cls = 'kpi' + (o.clave ? ' kpi--clave' : '');
    var h = '<article class="' + cls + '"><div class="kpi-cab"><span class="kpi-nombre">' + esc(o.nombre) + '</span>' + (o.vari ? '<span class="pill var ' + o.vari[1] + '">' + o.vari[0] + '</span>' : '') + '</div>';
    h += '<div class="kpi-cuerpo"><div class="kpi-valores"><div class="kpi-valor">' + esc(o.valor) + (o.pct != null ? ' <span class="kpi-pct">' + o.pct + '</span>' : '') + '</div><div class="kpi-sub">' + esc(o.sub || '') + '</div></div>';
    if (o.meta) h += '<span class="kpi-meta" data-estado="' + o.meta[1] + '">' + esc(o.meta[0]) + '</span><span class="juego-barra" data-estado="' + o.meta[1] + '"><span style="width:' + o.meta[2] + '%"></span></span>';
    h += '</div>' + (o.serie ? spark(o.serie) : '') + '</article>';
    return h;
  }
  // Tasa contra la meta de Indicadores: cumple desde la meta, cerca desde el 90%; sin meta no hay pastilla
  function contraMeta(valor, meta) {
    if (valor == null || !meta) return null;
    return ['Meta ' + Math.round(meta) + '%', valor >= meta ? 'cumple' : valor >= meta * 0.9 ? 'cerca' : 'falta', Math.max(4, Math.min(100, valor / meta * 100))];
  }
  function seccion(titulo, sub, cuerpo, derecha) {
    var esc = S().esc;
    return '<section class="e22"><div class="e136"><div class="e19"><h2 class="titulo-2">' + esc(titulo) + '</h2>' + (sub ? '<p class="e44">' + esc(sub) + '</p>' : '') + '</div>' + (derecha || '') + '</div>' + cuerpo + '</section>';
  }

  function controles(r, conAmbito) {
    var esc = S().esc, cfg = NEGOCIOS[S().negocio()];
    var n = r.cuentas_disponibles.length, sel = P.cuentas ? P.cuentas.length : n;
    var h = '<div class="cab-filtros e36">';
    if (r.ambito === 'clientes') h += '<button class="btn-sec" type="button" aria-haspopup="menu" aria-expanded="false" disabled title="Selector de cuentas: próxima entrega">' + esc(cfg.voc.cuentas) + ': ' + (sel === n ? 'Todas' : sel) + ' (' + n + ')</button>';
    h += '<div class="seg" role="group" aria-label="Período">' + [7, 14, 30].map(function (d) { return '<button type="button" data-p-dias="' + d + '" aria-pressed="' + (P.dias === d) + '">' + d + ' días</button>'; }).join('') + '</div>';
    h += '<span class="btn-sec" aria-label="Rango"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 5h14v15H5zM5 10h14M9 3v4M15 3v4"/></svg>' + fechaCorta(r.desde) + ' – ' + fechaCorta(r.hasta) + '</span>';
    h += '<button class="btn-sec" type="button" data-p-glosario aria-expanded="' + P.glosario + '"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 4h11a3 3 0 0 1 3 3v13H8a3 3 0 0 1-3-3zM5 17a3 3 0 0 1 3-3h11"/></svg>Glosario</button></div>';
    if (conAmbito && S().sesion() && S().sesion().rol === 'admin') {
      h += '<div class="seg" role="group" aria-label="Qué campañas" style="align-self:flex-start"><button type="button" data-p-ambito="clientes" aria-pressed="' + (r.ambito === 'clientes') + '">' + esc(cfg.voc.cuentas) + '</button><button type="button" data-p-ambito="agencia" aria-pressed="' + (r.ambito === 'agencia') + '">' + esc(cfg.corto) + '</button></div>';
    }
    return h;
  }
  function glosario(r) {
    if (!P.glosario) return '';
    var esc = S().esc;
    return '<section class="caja ini-bloque"><div class="ini-bloque-cab"><h3 class="fin-h3">Glosario</h3></div><dl class="e33" style="margin:0">' +
      Object.keys(r.glosario).map(function (k) { return '<div><dt class="e7">' + esc(k) + '</dt><dd class="e11" style="margin:0">' + esc(r.glosario[k]) + '</dd></div>'; }).join('') + '</dl></section>';
  }
  function avisos(r) {
    var esc = S().esc, lista = (r.avisos || []).slice();
    if (r.demo) lista.unshift('Estás viendo datos de ejemplo: el worker todavía no tiene acceso a GHL, Meta ni YouTube.');
    if (!lista.length) return '';
    return seccion('Pendientes para que los datos sean exactos', null, '<div class="caja"><ul class="e144">' + lista.map(function (a) { return '<li>' + esc(a) + '</li>'; }).join('') + '</ul></div>');
  }

  var SEM = { critico: ['Crítico', 'var(--rojo)'], atencion: ['Atención', 'var(--ambar)'], bien: ['Bien', 'var(--verde)'], sin_datos: ['Sin datos', 'var(--gris)'] };
  var VER = { escalar: ['Escalar', 'cumple'], mantener: ['Mantener', ''], revisar: ['Revisar', 'falta'], pausar: ['Pausar', 'falta'], sin_datos: ['Aprendiendo', ''] };
  function punto(color) { return '<span class="punto" style="background:' + color + '"></span>'; }

  function vistaPanel(r) {
    var esc = S().esc, k = r.kpi, cfg = NEGOCIOS[S().negocio()], voc = cfg.voc;
    var titulo = r.ambito === 'agencia' ? 'Campañas ' + cfg.corto : 'Panel de campañas · ' + r.embudo;
    var sub = fechaCorta(r.desde) + '–' + fechaCorta(r.hasta) + ' vs ' + fechaCorta(r.anterior.desde) + '–' + fechaCorta(r.anterior.hasta) + ' · el color sale del costo por cita creada';
    var h = '<header><div class="e19"><h1 class="titulo-1">' + esc(titulo) + '</h1><span class="e30">' + esc(sub) + '</span></div></header>';
    h += controles(r, ultimo.menu !== 'ag-campanas') + glosario(r);
    var obj = r.objetivo, cc = k.costo_cita.valor, metaCita = cc == null ? null :
      ['Objetivo ' + plata(obj) + ' · ' + (cc <= obj ? '−' : '+') + plata(Math.abs(cc - obj)), cc <= obj ? 'cumple' : cc <= obj * 1.3 ? 'cerca' : 'falta', Math.max(4, Math.min(100, obj / cc * 100))];
    h += seccion('KPI clave', 'lo que trae plata: la cita que asiste · cada costo es el gasto dividido por ese paso',
      '<div class="grilla" style="--n:4">' +
      kpi({ nombre: 'Costo por lead', clave: true, valor: plata(k.costo_lead.valor), sub: 'vs ' + plata(k.costo_lead.anterior) + ' período ant.', vari: vari(k.costo_lead.cambio, true), serie: k.costo_lead.serie }) +
      kpi({ nombre: 'Costo por cita', clave: true, valor: plata(cc), sub: 'vs ' + plata(k.costo_cita.anterior) + ' período ant.', vari: vari(k.costo_cita.cambio, true), meta: metaCita, serie: k.costo_cita.serie }) +
      kpi({ nombre: '% de asistencia', clave: true, valor: pctTxt(k.pct_asistencia.valor), sub: 'vs ' + pctTxt(k.pct_asistencia.anterior) + ' ant.', vari: vari(k.pct_asistencia.cambio, false), meta: contraMeta(k.pct_asistencia.valor, r.metas && r.metas.pct_asistencia), serie: k.pct_asistencia.serie }) +
      kpi({ nombre: 'Costo por asistencia', clave: true, valor: plata(k.costo_asistente.valor), sub: 'vs ' + plata(k.costo_asistente.anterior) + ' período ant.', vari: vari(k.costo_asistente.cambio, true), serie: k.costo_asistente.serie }) +
      '</div>');
    h += seccion('Funnel', 'gasto de anuncios → leads → citas que vienen de anuncios → asistieron (por fecha de la cita)',
      '<div class="grilla" style="--n:4">' +
      kpi({ nombre: 'Gasto total', valor: plata(k.gasto.valor), sub: 'Meta + YouTube · vs ' + plata(k.gasto.anterior) + ' ant.', vari: vari(k.gasto.cambio, false), serie: k.gasto.serie }) +
      kpi({ nombre: 'Leads', valor: n0(k.leads.valor), sub: 'vs ' + n0(k.leads.anterior) + ' ant.', vari: vari(k.leads.cambio, false), serie: k.leads.serie }) +
      kpi({ nombre: 'Citas creadas', valor: n0(k.citas.valor), pct: r.secundarias.pct_agenda == null ? null : pctTxt(r.secundarias.pct_agenda), sub: 'agendamiento · vs ' + n0(k.citas.anterior) + ' ant.', vari: vari(k.citas.cambio, false), serie: k.citas.serie }) +
      kpi({ nombre: 'Citas asistidas', valor: n0(k.asistio.valor), sub: r.secundarias.no_asistio + ' no se presentaron · vs ' + n0(k.asistio.anterior) + ' ant.', vari: vari(k.asistio.cambio, false), serie: k.asistio.serie }) +
      '</div>');
    var s = r.secundarias, pas = s.pasadas || 0;
    h += S().secundarias('panel-' + r.ambito, [
      S().secItem('No presentados', n0(s.no_asistio), 'no asistencia · vs ' + s.no_asistio_ant + ' ant.', pas ? Math.round(s.no_asistio / pas * 100) : null),
      S().secItem('Cancelaciones', n0(s.canceladas), 'cancelación · vs ' + s.canceladas_ant + ' ant.', pas ? Math.round(s.canceladas / pas * 100) : null),
      S().secItem('Clics', n0(s.clics), n0(s.impresiones) + ' impresiones', s.impresiones ? +(s.clics / s.impresiones * 100).toFixed(1) : null)
    ]);
    h += seccion('Agenda', 'del calendario de GHL · toda la agenda',
      '<div class="bloques">' + kpi({ nombre: 'Citas de hoy', clave: true, valor: n0(r.agenda.hoy), sub: r.agenda.proximos_7 + ' en los próximos 7 días' }) +
      '<article class="kpi kpi--alerta"><div class="kpi-cab"><span class="kpi-nombre">Sin marcar</span></div><div class="kpi-cuerpo"><div class="kpi-valores"><div class="kpi-valor">' + n0(r.agenda.sin_marcar) + '</div><div class="kpi-sub">citas que ya pasaron y siguen sin estado</div></div></div></article></div>',
      '<button class="kpi-ir" type="button" data-ir="calendario">Ver calendario →</button>');
    var v = r.veredictos;
    h += '<div class="bloques">' + seccion('Trazabilidad', 'anuncios de este embudo en el período',
      '<div class="grilla" style="--n:3">' + kpi({ nombre: 'Para pausar', valor: String(v.pausar), sub: 'gastan sin resultados' }) + kpi({ nombre: 'Para revisar', valor: String(v.revisar), sub: 'costo alto' }) + kpi({ nombre: 'Para escalar', clave: true, valor: String(v.escalar), sub: 'costo bajo' }) + '</div>',
      '<button class="kpi-ir" type="button" data-ir="trazabilidad">Ver trazabilidad →</button>') +
      '<section class="caja ini-bloque"><div class="ini-bloque-cab"><h3 class="fin-h3">Alertas</h3></div>' + (r.alertas.length ? '<ul class="rend-alertas">' + r.alertas.map(function (a) {
        return '<li class="rend-alerta" data-nivel="' + a.nivel + '"><div class="e3"><strong>' + esc(a.cuenta) + '</strong><span>' + esc(a.texto) + '</span></div></li>';
      }).join('') + '</ul>' : '<p class="vacio">Sin alertas en el período.</p>') + '</section></div>';
    // Semáforo
    var sem = r.semaforo, total = 0; Object.keys(sem).forEach(function (e) { total += sem[e].length; });
    if (r.ambito === 'clientes') {
      h += seccion('Semáforo de ' + voc.cuentas.toLowerCase(), total + ' ' + voc.cuentas.toLowerCase() + ' · por costo por cita creada (verde hasta ' + plata(obj) + ', rojo arriba de ' + plata(r.objetivo_rojo) + ')',
        '<div class="caja borde-vivo"><div class="semaforo-barra">' + Object.keys(SEM).map(function (e) { return sem[e].length ? '<span style="flex:' + sem[e].length + ';background:' + SEM[e][1] + '"></span>' : ''; }).join('') + '</div>' +
        '<div class="grilla" style="--n:4">' + Object.keys(SEM).map(function (e) {
          return '<div class="e19"><div class="e64"><strong class="e91">' + punto(SEM[e][1]) + SEM[e][0] + '</strong><strong class="e118">' + sem[e].length + '</strong></div><span class="e12">' + (sem[e].length ? esc(sem[e].join(', ')) : '—') + '</span></div>';
        }).join('') + '</div></div>');
    }
    // Tabla por cuenta
    var filas = r.cuentas.filter(function (f) { return P.filtro === 'todas' || f.estado === P.filtro; });
    var chips = '<div class="e53" role="group" aria-label="Filtrar por estado">' + [['todas', 'Todas', 'var(--menta)']].concat(Object.keys(SEM).map(function (e) { return [e, SEM[e][0], SEM[e][1]]; })).map(function (c) {
      var n = c[0] === 'todas' ? r.cuentas.length : r.cuentas.filter(function (f) { return f.estado === c[0]; }).length;
      return '<button type="button" class="e94" data-p-filtro="' + c[0] + '" aria-pressed="' + (P.filtro === c[0]) + '">' + punto(c[2]) + c[1] + ' <span class="e12">' + n + '</span></button>';
    }).join('') + '</div>';
    var tabla = '<div class="rend-scroll"><table class="rend-tabla"><thead><tr><th>' + esc(r.ambito === 'agencia' ? 'Cuenta' : voc.cuenta) + '</th><th class="rend-num">Gasto</th><th class="rend-num">Leads</th><th class="rend-num">Citas creadas</th><th class="rend-num">% agenda</th><th class="rend-num">Costo/cita</th><th class="rend-num">vs ant.</th><th class="rend-num">Asistencia</th><th class="rend-num">Sin marcar</th><th class="rend-num">Próx. 7 días</th></tr></thead><tbody>' +
      filas.map(function (f) {
        var cv = vari(f.cambio_costo_cita, true);
        return '<tr><td><div class="e91">' + punto(SEM[f.estado][1]) + '<div class="e3"><strong>' + esc(f.nombre) + '</strong><span class="e12">' + esc(f.nota) + '</span></div></div></td>' +
          '<td class="rend-num">' + plata(f.gasto || null) + '</td><td class="rend-num">' + (f.leads ? n0(f.leads) : '—') + '</td><td class="rend-num">' + f.citas + '</td><td class="rend-num">' + pctTxt(f.pct_agenda) + '</td>' +
          '<td class="rend-num"><strong>' + plata(f.costo_cita) + '</strong></td><td class="rend-num" style="color:' + (cv ? (cv[1] === 'bien' ? 'var(--verde-texto)' : 'var(--rojo-texto)') : 'var(--texto-4)') + '">' + (cv ? cv[0] : '—') + '</td>' +
          '<td class="rend-num">' + (f.pasadas ? pctTxt(f.pct_asistencia) + ' <span class="e12">(' + f.asistio + ' de ' + f.pasadas + ')</span>' : '—') + '</td>' +
          '<td class="rend-num"' + (f.sin_marcar ? ' style="color:var(--ambar-texto)"' : '') + '>' + f.sin_marcar + '</td><td class="rend-num">' + f.proximos_7 + '</td></tr>';
      }).join('') + (filas.length ? '' : '<tr><td colspan="10" class="e11">Nada en este estado.</td></tr>') + '</tbody></table></div>';
    h += seccion(r.ambito === 'agencia' ? 'Campañas propias' : 'Campañas por ' + voc.cuenta.toLowerCase(), 'citas creadas en el período por contactos que vienen de un anuncio · ver Glosario', chips + tabla);
    // Gráficos
    var conCosto = r.cuentas.filter(function (f) { return f.costo_cita != null; }).sort(function (a, b) { return b.costo_cita - a.costo_cita; });
    var maxC = conCosto.length ? conCosto[0].costo_cita : 1;
    var barras = conCosto.length ? '<div class="e33">' + conCosto.map(function (f) {
      return '<div class="fin-cat"><span class="fin-cat-n">' + esc(f.nombre) + '</span><span class="rend-barra"><span style="width:' + Math.max(3, f.costo_cita / maxC * 100) + '%;background:' + SEM[f.estado][1] + ';box-shadow:none"></span></span><span class="fin-cat-v">' + plata(f.costo_cita) + '</span></div>';
    }).join('') + '</div>' : '<p class="vacio">Sin citas en el período.</p>';
    h += '<div class="bloques">' + bloqueGraf('Costo por cita creada por ' + voc.cuenta.toLowerCase(), 'verde hasta ' + plata(obj) + ' · rojo arriba de ' + plata(r.objetivo_rojo), barras) +
      bloqueGraf('Leads y citas por día', 'todas las ' + voc.cuentas.toLowerCase() + ' del filtro', tendencia(r.tendencia)) + '</div>';
    h += avisos(r);
    return h;
  }
  function bloqueGraf(titulo, sub, cuerpo) {
    var esc = S().esc;
    return '<section class="caja ini-bloque"><div class="e19"><h3 class="fin-h3">' + esc(titulo) + '</h3><span class="e12">' + esc(sub) + '</span></div>' + cuerpo + '</section>';
  }
  function tendencia(dias) {
    if (!dias.length) return '';
    var W = 560, H = 180, max = Math.max.apply(null, dias.map(function (d) { return Math.max(d.leads, d.citas); })) || 1, paso = dias.length > 1 ? (W - 30) / (dias.length - 1) : 0;
    function linea(k) { return dias.map(function (d, i) { return (i ? 'L' : 'M') + (30 + i * paso).toFixed(1) + ' ' + (H - 24 - d[k] / max * (H - 40)).toFixed(1); }).join(' '); }
    var cada = Math.ceil(dias.length / 7), ejes = '';
    dias.forEach(function (d, i) { if (i % cada === 0 || i === dias.length - 1) ejes += '<text x="' + (30 + i * paso).toFixed(1) + '" y="' + (H - 4) + '" text-anchor="middle">' + fechaCorta(d.dia) + '</text>'; });
    return '<div class="e64"><span></span><span class="e12">' + punto('var(--menta)') + 'Leads &nbsp; ' + punto('var(--serie-2)') + 'Citas creadas</span></div>' +
      '<svg viewBox="0 0 ' + W + ' ' + H + '" style="width:100%;height:auto" role="img" aria-label="Leads y citas por día">' +
      '<g fill="var(--texto-4)" font-size="11">' + ejes + '<text x="0" y="20">' + max + '</text><text x="0" y="' + (H - 24) + '">0</text></g>' +
      '<line x1="30" x2="' + W + '" y1="' + (H - 24) + '" y2="' + (H - 24) + '" stroke="var(--linea)"/>' +
      '<path d="' + linea('leads') + '" fill="none" stroke="var(--menta)" stroke-width="2" stroke-linejoin="round"/>' +
      '<path d="' + linea('citas') + '" fill="none" stroke="var(--serie-2)" stroke-width="2" stroke-linejoin="round"/></svg>';
  }

  function vistaTraz(r) {
    var esc = S().esc, cfg = NEGOCIOS[S().negocio()];
    var h = '<header><div class="e19"><h1 class="titulo-1">Trazabilidad · ' + esc(r.embudo) + '</h1><span class="e30">' + fechaCorta(r.desde) + '–' + fechaCorta(r.hasta) + ' · qué anuncios traen citas creadas</span></div></header>';
    h += controles(r, true) + glosario(r);
    h += '<div class="seg" role="group" aria-label="Vista" style="align-self:flex-start"><button type="button" aria-pressed="true">Anuncios</button><button type="button" aria-pressed="false" disabled title="Fase 3: necesita el registro de ventas">' + esc(cfg.voc.contactos) + ' cerrados</button></div>';
    var n = r.cuentas_disponibles.length;
    var cuerpo = '<p class="e44">' + (r.una_cuenta ? 'todos los anuncios de esta cuenta' : n + ' ' + cfg.voc.cuentas.toLowerCase() + ': solo anuncios para pausar, revisar o escalar · elegí una sola en el selector para ver todos sus anuncios') + '</p>';
    if (r.mejor || r.mas_cara) {
      cuerpo += '<div class="bloques">';
      if (r.mejor) cuerpo += '<div class="rend-alerta" style="border-color:var(--verde-borde);background:var(--verde-fondo)"><div class="e3"><strong style="color:var(--verde-texto)">Mejor anuncio · ' + esc(r.mejor.cuenta) + '</strong><span>"' + esc(r.mejor.anuncio) + '" trajo ' + r.mejor.citas + ' citas a ' + plata(r.mejor.costo_cita) + ' cada una.</span></div></div>';
      if (r.mas_cara) cuerpo += '<div class="rend-alerta" data-nivel="cerca"><div class="e3"><strong>Cita más cara · ' + esc(r.mas_cara.cuenta) + '</strong><span>"' + esc(r.mas_cara.anuncio) + '" saca citas a ' + plata(r.mas_cara.costo_cita) + ' (' + r.mas_cara.citas + ' citas con ' + plata(r.mas_cara.gasto) + ').</span></div></div>';
      cuerpo += '</div>';
    }
    cuerpo += '<div class="rend-scroll"><table class="rend-tabla"><thead><tr><th>Anuncio</th><th class="rend-num">Gasto</th><th class="rend-num">Leads</th><th class="rend-num">Citas creadas</th><th class="rend-num">% agenda</th><th class="rend-num">Costo/lead</th><th class="rend-num">Costo/cita</th><th>Qué hacer</th></tr></thead><tbody>' +
      r.anuncios.map(function (a) {
        var v = VER[a.veredicto];
        return '<tr><td><div class="e3"><strong>' + esc(a.anuncio) + '</strong><span class="e12">' + esc(a.cuenta) + ' · ' + esc(a.campana) + ' · ' + (a.plataforma === 'youtube' ? 'YouTube' : 'Meta') + '</span></div></td>' +
          '<td class="rend-num">' + plata(a.gasto) + '</td><td class="rend-num">' + n0(a.leads) + '</td><td class="rend-num"><strong>' + a.citas + '</strong></td><td class="rend-num">' + pctTxt(a.pct_agenda) + '</td>' +
          '<td class="rend-num e30">' + plata(a.costo_lead) + '</td><td class="rend-num"><strong>' + plata(a.costo_cita) + '</strong></td><td><span class="rend-estado" data-estado="' + v[1] + '">' + v[0] + '</span></td></tr>';
      }).join('') + (r.anuncios.length ? '' : '<tr><td colspan="8" class="e11">Ningún anuncio para pausar, revisar o escalar en el período.</td></tr>') + '</tbody></table></div>';
    cuerpo += '<p class="ini-nota">El cruce es por ID del anuncio (o campaña + nombre del anuncio si GHL no lo trae); las copias con el mismo nombre dentro de una campaña se suman. ' + r.sin_anuncio + ' citas del período no traen el anuncio de origen.</p>';
    h += '<section class="caja ini-bloque">' + '<div class="e19"><h2 class="titulo-2">Trazabilidad: qué anuncios traen citas</h2></div>' + cuerpo + '</section>';
    h += avisos(r);
    return h;
  }

  function pedir(menu, negocio) {
    var ambito = menu === 'ag-campanas' ? 'agencia' : (P.ambito || 'clientes');
    var q = '?dias=' + P.dias + '&ambito=' + ambito + (P.cuentas ? '&cuentas=' + P.cuentas.join(',') : '');
    var ruta = menu === 'trazabilidad' ? 'trazabilidad' : 'panel';
    return fetch('/api/' + negocio + '/' + ruta + q, { credentials: 'same-origin' }).then(function (resp) {
      if (resp.status === 401) { location.href = '/ingresar'; throw new Error('sin sesión'); }
      if (!resp.ok) throw new Error('Error ' + resp.status);
      return resp.json();
    });
  }

  function mostrar(menu, negocio) {
    ultimo = { menu: menu, negocio: negocio };
    var principal = document.getElementById('principal');
    pedir(menu, negocio).then(function (r) {
      if (!ultimo || ultimo.menu !== menu || ultimo.negocio !== negocio) return;
      principal.innerHTML = menu === 'trazabilidad' ? vistaTraz(r) : vistaPanel(r);
      window.dcPostRender();
    }).catch(function (e) {
      if (!ultimo || ultimo.menu !== menu) return;
      principal.innerHTML = '<section class="caja ini-bloque"><h3 class="fin-h3">No se pudieron cargar los datos</h3><p class="e52" style="margin:0">' + S().esc(e.message) + '. Si abriste la suite sin el servidor, arrancalo con <code>flask --app servidor run</code>.</p></section>';
    });
  }

  document.addEventListener('click', function (e) {
    var t = e.target.closest ? e.target : null; if (!t || !ultimo) return;
    var b;
    if ((b = t.closest('[data-p-dias]'))) P.dias = +b.getAttribute('data-p-dias');
    else if ((b = t.closest('[data-p-ambito]'))) P.ambito = b.getAttribute('data-p-ambito');
    else if ((b = t.closest('[data-p-filtro]'))) P.filtro = b.getAttribute('data-p-filtro');
    else if (t.closest('[data-p-glosario]')) P.glosario = !P.glosario;
    else return;
    mostrar(ultimo.menu, ultimo.negocio);
  });

  window.MENUS_API = Object.assign(window.MENUS_API || {}, { panel: mostrar, trazabilidad: mostrar, 'ag-campanas': mostrar });
  window.MENUS_API_SALIR = function () { ultimo = null; P.ambito = null; P.cuentas = null; P.filtro = 'todas'; };
})();
