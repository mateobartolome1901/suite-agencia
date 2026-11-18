// Dinero: Finanzas (#finanzas), Cobros / Suscripciones (#cobros) y Ventas de la agencia (#ag-ventas). Todo en USD;
// lo que viene en otra moneda (pesos colombianos) se muestra en su moneda con el equivalente en dólares al lado.
(function () {
  var D = { menu: null, negocio: null, mes: null, datos: null, filtro: null };
  var MES_LARGO = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];
  var MES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];
  var CONCEPTO = { setup: 'Setup', fee: 'Fee mensual', comision: 'Comisión', otro: 'Otro' };
  var EST = { pagado: ['Pagado', 'cumple'], pendiente: ['Pendiente', 'cerca'], vencido: ['Vencido', 'falta'] };

  function S() { return window.SUITE; }
  function esc(s) { return S().esc(s == null ? '' : s); }
  function us(x) { return x == null ? '—' : S().us(x); }
  function cfg() { return NEGOCIOS[D.negocio]; }
  function corta(s) { if (!s) return '—'; var p = s.split('-'); return +p[2] + ' ' + MES[+p[1] - 1]; }
  function rangoMes(m) { var p = m.split('-'), ult = new Date(Date.UTC(+p[0], +p[1], 0)).getUTCDate(); return [m + '-01', m + '-' + String(ult).padStart(2, '0')]; }
  function moverMes(m, n) { var p = m.split('-'), d = new Date(Date.UTC(+p[0], +p[1] - 1 + n, 1)); return d.toISOString().slice(0, 7); }
  function hoyIso() { return new Date().toISOString().slice(0, 10); }
  function api(ruta, metodo, cuerpo) {
    var op = { method: metodo || 'GET', credentials: 'same-origin', headers: {} };
    if (cuerpo) { op.headers['Content-Type'] = 'application/json'; op.headers['X-CSRF'] = S().sesion().csrf; op.body = JSON.stringify(cuerpo); }
    return fetch('/api/' + D.negocio + ruta, op).then(function (r) {
      if (r.status === 401) { location.href = '/ingresar'; throw new Error('sin sesión'); }
      if (!r.ok) throw new Error(r.status === 400 ? 'Revisá los datos' : r.status === 403 ? 'Solo el administrador' : 'Error ' + r.status);
      return r.json();
    });
  }
  function principal(h) { document.getElementById('principal').innerHTML = h; window.dcPostRender(); }
  function capa(h) {
    var c = document.getElementById('d-capa');
    if (!c) { c = document.createElement('div'); c.id = 'd-capa'; document.body.appendChild(c); }
    c.innerHTML = h ? '<div class="cal-velo" data-d-cerrar></div><aside class="fc-capa ficha-cita" role="dialog" aria-modal="true"><div class="fc-cabeza"><div class="e19" style="flex:1"><h2 class="fc-titulo">' + h[0] + '</h2></div><button type="button" class="fc-volver" data-d-cerrar aria-label="Cerrar">✕</button></div>' + h[1] + '</aside>' : '';
  }
  function navMes(titulo, extra) {
    var p = D.mes.split('-');
    return '<div class="cal-barra"><h2 class="titulo-cal">' + esc(titulo || (MES_LARGO[+p[1] - 1] + ' ' + p[0])) + '</h2><div class="cal-paso"><button type="button" class="e112" data-d-mes="-1" aria-label="Mes anterior">‹</button><button type="button" class="e113" data-d-mes="0">Este mes</button><button type="button" class="e112" data-d-mes="1" aria-label="Mes siguiente">›</button>' + (extra || '') + '</div></div>';
  }
  function cabecera(titulo, sub) { return '<header><div class="e19"><h1 class="titulo-1">' + esc(titulo) + '</h1><span class="e30">' + sub + '</span></div></header>'; }
  function tabla(cab, filas, vacio) {
    return '<div class="rend-scroll"><table class="rend-tabla"><thead><tr>' + cab.map(function (c) { return '<th' + (c[1] ? ' class="rend-num"' : '') + '>' + esc(c[0]) + '</th>'; }).join('') + '</tr></thead><tbody>' +
      (filas.length ? filas.join('') : '<tr><td colspan="' + cab.length + '" class="e11">' + esc(vacio) + '</td></tr>') + '</tbody></table></div>';
  }
  function barras(obj, total, color) {
    var ks = Object.keys(obj).sort(function (a, b) { return obj[b] - obj[a]; });
    if (!ks.length) return '<p class="vacio">Nada en el período.</p>';
    var max = obj[ks[0]] || 1;
    return '<div class="e33">' + ks.map(function (k) {
      return '<div class="fin-cat"><span class="fin-cat-n">' + esc(k) + '</span><span class="rend-barra"><span style="width:' + Math.max(3, obj[k] / max * 100) + '%;background:' + color + ';box-shadow:none"></span></span><span class="fin-cat-v">' + us(obj[k]) + ' <small>' + (total ? Math.round(obj[k] / total * 100) : 0) + '%</small></span></div>';
    }).join('') + '</div>';
  }

  // ---- Finanzas ----
  function vistaFinanzas(r) {
    var c = cfg(), t = S().tarjeta, s = r.socios;
    var h = cabecera('Finanzas', 'Ingresos, gastos y lo que falta cobrar · USD' + (r.tasas && r.tasas.COP && c.id === 'plastia' ? ' · 1 USD = ' + Math.round(r.tasas.COP).toLocaleString('es-CO') + ' COP' : ''));
    h += navMes(null, '<button type="button" class="fin-boton" data-d-mov="ingreso">+ Ingreso</button><button type="button" class="fin-boton" data-d-mov="gasto">+ Gasto</button>' + (s ? '<button type="button" class="fin-boton" data-d-mov="transferencia">+ Transferencia</button>' : ''));
    var cards = [
      t({ nombre: 'Cash collected', clave: true, valor: us(r.total_ingresos), sub: 'todo lo cobrado en el mes' }),
      t({ nombre: 'Gastos', valor: us(r.total_gastos), pct: r.total_ingresos ? Math.round(r.total_gastos / r.total_ingresos * 100) : null, sub: 'incluye ' + us(r.pauta_propia) + ' de pauta propia' }),
      t({ nombre: 'Flujo de caja neto', oro: r.flujo > 0, valor: us(r.flujo), sub: 'cobrado − gastos' }),
      t({ nombre: 'Por cobrar', clave: true, ambar: r.por_cobrar > 0, valor: us(r.por_cobrar), sub: us(r.vencido) + ' vencido', ir: ['Ver cobros', 'cobros'] })
    ];
    if (c.modelo === 'comision') {
      cards.push(t({ nombre: 'Comisiones generadas', valor: us(r.comisiones.comision), sub: us(r.comisiones.comision_cobrada) + ' ya cobradas', ir: ['Ver bitácora', 'bitacora'] }));
      cards.push(t({ nombre: 'Closers por pagar', valor: us(r.comisiones.closer), sub: c.cobro.pctCloser + '% de la comisión de lo que cerraron' }));
    } else {
      cards.push(t({ nombre: 'Ganancia por socio', valor: us(r.flujo / (s ? s.socios.length : 1)), sub: (s ? s.socios.map(function (x) { return x.nombre + ' ' + x.pct + '%'; }).join(' · ') : '') }));
      cards.push(t({ nombre: 'Saldo de pauta ' + (s ? s.otro + ' → ' + s.pagador : ''), ambar: s && s.saldo > 0, valor: us(s ? s.saldo : 0), sub: s && s.saldo ? 'lo que falta transferir para quedar 50/50' : 'al día' }));
    }
    h += '<div class="grilla" style="--n:3">' + cards.join('') + '</div>';
    h += '<div class="bloques">' + S().bloque('Ingresos por categoría', barras(r.ingresos, r.total_ingresos, 'var(--verde)')) + S().bloque('Gastos por categoría', barras(r.gastos, r.total_gastos, 'var(--rojo)')) + '</div>';
    if (s) {
      var max = Math.max.apply(null, s.socios.map(function (x) { return Math.max(x.puso, x.parte); })) || 1;
      var aportes = '<div class="e33">' + s.socios.map(function (x) {
        return '<div class="fin-cat"><span class="fin-cat-n">' + esc(x.nombre) + (x.nombre === s.pagador ? ' · paga con su tarjeta' : ' · le transfiere a ' + esc(s.pagador)) + '</span><span class="rend-barra"><span style="width:' + Math.max(2, x.puso / max * 100) + '%"></span></span><span class="fin-cat-v">' + us(x.puso) + ' <small>de ' + us(x.parte) + '</small></span></div>';
      }).join('') + '<p class="ini-nota">Pauta propia del mes: ' + us(r.pauta_propia) + ' (sale sola de Meta). Cada socio pone su ' + s.socios[0].pct + '%: lo que pagó cada uno, descontando lo que se transfirieron.</p></div>';
      var trans = tabla([['Fecha'], ['De → a'], ['Nota'], ['Monto', 1]], s.transferencias.slice().reverse().map(function (x) { return '<tr><td>' + corta(x[0]) + '</td><td>' + esc(x[1]) + ' → ' + esc(x[2]) + '</td><td>' + esc(x[4]) + '</td><td class="rend-num">' + us(x[3]) + '</td></tr>'; }), 'Sin transferencias este mes.');
      h += '<div class="bloques">' + S().bloque('Pauta propia entre socios', aportes) + S().bloque('Transferencias ' + s.otro + ' → ' + s.pagador, trans) + '</div>';
    }
    var movs = r.movimientos.map(function (m) {
      return '<tr><td>' + corta(m.fecha) + '</td><td><span class="rend-estado" data-estado="' + (m.tipo === 'ingreso' ? 'cumple' : m.tipo === 'gasto' ? 'falta' : '') + '">' + ({ ingreso: 'Ingreso', gasto: 'Gasto', transferencia: 'Transferencia' })[m.tipo] + '</span></td><td>' + esc(m.categoria || (m.socio ? m.socio + ' → ' + m.socio_destino : '—')) + '</td><td>' + esc(m.concepto) + '</td><td class="rend-num">' + S().conUsd(m.monto, m.moneda, m.monto_usd) + '</td><td><button type="button" class="e126" data-d-borrar-mov="' + m.id + '">Quitar</button></td></tr>';
    });
    h += '<section class="e22"><div class="e19"><h2 class="titulo-2">Movimientos del mes</h2><p class="e44">ingresos y gastos cargados a mano · los cobros pagados y la pauta propia entran solos</p></div><div class="caja">' +
      tabla([['Fecha'], ['Tipo'], ['Categoría'], ['Concepto'], ['Monto', 1], ['']], movs, 'Todavía no cargaste movimientos este mes.') + '</div></section>';
    var cob = r.cobros_pagados.map(function (x) { return '<tr><td>' + corta(x.pagado) + '</td><td><strong>' + esc(x.cuenta) + '</strong></td><td>' + CONCEPTO[x.concepto] + (x.periodo ? ' · ' + x.periodo : '') + '</td><td class="rend-num">' + S().conUsd(x.monto, x.moneda, x.monto_usd) + '</td></tr>'; });
    h += '<section class="e22"><div class="e19"><h2 class="titulo-2">Cobros pagados en el mes</h2></div><div class="caja">' + tabla([['Pagado'], [cfg().voc.cuenta], ['Concepto'], ['Monto', 1]], cob, 'Ningún cobro marcado como pagado este mes.') + '</div></section>';
    return h;
  }
  function formMov(tipo) {
    var c = cfg(), cats = (D.datos.categorias || {})[tipo] || [], socios = c.socios.map(function (s) { return s.nombre; });
    var h = '<form class="e22" id="d-form-mov" data-tipo="' + tipo + '"><div class="fc-rapidos">' +
      '<label class="ct-dato">Fecha<input class="ct-input" type="date" name="fecha" required value="' + hoyIso() + '"></label>' +
      '<label class="ct-dato">Monto<input class="ct-input" name="monto" inputmode="decimal" required></label>' +
      '<label class="ct-dato">Moneda<select class="ct-input" name="moneda"><option>USD</option><option>COP</option></select></label>';
    if (tipo === 'transferencia') {
      h += '<label class="ct-dato">De<select class="ct-input" name="socio">' + socios.map(function (s) { return '<option>' + esc(s) + '</option>'; }).join('') + '</select></label>' +
        '<label class="ct-dato">A<select class="ct-input" name="socio_destino">' + socios.slice().reverse().map(function (s) { return '<option>' + esc(s) + '</option>'; }).join('') + '</select></label>';
    } else {
      h += '<label class="ct-dato">Categoría<select class="ct-input" name="categoria">' + cats.map(function (k) { return '<option>' + esc(k) + '</option>'; }).join('') + '</select></label>' +
        (socios.length > 1 ? '<label class="ct-dato">' + (tipo === 'gasto' ? 'Lo pagó' : 'Lo cobró') + '<select class="ct-input" name="socio"><option value="">La empresa</option>' + socios.map(function (s) { return '<option>' + esc(s) + '</option>'; }).join('') + '</select></label>' : '');
    }
    h += '<label class="ct-dato ct-dato--ancho">Concepto<input class="ct-input" name="concepto" maxlength="200" placeholder="' + (tipo === 'transferencia' ? 'Mi parte de la pauta, semana 3' : '') + '"></label></div>' +
      '<button type="submit" class="fin-boton" style="width:100%">Guardar</button><p class="e12" id="d-msg" style="margin:0"></p></form>';
    capa([{ ingreso: 'Nuevo ingreso', gasto: 'Nuevo gasto', transferencia: 'Transferencia entre socios' }[tipo], h]);
  }

  // ---- Cobros / Suscripciones ----
  function vistaCobros(r) {
    var c = cfg(), v = c.voc, t = S().tarjeta, fee = c.modelo === 'fee';
    var h = cabecera(fee ? 'Suscripciones' : 'Cobros', fee ? 'Fee mensual de cada ' + esc(v.cuenta.toLowerCase()) + ' (se genera solo cada mes desde su alta), setups y mora' : 'Setups de las ' + esc(v.cuentas.toLowerCase()) + ' y comisiones por cobrar · USD');
    h += '<div class="cal-barra"><span></span><div class="cal-paso"><button type="button" class="fin-boton" data-d-cobro>+ Registrar cobro</button></div></div>';
    h += '<div class="grilla" style="--n:4">' + [
      t({ nombre: fee ? 'MRR' : 'Cobrado este mes', clave: true, valor: us(fee ? r.mrr : r.cobrado_mes), sub: fee ? r.planes.filter(function (p) { return p.fee && !p.baja; }).length + ' ' + v.cuentas.toLowerCase() + ' con fee' : 'setups y comisiones' }),
      t({ nombre: 'Cobrado este mes', valor: us(r.cobrado_mes), sub: 'marcado como pagado' }),
      t({ nombre: 'Por cobrar', ambar: r.por_cobrar > 0, valor: us(r.por_cobrar), sub: 'pendiente + vencido' }),
      t({ nombre: 'Vencido', valor: us(r.vencido), sub: r.cobros.filter(function (x) { return x.estado === 'vencido'; }).length + ' cobros con mora' })
    ].join('') + '</div>';
    if (fee) {
      var planes = r.planes.map(function (p) {
        var e = EST[p.estado_mes] || ['Sin fee', ''];
        return '<tr><td><strong>' + esc(p.nombre) + '</strong></td><td class="rend-num">' + us(p.setup) + '</td><td class="rend-num">' + us(p.fee) + '</td><td>' + corta(p.alta) + '</td><td><span class="rend-estado" data-estado="' + e[1] + '">' + e[0] + '</span>' + (p.mora ? ' <span class="e12">' + p.mora + ' días</span>' : '') + '</td><td>' +
          (p.cobro_mes && p.estado_mes !== 'pagado' ? '<button type="button" class="e126" data-d-pagar="' + p.cobro_mes + '">Marcar pagado</button>' : '') + '</td></tr>';
      });
      h += '<section class="e22"><div class="e19"><h2 class="titulo-2">' + esc(v.cuentas) + ' y su plan</h2><p class="e44">el setup, el fee y la fecha de alta se cargan en la Ficha de ' + esc(v.cuentas.toLowerCase()) + '</p></div><div class="caja">' +
        tabla([[v.cuenta], ['Setup', 1], ['Fee', 1], ['Alta'], ['Este mes'], ['']], planes, 'Cargá el plan de cada ' + v.cuenta.toLowerCase() + ' en su ficha.') + '</div></section>';
    }
    var filas = r.cobros.filter(function (x) { return !D.filtro || x.estado === D.filtro; }).map(function (x) {
      var e = EST[x.estado];
      return '<tr><td>' + corta(x.vence) + '</td><td><strong>' + esc(x.cuenta) + '</strong></td><td>' + CONCEPTO[x.concepto] + (x.periodo ? ' · ' + x.periodo : '') + (x.nota ? ' <span class="e12">' + esc(x.nota) + '</span>' : '') + '</td><td class="rend-num">' + S().conUsd(x.monto, x.moneda, x.monto_usd) + '</td><td><span class="rend-estado" data-estado="' + e[1] + '">' + e[0] + '</span>' + (x.mora ? ' <span class="e12">' + x.mora + ' días</span>' : '') + (x.pagado ? ' <span class="e12">' + corta(x.pagado) + '</span>' : '') + '</td><td>' +
        (x.pagado ? '<button type="button" class="e126" data-d-despagar="' + x.id + '">Deshacer</button>' : '<button type="button" class="e126" data-d-pagar="' + x.id + '">Marcar pagado</button>') + ' <button type="button" class="e126" data-d-borrar-cobro="' + x.id + '">Quitar</button></td></tr>';
    });
    var chips = '<div class="e53" role="group" aria-label="Filtrar">' + [[null, 'Todos'], ['vencido', 'Vencidos'], ['pendiente', 'Pendientes'], ['pagado', 'Pagados']].map(function (f) {
      return '<button type="button" class="e94" data-d-filtro="' + (f[0] || '') + '" aria-pressed="' + (D.filtro === f[0]) + '">' + f[1] + '</button>';
    }).join('') + '</div>';
    h += '<section class="e22"><div class="e19"><h2 class="titulo-2">Cobros</h2></div>' + chips + '<div class="caja">' + tabla([['Vence'], [v.cuenta], ['Concepto'], ['Monto', 1], ['Estado'], ['']], filas, 'Sin cobros.') + '</div></section>';
    return h;
  }
  function formCobro() {
    var c = cfg();
    api('/cuentas').then(function (cuentas) {
      var cl = cuentas.filter(function (x) { return !x.propia && x.activo; });
      var h = '<form class="e22" id="d-form-cobro"><div class="fc-rapidos">' +
        '<label class="ct-dato ct-dato--ancho">' + esc(c.voc.cuenta) + '<select class="ct-input" name="cuenta_id" required>' + cl.map(function (x) { return '<option value="' + x.id + '">' + esc(x.nombre) + '</option>'; }).join('') + '</select></label>' +
        '<label class="ct-dato">Concepto<select class="ct-input" name="concepto"><option value="setup">Setup</option><option value="comision">Comisión</option><option value="fee">Fee mensual</option><option value="otro">Otro</option></select></label>' +
        '<label class="ct-dato">Monto<input class="ct-input" name="monto" inputmode="decimal" required value="' + (c.cobro.setup || '') + '"></label>' +
        '<label class="ct-dato">Moneda<select class="ct-input" name="moneda"><option>USD</option><option>COP</option></select></label>' +
        '<label class="ct-dato">Vence<input class="ct-input" type="date" name="vence" value="' + hoyIso() + '"></label>' +
        '<label class="ct-dato">Pagado el (si ya pagó)<input class="ct-input" type="date" name="pagado"></label>' +
        '<label class="ct-dato ct-dato--ancho">Nota<input class="ct-input" name="nota" maxlength="200"></label></div>' +
        '<button type="submit" class="fin-boton" style="width:100%">Guardar</button><p class="e12" id="d-msg" style="margin:0"></p></form>';
      capa(['Registrar cobro', h]);
    });
  }

  // ---- Ventas de la agencia ----
  function vistaAgencia(r) {
    var c = cfg(), t = S().tarjeta, v = c.voc, fee = c.modelo === 'fee';
    var h = cabecera(r.embudo, 'Tu propio embudo de venta: llamadas de la subcuenta propia en GHL, ' + v.cuentas.toLowerCase() + ' nuevos y lo que facturan · USD');
    h += navMes();
    h += '<div class="grilla" style="--n:4">' + [
      t({ nombre: 'Llamadas agendadas', clave: true, valor: String(r.agendadas), sub: 'por fecha de la llamada · ' + r.desde_anuncios + ' creadas desde anuncios' }),
      t({ nombre: 'Llamadas asistidas', valor: String(r.asistidas), pct: r.pct_asistencia == null ? null : Math.round(r.pct_asistencia), sub: 'de las pasadas' }),
      t({ nombre: v.cuentas + ' nuevos', clave: true, valor: String(r.cierres), sub: 'alta en el mes · tasa de cierre ' + (r.tasa_cierre == null ? '—' : Math.round(r.tasa_cierre) + '%') }),
      t({ nombre: 'CAC', valor: us(r.cac), sub: 'pauta ÷ ' + v.cuentas.toLowerCase() + ' nuevos' }),
      t({ nombre: 'Costo por llamada', valor: us(r.costo_cita), sub: us(r.gasto) + ' de pauta ÷ ' + r.desde_anuncios + ' creadas desde anuncios · ' + r.leads + ' leads' }),
      t({ nombre: 'Setups cobrados', valor: us(r.setups_cobrados), sub: us(r.setups_pendientes) + ' pendientes' }),
      t({ nombre: fee ? 'MRR' : v.cuentas + ' activos', clave: fee, valor: fee ? us(r.mrr) : String(r.activos), sub: fee ? r.activos + ' ' + v.cuentas.toLowerCase() + ' con fee' : 'con plan cargado' }),
      t({ nombre: 'Llamadas de hoy', valor: String(r.agenda.hoy), sub: r.agenda.proximos_7 + ' en 7 días · ' + r.agenda.sin_marcar + ' sin marcar', ir: ['Ver agenda', 'ag-agenda'] })
    ].join('') + '</div>';
    var filas = r.nuevos.map(function (x) { return '<tr><td><strong>' + esc(x.nombre) + '</strong></td><td>' + corta(x.alta) + '</td><td class="rend-num">' + us(x.setup) + '</td><td class="rend-num">' + us(x.fee) + '</td></tr>'; });
    h += '<section class="e22"><div class="e19"><h2 class="titulo-2">' + esc(v.cuentas) + ' nuevos del mes</h2><p class="e44">se cuentan por la fecha de alta de su ficha</p></div><div class="caja">' + tabla([[v.cuenta], ['Alta'], ['Setup', 1], ['Fee', 1]], filas, 'Ningún alta este mes.') + '</div></section>';
    if (r.demo) h += '<p class="ini-nota">Llamadas y pauta de ejemplo hasta que el worker tenga acceso a la subcuenta propia en GHL y a Meta.</p>';
    return h;
  }

  // ---- Cargar y eventos ----
  function cargar() {
    var menu = D.menu, negocio = D.negocio;
    var q = '?desde=' + rangoMes(D.mes)[0] + '&hasta=' + rangoMes(D.mes)[1];
    var ruta = menu === 'finanzas' ? '/finanzas' + q : menu === 'cobros' ? '/cobros' : '/ventas-agencia' + q;
    return api(ruta).then(function (r) {
      if (D.menu !== menu || D.negocio !== negocio) return;
      D.datos = r;
      principal(menu === 'finanzas' ? vistaFinanzas(r) : menu === 'cobros' ? vistaCobros(r) : vistaAgencia(r));
    }).catch(function (e) { if (D.menu) principal('<section class="caja ini-bloque"><h3 class="fin-h3">No se pudo cargar</h3><p class="e52" style="margin:0">' + esc(e.message) + '.</p></section>'); });
  }
  function mostrar(menu, negocio) {
    if (D.negocio !== negocio || !D.mes) D.mes = hoyIso().slice(0, 7);
    D.menu = menu; D.negocio = negocio; cargar();
  }
  function num(s) { s = String(s || '').trim(); if (/,/.test(s) && /\./.test(s)) s = s.replace(/\./g, ''); s = s.replace(',', '.'); return s === '' ? null : Number(s); }
  function guardar(p) { p.then(function () { capa(''); SONIDO.sonar('listo'); cargar(); }).catch(function (e) { var m = document.getElementById('d-msg'); if (m) m.textContent = 'No se pudo guardar: ' + e.message + '.'; else alert(e.message); }); }

  document.addEventListener('click', function (e) {
    var t = e.target.closest ? e.target : null; if (!t || !D.menu) return;
    var b;
    if (t.closest('[data-d-cerrar]')) { capa(''); return; }
    if ((b = t.closest('[data-d-mes]'))) { var n = +b.getAttribute('data-d-mes'); D.mes = n ? moverMes(D.mes, n) : hoyIso().slice(0, 7); cargar(); return; }
    if ((b = t.closest('[data-d-mov]'))) { formMov(b.getAttribute('data-d-mov')); return; }
    if (t.closest('[data-d-cobro]')) { formCobro(); return; }
    if ((b = t.closest('[data-d-filtro]'))) { D.filtro = b.getAttribute('data-d-filtro') || null; principal(vistaCobros(D.datos)); return; }
    if ((b = t.closest('[data-d-pagar]'))) { guardar(api('/cobros/' + b.getAttribute('data-d-pagar'), 'PATCH', { pagado: hoyIso() })); return; }
    if ((b = t.closest('[data-d-despagar]'))) { guardar(api('/cobros/' + b.getAttribute('data-d-despagar'), 'PATCH', { pagado: null })); return; }
    if ((b = t.closest('[data-d-borrar-cobro], [data-d-borrar-mov]'))) {
      if (b.getAttribute('data-confirmar') !== '1') { b.setAttribute('data-confirmar', '1'); b.textContent = '¿Seguro?'; return; }
      var id = b.getAttribute('data-d-borrar-cobro');
      guardar(api(id ? '/cobros/' + id : '/movimientos/' + b.getAttribute('data-d-borrar-mov'), 'PATCH', { borrar: true }));
    }
  });
  document.addEventListener('submit', function (e) {
    var f = e.target;
    if (f.id === 'd-form-mov') {
      e.preventDefault();
      var tipo = f.getAttribute('data-tipo'), cuerpo = { tipo: tipo, fecha: f.fecha.value, monto: num(f.monto.value), moneda: f.moneda.value, concepto: f.concepto.value };
      if (f.categoria) cuerpo.categoria = f.categoria.value;
      if (f.socio) cuerpo.socio = f.socio.value;
      if (f.socio_destino) cuerpo.socio_destino = f.socio_destino.value;
      if (!(cuerpo.monto > 0)) { document.getElementById('d-msg').textContent = 'El monto tiene que ser un número.'; return; }
      guardar(api('/movimientos', 'POST', cuerpo));
    }
    if (f.id === 'd-form-cobro') {
      e.preventDefault();
      var c = { cuenta_id: +f.cuenta_id.value, concepto: f.concepto.value, monto: num(f.monto.value), moneda: f.moneda.value, vence: f.vence.value, pagado: f.pagado.value || null, nota: f.nota.value };
      if (!(c.monto > 0)) { document.getElementById('d-msg').textContent = 'El monto tiene que ser un número.'; return; }
      guardar(api('/cobros', 'POST', c));
    }
  });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') { var c = document.getElementById('d-capa'); if (c && c.innerHTML) capa(''); } });

  window.MENUS_API = window.MENUS_API || {};
  ['finanzas', 'cobros', 'ag-ventas'].forEach(function (k) { window.MENUS_API[k] = mostrar; });
  var salir = window.MENUS_API_SALIR;
  window.MENUS_API_SALIR = function () { D.menu = null; capa(''); if (salir) salir(); };
})();
