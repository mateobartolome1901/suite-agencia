// Tableros y listas: Tareas (#tareas), Tablero de edición (#tablero-edicion), Guiones (#guiones), Storyboards (#storyboards)
// y Estilos de edición (#estilos). Una sola API (/api/<negocio>/items?tipo=…) y las clases originales tb-* y sb-*.
(function () {
  var MENU_TIPO = { tareas: 'tarea', 'tablero-edicion': 'video', guiones: 'guion', storyboards: 'storyboard', estilos: 'estilo' };
  var COLS = {
    tarea: { por_hacer: 'Por hacer', haciendo: 'Haciendo', esperando: 'Esperando', hecho: 'Hecho' },
    video: { guiones: 'Guiones', por_editar: 'Por editar', storyboard: 'Storyboard', correccion: 'En corrección', editando: 'Editando', editados: 'Editados' },
    guion: { borrador: 'Borrador', para_revisar: 'Para revisar', aprobado: 'Aprobado', descartado: 'Descartado' },
    storyboard: { pendiente: 'Pendientes', nuevo: 'Nuevos', corregido: 'Corregidos', terminado: 'Terminados' },
    estilo: { activo: 'Activos', archivado: 'Archivados' }
  };
  var TITULO = { tarea: ['Tareas', 'Tablero del equipo: arrastrá las tarjetas entre columnas. Las de hoy y las vencidas aparecen en el Inicio.'],
    video: ['Tablero de edición', 'El flujo de cada video, del guion al video editado, con su costo estimado.'],
    guion: ['Guiones', 'Los guiones de los videos: ángulo, cuenta y texto. Al aprobarlos pasan al Tablero de edición.'],
    storyboard: ['Storyboards', 'Revisar el borrador de cada video antes de editarlo: escenas, notas, aprobar o mandar a corregir.'],
    estilo: ['Estilos de edición', 'Catálogo de estilos: guía escrita, preset y link de ejemplo.'] };
  // Campos de cada tipo (además de título, columna, responsable y fecha): [clave, etiqueta, tipo]
  var CAMPOS = {
    tarea: [['notas', 'Notas', 'largo'], ['checklist', 'Checklist (una línea por paso; «x » adelante = hecho)', 'largo'], ['prioridad', 'Prioridad', ['', 'alta', 'media', 'baja']]],
    video: [['cuenta', 'Cuenta', 'texto'], ['angulo', 'Ángulo', 'texto'], ['guion', 'Guion', 'largo'], ['link', 'Link del material o del video', 'texto'], ['costo', 'Costo estimado (USD)', 'texto']],
    guion: [['cuenta', 'Cuenta', 'texto'], ['angulo', 'Ángulo', 'texto'], ['estilo', 'Estilo de edición', 'texto'], ['texto', 'Guion', 'muylargo']],
    storyboard: [['cuenta', 'Cuenta', 'texto'], ['link', 'Link del borrador', 'texto'], ['escenas', 'Escenas (una por línea)', 'largo'], ['notas', 'Notas para corregir', 'largo']],
    estilo: [['descripcion', 'Guía escrita', 'largo'], ['preset', 'Preset (nombre o archivo)', 'texto'], ['link', 'Link de ejemplo', 'texto']]
  };
  var T = { menu: null, negocio: null, tipo: null, datos: null, filtro: null, arrastrando: null };

  function S() { return window.SUITE; }
  function esc(s) { return S().esc(s == null ? '' : s); }
  function hoyIso() { return new Date().toISOString().slice(0, 10); }
  function corta(s) { var m = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'], p = s.split('-'); return +p[2] + ' ' + m[+p[1] - 1]; }
  function iniciales(s) { return (s || '?').replace(/@.*/, '').split(/[\s._-]+/).filter(Boolean).slice(0, 2).map(function (x) { return x[0].toUpperCase(); }).join(''); }
  function api(ruta, metodo, cuerpo) {
    var op = { method: metodo || 'GET', credentials: 'same-origin', headers: {} };
    if (cuerpo) { op.headers['Content-Type'] = 'application/json'; op.headers['X-CSRF'] = S().sesion().csrf; op.body = JSON.stringify(cuerpo); }
    return fetch('/api/' + T.negocio + ruta, op).then(function (r) {
      if (r.status === 401) { location.href = '/ingresar'; throw new Error('sin sesión'); }
      if (!r.ok) throw new Error(r.status === 400 ? 'Revisá los datos' : 'Error ' + r.status);
      return r.json();
    });
  }
  function principal(h) { document.getElementById('principal').innerHTML = h; window.dcPostRender(); }
  function capa(h) {
    var c = document.getElementById('t-capa');
    if (!c) { c = document.createElement('div'); c.id = 't-capa'; document.body.appendChild(c); }
    c.innerHTML = h ? '<div class="cal-velo" data-t-cerrar></div><aside class="fc-capa ficha-cita" role="dialog" aria-modal="true">' + h + '</aside>' : '';
  }

  function chips(x) {
    var d = x.datos || {}, h = '';
    if (x.vence) { var est = x.vence < hoyIso() && x.columna !== 'hecho' ? 'vencida' : x.vence === hoyIso() ? 'hoy' : ''; h += '<span class="tb-chip' + (est ? ' tb-chip--' + est : '') + '">' + corta(x.vence) + '</span>'; }
    if (d.prioridad) h += '<span class="tb-chip tb-chip--' + d.prioridad + '">' + esc(d.prioridad) + '</span>';
    if (d.cuenta) h += '<span class="tb-chip tb-chip--cli">' + esc(d.cuenta) + '</span>';
    if (d.angulo) h += '<span class="tb-chip">' + esc(d.angulo) + '</span>';
    if (d.costo) h += '<span class="tb-chip">US$' + esc(d.costo) + '</span>';
    if (d.checklist) { var l = d.checklist.split('\n').filter(function (s) { return s.trim(); }), hechos = l.filter(function (s) { return /^x\s/i.test(s.trim()); }).length; if (l.length) h += '<span class="tb-chip' + (hechos === l.length ? ' tb-chip--ok' : '') + '">✓ ' + hechos + '/' + l.length + '</span>'; }
    return h;
  }
  function tarjeta(x) {
    return '<article class="tb-card' + (x.columna === 'hecho' ? ' tb-card--hecha' : '') + '" draggable="true" data-t-item="' + x.id + '"><div class="tb-card-fila"><span class="tb-card-tit">' + esc(x.titulo) + '</span>' +
      (x.responsable ? '<span class="tb-avatar" title="' + esc(x.responsable) + '">' + esc(iniciales(x.responsable)) + '</span>' : '') + '</div>' +
      (chips(x) ? '<div class="tb-card-fila" style="flex-wrap:wrap;gap:4px">' + chips(x) + '</div>' : '') + '</article>';
  }
  function vista(r) {
    var tipo = T.tipo, tit = TITULO[tipo];
    var h = '<header><div class="e19"><h1 class="titulo-1">' + esc(tit[0]) + '</h1><span class="e30">' + esc(tit[1]) + '</span></div><div class="cab-filtros e36"><button type="button" class="fin-boton" data-t-nuevo="' + r.columnas[0] + '">+ Nueva</button></div></header>';
    if (tipo === 'storyboard' || tipo === 'estilo') {
      var lista = r.items.filter(function (x) { return !T.filtro || x.columna === T.filtro; });
      h += '<div class="sb-filtros">' + [null].concat(r.columnas).map(function (c) {
        var n = c ? r.items.filter(function (x) { return x.columna === c; }).length : r.items.length;
        return '<button type="button" class="sb-pil' + (T.filtro === c ? ' sb-pil--on' : '') + '" data-t-filtro="' + (c || '') + '">' + (c ? COLS[tipo][c] : 'Todos') + ' <span class="sb-pil-n">' + n + '</span></button>';
      }).join('') + '</div>';
      h += '<div class="sb-items">' + (lista.length ? lista.map(function (x) {
        var d = x.datos || {};
        return '<button type="button" class="sb-item' + (x.columna === 'pendiente' ? ' sb-item--revisar' : '') + '" data-t-item="' + x.id + '" style="grid-template-columns:minmax(0,1fr) auto;text-align:left;font:inherit;color:inherit;cursor:pointer"><span class="sb-item-txt"><span class="sb-item-tit">' + esc(x.titulo) + '</span>' +
          '<span class="sb-item-sub">' + esc([d.cuenta, d.preset, (d.escenas || '').split('\n').filter(Boolean).length ? (d.escenas.split('\n').filter(Boolean).length + ' escenas') : '', d.descripcion ? d.descripcion.slice(0, 120) : ''].filter(Boolean).join(' · ')) + '</span></span>' +
          '<span class="rend-estado" data-estado="' + ({ terminado: 'cumple', corregido: '', nuevo: 'cerca', pendiente: 'cerca', activo: 'cumple' }[x.columna] || '') + '">' + COLS[tipo][x.columna] + '</span></button>';
      }).join('') : '<p class="vacio">Nada por acá todavía.</p>') + '</div>';
      return h;
    }
    h += '<div class="tb-tablero">' + r.columnas.map(function (c) {
      var lista = r.items.filter(function (x) { return x.columna === c; });
      return '<section class="tb-col" data-t-col="' + c + '"><div class="tb-col-cab"><span class="tb-col-nombre">' + COLS[tipo][c] + '</span><span class="tb-col-n">' + lista.length + '</span></div>' +
        '<div class="tb-tarjetas">' + lista.map(tarjeta).join('') + '</div><button type="button" class="tb-anadir" data-t-nuevo="' + c + '">+ Añadir tarjeta</button></section>';
    }).join('') + '</div>';
    return h;
  }
  function editor(x, columna) {
    var tipo = T.tipo, d = (x && x.datos) || {}, nuevo = !x;
    var h = '<div class="fc-cabeza"><div class="e19" style="flex:1"><span class="fc-eyebrow">' + esc(TITULO[tipo][0]) + '</span><h2 class="fc-titulo">' + (nuevo ? 'Nueva' : esc(x.titulo)) + '</h2></div><button type="button" class="fc-volver" data-t-cerrar aria-label="Cerrar">✕</button></div>';
    h += '<form class="e22" id="t-form" data-id="' + (nuevo ? '' : x.id) + '"><div class="fc-rapidos">' +
      '<label class="ct-dato ct-dato--ancho">Título<input class="ct-input" name="titulo" required maxlength="300" value="' + esc(nuevo ? '' : x.titulo) + '"></label>' +
      '<label class="ct-dato">Columna<select class="ct-input" name="columna">' + Object.keys(COLS[tipo]).map(function (c) { return '<option value="' + c + '"' + (c === (nuevo ? columna : x.columna) ? ' selected' : '') + '>' + COLS[tipo][c] + '</option>'; }).join('') + '</select></label>' +
      '<label class="ct-dato">Fecha<input class="ct-input" type="date" name="vence" value="' + esc(nuevo ? '' : (x.vence || '')) + '"></label>' +
      '<label class="ct-dato ct-dato--ancho">Responsable<input class="ct-input" name="responsable" maxlength="200" value="' + esc(nuevo ? '' : x.responsable) + '" placeholder="nombre o email"></label>';
    CAMPOS[tipo].forEach(function (c) {
      var v = d[c[0]] == null ? '' : d[c[0]];
      if (Array.isArray(c[2])) h += '<label class="ct-dato">' + esc(c[1]) + '<select class="ct-input" name="d_' + c[0] + '">' + c[2].map(function (o) { return '<option' + (o === v ? ' selected' : '') + '>' + esc(o) + '</option>'; }).join('') + '</select></label>';
      else if (c[2] === 'texto') h += '<label class="ct-dato">' + esc(c[1]) + '<input class="ct-input" name="d_' + c[0] + '" value="' + esc(v) + '"></label>';
      else h += '<label class="ct-dato ct-dato--ancho">' + esc(c[1]) + '<textarea class="ct-input ct-input--largo" name="d_' + c[0] + '" rows="' + (c[2] === 'muylargo' ? 14 : 4) + '">' + esc(v) + '</textarea></label>';
    });
    h += '</div><button type="submit" class="fin-boton" style="width:100%">Guardar</button><p class="e12" id="t-msg" style="margin:0">' + (nuevo ? '' : 'Última edición: ' + esc(x.quien || '')) + '</p>' +
      (nuevo ? '' : '<button type="button" class="tb-boton tb-boton--peligro" data-t-borrar="' + x.id + '" style="align-self:flex-start">Archivar</button>') + '</form>';
    capa(h);
  }

  function cargar() {
    var menu = T.menu, negocio = T.negocio;
    return api('/items?tipo=' + T.tipo).then(function (r) {
      if (T.menu !== menu || T.negocio !== negocio) return;
      T.datos = r; principal(vista(r));
    }).catch(function (e) { if (T.menu) principal('<section class="caja ini-bloque"><h3 class="fin-h3">No se pudo cargar</h3><p class="e52" style="margin:0">' + esc(e.message) + '.</p></section>'); });
  }
  function mostrar(menu, negocio) { T.menu = menu; T.negocio = negocio; T.tipo = MENU_TIPO[menu]; T.filtro = null; cargar(); }
  function buscar(id) { return T.datos.items.filter(function (x) { return x.id === id; })[0]; }

  document.addEventListener('click', function (e) {
    var t = e.target.closest ? e.target : null; if (!t || !T.menu) return;
    var b;
    if (t.closest('[data-t-cerrar]')) { capa(''); return; }
    if ((b = t.closest('[data-t-nuevo]'))) { editor(null, b.getAttribute('data-t-nuevo')); return; }
    if ((b = t.closest('[data-t-filtro]'))) { T.filtro = b.getAttribute('data-t-filtro') || null; principal(vista(T.datos)); return; }
    if ((b = t.closest('[data-t-borrar]'))) { api('/items/' + b.getAttribute('data-t-borrar'), 'PATCH', { borrar: true }).then(function () { capa(''); cargar(); }); return; }
    if ((b = t.closest('[data-t-item]'))) { editor(buscar(+b.getAttribute('data-t-item'))); SONIDO.sonar('menu'); }
  });
  // Arrastrar tarjetas entre columnas
  document.addEventListener('dragstart', function (e) { var c = e.target.closest && e.target.closest('.tb-card[data-t-item]'); if (!c || !T.menu) return; T.arrastrando = +c.getAttribute('data-t-item'); e.dataTransfer.effectAllowed = 'move'; c.classList.add('tb-card--hueco'); });
  document.addEventListener('dragend', function (e) { var c = e.target.closest && e.target.closest('.tb-card'); if (c) c.classList.remove('tb-card--hueco'); });
  document.addEventListener('dragover', function (e) { if (T.arrastrando && e.target.closest && e.target.closest('[data-t-col]')) e.preventDefault(); });
  document.addEventListener('drop', function (e) {
    var col = e.target.closest && e.target.closest('[data-t-col]'); if (!col || !T.arrastrando) return;
    e.preventDefault();
    var x = buscar(T.arrastrando), destino = col.getAttribute('data-t-col'); T.arrastrando = null;
    if (!x || x.columna === destino) return;
    x.columna = destino; principal(vista(T.datos)); SONIDO.sonar('menu');
    api('/items/' + x.id, 'PATCH', { columna: destino }).catch(cargar);
  });
  document.addEventListener('submit', function (e) {
    if (e.target.id !== 't-form') return;
    e.preventDefault();
    var f = e.target, id = f.getAttribute('data-id'), datos = {};
    CAMPOS[T.tipo].forEach(function (c) { var el = f['d_' + c[0]]; if (el && el.value !== '') datos[c[0]] = el.value; });
    var cuerpo = { titulo: f.titulo.value, columna: f.columna.value, vence: f.vence.value || null, responsable: f.responsable.value, datos: datos };
    if (!id) cuerpo.tipo = T.tipo;
    api(id ? '/items/' + id : '/items', id ? 'PATCH' : 'POST', cuerpo).then(function () { capa(''); SONIDO.sonar('listo'); cargar(); })
      .catch(function (err) { document.getElementById('t-msg').textContent = 'No se pudo guardar: ' + err.message + '.'; });
  });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') { var c = document.getElementById('t-capa'); if (c && c.innerHTML) capa(''); } });

  window.MENUS_API = window.MENUS_API || {};
  Object.keys(MENU_TIPO).forEach(function (k) { window.MENUS_API[k] = mostrar; });
  var salir = window.MENUS_API_SALIR;
  window.MENUS_API_SALIR = function () { T.menu = null; capa(''); if (salir) salir(); };
})();
