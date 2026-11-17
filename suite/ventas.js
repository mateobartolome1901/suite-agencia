// Fase 3: Bitácora / Registro de ventas (#bitacora) y Contactos (#pacientes).
// Lee /api/<negocio>/ventas y /contactos; registra con POST /ventas y corrige con PATCH /ventas/<id>.
(function () {
  var V = { menu: null, negocio: null, mes: null, datos: null, capa: null, q: '', contactos: null, timer: null };
  var MES_LARGO = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];
  var MES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];
  var EST = { asistio: ['Asistió', 'cumple'], no_asistio: ['No asistió', 'falta'], confirmada: ['Pendiente', 'cerca'], cancelada: ['Cancelada', ''], reprogramada: ['Reprogramada', ''] };

  function S() { return window.SUITE; }
  function esc(s) { return S().esc(s == null ? '' : s); }
  function voc() { return NEGOCIOS[V.negocio].voc; }
  function comision() { return NEGOCIOS[V.negocio].modelo === 'comision'; }
  function plata(x) { return x == null ? '—' : (x < 0 ? '−' : '') + 'US$' + Math.round(Math.abs(x)).toLocaleString('en-US'); }
  function corta(s) { var p = s.split('-'); return +p[2] + ' ' + MES[+p[1] - 1]; }
  function hora(m) { return String(Math.floor(m / 60)).padStart(2, '0') + ':' + String(m % 60).padStart(2, '0'); }
  function rangoMes(m) { var p = m.split('-'), ult = new Date(Date.UTC(+p[0], +p[1], 0)).getUTCDate(); return [m + '-01', m + '-' + String(ult).padStart(2, '0')]; }
  function moverMes(m, n) { var p = m.split('-'), d = new Date(Date.UTC(+p[0], +p[1] - 1 + n, 1)); return d.toISOString().slice(0, 7); }
  function vari(a, b, menosEsMejor) {
    if (a == null || !b) return null;
    var c = (a - b) / Math.abs(b) * 100, bueno = menosEsMejor ? c <= 0 : c >= 0;
    return [(c > 0 ? '+' : '−') + Math.abs(c).toFixed(1) + '%', bueno ? 'bien' : 'mal'];
  }
  function api(ruta, metodo, cuerpo) {
    var op = { method: metodo || 'GET', credentials: 'same-origin', headers: {} };
    if (cuerpo) { op.headers['Content-Type'] = 'application/json'; op.headers['X-CSRF'] = S().sesion().csrf; op.body = JSON.stringify(cuerpo); }
    return fetch('/api/' + V.negocio + ruta, op).then(function (r) {
      if (r.status === 401) { location.href = '/ingresar'; throw new Error('sin sesión'); }
      if (!r.ok) throw new Error(r.status === 400 ? 'Revisá los datos' : r.status === 403 ? 'No tenés permiso' : 'Error ' + r.status);
      return r.json();
    });
  }
  function principal(h) { document.getElementById('principal').innerHTML = h; window.dcPostRender(); }
  function capa(h) {
    var c = document.getElementById('v-capa');
    if (!c) { c = document.createElement('div'); c.id = 'v-capa'; document.body.appendChild(c); }
    c.innerHTML = h ? '<div class="cal-velo" data-v-cerrar></div><aside class="fc-capa ficha-cita" role="dialog" aria-modal="true">' + h + '</aside>' : '';
  }
  function cabCapa(eyebrow, titulo, sub) {
    return '<div class="fc-cabeza"><div class="e19" style="flex:1;min-width:0;gap:10px">' + (eyebrow ? '<span class="ficha-clinica">' + esc(eyebrow) + '</span>' : '') + '<h2 class="fc-titulo">' + esc(titulo) + '</h2>' + (sub ? '<span class="e30">' + sub + '</span>' : '') + '</div><button type="button" class="fc-volver" data-v-cerrar aria-label="Cerrar">✕</button></div>';
  }

  function tituloMenu() { var t = 'Bitácora'; NEGOCIOS[V.negocio].menus.forEach(function (g) { g.items.forEach(function (it) { if (it[0] === V.menu) t = it[1]; }); }); return t; }

  // ---- Bitácora ----
  function vistaBitacora(r) {
    var v = voc(), cfg = NEGOCIOS[V.negocio], s = r.resumen, a = r.anterior, com = comision();
    var p = r.desde.split('-'), titulo = MES_LARGO[+p[1] - 1] + ' ' + p[0];
    var h = '<header><div class="e19"><h1 class="titulo-1">' + esc(tituloMenu()) + '</h1><span class="e30">' + (com
      ? 'Ventas de ' + esc(v.servicios.toLowerCase()) + ' por ' + esc(v.cuenta.toLowerCase()) + ' · comisión ' + r.comision_pct + '% de (venta − costos − pauta) · ' + esc(v.vendedor.toLowerCase()) + ' ' + r.closer_pct + '% de la comisión'
      : 'Lo que venden tus ' + esc(v.cuentas.toLowerCase()) + ' con las citas de la agencia: el retorno de cada uno sobre la pauta') + '</span></div>' +
      '<div class="cab-filtros e36"><button class="btn-sec" type="button" disabled>' + esc(v.cuentas) + ': Todas (' + r.cuentas_disponibles.length + ')</button></div></header>';
    h += '<div class="cal-barra"><h2 class="titulo-cal">' + esc(titulo) + '</h2><div class="cal-paso"><button type="button" class="e112" data-v-mes="-1" aria-label="Mes anterior">‹</button><button type="button" class="e113" data-v-mes="0">Este mes</button><button type="button" class="e112" data-v-mes="1" aria-label="Mes siguiente">›</button>' +
      '<button type="button" class="fin-boton" data-v-nueva>+ Registrar ' + (com ? 'venta' : 'cierre') + '</button></div></div>';
    var t = S().tarjeta, pctDe = function (x) { return s.monto ? Math.round(x / s.monto * 100) : null; };
    var cards = com ? [
      t({ nombre: 'Ventas', clave: true, valor: plata(s.monto), sub: s.ventas + ' ' + v.servicios.toLowerCase() + ' · vs ' + plata(a.monto) + ' mes ant.', vari: vari(s.monto, a.monto) }),
      t({ nombre: 'Costos de ' + v.servicios.toLowerCase(), valor: plata(s.costos), pct: pctDe(s.costos), sub: 'de lo vendido' }),
      t({ nombre: 'Pauta del período', valor: plata(s.pauta), pct: pctDe(s.pauta), sub: 'Meta + YouTube de las ' + v.cuentas.toLowerCase() + ' con ventas o pauta' }),
      t({ nombre: 'Margen', valor: plata(s.margen), sub: 'venta − costos − pauta', vari: vari(s.margen, a.margen) }),
      t({ nombre: 'Comisión ' + cfg.corto, clave: true, valor: plata(s.comision), sub: r.comision_pct + '% del margen (nunca negativa) · vs ' + plata(a.comision) + ' ant.', vari: vari(s.comision, a.comision) }),
      t({ nombre: v.vendedores, valor: plata(s.closer), sub: r.closer_pct + '% de la comisión de lo que cerraron' }),
      t({ nombre: 'Neto ' + cfg.corto, clave: true, valor: plata(s.neto), sub: 'comisión − ' + v.vendedores.toLowerCase() }),
      t({ nombre: 'Comisión por cobrar', ambar: s.por_cobrar > 0, valor: plata(s.por_cobrar), sub: plata(s.comision_cobrada) + ' ya cobrado' })
    ] : [
      t({ nombre: 'Cierres', clave: true, valor: String(s.ventas), sub: 'vs ' + a.ventas + ' mes ant.', vari: vari(s.ventas, a.ventas) }),
      t({ nombre: 'Volumen vendido', clave: true, valor: plata(s.monto), sub: 'vs ' + plata(a.monto) + ' mes ant.', vari: vari(s.monto, a.monto) }),
      t({ nombre: 'Pauta del período', valor: plata(s.pauta), sub: 'Meta + YouTube de los ' + v.cuentas.toLowerCase() }),
      t({ nombre: 'Retorno', clave: true, valor: s.retorno == null ? '—' : s.retorno.toFixed(1) + 'x', sub: 'volumen vendido ÷ pauta' })
    ];
    h += '<div class="grilla" style="--n:4">' + cards.join('') + '</div>';
    // Por cuenta
    var filas = r.cuentas.filter(function (c) { return c.ventas || c.pauta; });
    h += '<section class="e22"><div class="e19"><h2 class="titulo-2">Por ' + esc(v.cuenta.toLowerCase()) + '</h2><p class="e44">' + (com ? 'la pauta de cada ' + esc(v.cuenta.toLowerCase()) + ' se descuenta de sus ventas del mes' : 'cuánto vendió cada ' + esc(v.cuenta.toLowerCase()) + ' por cada dólar de pauta') + '</p></div>' +
      '<div class="caja"><div class="rend-scroll"><table class="rend-tabla"><thead><tr><th>' + esc(v.cuenta) + '</th><th class="rend-num">' + (com ? 'Ventas' : 'Cierres') + '</th><th class="rend-num">Monto</th>' + (com ? '<th class="rend-num">Costos</th>' : '') + '<th class="rend-num">Pauta</th>' +
      (com ? '<th class="rend-num">Margen</th><th class="rend-num">Comisión</th><th class="rend-num">' + esc(v.vendedor) + '</th>' : '<th class="rend-num">Retorno</th>') + '</tr></thead><tbody>' +
      filas.map(function (c) {
        return '<tr><td><strong>' + esc(c.nombre) + '</strong></td><td class="rend-num">' + c.ventas + '</td><td class="rend-num">' + plata(c.monto) + '</td>' + (com ? '<td class="rend-num">' + plata(c.costos) + '</td>' : '') + '<td class="rend-num">' + plata(c.pauta) + '</td>' +
          (com ? '<td class="rend-num" style="color:' + (c.margen < 0 ? 'var(--rojo-texto)' : 'inherit') + '">' + plata(c.margen) + '</td><td class="rend-num"><strong>' + plata(c.comision) + '</strong></td><td class="rend-num">' + plata(c.closer) + '</td>'
            : '<td class="rend-num"><strong>' + (c.retorno == null ? '—' : c.retorno.toFixed(1) + 'x') + '</strong></td>') + '</tr>';
      }).join('') + (filas.length ? '' : '<tr><td colspan="8" class="e11">Sin ventas ni pauta en el mes.</td></tr>') + '</tbody></table></div></div></section>';
    // Ventas del mes
    h += '<section class="e22"><div class="e19"><h2 class="titulo-2">' + (com ? 'Ventas del mes' : 'Cierres del mes') + '</h2><p class="e44">' + r.ventas.length + ' cargadas · tocá una fila para corregirla</p></div>' +
      '<div class="caja"><div class="rend-scroll"><table class="rend-tabla"><thead><tr><th>Fecha</th><th>' + esc(v.contacto) + '</th><th>' + esc(v.cuenta) + '</th><th>' + esc(v.servicio) + '</th><th class="rend-num">Venta</th>' +
      (com ? '<th class="rend-num">Costos</th><th class="rend-num">Pauta</th><th class="rend-num">Comisión</th><th class="rend-num">' + esc(v.vendedor) + '</th><th>Cobrada</th>' : '') + '</tr></thead><tbody>' +
      r.ventas.map(function (x) {
        return '<tr data-v-editar="' + x.id + '" style="cursor:pointer"><td>' + corta(x.fecha) + '</td><td><strong>' + esc(x.contacto || '—') + '</strong></td><td class="e30">' + esc(x.cuenta) + '</td><td>' + esc(x.servicio || '—') + '</td><td class="rend-num">' + plata(x.monto) + '</td>' +
          (com ? '<td class="rend-num">' + plata(x.costo) + '</td><td class="rend-num e30">' + plata(x.pauta) + '</td><td class="rend-num"><strong>' + plata(x.comision) + '</strong></td><td class="rend-num">' + (x.vendedor ? plata(x.closer) + ' <span class="e12">' + esc(x.vendedor.split('@')[0]) + '</span>' : '—') + '</td>' +
            '<td><span class="rend-estado" data-estado="' + (x.comision_cobrada ? 'cumple' : x.comision ? 'cerca' : '') + '">' + (x.comision_cobrada ? 'Cobrada' : x.comision ? 'Por cobrar' : '—') + '</span></td>' : '') + '</tr>';
      }).join('') + (r.ventas.length ? '' : '<tr><td colspan="10" class="e11">Todavía no hay ventas cargadas este mes. Usá «+ Registrar».</td></tr>') + '</tbody></table></div></div></section>';
    if (com && r.vendedores.length) {
      h += S().bloque('Comisión por ' + v.vendedor.toLowerCase(), '<ol class="ini-ranking">' + r.vendedores.map(function (x, i) {
        return '<li><span class="rend-pos">' + (i + 1) + '</span><span class="e3" style="flex:1"><strong>' + esc(x.vendedor) + '</strong><span class="e12">' + x.ventas + ' ventas · ' + plata(x.monto) + ' vendidos</span></span><strong>' + plata(x.closer) + '</strong></li>';
      }).join('') + '</ol>');
    }
    return h;
  }
  function formVenta(x) {
    var v = voc(), com = comision(), admin = S().sesion() && S().sesion().rol === 'admin', r = V.datos;
    x = x || { cuenta_id: r.cuentas_disponibles.length === 1 ? r.cuentas_disponibles[0].id : '', fecha: (r.hoy || new Date().toISOString().slice(0, 10)), contacto: '', servicio: '', monto: '', costo: '', vendedor: '', notas: '' };
    var h = cabCapa(null, x.id ? 'Corregir ' + (com ? 'venta' : 'cierre') : 'Registrar ' + (com ? 'venta' : 'cierre'), x.id ? 'Cargada por ' + esc(x.quien || '') : '');
    h += '<form class="e22" id="v-form" data-id="' + (x.id || '') + '"><div class="fc-rapidos">' +
      '<label class="ct-dato ct-dato--ancho">' + esc(v.cuenta) + '<select class="ct-input" name="cuenta_id" required><option value="">Elegir…</option>' + r.cuentas_disponibles.map(function (c) { return '<option value="' + c.id + '"' + (c.id === x.cuenta_id ? ' selected' : '') + '>' + esc(c.nombre) + '</option>'; }).join('') + '</select></label>' +
      '<label class="ct-dato">Fecha<input class="ct-input" type="date" name="fecha" required value="' + esc(x.fecha) + '"></label>' +
      '<label class="ct-dato">' + esc(v.contacto) + '<input class="ct-input" name="contacto" maxlength="200" value="' + esc(x.contacto) + '"></label>' +
      '<label class="ct-dato">' + esc(v.servicio) + '<input class="ct-input" name="servicio" maxlength="200" value="' + esc(x.servicio) + '"></label>' +
      '<label class="ct-dato">' + (com ? 'Venta' : 'Volumen') + ' (USD)<input class="ct-input" name="monto" inputmode="decimal" required value="' + esc(x.monto == null ? '' : x.monto) + '"></label>' +
      (com ? '<label class="ct-dato">Costos de la ' + esc(v.servicio.toLowerCase()) + ' (USD)<input class="ct-input" name="costo" inputmode="decimal" value="' + esc(x.costo == null ? '' : x.costo) + '" placeholder="0"></label>' : '') +
      (com && admin ? '<label class="ct-dato">' + esc(v.vendedor) + ' que cerró (email)<input class="ct-input" type="email" name="vendedor" value="' + esc(x.vendedor) + '" placeholder="vacío: sin ' + esc(v.vendedor.toLowerCase()) + '"></label>' : '') +
      '<label class="ct-dato ct-dato--ancho">Notas<textarea class="ct-input ct-input--largo" name="notas" maxlength="2000">' + esc(x.notas) + '</textarea></label></div>' +
      (com && admin && x.id ? '<label class="e91"><input type="checkbox" name="comision_cobrada"' + (x.comision_cobrada ? ' checked' : '') + '> Comisión cobrada</label>' : '') +
      '<button type="submit" class="fin-boton" style="width:100%">Guardar</button><p class="e12" id="v-msg" style="margin:0"></p>' +
      (x.id && r.puede_borrar ? '<button type="button" class="e126" data-v-borrar="' + x.id + '" style="align-self:flex-start;color:var(--rojo-texto)">Quitar de la bitácora</button>' : '') + '</form>';
    capa(h);
  }

  // ---- Contactos ----
  function vistaContactos(r) {
    var v = voc();
    var h = '<header><div class="e19"><h1 class="titulo-1">' + esc(v.contactos) + '</h1><span class="e30">Historial de cada ' + esc(v.contacto.toLowerCase()) + ': citas, resultado de cada llamada y ventas, con su ' + esc(v.cuenta.toLowerCase()) + '</span></div></header>';
    h += '<label class="ct-dato" style="max-width:760px">Buscar ' + esc(v.contacto.toLowerCase()) + '<input class="ct-input" type="search" id="v-q" placeholder="Nombre, teléfono o email" value="' + esc(V.q) + '" autocomplete="off"></label>';
    h += '<div id="v-lista">' + listaContactos(r) + '</div>';
    return h;
  }
  function listaContactos(r) {
    if (!r.contactos.length) return '<p class="vacio">' + (V.q ? 'Nadie con ese dato.' : 'Todavía no hay ' + esc(voc().contactos.toLowerCase()) + '.') + '</p>';
    return '<div class="ct-lista">' + r.contactos.map(function (p, i) {
      return '<button type="button" class="ct-fila" data-v-contacto="' + i + '"><strong>' + esc(p.nombre) + '</strong> · ' + esc(p.cuenta) + (p.ventas.length ? ' <span class="rend-estado" data-estado="cumple">' + p.ventas.length + ' venta' + (p.ventas.length > 1 ? 's' : '') + '</span>' : '') + '</button>';
    }).join('') + '</div>' + (r.total > r.contactos.length ? '<p class="ini-nota">Mostrando ' + r.contactos.length + ' de ' + r.total + ': buscá para encontrar al resto.</p>' : '');
  }
  function fichaContacto(p) {
    var v = voc();
    var h = cabCapa(p.cuenta, p.nombre, p.citas.length + ' cita' + (p.citas.length === 1 ? '' : 's') + ' · ' + p.ventas.length + ' venta' + (p.ventas.length === 1 ? '' : 's'));
    h += '<section class="fc-seccion"><h3 class="fin-h3">Datos</h3><dl class="ficha-datos">' + (p.telefono ? '<div><dt>Teléfono</dt><dd><a href="tel:' + esc(p.telefono.replace(/[^\d+]/g, '')) + '" style="color:inherit">' + esc(p.telefono) + '</a></dd></div>' : '') + (p.email ? '<div><dt>Email</dt><dd>' + esc(p.email) + '</dd></div>' : '') + '<div><dt>Último movimiento</dt><dd>' + (p.ultima ? corta(p.ultima) : '—') + '</dd></div></dl></section>';
    h += '<section class="fc-seccion"><h3 class="fin-h3">Citas</h3>' + (p.citas.length ? '<dl class="ficha-datos">' + p.citas.map(function (c) {
      var e = EST[c.estado] || EST.confirmada, r = c.resultado;
      return '<div><dt>' + corta(c.fecha) + ' · ' + hora(c.minuto) + ' · <span class="rend-estado" data-estado="' + e[1] + '">' + e[0] + '</span></dt><dd>' + esc(r ? [r.resultado ? RES[r.resultado] && RES[r.resultado]() : '', r.servicio, r.monto ? plata(r.monto) : '', r.notas].filter(Boolean).join(' · ') || 'Sin resultado cargado' : 'Sin resultado cargado') + '</dd></div>';
    }).join('') + '</dl>' : '<p class="vacio">Sin citas en los últimos 90 días.</p>') + '</section>';
    h += '<section class="fc-seccion"><h3 class="fin-h3">Ventas</h3>' + (p.ventas.length ? '<dl class="ficha-datos">' + p.ventas.map(function (x) {
      return '<div><dt>' + corta(x.fecha) + '</dt><dd>' + esc([x.servicio, plata(x.monto)].filter(Boolean).join(' · ')) + '</dd></div>';
    }).join('') + '</dl>' : '<p class="vacio">Sin ventas cargadas.</p>') + '</section>';
    capa(h);
  }
  var RES = {
    avanza: function () { return voc().citaPrincipal + ' agendada'; }, pendiente: function () { return 'Pendiente de ' + voc().compromiso.toLowerCase(); },
    seguimiento: function () { return 'En seguimiento'; }, no_interesado: function () { return 'No interesado'; }, perdido: function () { return 'Perdido'; }, no_califica: function () { return 'No califica'; }
  };

  // ---- Cargar y eventos ----
  function error(e) { if (V.menu) principal('<section class="caja ini-bloque"><h3 class="fin-h3">No se pudo cargar</h3><p class="e52" style="margin:0">' + esc(e.message) + '.</p></section>'); }
  function cargar() {
    var menu = V.menu, negocio = V.negocio;
    if (menu === 'pacientes') {
      return api('/contactos' + (V.q ? '?q=' + encodeURIComponent(V.q) : '')).then(function (r) {
        if (V.menu !== menu || V.negocio !== negocio) return;
        V.contactos = r;
        var lista = document.getElementById('v-lista');
        if (lista && document.getElementById('v-q')) lista.innerHTML = listaContactos(r); else principal(vistaContactos(r));
      }).catch(error);
    }
    var q = V.mes ? '?desde=' + rangoMes(V.mes)[0] + '&hasta=' + rangoMes(V.mes)[1] : '';
    return api('/ventas' + q).then(function (r) {
      if (V.menu !== menu || V.negocio !== negocio) return;
      V.datos = r; if (!V.mes) V.mes = r.desde.slice(0, 7);
      principal(vistaBitacora(r));
    }).catch(error);
  }
  function mostrar(menu, negocio) {
    if (V.negocio !== negocio) { V.mes = null; V.q = ''; }
    V.menu = menu; V.negocio = negocio;
    if (menu === 'pacientes') principal(vistaContactos({ contactos: [], total: 0 }));
    cargar();
  }
  document.addEventListener('click', function (e) {
    var t = e.target.closest ? e.target : null; if (!t || !V.menu) return;
    var b;
    if (t.closest('[data-v-cerrar]')) { capa(''); return; }
    if ((b = t.closest('[data-v-contacto]'))) { fichaContacto(V.contactos.contactos[+b.getAttribute('data-v-contacto')]); SONIDO.sonar('menu'); return; }
    if (!V.datos || V.menu !== 'bitacora') return;
    if ((b = t.closest('[data-v-mes]'))) { var n = +b.getAttribute('data-v-mes'); V.mes = n === 0 ? null : moverMes(V.mes, n); cargar(); return; }
    if (t.closest('[data-v-nueva]')) { formVenta(null); SONIDO.sonar('menu'); return; }
    if ((b = t.closest('[data-v-editar]'))) { var id = +b.getAttribute('data-v-editar'); formVenta(V.datos.ventas.filter(function (x) { return x.id === id; })[0]); return; }
    if ((b = t.closest('[data-v-borrar]'))) {
      if (b.getAttribute('data-confirmar') !== '1') { b.setAttribute('data-confirmar', '1'); b.textContent = 'Tocá de nuevo para quitarla'; return; }
      api('/ventas/' + b.getAttribute('data-v-borrar'), 'PATCH', { borrar: true }).then(function () { capa(''); SONIDO.sonar('listo'); cargar(); });
    }
  });
  document.addEventListener('input', function (e) {
    if (e.target.id !== 'v-q') return;
    V.q = e.target.value; clearTimeout(V.timer); V.timer = setTimeout(cargar, 250);
  });
  document.addEventListener('submit', function (e) {
    if (e.target.id !== 'v-form') return;
    e.preventDefault();
    var f = e.target, id = f.getAttribute('data-id'), num = function (s) { s = String(s || '').trim().replace(',', '.'); return s === '' ? null : Number(s); };
    var cuerpo = { cuenta_id: +f.cuenta_id.value, fecha: f.fecha.value, contacto: f.contacto.value, servicio: f.servicio.value, monto: num(f.monto.value), notas: f.notas.value };
    if (f.costo) cuerpo.costo = num(f.costo.value);
    if (f.vendedor) cuerpo.vendedor = f.vendedor.value;
    if (f.comision_cobrada) cuerpo.comision_cobrada = f.comision_cobrada.checked;
    if (!(cuerpo.monto >= 0) || (cuerpo.costo != null && !(cuerpo.costo >= 0))) { document.getElementById('v-msg').textContent = 'Los montos tienen que ser números.'; return; }
    api(id ? '/ventas/' + id : '/ventas', id ? 'PATCH' : 'POST', cuerpo).then(function () { capa(''); SONIDO.sonar('listo'); cargar(); })
      .catch(function (err) { document.getElementById('v-msg').textContent = 'No se pudo guardar: ' + err.message + '.'; });
  });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && document.getElementById('v-capa') && document.getElementById('v-capa').innerHTML) capa(''); });

  window.MENUS_API = window.MENUS_API || {};
  window.MENUS_API.bitacora = mostrar;
  window.MENUS_API.pacientes = mostrar;
  var salir = window.MENUS_API_SALIR;
  window.MENUS_API_SALIR = function () { V.menu = null; V.datos = null; capa(''); if (salir) salir(); };
})();
