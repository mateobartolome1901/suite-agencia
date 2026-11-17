// Indicadores (Administración, solo admin): metas contra las que se juzga todo. Lee y guarda /api/<negocio>/indicadores.
// Cada campo se guarda solo al salir de él (como el original: «Último cambio» arriba a la derecha).
(function () {
  var actual = null; // { negocio, datos }

  function S() { return window.SUITE; }
  function num(v) { return v == null ? '' : String(Math.round(v * 100) / 100); }
  function cuando(iso) {
    var d = new Date(iso + (/[zZ+]/.test(iso.slice(-6)) ? '' : 'Z'));
    var m = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];
    var h = d.getHours(), ap = h < 12 ? 'a.m.' : 'p.m.';
    return d.getDate() + ' ' + m[d.getMonth()] + ', ' + String(h % 12 || 12).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0') + ' ' + ap;
  }
  function ultimo(u) { return u ? 'Último cambio: ' + u.quien + ' · ' + cuando(u.cuando) : 'Todavía sin cambios: se usan los valores de fábrica.'; }

  function campo(c, valor) {
    var esc = S().esc, ph = c.defecto != null ? num(c.defecto) : 'sin meta';
    return '<label class="ind-campo"><span class="ind-nombre">' + esc(c.nombre) + '</span>' +
      '<span class="ind-fila"><input class="rec-input ind-input" type="text" inputmode="decimal" autocomplete="off" data-ind="' + esc(c.clave) + '" value="' + esc(num(valor)) + '" placeholder="' + esc(ph) + '" aria-label="' + esc(c.nombre) + '">' +
      '<span class="ind-unidad">' + esc(c.unidad) + '</span></span>' +
      '<span class="e12">' + esc(c.ayuda) + (c.defecto != null ? ' · vacío: ' + num(c.defecto) : '') + '</span></label>';
  }

  function vista(negocio, r) {
    var esc = S().esc, cfg = NEGOCIOS[negocio], voc = cfg.voc;
    var h = '<header><div class="e19"><h1 class="titulo-1">Indicadores</h1><span class="e30">Metas y proyección del negocio que usan los demás menús</span></div></header>';
    h += '<div class="ind-intro"><p class="e52" style="margin:0;max-width:720px">Cargá acá las metas. El panel de campañas pinta el semáforo con los costos objetivo y Trazabilidad decide qué anuncios escalar o pausar. El calendario, Rendimiento e Inicio también van a leer de acá.</p>' +
      '<span class="e12" id="ind-ultimo">' + esc(ultimo(r.ultimo)) + '</span></div>';
    r.secciones.forEach(function (s) {
      var cuerpo = '<div class="caja">' + s.grupos.map(function (g) {
        return (g.nombre ? '<h3 class="fin-h3">' + esc(g.nombre) + '</h3>' : '') +
          '<div class="grilla ind-grilla" style="--n:4">' + g.campos.map(function (c) { return campo(c, r.valores[c.clave]); }).join('') + '</div>';
      }).join('') + '</div>';
      h += '<section class="e22"><div class="e19"><h2 class="titulo-2">' + esc(s.titulo) + '</h2><p class="e44">' + esc(s.sub) + '</p></div>' + cuerpo + '</section>';
    });
    var clientes = r.cuentas.filter(function (c) { return !c.propia; });
    var porDefecto = r.secciones.filter(function (s) { return s.id === 'clientes'; })[0].grupos[0].campos[0];
    var defecto = r.valores[porDefecto.clave] != null ? r.valores[porDefecto.clave] : porDefecto.defecto;
    var tabla = '<div class="caja"><div class="rend-scroll"><table class="rend-tabla"><thead><tr><th>' + esc(voc.cuenta) + '</th><th>Grupo</th><th class="rend-num">Costo por cita · verde hasta</th></tr></thead><tbody>' +
      clientes.map(function (c) {
        return '<tr><td><strong>' + esc(c.nombre) + '</strong></td><td class="e30">' + esc(c.grupo || '') + '</td>' +
          '<td class="rend-num"><span class="ind-fila ind-fila--celda"><input class="rec-input ind-input" type="text" inputmode="decimal" autocomplete="off" data-ind-cuenta="' + c.id + '" value="' + esc(num(c.objetivo_costo_cita)) + '" placeholder="' + esc(num(defecto)) + '" aria-label="Objetivo de ' + esc(c.nombre) + '"><span class="ind-unidad">' + esc(porDefecto.unidad) + '</span></span></td></tr>';
      }).join('') + (clientes.length ? '' : '<tr><td colspan="3" class="e11">Todavía no hay ' + esc(voc.cuentas.toLowerCase()) + ' cargadas.</td></tr>') + '</tbody></table></div></div>';
    h += '<section class="e22"><div class="e19"><h2 class="titulo-2">Objetivo por ' + esc(voc.cuenta.toLowerCase()) + '</h2><p class="e44">Opcional. Vacío: usa el del embudo (' + esc(num(defecto)) + ' ' + esc(porDefecto.unidad) + '). Sirve para ' + esc(voc.cuentas.toLowerCase()) + ' con otra ciudad o ticket.</p></div>' + tabla + '</section>';
    return h;
  }

  function pedir(negocio, metodo, cuerpo) {
    var op = { method: metodo || 'GET', credentials: 'same-origin', headers: {} };
    if (cuerpo) { op.headers['Content-Type'] = 'application/json'; op.headers['X-CSRF'] = S().sesion().csrf; op.body = JSON.stringify(cuerpo); }
    return fetch('/api/' + negocio + '/indicadores', op).then(function (r) {
      if (r.status === 401) { location.href = '/ingresar'; throw new Error('sin sesión'); }
      if (r.status === 403) throw new Error('Solo el administrador puede ver Indicadores');
      if (r.status === 400) throw new Error('Valor no válido');
      if (!r.ok) throw new Error('Error ' + r.status);
      return r.json();
    });
  }

  function mostrar(menu, negocio) {
    actual = { negocio: negocio, datos: null };
    var principal = document.getElementById('principal');
    pedir(negocio).then(function (r) {
      if (!actual || actual.negocio !== negocio) return;
      actual.datos = r;
      principal.innerHTML = vista(negocio, r);
      window.dcPostRender();
    }).catch(function (e) {
      if (!actual) return;
      principal.innerHTML = '<header><div class="e19"><h1 class="titulo-1">Indicadores</h1></div></header><section class="caja ini-bloque"><h3 class="fin-h3">No se pudieron cargar las metas</h3><p class="e52" style="margin:0">' + S().esc(e.message) + '.</p></section>';
    });
  }

  // Guardar al salir del campo (o con Enter), solo si cambió
  document.addEventListener('change', function (e) {
    var t = e.target; if (!actual || !actual.datos || !t.matches || !t.matches('.ind-input')) return;
    var txt = t.value.trim().replace(',', '.'), valor = txt === '' ? null : Number(txt);
    if (valor !== null && !(valor >= 0)) { t.setAttribute('aria-invalid', 'true'); return; }
    t.removeAttribute('aria-invalid');
    var cuerpo = {};
    if (t.hasAttribute('data-ind')) { cuerpo.valores = {}; cuerpo.valores[t.getAttribute('data-ind')] = valor; }
    else { cuerpo.cuentas = {}; cuerpo.cuentas[t.getAttribute('data-ind-cuenta')] = valor; }
    var negocio = actual.negocio;
    pedir(negocio, 'PUT', cuerpo).then(function (r) {
      if (!actual || actual.negocio !== negocio) return;
      actual.datos = r;
      t.closest('.ind-campo, .ind-fila').setAttribute('data-guardado', '1');
      setTimeout(function () { var x = t.closest('[data-guardado]'); if (x) x.removeAttribute('data-guardado'); }, 1400);
      document.getElementById('ind-ultimo').textContent = ultimo(r.ultimo);
      SONIDO.sonar('listo');
    }).catch(function () { t.setAttribute('aria-invalid', 'true'); });
  });
  document.addEventListener('keydown', function (e) { if (e.key === 'Enter' && e.target.matches && e.target.matches('.ind-input')) e.target.blur(); });

  window.MENUS_API = window.MENUS_API || {};
  window.MENUS_API.indicadores = mostrar;
  var salir = window.MENUS_API_SALIR;
  window.MENUS_API_SALIR = function () { actual = null; if (salir) salir(); };
})();
