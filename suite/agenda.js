// Agenda (fase 2): Calendario de citas (día / semana / mes), ficha de la cita con el resultado de la llamada y Seguimientos.
// Lee /api/<negocio>/agenda y /seguimientos; guarda en /api/<negocio>/citas/<id>/resultado. Clases de marca.css (cal-*, fc-*, ficha-*).
(function () {
  var A = { vista: 'semana', ref: null, busca: '', ficha: null, datos: null, menu: null, negocio: null, segBusca: '' };
  var DIAS = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'];
  var DIAS_LARGO = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
  var MES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];
  var MES_LARGO = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];
  var HORA_INI = 8, HORA_FIN = 20, ALTO_HORA = 72;
  var EST = { asistio: ['✓', 'asistió', 'Asistió', 'cumple'], no_asistio: ['✕', 'no asistió', 'No asistió', 'falta'], confirmada: ['•', 'sin marcar', 'Pendiente', 'cerca'],
    cancelada: ['', 'cancelada', 'Cancelada', ''], reprogramada: ['↻', 'reprogramada', 'Reprogramada', ''] };

  function S() { return window.SUITE; }
  function esc(s) { return S().esc(s == null ? '' : s); }
  function voc() { return NEGOCIOS[A.negocio].voc; }
  // Fechas como texto ISO (aaaa-mm-dd) para no depender de la zona del navegador
  function f2d(s) { var p = s.split('-'); return new Date(Date.UTC(+p[0], +p[1] - 1, +p[2])); }
  function d2f(d) { return d.toISOString().slice(0, 10); }
  function suma(s, n) { var d = f2d(s); d.setUTCDate(d.getUTCDate() + n); return d2f(d); }
  function dsem(s) { return (f2d(s).getUTCDay() + 6) % 7; } // 0 = lunes
  function corta(s) { var d = f2d(s); return d.getUTCDate() + ' ' + MES[d.getUTCMonth()]; }
  function hora(m) { return String(Math.floor(m / 60)).padStart(2, '0') + ':' + String(m % 60).padStart(2, '0'); }
  function plata(x) { return x == null ? '—' : 'US$' + Math.round(x).toLocaleString('en-US'); }
  function pctTxt(x) { return x == null ? '—' : Math.round(x) + '%'; }

  function rango() {
    var r = A.ref;
    if (A.vista === 'dia') return [r, r];
    if (A.vista === 'semana') { var l = suma(r, -dsem(r)); return [l, suma(l, 6)]; }
    var d = f2d(r), ini = d2f(new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), 1))), fin = d2f(new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth() + 1, 0)));
    return [ini, fin];
  }
  function api(ruta, metodo, cuerpo) {
    var op = { method: metodo || 'GET', credentials: 'same-origin', headers: {} };
    if (cuerpo) { op.headers['Content-Type'] = 'application/json'; op.headers['X-CSRF'] = S().sesion().csrf; op.body = JSON.stringify(cuerpo); }
    return fetch('/api/' + A.negocio + ruta, op).then(function (r) {
      if (r.status === 401) { location.href = '/ingresar'; throw new Error('sin sesión'); }
      if (!r.ok) throw new Error(r.status === 403 ? 'No tenés permiso para ver esto' : 'Error ' + r.status);
      return r.json();
    });
  }

  // ---- Tarjetas (misma tarjeta que el Panel) ----
  function vari(c, menosEsMejor) {
    if (c == null || !isFinite(c)) return null;
    var bueno = menosEsMejor ? c <= 0 : c >= 0;
    return [(c > 0 ? '+' : '−') + Math.abs(c).toFixed(1) + '%', bueno ? 'bien' : 'mal'];
  }
  function contraMeta(valor, meta) {
    if (valor == null || !meta) return null;
    var dif = Math.round(valor - meta);
    return ['Meta ' + Math.round(meta) + '% · ' + (dif >= 0 ? '+' : '−') + Math.abs(dif) + ' pts', valor >= meta ? 'cumple' : valor >= meta * 0.9 ? 'cerca' : 'falta', Math.max(4, Math.min(100, valor / meta * 100))];
  }
  function kpi(o) {
    var h = '<article class="kpi' + (o.clave ? ' kpi--clave' : '') + '"><div class="kpi-cab"><span class="kpi-nombre">' + esc(o.nombre) + '</span>' + (o.vari ? '<span class="pill var ' + o.vari[1] + '">' + o.vari[0] + '</span>' : '<span class="pill var">—</span>') + '</div>';
    h += '<div class="kpi-cuerpo"><div class="kpi-valores"><div class="kpi-valor">' + esc(o.valor) + (o.pct != null ? ' <span class="kpi-pct">' + o.pct + '</span>' : '') + '</div><div class="kpi-sub">' + esc(o.sub || '') + '</div></div>';
    if (o.meta) h += '<span class="kpi-meta" data-estado="' + o.meta[1] + '">' + esc(o.meta[0]) + '</span><span class="juego-barra" data-estado="' + o.meta[1] + '"><span style="width:' + o.meta[2] + '%"></span></span>';
    return h + '</div></article>';
  }

  // ---- Calendario ----
  function porDia(citas) {
    var m = {};
    citas.forEach(function (c) { (m[c.fecha] = m[c.fecha] || []).push(c); });
    Object.keys(m).forEach(function (k) { m[k].sort(function (a, b) { return a.minuto - b.minuto; }); });
    return m;
  }
  function conteo(lista) {
    var a = 0, n = 0; (lista || []).forEach(function (c) { if (c.estado === 'asistio') a++; if (c.estado === 'no_asistio') n++; });
    return (lista ? lista.length : 0) + ' cita' + (lista && lista.length === 1 ? '' : 's') + (a ? ' ✓' + a : '') + (n ? ' ✕' + n : '');
  }
  function bloque(c, estilo) {
    var e = EST[c.estado] || EST.confirmada, val = c.resultado && c.resultado.resultado === 'avanza';
    return '<button type="button" class="cal-cita" data-a-cita="' + esc(c.id) + '" data-estado="' + c.estado + '"' + (val ? ' data-val="1"' : '') + ' style="' + estilo + '">' +
      '<strong>' + (val ? '<i class="cal-estrella">★</i>' : '') + (e[0] ? e[0] + ' ' : '') + hora(c.minuto) + ' · ' + esc(c.nombre) + '</strong><span>' + esc(c.cuenta) + '</span></button>';
  }
  function columnas(dias, mapa, hoy) {
    var cab = '<div class="cal-esquina"></div>' + dias.map(function (d) {
      var x = f2d(d);
      return '<button type="button" class="cal-col-cab" data-a-dia="' + d + '"' + (d === hoy ? ' data-hoy="si"' : '') + '><span class="e12" style="text-transform:uppercase">' + DIAS[dsem(d)] + '</span><strong class="cal-col-num">' + x.getUTCDate() + '</strong><span class="e12">' + conteo(mapa[d]) + '</span></button>';
    }).join('');
    var horas = '<div class="cal-horas">';
    for (var h = HORA_INI; h < HORA_FIN; h++) horas += '<span style="height:' + ALTO_HORA + 'px">' + String(h).padStart(2, '0') + ':00</span>';
    horas += '</div>';
    var ahora = new Date(), minAhora = ahora.getHours() * 60 + ahora.getMinutes();
    var cols = dias.map(function (d) {
      var lista = (mapa[d] || []).filter(function (c) { return c.minuto >= HORA_INI * 60 && c.minuto < HORA_FIN * 60; });
      // las que se pisan (mismo bloque de 30 min) se reparten el ancho
      var grupos = {}; lista.forEach(function (c) { var k = Math.floor(c.minuto / 30); (grupos[k] = grupos[k] || []).push(c); });
      var h = '<div class="cal-col"' + (d === hoy ? ' data-hoy="si"' : '') + ' style="height:' + (HORA_FIN - HORA_INI) * ALTO_HORA + 'px;background-size:100% ' + ALTO_HORA + 'px">';
      Object.keys(grupos).forEach(function (k) {
        var g = grupos[k], w = 100 / g.length;
        g.forEach(function (c, i) {
          var top = (c.minuto - HORA_INI * 60) / 60 * ALTO_HORA;
          h += bloque(c, 'position:absolute;top:' + (top + 1) + 'px;height:' + (ALTO_HORA / 2 - 2) + 'px;left:calc(' + (w * i) + '% + 3px);width:calc(' + w + '% - 6px)');
        });
      });
      if (d === hoy && minAhora >= HORA_INI * 60 && minAhora < HORA_FIN * 60) h += '<span class="cal-ahora" style="top:' + ((minAhora - HORA_INI * 60) / 60 * ALTO_HORA) + 'px"></span>';
      return h + '</div>';
    }).join('');
    var estilo = dias.length === 1 ? ' style="grid-template-columns:56px minmax(0,1fr);min-width:0"' : '';
    return '<div class="cal-semana-scroll"><div class="cal-semana"' + estilo + '>' + cab + horas + cols + '</div></div>';
  }
  function movil(dias, mapa, hoy) {
    var tira = A.vista === 'mes' ? '' : '<div class="cal-tira">' + (A.vista === 'dia' ? semanaDe(A.ref) : dias).map(function (d) {
      var n = (mapa[d] || []).length;
      return '<button type="button" class="cal-tira-dia" data-a-dia="' + d + '"' + (d === hoy ? ' data-hoy="si"' : '') + (A.vista === 'dia' && d === A.ref ? ' aria-current="date"' : '') + '><span>' + DIAS[dsem(d)] + '</span><strong>' + f2d(d).getUTCDate() + '</strong><i>' + (n || '') + '</i></button>';
    }).join('') + '</div>';
    var lista = dias.map(function (d) {
      var x = f2d(d), citas = mapa[d] || [];
      return '<div class="cal-m-dia"' + (d === hoy ? ' data-hoy="si"' : '') + ' id="m-' + d + '"><div class="cal-m-cab"><span>' + DIAS_LARGO[dsem(d)] + ' ' + x.getUTCDate() + ' ' + MES[x.getUTCMonth()] + (d === hoy ? ' · hoy' : '') + '</span><span class="cal-m-cuenta">' + (citas.length ? conteo(citas) : '') + '</span></div>' +
        (citas.length ? citas.map(function (c) {
          var e = EST[c.estado] || EST.confirmada, val = c.resultado && c.resultado.resultado === 'avanza';
          return '<button type="button" class="cal-m-cita' + (c.estado === 'cancelada' ? ' cal-m-cita--canc' : '') + (val ? ' cal-m-cita--val' : '') + '" data-a-cita="' + esc(c.id) + '" style="--tipo:var(--menta)"><span class="cal-m-hora">' + hora(c.minuto) + '</span>' +
            '<span class="cal-m-txt"><strong>' + (val ? '<i class="cal-estrella">★</i>' : '') + esc(c.nombre) + '</strong><span>' + esc(c.cuenta) + ' · ' + esc(A.datos.embudo) + '</span></span><span class="cal-m-est rend-estado" data-estado="' + e[3] + '">' + e[2] + '</span></button>';
        }).join('') : '<p class="cal-m-vacio">Sin citas</p>') + '</div>';
    }).join('');
    return '<div class="cal-movil">' + tira + lista + '</div>';
  }
  function semanaDe(d) { var l = suma(d, -dsem(d)), o = []; for (var i = 0; i < 7; i++) o.push(suma(l, i)); return o; }
  function mes(mapa, hoy) {
    var r = rango(), ini = suma(r[0], -dsem(r[0])), fin = suma(r[1], 6 - dsem(r[1])), h = '<div class="cal-mes">' + DIAS.map(function (d) { return '<span>' + d + '</span>'; }).join('');
    for (var d = ini; d <= fin; d = suma(d, 1)) {
      var citas = mapa[d] || [], fuera = d < r[0] || d > r[1];
      h += '<div class="cal-mes-celda"' + (fuera ? ' data-fuera="1"' : '') + (d === hoy ? ' data-hoy="si"' : '') + '><button type="button" class="cal-dia-num" data-a-dia="' + d + '"><span>' + f2d(d).getUTCDate() + '</span><span class="e12">' + (citas.length || '') + '</span></button>';
      if (!fuera) {
        citas.slice(0, 3).forEach(function (c) { h += bloque(c, 'position:relative;width:100%'); });
        if (citas.length > 3) h += '<button type="button" class="cal-mas" data-a-dia="' + d + '">+' + (citas.length - 3) + ' más</button>';
      }
      h += '</div>';
    }
    return h + '</div>' + movilMes();
  }
  function movilMes() { return ''; }

  function titulo() {
    var r = rango(), a = f2d(r[0]);
    if (A.vista === 'dia') return DIAS_LARGO[dsem(r[0])] + ' ' + a.getUTCDate() + ' de ' + MES_LARGO[a.getUTCMonth()];
    if (A.vista === 'semana') return 'Semana del ' + corta(r[0]) + ' al ' + corta(r[1]);
    return MES_LARGO[a.getUTCMonth()] + ' ' + a.getUTCFullYear();
  }
  function buscador() {
    var q = A.busca.trim().toLowerCase(), res = '';
    if (q) {
      var hall = A.datos.citas.filter(function (c) { return c.nombre.toLowerCase().indexOf(q) >= 0; }).slice(0, 12);
      res = '<div class="cal-busca-res">' + (hall.length ? hall.map(function (c) {
        return '<button type="button" class="cal-busca-item" data-a-cita="' + esc(c.id) + '"><span class="cal-busca-punto" style="background:var(--menta)"></span><span class="e3 e47"><strong>' + esc(c.nombre) + '</strong><span class="cal-busca-sub">' + corta(c.fecha) + ' · ' + hora(c.minuto) + ' · ' + esc(c.cuenta) + '</span></span><span class="cal-busca-est">' + (EST[c.estado] || EST.confirmada)[2] + '</span></button>';
      }).join('') : '<p class="cal-busca-nada">Nadie con ese nombre en este período.</p>') + '</div>';
    }
    return '<div class="cal-busca" data-pop="busca"><svg class="cal-busca-ico" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/></svg>' +
      '<input class="cal-busca-campo" type="search" id="a-busca" placeholder="Buscar ' + esc(voc().contacto.toLowerCase()) + '" value="' + esc(A.busca) + '" autocomplete="off">' + res + '</div>';
  }

  function vistaCalendario() {
    var r = A.datos, k = r.kpi, v = voc(), cfg = NEGOCIOS[A.negocio], hoy = r.hoy, s = r.secundarias;
    var h = '<header><div class="e19"><h1 class="titulo-1">Calendario de citas</h1><span class="e30">' + corta(r.desde) + (r.hasta !== r.desde ? ' – ' + corta(r.hasta) : '') + ' · GHL · por fecha de la cita · hoy ' + corta(hoy) + '</span></div>' +
      '<div class="cab-filtros e36"><button class="btn-sec" type="button" disabled title="Selector de ' + esc(v.cuentas.toLowerCase()) + ': próxima entrega">' + esc(v.cuentas) + ': Todas (' + r.cuentas_disponibles.length + ')</button></div></header>';
    var cards = [
      kpi({ nombre: 'Citas agendadas', clave: true, valor: String(k.agendadas.valor), sub: 'vs ' + k.agendadas.anterior + ' mismo tramo ant.', vari: vari(k.agendadas.cambio) }),
      kpi({ nombre: 'Citas asistidas', clave: true, valor: String(k.asistio.valor), sub: 'vs ' + k.asistio.anterior + ' mismo tramo ant.', vari: vari(k.asistio.cambio) }),
      kpi({ nombre: '% asistencia', clave: true, valor: pctTxt(k.pct_asistencia.valor), sub: 'vs ' + pctTxt(k.pct_asistencia.anterior) + ' mismo tramo ant.', vari: vari(k.pct_asistencia.cambio), meta: contraMeta(k.pct_asistencia.valor, r.metas.pct_asistencia) }),
      kpi({ nombre: 'Calificadas', valor: String(k.califica.valor), pct: k.asistio.valor ? Math.round(k.califica.valor / k.asistio.valor * 100) + '%' : null, sub: 'vs ' + k.califica.anterior + ' mismo tramo ant.', vari: vari(k.califica.cambio) }),
      kpi({ nombre: v.citasPrincipales + ' agendadas', valor: String(k.avanza.valor), pct: k.agendadas.valor ? Math.round(k.avanza.valor / k.agendadas.valor * 100) + '%' : null, sub: 'vs ' + k.avanza.anterior + ' mismo tramo ant.', vari: vari(k.avanza.cambio) }),
      kpi({ nombre: 'Tasa de cierre efectiva', clave: true, valor: pctTxt(k.pct_cierre.valor), sub: 'vs ' + pctTxt(k.pct_cierre.anterior) + ' mismo tramo ant.', vari: vari(k.pct_cierre.cambio), meta: contraMeta(k.pct_cierre.valor, r.metas.pct_cierre) })
    ];
    h += '<section class="e22"><div class="e136"><div class="e19"><h2 class="titulo-2">Indicadores de la agenda</h2></div></div><div class="grilla" style="--n:6">' + cards.join('') + '</div></section>';
    var pas = s.pasadas;
    h += S().secundarias('agenda', [
      S().secItem('No asistieron', String(s.no_asistio), 'de las pasadas', pas ? Math.round(s.no_asistio / pas * 100) : null),
      S().secItem('Reprogramadas', String(s.reprogramadas), '% reprogramación', s.agendadas ? Math.round(s.reprogramadas / s.agendadas * 100) : null),
      S().secItem('Canceladas', String(s.canceladas), '% cancelación', pas ? Math.round(s.canceladas / pas * 100) : null),
      S().secItem('Citas pasadas', String(pas), 'hasta ahora, marcadas o no'),
      S().secItem('Citas pendientes', String(s.pendientes_7), s.pendientes_hoy + ' hoy · ' + s.pendientes_7 + ' en 7 días'),
      S().secItem('Sin marcar', String(s.sin_marcar), 'ya pasaron y siguen sin estado'),
      S().secItem('Seguimientos activos', String(s.seguimientos), s.vencidos + ' vencidos')
    ], ['Ver seguimientos', 'seguimientos']);
    var mapa = porDia(r.citas), dias = [];
    for (var d = r.desde; d <= r.hasta; d = suma(d, 1)) dias.push(d);
    var seg = '<div class="seg" role="group" aria-label="Vista">' + [['dia', 'Día'], ['semana', 'Semana'], ['mes', 'Mes']].map(function (x) { return '<button type="button" data-a-vista="' + x[0] + '" aria-pressed="' + (A.vista === x[0]) + '">' + x[1] + '</button>'; }).join('') + '</div>';
    var cal = '<div class="cal-barra"><div class="cal-nav"><div class="cal-nav-fila"><div class="cal-paso"><button type="button" class="e112" data-a-paso="-1" aria-label="Anterior">‹</button><button type="button" class="e113" data-a-paso="0">Hoy</button><button type="button" class="e112" data-a-paso="1" aria-label="Siguiente">›</button></div>' + seg + '</div>' +
      '<h2 class="titulo-cal">' + esc(titulo()) + '</h2></div>' +
      '<div class="cal-acciones">' + buscador() + '<div class="cal-leyenda"><span><span class="punto" style="background:var(--menta);border-radius:3px"></span>' + esc(r.embudo) + '</span><span style="color:var(--verde-texto)">✓ asistió</span><span style="color:var(--rojo-texto)">✕ no asistió</span><span style="color:var(--ambar-texto)">• sin marcar</span><span style="text-decoration:line-through;color:var(--texto-4)">cancelada</span><span class="cal-ley-val">★ pasó a ' + esc(v.citaPrincipal.toLowerCase()) + '</span></div></div></div>';
    cal += A.vista === 'mes' ? mes(mapa, hoy) : columnas(dias, mapa, hoy) + movil(dias, mapa, hoy);
    cal += '<p class="ini-nota cal-ayuda">Hora de cada ' + esc(v.cuenta.toLowerCase()) + '. Tocá una cita para abrir la ficha del ' + esc(v.contacto.toLowerCase()) + ' y el día para ver el detalle. Las canceladas no suman.</p>';
    h += '<section class="caja" id="a-cal">' + cal + '</section>';
    if (r.demo) h += '<p class="ini-nota">Datos de ejemplo: nombres inventados. Cuando el worker tenga acceso a GHL, acá aparecen las citas reales.</p>';
    return h;
  }

  // ---- Ficha de la cita ----
  function resLabel(k) {
    var v = voc();
    return { avanza: v.citaPrincipal + ' agendada', pendiente: 'Pendiente de ' + v.compromiso.toLowerCase(), seguimiento: 'En seguimiento', no_interesado: 'No interesado', perdido: 'Perdido', no_califica: 'No califica' }[k];
  }
  function chips(nombre, opciones, actual) {
    return '<div class="e53" role="group" aria-label="' + esc(nombre) + '">' + opciones.map(function (o) {
      return '<button type="button" class="e94" data-a-campo="' + o[0] + '" data-a-valor="' + o[1] + '" aria-pressed="' + (String(actual) === String(o[1])) + '">' + esc(o[2]) + '</button>';
    }).join('') + '</div>';
  }
  function ficha() {
    var c = A.ficha; if (!c) return '';
    var v = voc(), r = c.resultado || {}, F = A.form, e = EST[c.estado] || EST.confirmada, puede = A.datos ? A.datos.puede_editar : true;
    var x = f2d(c.fecha);
    var h = '<div class="cal-velo" data-a-cerrar></div><aside class="fc-capa ficha-cita" role="dialog" aria-modal="true" aria-label="Ficha de ' + esc(c.nombre) + '">';
    h += '<div class="fc-cabeza"><div class="e19" style="flex:1;min-width:0;gap:10px"><span class="ficha-clinica">' + esc(c.cuenta) + '</span><h2 class="fc-titulo">' + esc(c.nombre) + '</h2><span class="e30">' + esc(A.datos ? A.datos.embudo : '') + ' · ' + DIAS_LARGO[dsem(c.fecha)] + ' ' + x.getUTCDate() + ' ' + MES[x.getUTCMonth()] + ' · ' + hora(c.minuto) + ' · <span class="rend-estado" data-estado="' + e[3] + '">' + e[2] + '</span></span></div>' +
      '<button type="button" class="fc-volver" data-a-cerrar aria-label="Cerrar">✕</button></div>';
    h += '<section class="fc-seccion"><h3 class="fin-h3">Datos del ' + esc(v.contacto.toLowerCase()) + '</h3><div class="e53">' +
      (c.telefono ? '<a class="e113" href="tel:' + esc(c.telefono.replace(/[^\d+]/g, '')) + '" style="text-decoration:none">' + esc(c.telefono) + '</a>' : '') +
      '<button type="button" class="e113" disabled title="Necesita el token de GHL de la subcuenta">Abrir chat</button></div>' +
      '<dl class="ficha-datos">' +
      (c.email ? '<div><dt>Email</dt><dd>' + esc(c.email) + '</dd></div>' : '') +
      '<div><dt>Anuncio de origen</dt><dd>' + esc(c.anuncio || 'Sin anuncio de origen en GHL') + '</dd></div>' +
      '<div><dt>Alta de la cita</dt><dd>' + corta(c.creada) + '</dd></div>' +
      '<div><dt>Estado en GHL</dt><dd>' + (EST[c.estado_crm] || EST.confirmada)[2] + (c.estado !== c.estado_crm ? ' · marcado acá como ' + e[2].toLowerCase() : '') + '</dd></div>' +
      (r.quien ? '<div><dt>Último resultado</dt><dd>' + esc(r.quien) + '</dd></div>' : '') + '</dl></section>';
    if (!puede) {
      h += '<section class="fc-seccion"><h3 class="fin-h3">Resultado de la llamada</h3><dl class="ficha-datos"><div><dt>Resultado</dt><dd>' + esc(r.resultado ? resLabel(r.resultado) : 'Sin cargar') + '</dd></div>' + (r.notas ? '<div><dt>Notas</dt><dd>' + esc(r.notas) + '</dd></div>' : '') + '</dl></section>';
      return h + '</aside>';
    }
    h += '<form class="e22" id="a-form"><h3 class="fin-h3">Resultado de la llamada</h3>' +
      '<div class="e115"><span class="ct-etq">Asistencia</span>' + chips('Asistencia', [['asistencia', 'asistio', 'Asistió'], ['asistencia', 'no_asistio', 'No asistió'], ['asistencia', 'cancelada', 'Canceló']], F.asistencia) + '</div>' +
      '<div class="e115"><span class="ct-etq">¿Califica?</span>' + chips('Califica', [['califica', 'true', 'Sí'], ['califica', 'false', 'No']], F.califica) + '</div>' +
      '<div class="e115"><span class="ct-etq">Resultado</span>' + chips('Resultado', ['avanza', 'pendiente', 'seguimiento', 'no_interesado', 'perdido', 'no_califica'].map(function (k) { return ['resultado', k, resLabel(k)]; }), F.resultado) + '</div>' +
      '<div class="fc-rapidos"><label class="ct-dato">' + esc(v.servicio) + ' cotizado<input class="ct-input" name="servicio" value="' + esc(F.servicio || '') + '" maxlength="200"></label>' +
      '<label class="ct-dato">Monto cotizado (USD)<input class="ct-input" name="monto" inputmode="decimal" value="' + esc(F.monto == null ? '' : F.monto) + '" placeholder="0"></label></div>' +
      '<label class="ct-dato">Próximo seguimiento<input class="ct-input ct-input--fecha" type="date" name="proximo" value="' + esc(F.proximo || '') + '"></label>' +
      '<label class="ct-dato">Notas<textarea class="ct-input ct-input--largo" name="notas" rows="4" maxlength="4000">' + esc(F.notas || '') + '</textarea></label>' +
      '<button type="submit" class="fin-boton" style="width:100%">Guardar</button>' +
      '<p class="e12" id="a-form-msg" style="margin:0">Se guarda en la plataforma. Cuando esté el token de escritura de GHL, también va a actualizar la cita y las notas allá.</p></form>';
    return h + '</aside>';
  }
  function abrirFicha(c) {
    var r = c.resultado || {};
    A.ficha = c;
    A.form = { asistencia: r.asistencia || '', califica: r.califica == null ? '' : String(r.califica), resultado: r.resultado || '', servicio: r.servicio || '', monto: r.monto, proximo: r.proximo || '', notas: r.notas || '' };
    pintarFicha();
    SONIDO.sonar('menu');
  }
  function pintarFicha() {
    var cont = document.getElementById('a-ficha');
    if (!cont) { cont = document.createElement('div'); cont.id = 'a-ficha'; document.body.appendChild(cont); }
    cont.innerHTML = ficha();
    document.documentElement.classList.toggle('ficha-abierta', !!A.ficha);
  }
  function cerrarFicha() { A.ficha = null; pintarFicha(); }
  function leerForm() {
    var f = document.getElementById('a-form'); if (!f) return;
    A.form.servicio = f.servicio.value; A.form.monto = f.monto.value; A.form.proximo = f.proximo.value; A.form.notas = f.notas.value;
  }

  // ---- Seguimientos ----
  var COLS = [['vencidos', 'Vencidos', 'var(--rojo)'], ['hoy', 'Hoy', 'var(--menta)'], ['manana', 'Mañana', 'var(--texto-2)'], ['semana', 'Esta semana', 'var(--texto-2)'], ['despues', 'Más adelante', 'var(--texto-2)'], ['sin_fecha', 'Sin fecha', 'var(--ambar)']];
  function vistaSeg(r) {
    var v = voc(), cfg = NEGOCIOS[A.negocio], q = A.segBusca.trim().toLowerCase();
    var alDia = r.activos ? Math.round((r.activos - r.vencidos) / r.activos * 100) : null;
    var h = '<header><div class="e19"><h1 class="titulo-1">Seguimientos</h1><span class="e30">' + esc(v.contactos) + ' en seguimiento o pendientes de ' + esc(v.compromiso.toLowerCase()) + ', por fecha del próximo contacto</span></div></header>';
    h += '<div class="grilla" style="--n:3">' +
      kpi({ nombre: 'Seguimientos activos', valor: String(r.activos), sub: r.pendientes + ' pendientes de ' + v.compromiso.toLowerCase(), meta: alDia == null ? null : [alDia + '% al día · ' + r.vencidos + ' vencidos', alDia === 100 ? 'cumple' : alDia >= 80 ? 'cerca' : 'falta', Math.max(4, alDia)] }).replace('<span class="pill var">—</span>', '') +
      kpi({ nombre: 'Vencidos', valor: String(r.vencidos), sub: r.para_hoy + ' para hoy · hay que contactarlos' }).replace('<span class="pill var">—</span>', '').replace('class="kpi-valor"', 'class="kpi-valor"' + (r.vencidos ? ' style="color:var(--rojo-texto)"' : '')) +
      kpi({ nombre: 'Monto cotizado', valor: plata(r.monto), sub: 'USD en seguimiento' }).replace('<span class="pill var">—</span>', '') + '</div>';
    h += '<div class="cal-busca seg-busca"><svg class="cal-busca-ico" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/></svg><input class="cal-busca-campo" type="search" id="a-seg-busca" placeholder="Buscar ' + esc(v.contacto.toLowerCase()) + '" value="' + esc(A.segBusca) + '" autocomplete="off"></div>';
    h += '<div class="seg-cols">' + COLS.map(function (col) {
      var lista = r.columnas[col[0]].filter(function (c) { return !q || c.nombre.toLowerCase().indexOf(q) >= 0; });
      return '<section class="caja seg-col"><div class="seg-col-cab" style="--color:' + col[2] + '"><h3 class="fin-h3" style="color:' + (col[0] === 'vencidos' ? 'var(--rojo-texto)' : col[0] === 'sin_fecha' ? 'var(--ambar-texto)' : 'var(--texto)') + '">' + col[1] + '</h3><strong class="e125">' + lista.length + '</strong></div>' +
        (lista.length ? lista.map(function (c) { return tarjetaSeg(c, r.hoy, col[0]); }).join('') : '<p class="vacio">Nada por acá</p>') + '</section>';
    }).join('') + '</div>';
    if (r.demo && !r.activos) h += '<p class="ini-nota">Con datos de ejemplo la lista arranca vacía: aparece gente cuando en la ficha de una cita marcás «En seguimiento» o «Pendiente de ' + esc(v.compromiso.toLowerCase()) + '».</p>';
    return h;
  }
  function tarjetaSeg(c, hoy, col) {
    var r = c.resultado, dias = r.proximo ? Math.round((f2d(r.proximo) - f2d(hoy)) / 864e5) : null;
    var cuando = r.proximo == null ? 'Sin fecha de próximo contacto' : dias < 0 ? 'Venció hace ' + (-dias) + ' día' + (dias === -1 ? '' : 's') + ' · ' + corta(r.proximo) : dias === 0 ? 'Hoy · ' + corta(r.proximo) : 'En ' + dias + ' día' + (dias === 1 ? '' : 's') + ' · ' + corta(r.proximo);
    return '<article class="seg-card"><div class="e3"><strong class="e122">' + esc(c.nombre) + '</strong><span class="e12">' + esc(c.cuenta) + '</span></div>' +
      '<span class="rend-estado" data-estado="' + (r.resultado === 'pendiente' ? 'cerca' : '') + '" style="align-self:flex-start">' + esc(resLabel(r.resultado)) + '</span>' +
      ((r.servicio || r.monto) ? '<span class="e52">' + esc([r.servicio, r.monto ? plata(r.monto) : ''].filter(Boolean).join(' · ')) + '</span>' : '') +
      (r.notas ? '<p class="seg-nota">' + esc(r.notas) + '</p>' : '') +
      '<span class="e12" style="color:' + (dias != null && dias < 0 ? 'var(--rojo-texto)' : 'var(--texto-3)') + ';font-weight:600">' + cuando + '</span>' +
      '<div class="e53"><button type="button" class="fin-boton seg-abrir" data-a-seg-abrir="' + esc(c.id) + '">Abrir ficha</button>' +
      [[1, 'Mañana'], [3, '+3 días'], [7, '+1 sem.']].map(function (p) { return '<button type="button" class="e94" data-a-posponer="' + esc(c.id) + '" data-a-dias="' + p[0] + '">' + p[1] + '</button>'; }).join('') + '</div></article>';
  }

  // ---- Pintar y eventos ----
  function principal(html) { document.getElementById('principal').innerHTML = html; window.dcPostRender(); }
  function cargar() {
    var menu = A.menu, negocio = A.negocio;
    if (menu === 'seguimientos') {
      return api('/seguimientos').then(function (r) { if (A.menu !== menu || A.negocio !== negocio) return; A.seg = r; principal(vistaSeg(r)); }).catch(error);
    }
    var q = A.ref ? '?desde=' + rango()[0] + '&hasta=' + rango()[1] : '';
    return api('/agenda' + q).then(function (r) {
      if (A.menu !== menu || A.negocio !== negocio) return;
      A.datos = r; if (!A.ref) A.ref = r.hoy;
      var foco = document.activeElement && document.activeElement.id === 'a-busca';
      principal(vistaCalendario());
      if (foco) { var b = document.getElementById('a-busca'); b.focus(); b.setSelectionRange(b.value.length, b.value.length); }
    }).catch(error);
  }
  function error(e) {
    if (!A.menu) return;
    principal('<header><div class="e19"><h1 class="titulo-1">' + (A.menu === 'seguimientos' ? 'Seguimientos' : 'Calendario de citas') + '</h1></div></header><section class="caja ini-bloque"><h3 class="fin-h3">No se pudo cargar la agenda</h3><p class="e52" style="margin:0">' + esc(e.message) + '.</p></section>');
  }
  function mostrar(menu, negocio) {
    if (A.negocio !== negocio) { A.ref = null; A.busca = ''; A.segBusca = ''; }
    A.menu = menu; A.negocio = negocio;
    cargar();
  }
  function buscarCita(id) {
    var listas = [];
    if (A.datos) listas = listas.concat(A.datos.citas);
    if (A.seg) Object.keys(A.seg.columnas).forEach(function (k) { listas = listas.concat(A.seg.columnas[k]); });
    return listas.filter(function (c) { return c.id === id; })[0];
  }
  function guardar(cuerpo, id) {
    return api('/citas/' + encodeURIComponent(id) + '/resultado', 'POST', cuerpo).then(function (c) {
      SONIDO.sonar('listo');
      return cargar().then(function () { return c; });
    });
  }

  document.addEventListener('click', function (e) {
    var t = e.target.closest ? e.target : null; if (!t || !A.menu) return;
    var b;
    if ((b = t.closest('[data-a-cerrar]'))) { cerrarFicha(); return; }
    if ((b = t.closest('[data-a-campo]'))) {
      leerForm();
      var campo = b.getAttribute('data-a-campo'), val = b.getAttribute('data-a-valor');
      A.form[campo] = A.form[campo] === val ? '' : val; // tocar de nuevo desmarca
      if (campo === 'asistencia' && val !== 'asistio' && A.form[campo]) { /* sin asistencia no hay calificación */ }
      SONIDO.sonar('menu'); pintarFicha(); return;
    }
    if ((b = t.closest('[data-a-cita]'))) { var c = buscarCita(b.getAttribute('data-a-cita')); if (c) { A.busca = ''; abrirFicha(c); } return; }
    if ((b = t.closest('[data-a-seg-abrir]'))) { var c2 = buscarCita(b.getAttribute('data-a-seg-abrir')); if (c2) abrirFicha(c2); return; }
    if ((b = t.closest('[data-a-posponer]'))) {
      var id = b.getAttribute('data-a-posponer'), n = +b.getAttribute('data-a-dias');
      b.disabled = true;
      guardar({ proximo: suma(A.seg.hoy, n) }, id).catch(function () { b.disabled = false; });
      return;
    }
    if (!A.datos || A.menu !== 'calendario') return;
    if ((b = t.closest('[data-a-vista]'))) { A.vista = b.getAttribute('data-a-vista'); SONIDO.sonar('menu'); cargar(); return; }
    if ((b = t.closest('[data-a-paso]'))) {
      var p = +b.getAttribute('data-a-paso');
      if (p === 0) A.ref = A.datos.hoy;
      else if (A.vista === 'dia') A.ref = suma(A.ref, p);
      else if (A.vista === 'semana') A.ref = suma(A.ref, 7 * p);
      else { var d = f2d(A.ref); A.ref = d2f(new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth() + p, 1))); }
      cargar(); return;
    }
    if ((b = t.closest('[data-a-dia]'))) { A.ref = b.getAttribute('data-a-dia'); A.vista = 'dia'; SONIDO.sonar('menu'); cargar(); return; }
  });
  document.addEventListener('input', function (e) {
    if (e.target.id === 'a-busca') {
      A.busca = e.target.value;
      var caja = e.target.closest('.cal-busca'), viejo = caja.querySelector('.cal-busca-res'), tmp = document.createElement('div');
      tmp.innerHTML = buscador();
      var nuevo = tmp.querySelector('.cal-busca-res');
      if (viejo) viejo.remove();
      if (nuevo) caja.appendChild(nuevo);
    }
    if (e.target.id === 'a-seg-busca') { A.segBusca = e.target.value; principal(vistaSeg(A.seg)); var s = document.getElementById('a-seg-busca'); s.focus(); s.setSelectionRange(s.value.length, s.value.length); }
  });
  document.addEventListener('submit', function (e) {
    if (e.target.id !== 'a-form') return;
    e.preventDefault(); leerForm();
    var F = A.form, monto = String(F.monto == null ? '' : F.monto).trim().replace(',', '.');
    if (monto && !(Number(monto) >= 0)) { document.getElementById('a-form-msg').textContent = 'El monto tiene que ser un número.'; return; }
    var cuerpo = { asistencia: F.asistencia || null, califica: F.califica === '' ? null : F.califica === 'true', resultado: F.resultado || null,
      servicio: F.servicio, monto: monto === '' ? null : Number(monto), proximo: F.proximo || null, notas: F.notas };
    var btn = e.target.querySelector('button[type="submit"]'); btn.disabled = true; btn.textContent = 'Guardando…';
    guardar(cuerpo, A.ficha.id).then(function (c) { abrirFicha(c); var m = document.getElementById('a-form-msg'); if (m) m.textContent = 'Guardado.'; })
      .catch(function (err) { btn.disabled = false; btn.textContent = 'Guardar'; document.getElementById('a-form-msg').textContent = 'No se pudo guardar (' + err.message + ').'; });
  });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && A.ficha) cerrarFicha(); });

  window.MENUS_API = window.MENUS_API || {};
  window.MENUS_API.calendario = mostrar;
  window.MENUS_API.seguimientos = mostrar;
  var salir = window.MENUS_API_SALIR;
  window.MENUS_API_SALIR = function () { A.menu = null; A.datos = null; A.seg = null; if (A.ficha) cerrarFicha(); if (salir) salir(); };
})();
