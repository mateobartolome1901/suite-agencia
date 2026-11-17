// Métricas secundarias (.sec): bloque plegable de ancho completo. Abierto por defecto; el estado se guarda por clave.
var SEC_CERRADAS = (function () { try { return JSON.parse(localStorage.getItem('gds_sec') || '{}'); } catch (e) { return {}; } })();
function guardarSec() { try { localStorage.setItem('gds_sec', JSON.stringify(SEC_CERRADAS)); } catch (e) { /* sin almacenamiento */ } }

// Números que cuentan: al aparecer o cambiar, el valor sube desde el anterior (o desde 0) en ~0.8 s, con el mismo
// formato (separador de miles, decimales, US$, %, «k»). Solo el primer número del texto; horas y fechas no se tocan.
var CONTAR = '.kpi-valor, .sec-valor, .rend-monto, .juego-monto, .wins-monto, .ini-anillo-pct, .rend-mini strong, .ini-ranking-total, [data-contar]';
var MOV_REDUCIDO = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
function numeroDe(txt) {
  if (/\d:\d|\d\/\d|\d-\d/.test(txt)) return null;
  var m = /\d[\d,]*(?:\.\d+)?/.exec(txt);
  if (!m) return null;
  var s = m[0], dec = s.indexOf('.') >= 0 ? s.split('.')[1].length : 0;
  return { i: m.index, s: s, v: parseFloat(s.replace(/,/g, '')), dec: dec, miles: s.indexOf(',') >= 0 };
}
function contarNumero(el) {
  var nodo = el.firstChild;
  if (!nodo || nodo.nodeType !== 3) return;
  var txt = nodo.nodeValue;
  if (el._contarFin === txt) return;
  var fin = numeroDe(txt), desde = el._contarValor || 0;
  el._contarFin = txt;
  if (!fin || MOV_REDUCIDO || fin.v === desde) { el._contarValor = fin ? fin.v : 0; return; }
  var t0 = null, dur = 800, id = (el._contarId || 0) + 1;
  el._contarId = id;
  var fmt = function (x) {
    var s = x.toFixed(fin.dec);
    if (fin.miles) { var p = s.split('.'); p[0] = p[0].replace(/\B(?=(\d{3})+(?!\d))/g, ','); s = p.join('.'); }
    return txt.slice(0, fin.i) + s + txt.slice(fin.i + fin.s.length);
  };
  var paso = function (ts) {
    if (el._contarId !== id || el.firstChild !== nodo || el._contarFin !== txt) return;  // otro render ya lo cambió
    if (t0 === null) t0 = ts;
    var k = Math.min(1, (ts - t0) / dur), e = 1 - Math.pow(1 - k, 3), x = desde + (fin.v - desde) * e;
    nodo.nodeValue = k < 1 ? fmt(x) : txt;
    el._contarValor = desde + (fin.v - desde) * e;
    if (k < 1) requestAnimationFrame(paso);
  };
  requestAnimationFrame(paso);
}
// Luz que sigue al mouse en las tarjetas (.kpi::before usa --mx / --my). Una vez por cuadro como mucho.
(function () {
  var ult = null, pendiente = false;
  document.addEventListener('pointermove', function (e) {
    ult = e;
    if (pendiente) return;
    pendiente = true;
    requestAnimationFrame(function () {
      pendiente = false;
      var k = ult.target.closest && ult.target.closest('.kpi');
      if (!k) return;
      var r = k.getBoundingClientRect();
      k.style.setProperty('--mx', (ult.clientX - r.left) + 'px'); k.style.setProperty('--my', (ult.clientY - r.top) + 'px');
    });
  }, { passive: true });
})();
// Mientras se hace scroll (en cualquier contenedor), html[data-desplazando] frena los adornos en bucle (marca.css)
(function () {
  var html = document.documentElement, t = null;
  document.addEventListener('scroll', function () {
    if (t === null) html.setAttribute('data-desplazando', '');
    else clearTimeout(t);
    t = setTimeout(function () { t = null; html.removeAttribute('data-desplazando'); }, 160);
  }, { capture: true, passive: true });
})();
document.addEventListener('click', function (e) {
  var b = e.target.closest && e.target.closest('.sec-cab');
  var s = b && b.closest('[data-sec]');
  if (!s) return;
  var k = s.getAttribute('data-sec');
  if (SEC_CERRADAS[k]) delete SEC_CERRADAS[k]; else SEC_CERRADAS[k] = 1;
  guardarSec(); window.dcPostRender();
});

window.dcPostRender = function () {
  document.querySelectorAll('h2.titulo-2').forEach(function (h2) {
    var x = cabezaDe(h2);
    if (!x) return;
    var plegado = !!PLEGADOS[h2.textContent.trim()];
    h2.setAttribute('data-plegable', '1'); h2.setAttribute('role', 'button'); h2.setAttribute('tabindex', '0'); h2.setAttribute('aria-expanded', plegado ? 'false' : 'true');
    Array.prototype.forEach.call(x.sec.children, function (c) { if (c === x.cab) return; if (plegado) c.setAttribute('data-plegado', '1'); else c.removeAttribute('data-plegado'); });
  });
  document.querySelectorAll('[data-sec]').forEach(function (s) {
    var cerrada = !!SEC_CERRADAS[s.getAttribute('data-sec')], cab = s.querySelector('.sec-cab');
    if (cerrada) s.setAttribute('data-sec-cerrado', '1'); else s.removeAttribute('data-sec-cerrado');
    if (cab) cab.setAttribute('aria-expanded', cerrada ? 'false' : 'true');
  });
  document.querySelectorAll(CONTAR).forEach(contarNumero);
};
(function () {
  function alternar(h2) {
    var k = h2.textContent.trim();
    if (PLEGADOS[k]) delete PLEGADOS[k]; else PLEGADOS[k] = 1;
    guardarPlegados(); window.dcPostRender();
  }
  document.addEventListener('click', function (e) { var h = e.target.closest && e.target.closest('h2[data-plegable]'); if (h) alternar(h); });
  document.addEventListener('keydown', function (e) { if ((e.key === 'Enter' || e.key === ' ') && e.target.matches && e.target.matches('h2[data-plegable]')) { e.preventDefault(); alternar(e.target); } });
})();

// --- Sonidos de la interfaz: todos clics de vidrio cortos (≤ 100 ms), con el volumen igualado.
//  · menu (glass_002): menú lateral, switches de vista y pestañas · listo: el mismo, al guardar ficha o asistencia
//  · metrica (glass_006): accesos directos a otros menús («Ver … →» de tarjetas y alertas)
//  · abrir (glass_002 +2 semitonos) / cerrar (glass_002 −3 semitonos): desplegables (secciones, grupos, filtros, calendario)
//  · interruptor (glass_005): al activar los sonidos
// Se apagan con el botón «Sonidos» del menú lateral (gds_sonido en el navegador) y con «reducir movimiento» no cambian.
var SONIDO = (function () {
  var ctx = null, on = true;
  try { on = localStorage.getItem('gds_sonido') !== '0'; } catch (e) { /* sin almacenamiento */ }
  function audio() {
    if (!ctx) { var A = window.AudioContext || window.webkitAudioContext; if (!A) return null; ctx = new A(); }
    if (ctx.state === 'suspended') ctx.resume();
    return ctx;
  }
  // Sonidos de interfaz del pack «Interface Sounds» de Kenney (CC0, uso libre; ver sonidos/LICENCIA-kenney.txt).
  // Se bajan una vez y se decodifican en memoria; cada clic reproduce el búfer (sin demora ni descarga).
  var VOL = { menu: 0.25, metrica: 0.28, abrir: 0.27, cerrar: 0.24, interruptor: 0.3, listo: 0.25 }, buf = {}, pidiendo = {};
  function cargarSonido(c, k) {
    if (buf[k] || pidiendo[k]) return;
    pidiendo[k] = true;
    fetch('/static/sonidos/' + k + '.mp3').then(function (r) { return r.arrayBuffer(); })
      .then(function (a) { return new Promise(function (ok, mal) { c.decodeAudioData(a, ok, mal); }); })
      .then(function (b) { buf[k] = b; }).catch(function () { pidiendo[k] = false; });
  }
  function reproducir(c, k) {
    if (!buf[k]) { cargarSonido(c, k); return; }
    var s = c.createBufferSource(), g = c.createGain();
    s.buffer = buf[k]; g.gain.value = VOL[k] || 0.25;
    s.connect(g); g.connect(c.destination); s.start();
  }
  // Al primer gesto se precargan todos, así el primer clic ya suena
  function precargar() { var c = audio(); if (c) Object.keys(VOL).forEach(function (k) { cargarSonido(c, k); }); }
  ['pointerdown', 'keydown'].forEach(function (ev) { document.addEventListener(ev, function f() { if (on) precargar(); document.removeEventListener(ev, f, true); }, true); });
  function sonar(k) { if (!on || !VOL[k]) return; var c = audio(); if (c) try { reproducir(c, k); } catch (e) { /* sin audio */ } }
  // Qué sonido lleva cada clic (se mira antes de que el menú cambie su estado: fase de captura)
  document.addEventListener('click', function (e) {
    var el = e.target.closest ? e.target : null;
    if (!el || el.closest('[data-sin-sonido]')) return;
    var d = el.closest('[aria-expanded], .sec-cab, h2[data-plegable]');
    if (d) return sonar(d.getAttribute('aria-expanded') === 'true' ? 'cerrar' : 'abrir');
    if (el.closest('.lateral a, .lateral button, [role="group"] button, [role="tablist"] button')) return sonar('menu');
    if (el.closest('.kpi-ir, .ini-alerta .rend-link')) return sonar('metrica');
  }, true);
  return {
    sonar: sonar, activo: function () { return on; },
    alternar: function () {
      on = !on;
      try { localStorage.setItem('gds_sonido', on ? '1' : '0'); } catch (e) { /* sin almacenamiento */ }
      if (on) { precargar(); sonar('interruptor'); }
      return on;
    }
  };
})();
