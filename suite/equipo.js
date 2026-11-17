// Ficha de cuentas (#recursos) con las fuentes elegidas, Usuarios (#usuarios), Rendimiento (#rendimiento),
// Reportes semanales (#semanal) y Conversaciones (#conversaciones).
(function () {
  var E = { menu: null, negocio: null, datos: null, conv: null, cuentaConv: null, fuentes: null, editando: null };
  var TIPOS_CAL = { calificacion: 'Llamada de calificación / evaluación', principal: 'Cita principal', entrada: 'Primer contacto' };
  var ROLES = { admin: 'Admin', vendedor: 'Closer / setter', operador: 'Equipo de la cuenta', cuenta: 'Cliente (portal)' };
  var FICHA = [['contacto', 'Contacto y doctor / realtor'], ['servicios', 'Servicios y precios'], ['condiciones', 'Condiciones comerciales'], ['califica', 'Quién califica'], ['objeciones', 'Objeciones y respuestas'], ['logistica', 'Logística (dirección, horarios)'], ['material', 'Material (links)']];

  function S() { return window.SUITE; }
  function esc(s) { return S().esc(s == null ? '' : s); }
  function us(x) { return x == null ? '—' : S().us(x); }
  function cfg() { return NEGOCIOS[E.negocio]; }
  function pctTxt(x) { return x == null ? '—' : Math.round(x) + '%'; }
  function corta(s) { if (!s) return '—'; var m = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'], p = s.slice(0, 10).split('-'); return +p[2] + ' ' + m[+p[1] - 1]; }
  function api(ruta, metodo, cuerpo, global) {
    var op = { method: metodo || 'GET', credentials: 'same-origin', headers: {} };
    if (cuerpo) { op.headers['Content-Type'] = 'application/json'; op.headers['X-CSRF'] = S().sesion().csrf; op.body = JSON.stringify(cuerpo); }
    return fetch('/api' + (global ? '' : '/' + E.negocio) + ruta, op).then(function (r) {
      if (r.status === 401) { location.href = '/ingresar'; throw new Error('sin sesión'); }
      if (!r.ok) throw new Error(r.status === 400 ? 'Revisá los datos' : r.status === 409 ? 'Ese email ya existe' : r.status === 403 ? 'No tenés permiso' : 'Error ' + r.status);
      return r.json();
    });
  }
  function principal(h) { document.getElementById('principal').innerHTML = h; window.dcPostRender(); }
  function capa(h) {
    var c = document.getElementById('e-capa');
    if (!c) { c = document.createElement('div'); c.id = 'e-capa'; document.body.appendChild(c); }
    c.innerHTML = h ? '<div class="cal-velo" data-e-cerrar></div><aside class="fc-capa ficha-cita" role="dialog" aria-modal="true" style="width:min(620px,100vw)">' + h + '</aside>' : '';
  }
  function cab(t, sub, boton) { return '<header><div class="e19"><h1 class="titulo-1">' + esc(t) + '</h1><span class="e30">' + sub + '</span></div>' + (boton ? '<div class="cab-filtros e36">' + boton + '</div>' : '') + '</header>'; }
  function tabla(c, filas, vacio) {
    return '<div class="rend-scroll"><table class="rend-tabla"><thead><tr>' + c.map(function (x) { return '<th' + (x[1] ? ' class="rend-num"' : '') + '>' + esc(x[0]) + '</th>'; }).join('') + '</tr></thead><tbody>' +
      (filas.length ? filas.join('') : '<tr><td colspan="' + c.length + '" class="e11">' + esc(vacio) + '</td></tr>') + '</tbody></table></div>';
  }
  function cerrarCabeza(t, sub) { return '<div class="fc-cabeza"><div class="e19" style="flex:1;gap:8px"><h2 class="fc-titulo">' + esc(t) + '</h2>' + (sub ? '<span class="e30">' + sub + '</span>' : '') + '</div><button type="button" class="fc-volver" data-e-cerrar aria-label="Cerrar">✕</button></div>'; }

  // ---------- Ficha de cuentas ----------
  function vistaCuentas(lista) {
    var c = cfg(), v = c.voc, admin = S().sesion().rol === 'admin';
    var h = cab('Ficha de ' + v.cuentas.toLowerCase(), 'Cada ' + esc(v.cuenta.toLowerCase()) + ' con su subcuenta de GHL, su cuenta publicitaria, qué calendarios y campañas cuentan, su moneda y su plan', admin ? '<button type="button" class="fin-boton" data-e-cuenta="nueva">+ Nueva ' + esc(v.cuenta.toLowerCase()) + '</button>' : '');
    var filas = lista.map(function (x) {
      var fuentes = (x.calendarios || []).length + ' cal. · ' + ((x.campanas || []).length ? x.campanas.length + ' camp.' : 'todas las campañas');
      return '<tr data-e-cuenta="' + x.id + '" style="cursor:pointer"><td><strong>' + esc(x.nombre) + '</strong>' + (x.propia ? ' <span class="rend-estado" data-estado="cumple">Propia</span>' : '') + (x.activo ? '' : ' <span class="rend-estado">Inactiva</span>') + '</td><td class="e30">' + esc(x.grupo || '') + '</td>' +
        '<td>' + (x.crm_location_id ? '<span class="rend-estado" data-estado="' + (x.tiene_token ? 'cumple' : 'cerca') + '">' + (x.tiene_token ? 'Conectada' : 'Falta token') + '</span>' : '<span class="rend-estado" data-estado="falta">Sin subcuenta</span>') + '</td>' +
        '<td>' + ((x.meta_cuentas || []).length ? esc(x.meta_cuentas.join(', ')) : '—') + '</td><td>' + fuentes + '</td><td>' + esc(x.moneda || 'USD') + '</td><td class="rend-num">' + (x.plan_fee ? us(x.plan_fee) + '/mes' : x.plan_setup ? us(x.plan_setup) + ' setup' : '—') + '</td></tr>';
    });
    h += '<div class="caja">' + tabla([[v.cuenta], ['Grupo'], ['GHL'], ['Meta'], ['Fuentes'], ['Moneda'], ['Plan', 1]], filas, 'Todavía no hay ' + v.cuentas.toLowerCase() + '.') + '</div>';
    h += '<p class="ini-nota">La subcuenta y la cuenta publicitaria pueden tener cosas de otros negocios: en cada ficha elegí qué calendarios y qué campañas cuentan. Si no elegís calendarios, se reconocen por el nombre; si no elegís campañas, cuentan todas.</p>';
    return h;
  }
  function editorCuenta(x) {
    var c = cfg(), v = c.voc, nueva = !x, admin = S().sesion().rol === 'admin';
    x = x || { nombre: '', grupo: 'Activas', propia: false, crm_location_id: '', meta_cuentas: [], calendarios: [], campanas: [], moneda: c.id === 'plastia' ? 'COP' : 'USD', plan_setup: c.cobro.setup, plan_fee: c.cobro.fee || null, alta: new Date().toISOString().slice(0, 10), activo: true, ficha: {} };
    E.editando = JSON.parse(JSON.stringify(x));
    var f = x.ficha || {};
    var h = cerrarCabeza(nueva ? 'Nueva ' + v.cuenta.toLowerCase() : x.nombre, nueva ? '' : (x.propia ? 'Cuenta propia de ' + esc(c.corto) : esc(x.grupo || '')));
    h += '<form class="e22" id="e-form-cuenta" data-id="' + (nueva ? '' : x.id) + '">';
    if (admin) {
      h += '<section class="fc-seccion"><h3 class="fin-h3">Datos</h3><div class="fc-rapidos">' +
        '<label class="ct-dato ct-dato--ancho">Nombre<input class="ct-input" name="nombre" required value="' + esc(x.nombre) + '"></label>' +
        '<label class="ct-dato">Grupo<input class="ct-input" name="grupo" value="' + esc(x.grupo || '') + '"></label>' +
        '<label class="ct-dato">Moneda en que vende<select class="ct-input" name="moneda">' + ['USD', 'COP', 'MXN'].map(function (m) { return '<option' + (m === x.moneda ? ' selected' : '') + '>' + m + '</option>'; }).join('') + '</select></label>' +
        '<label class="ct-dato">Setup (USD)<input class="ct-input" name="plan_setup" inputmode="decimal" value="' + esc(x.plan_setup == null ? '' : x.plan_setup) + '"></label>' +
        '<label class="ct-dato">Fee mensual (USD)<input class="ct-input" name="plan_fee" inputmode="decimal" value="' + esc(x.plan_fee == null ? '' : x.plan_fee) + '" placeholder="sin fee"></label>' +
        '<label class="ct-dato">Alta<input class="ct-input" type="date" name="alta" value="' + esc(x.alta || '') + '"></label>' +
        '<label class="ct-dato">Baja<input class="ct-input" type="date" name="baja" value="' + esc(x.baja || '') + '"></label>' +
        '<label class="ct-dato">Objetivo de costo por cita (opcional)<input class="ct-input" name="objetivo_costo_cita" inputmode="decimal" value="' + esc(x.objetivo_costo_cita == null ? '' : x.objetivo_costo_cita) + '"></label>' +
        '<label class="e91"><input type="checkbox" name="propia"' + (x.propia ? ' checked' : '') + '> Es la cuenta propia de ' + esc(c.corto) + ' (sus campañas y su embudo de venta)</label>' +
        '<label class="e91"><input type="checkbox" name="activo"' + (x.activo !== false ? ' checked' : '') + '> Activa</label></div></section>';
      h += '<section class="fc-seccion"><h3 class="fin-h3">Fuentes de datos</h3><div class="fc-rapidos">' +
        '<label class="ct-dato ct-dato--ancho">ID de la subcuenta de GHL (location id)<input class="ct-input" name="crm_location_id" value="' + esc(x.crm_location_id || '') + '"></label>' +
        '<label class="ct-dato ct-dato--ancho">Cuentas publicitarias de Meta (act_…, separadas por coma)<input class="ct-input" name="meta_cuentas" value="' + esc((x.meta_cuentas || []).join(', ')) + '"></label></div>' +
        (nueva ? '<p class="ini-nota">Guardá la cuenta y volvé a abrirla para elegir calendarios y campañas.</p>' : '<button type="button" class="tb-boton" data-e-fuentes="' + x.id + '">Traer calendarios y campañas</button><div id="e-fuentes">' + fuentesHtml() + '</div>') + '</section>';
    }
    h += '<section class="fc-seccion"><h3 class="fin-h3">Ficha comercial</h3><p class="e12" style="margin:0">Lo que hace falta para vender por la cuenta: lo ve el ' + esc(v.vendedor.toLowerCase()) + '.</p>' +
      FICHA.map(function (k) { return '<label class="ct-dato">' + esc(k[1]) + '<textarea class="ct-input ct-input--largo" name="f_' + k[0] + '" rows="3">' + esc(f[k[0]] || '') + '</textarea></label>'; }).join('') + '</section>';
    h += (admin ? '<button type="submit" class="fin-boton" style="width:100%">Guardar</button>' : '') + '<p class="e12" id="e-msg" style="margin:0"></p></form>';
    capa(h);
  }
  function fuentesHtml() {
    var x = E.editando, fu = E.fuentes, h = '';
    var cal = (fu && fu.calendarios) || (x.calendarios || []).map(function (c) { return { id: c.id, nombre: c.nombre }; });
    var elegidos = {}; (x.calendarios || []).forEach(function (c) { elegidos[c.id] = c.tipo; });
    h += '<h4 class="ct-etq" style="margin:12px 0 6px">Calendarios de GHL que cuentan</h4>' + (cal.length ? '<div class="e33">' + cal.map(function (c) {
      return '<label class="ct-dato" style="flex-direction:row;align-items:center;gap:10px"><span style="flex:1;color:var(--texto)">' + esc(c.nombre || c.id) + (c.activo === false ? ' <span class="e12">(inactivo)</span>' : '') + '</span><select class="ct-input" style="width:auto" data-e-cal="' + esc(c.id) + '" data-nombre="' + esc(c.nombre || '') + '"><option value="">No cuenta</option>' +
        Object.keys(TIPOS_CAL).map(function (t) { return '<option value="' + t + '"' + (elegidos[c.id] === t ? ' selected' : '') + '>' + TIPOS_CAL[t] + '</option>'; }).join('') + '</select></label>';
    }).join('') + '</div>' : '<p class="vacio">Tocá «Traer calendarios y campañas» (necesita el token de la subcuenta).</p>');
    var camp = (fu && fu.campanas) || (x.campanas || []);
    var elegidas = {}; (x.campanas || []).forEach(function (c) { elegidas[c.id] = 1; });
    h += '<h4 class="ct-etq" style="margin:14px 0 6px">Campañas de Meta que cuentan <span class="e12">(ninguna marcada = todas)</span></h4>' + (camp.length ? '<div class="e33">' + camp.map(function (c) {
      return '<label class="e91"><input type="checkbox" data-e-camp="' + esc(c.id) + '" data-nombre="' + esc(c.nombre || '') + '"' + (elegidas[c.id] ? ' checked' : '') + '> ' + esc(c.nombre || c.id) + (c.estado ? ' <span class="e12">' + esc(c.estado.toLowerCase()) + '</span>' : '') + '</label>';
    }).join('') + '</div>' : '<p class="vacio">Sin campañas para mostrar (necesita el token de Meta).</p>');
    if (fu && fu.avisos && fu.avisos.length) h += '<p class="chat-aviso" style="margin-top:10px">' + fu.avisos.map(esc).join('<br>') + '</p>';
    return h;
  }

  // ---------- Usuarios ----------
  function vistaUsuarios(r) {
    var h = cab('Usuarios', 'Quién entra, con qué rol, a qué negocios y a qué cuentas. Nunca se borran: se desactivan.', '<button type="button" class="fin-boton" data-e-usuario="nuevo">+ Nuevo usuario</button>');
    var filas = r.usuarios.map(function (u) {
      return '<tr data-e-usuario="' + u.id + '" style="cursor:pointer"><td><strong>' + esc(u.nombre || u.email.split('@')[0]) + '</strong><br><span class="e12">' + esc(u.email) + '</span></td><td>' + esc(ROLES[u.rol] || u.rol) + '</td><td>' + esc(u.negocios.map(function (n) { return NEGOCIOS[n] ? NEGOCIOS[n].corto : n; }).join(' · ')) + '</td>' +
        '<td>' + (u.rol === 'admin' ? 'Todas' : u.cuentas.length + ' cuentas') + '</td><td><span class="rend-estado" data-estado="' + (u.activo ? 'cumple' : '') + '">' + (u.activo ? 'Activo' : 'Desactivado') + '</span></td><td class="e30">' + (u.ultimo_ingreso ? corta(u.ultimo_ingreso) : 'nunca') + '</td></tr>';
    });
    h += '<div class="caja">' + tabla([['Usuario'], ['Rol'], ['Negocios'], ['Cuentas'], ['Estado'], ['Último ingreso']], filas, 'Sin usuarios.') + '</div>';
    h += '<section class="caja ini-bloque"><h3 class="fin-h3">Seguridad</h3><ul class="e144"><li>Se entra solo con Google y solo con emails cargados acá y activos.</li><li>Cada admin ve y maneja solo sus negocios (Luis: TPA).</li><li>Closers, equipo de la cuenta y clientes ven solo las cuentas asignadas, nunca la cuenta propia ni las finanzas.</li><li>Cada cambio de metas, cuentas, ventas, cobros y usuarios queda en la auditoría.</li></ul></section>';
    return h;
  }
  function editorUsuario(u) {
    var r = E.datos, nuevo = !u, mios = Object.keys(r.cuentas);
    u = u || { email: '', nombre: '', rol: 'vendedor', negocios: [E.negocio], cuentas: [], activo: true };
    var h = cerrarCabeza(nuevo ? 'Nuevo usuario' : (u.nombre || u.email), nuevo ? '' : esc(u.email));
    h += '<form class="e22" id="e-form-usuario" data-id="' + (nuevo ? '' : u.id) + '"><div class="fc-rapidos">' +
      '<label class="ct-dato ct-dato--ancho">Email de Google<input class="ct-input" type="email" name="email" required value="' + esc(u.email) + '"' + (nuevo ? '' : ' readonly') + '></label>' +
      '<label class="ct-dato">Nombre<input class="ct-input" name="nombre" value="' + esc(u.nombre) + '"></label>' +
      '<label class="ct-dato">Rol<select class="ct-input" name="rol">' + Object.keys(ROLES).map(function (k) { return '<option value="' + k + '"' + (k === u.rol ? ' selected' : '') + '>' + ROLES[k] + '</option>'; }).join('') + '</select></label></div>' +
      '<div class="e115"><span class="ct-etq">Negocios</span>' + mios.map(function (n) { return '<label class="e91"><input type="checkbox" name="negocio" value="' + n + '"' + (u.negocios.indexOf(n) >= 0 ? ' checked' : '') + '> ' + esc(NEGOCIOS[n] ? NEGOCIOS[n].nombre : n) + '</label>'; }).join('') + '</div>' +
      '<div class="e115"><span class="ct-etq">Cuentas que ve (no admin)</span>' + mios.map(function (n) {
        return '<strong class="e12">' + esc(NEGOCIOS[n] ? NEGOCIOS[n].corto : n) + '</strong>' + r.cuentas[n].filter(function (c) { return !c.propia; }).map(function (c) { return '<label class="e91"><input type="checkbox" name="cuenta" value="' + c.id + '"' + (u.cuentas.indexOf(c.id) >= 0 ? ' checked' : '') + '> ' + esc(c.nombre) + '</label>'; }).join('');
      }).join('') + '</div>' +
      (nuevo ? '' : '<label class="e91"><input type="checkbox" name="activo"' + (u.activo ? ' checked' : '') + '> Activo</label>') +
      '<button type="submit" class="fin-boton" style="width:100%">Guardar</button><p class="e12" id="e-msg" style="margin:0"></p></form>';
    capa(h);
  }

  // ---------- Rendimiento ----------
  function vistaRendimiento(r) {
    var c = cfg(), v = c.voc, m = r.metas;
    var h = cab(S().sesion().rol === 'admin' ? 'Rendimiento de ' + v.vendedores.toLowerCase() : 'Mi rendimiento', 'Llamadas con resultado cargado, asistencia, cierres y comisión del mes' + (r.closer_pct ? ' (' + r.closer_pct + '% de la comisión de ' + esc(c.corto) + ')' : ''));
    function est(val, meta) { return val == null || !meta ? '' : val >= meta ? 'cumple' : val >= meta * 0.9 ? 'cerca' : 'falta'; }
    var filas = r.filas.map(function (x, i) {
      return '<tr><td><span class="rend-pos' + (i === 0 ? ' rend-pos--1' : '') + '">' + (i + 1) + '</span> <strong>' + esc(x.vendedor.split('@')[0]) + '</strong></td><td class="rend-num">' + x.llamadas + '</td>' +
        '<td class="rend-num"><span class="rend-estado" data-estado="' + est(x.pct_asistencia, m.pct_asistencia) + '">' + pctTxt(x.pct_asistencia) + '</span></td><td class="rend-num">' + x.califica + '</td><td class="rend-num">' + x.avanza + '</td>' +
        '<td class="rend-num"><span class="rend-estado" data-estado="' + est(x.pct_cierre, m.pct_cierre) + '">' + pctTxt(x.pct_cierre) + '</span></td><td class="rend-num">' + x.ventas + '</td><td class="rend-num">' + us(x.monto) + '</td><td class="rend-num"><strong>' + us(x.comision) + '</strong></td></tr>';
    });
    h += '<div class="caja">' + tabla([[v.vendedor], ['Llamadas', 1], ['% asistencia', 1], ['Califican', 1], [v.citasPrincipales, 1], ['% cierre', 1], ['Ventas', 1], ['Vendido', 1], ['Comisión', 1]], filas, 'Todavía nadie cargó resultados de llamadas este mes.') + '</div>';
    h += '<p class="ini-nota">Las tasas se pintan contra las metas de Indicadores (asistencia ' + (m.pct_asistencia ? Math.round(m.pct_asistencia) + '%' : 'sin meta') + ', cierre ' + (m.pct_cierre ? Math.round(m.pct_cierre) + '%' : 'sin meta') + '). La comisión sale de la bitácora: ventas con su ' + esc(v.vendedor.toLowerCase()) + ' cargado.</p>';
    return h;
  }

  // ---------- Reportes semanales ----------
  function vistaSemanal(r) {
    var h = cab('Reportes semanales', 'El reporte de los lunes por embudo: números de la semana, cuello de botella, ' + esc(cfg().voc.cuentas.toLowerCase()) + ' en rojo y los anuncios que mejor funcionaron');
    h += r.semanas.map(function (s, i) {
      var cambio = s.cambio_costo == null ? '' : ' <span class="pill var ' + (s.cambio_costo <= 0 ? 'bien' : 'mal') + '">' + (s.cambio_costo > 0 ? '+' : '−') + Math.abs(s.cambio_costo).toFixed(1) + '%</span>';
      return '<section class="caja ini-bloque"><div class="ini-bloque-cab"><h3 class="fin-h3">' + esc(s.embudo) + ' · semana del ' + corta(s.desde) + ' al ' + corta(s.hasta) + '</h3>' + (i === 0 ? '<span class="rend-estado" data-estado="cumple">Última</span>' : '') + '</div>' +
        '<div class="grilla" style="--n:4">' + [['Gasto', us(s.gasto)], ['Leads', String(s.leads)], ['Citas creadas', String(s.citas)], ['Costo por cita', (s.costo_cita == null ? '—' : us(s.costo_cita)) + cambio]].map(function (k) {
          return '<div class="e19"><span class="e11">' + k[0] + '</span><strong class="e118">' + k[1] + '</strong></div>';
        }).join('') + '</div>' +
        '<dl class="ficha-datos"><div><dt>Cuello de botella</dt><dd>' + esc(s.cuello || 'Ninguno: la semana está dentro de las metas.') + '</dd></div>' +
        '<div><dt>' + esc(cfg().voc.cuentas) + ' en rojo</dt><dd>' + esc(s.criticas.length ? s.criticas.join(', ') : 'Ninguna') + '</dd></div>' +
        '<div><dt>Anuncios que mejor funcionaron</dt><dd>' + (s.angulos.length ? s.angulos.map(function (a) { return esc(a.anuncio) + ' <span class="e12">(' + esc(a.cuenta) + ' · ' + a.citas + ' citas a ' + us(a.costo_cita) + ')</span>'; }).join('<br>') : 'Sin citas con anuncio en la semana.') + '</dd></div></dl></section>';
    }).join('');
    if (r.demo) h += '<p class="ini-nota">Datos de ejemplo hasta conectar GHL y Meta.</p>';
    return h;
  }

  // ---------- Conversaciones ----------
  function vistaConv(r) {
    var h = cab('Conversaciones', 'Los chats de GHL de cada ' + esc(cfg().voc.cuenta.toLowerCase()) + ' dentro de la suite');
    h += '<div class="cv-wrap"><div class="cv-lista"><div class="cv-filtros"><select class="cv-sel" id="e-conv-cuenta">' + r.cuentas.map(function (c) { return '<option value="' + c.id + '"' + (c.id === r.cuenta_id ? ' selected' : '') + '>' + esc(c.nombre) + '</option>'; }).join('') + '</select></div>' +
      '<div class="cv-items">' + (r.aviso ? '<p class="chat-aviso">' + esc(r.aviso) + '</p>' : '') + r.conversaciones.map(function (x) {
        return '<button type="button" class="cv-item' + (x.no_leidos ? ' cv-item--nuevo' : '') + (E.conv && E.conv.id === x.id ? ' cv-item--on' : '') + '" data-e-conv="' + esc(x.id) + '"><span class="cv-item-cab"><span class="cv-item-nombre">' + esc(x.nombre) + '</span>' + (x.no_leidos ? '<span class="cv-item-n">' + x.no_leidos + '</span>' : '') + '</span><span class="cv-item-ultimo">' + esc(x.ultimo) + '</span></button>';
      }).join('') + (!r.aviso && !r.conversaciones.length ? '<p class="cv-nada">Sin conversaciones.</p>' : '') + '</div></div>' +
      '<div class="cv-chat" id="e-chat">' + (E.conv ? '' : '<div class="cv-nada"><p>Elegí una conversación.</p></div>') + '</div></div>';
    return h;
  }
  function pintarChat(msgs, aviso) {
    var x = E.conv, el = document.getElementById('e-chat'); if (!el) return;
    el.innerHTML = '<div class="cv-cab"><span class="e47"><span class="cv-cab-nombre">' + esc(x.nombre) + '</span></span></div>' + (aviso ? '<p class="chat-aviso chat-aviso--mal">' + esc(aviso) + '</p>' : '') +
      '<div class="chat-hilo">' + (msgs.length ? msgs.map(function (m) { return '<div class="chat-msg chat-msg--' + (m.saliente ? 'out' : 'in') + '"><p class="chat-texto">' + esc(m.texto) + '</p><span class="chat-meta">' + (m.fecha ? corta(m.fecha) + ' ' + m.fecha.slice(11, 16) : '') + '</span></div>'; }).join('') : '<p class="chat-vacio">Sin mensajes.</p>') + '</div>' +
      '<form class="chat-escribir" id="e-chat-form"><textarea class="chat-caja" name="texto" rows="1" placeholder="Escribí un mensaje (SMS)"></textarea><button type="submit" class="chat-enviar">Enviar</button></form>';
    var hilo = el.querySelector('.chat-hilo'); hilo.scrollTop = hilo.scrollHeight;
  }

  // ---------- Cargar y eventos ----------
  function cargar() {
    var menu = E.menu, negocio = E.negocio, p;
    if (menu === 'recursos') p = api('/cuentas').then(function (l) { E.datos = l; return vistaCuentas(l); }).catch(function (e) {
      if (/permiso/.test(e.message)) return cab('Ficha de ' + cfg().voc.cuentas.toLowerCase(), 'Pedile al admin que cargue la ficha comercial de tus cuentas.');
      throw e;
    });
    else if (menu === 'usuarios') p = api('/usuarios', 'GET', null, true).then(function (r) { E.datos = r; return vistaUsuarios(r); });
    else if (menu === 'rendimiento') p = api('/rendimiento').then(vistaRendimiento);
    else if (menu === 'semanal') p = api('/semanal').then(vistaSemanal);
    else p = api('/conversaciones' + (E.cuentaConv ? '?cuenta_id=' + E.cuentaConv : '')).then(function (r) { E.datos = r; return vistaConv(r); });
    return p.then(function (h) { if (E.menu === menu && E.negocio === negocio) principal(h); })
      .catch(function (e) { if (E.menu) principal('<section class="caja ini-bloque"><h3 class="fin-h3">No se pudo cargar</h3><p class="e52" style="margin:0">' + esc(e.message) + '.</p></section>'); });
  }
  function mostrar(menu, negocio) { if (E.negocio !== negocio) { E.cuentaConv = null; E.conv = null; } E.menu = menu; E.negocio = negocio; cargar(); }
  function num(s) { s = String(s || '').trim(); if (/,/.test(s) && /\./.test(s)) s = s.replace(/\./g, ''); s = s.replace(',', '.'); return s === '' ? null : Number(s); }

  document.addEventListener('click', function (e) {
    var t = e.target.closest ? e.target : null; if (!t || !E.menu) return;
    var b;
    if (t.closest('[data-e-cerrar]')) { capa(''); E.fuentes = null; return; }
    if ((b = t.closest('[data-e-cuenta]'))) {
      var id = b.getAttribute('data-e-cuenta'); E.fuentes = null;
      editorCuenta(id === 'nueva' ? null : E.datos.filter(function (x) { return String(x.id) === id; })[0]); return;
    }
    if ((b = t.closest('[data-e-fuentes]'))) {
      b.textContent = 'Buscando…';
      api('/cuentas/' + b.getAttribute('data-e-fuentes') + '/fuentes').then(function (r) { E.fuentes = r; document.getElementById('e-fuentes').innerHTML = fuentesHtml(); b.textContent = 'Volver a traer'; })
        .catch(function (err) { b.textContent = 'No se pudo (' + err.message + ')'; });
      return;
    }
    if ((b = t.closest('[data-e-usuario]'))) { var u = b.getAttribute('data-e-usuario'); editorUsuario(u === 'nuevo' ? null : E.datos.usuarios.filter(function (x) { return String(x.id) === u; })[0]); return; }
    if ((b = t.closest('[data-e-conv]'))) {
      var cid = b.getAttribute('data-e-conv');
      E.conv = E.datos.conversaciones.filter(function (x) { return x.id === cid; })[0];
      Array.prototype.forEach.call(document.querySelectorAll('.cv-item'), function (el) { el.classList.toggle('cv-item--on', el === b); });
      api('/conversaciones/' + encodeURIComponent(cid) + '?cuenta_id=' + E.datos.cuenta_id).then(function (r) { pintarChat(r.mensajes, r.aviso); }).catch(function (err) { pintarChat([], err.message); });
    }
  });
  document.addEventListener('change', function (e) { if (e.target.id === 'e-conv-cuenta') { E.cuentaConv = +e.target.value; E.conv = null; cargar(); } });
  document.addEventListener('submit', function (e) {
    var f = e.target, msg = function (txt) { var m = document.getElementById('e-msg'); if (m) m.textContent = txt; };
    var ok = function () { capa(''); E.fuentes = null; SONIDO.sonar('listo'); cargar(); };
    if (f.id === 'e-form-cuenta') {
      e.preventDefault();
      var id = f.getAttribute('data-id'), ficha = {};
      FICHA.forEach(function (k) { var v = f['f_' + k[0]].value.trim(); if (v) ficha[k[0]] = v; });
      var cuerpo = { ficha: ficha };
      if (f.nombre) {
        cuerpo.nombre = f.nombre.value; cuerpo.grupo = f.grupo.value; cuerpo.moneda = f.moneda.value; cuerpo.plan_setup = num(f.plan_setup.value); cuerpo.plan_fee = num(f.plan_fee.value);
        cuerpo.alta = f.alta.value || null; cuerpo.baja = f.baja.value || null; cuerpo.objetivo_costo_cita = num(f.objetivo_costo_cita.value);
        cuerpo.propia = f.propia.checked; cuerpo.activo = f.activo.checked; cuerpo.crm_location_id = f.crm_location_id.value.trim();
        cuerpo.meta_cuentas = f.meta_cuentas.value.split(',').map(function (s) { return s.trim(); }).filter(Boolean);
        if (document.querySelector('[data-e-cal]') || document.querySelector('[data-e-camp]')) {
          cuerpo.calendarios = Array.prototype.filter.call(document.querySelectorAll('[data-e-cal]'), function (s) { return s.value; }).map(function (s) { return { id: s.getAttribute('data-e-cal'), nombre: s.getAttribute('data-nombre'), tipo: s.value }; });
          cuerpo.campanas = Array.prototype.filter.call(document.querySelectorAll('[data-e-camp]'), function (c) { return c.checked; }).map(function (c) { return { id: c.getAttribute('data-e-camp'), nombre: c.getAttribute('data-nombre') }; });
        }
      }
      api(id ? '/cuentas/' + id : '/cuentas', id ? 'PATCH' : 'POST', cuerpo).then(ok).catch(function (err) { msg('No se pudo guardar: ' + err.message + '.'); });
    }
    if (f.id === 'e-form-usuario') {
      e.preventDefault();
      var uid = f.getAttribute('data-id');
      var cu = { email: f.email.value, nombre: f.nombre.value, rol: f.rol.value,
        negocios: Array.prototype.filter.call(f.querySelectorAll('[name=negocio]'), function (c) { return c.checked; }).map(function (c) { return c.value; }),
        cuentas: Array.prototype.filter.call(f.querySelectorAll('[name=cuenta]'), function (c) { return c.checked; }).map(function (c) { return +c.value; }) };
      if (f.activo) cu.activo = f.activo.checked;
      if (uid) delete cu.email;
      api(uid ? '/usuarios/' + uid : '/usuarios', uid ? 'PATCH' : 'POST', cu, true).then(ok).catch(function (err) { msg('No se pudo guardar: ' + err.message + '.'); });
    }
    if (f.id === 'e-chat-form') {
      e.preventDefault();
      var texto = f.texto.value.trim(); if (!texto || !E.conv) return;
      var btn = f.querySelector('button'); btn.setAttribute('aria-disabled', 'true');
      api('/conversaciones/' + encodeURIComponent(E.conv.id), 'POST', { texto: texto, contacto_id: E.conv.contacto_id, cuenta_id: E.datos.cuenta_id }).then(function () {
        SONIDO.sonar('listo');
        return api('/conversaciones/' + encodeURIComponent(E.conv.id) + '?cuenta_id=' + E.datos.cuenta_id).then(function (r) { pintarChat(r.mensajes, r.aviso); });
      }).catch(function (err) { btn.removeAttribute('aria-disabled'); alert('No se pudo enviar: ' + err.message); });
    }
  });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') { var c = document.getElementById('e-capa'); if (c && c.innerHTML) { capa(''); E.fuentes = null; } } });

  window.MENUS_API = window.MENUS_API || {};
  ['recursos', 'usuarios', 'rendimiento', 'semanal', 'conversaciones'].forEach(function (k) { window.MENUS_API[k] = mostrar; });
  var salir = window.MENUS_API_SALIR;
  window.MENUS_API_SALIR = function () { E.menu = null; capa(''); if (salir) salir(); };
})();
