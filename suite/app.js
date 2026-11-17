// Suite de agencia: menú lateral con selector de negocio (como subcuentas) e Inicio por modelo de cobro.
(function () {
  var HOY = new Date(2026, 10, 17), DIAS_MES = 30, AVANCE = HOY.getDate() / DIAS_MES;
  var MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];
  var estado = { negocio: leer('suite_negocio', 'plastia'), menu: (location.hash || '#resumen').slice(1), vista: 'mes', mes: HOY.getMonth(), anio: HOY.getFullYear(), grupos: JSON.parse(leer('suite_grupos', '{}')) };
  if (!NEGOCIOS[estado.negocio]) estado.negocio = 'plastia';

  function leer(k, def) { try { var v = localStorage.getItem(k); return v === null ? def : v; } catch (e) { return def; } }
  function guardar(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* sin almacenamiento */ } }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function us(n) { return (n < 0 ? '−' : '') + 'US$' + Math.round(Math.abs(n)).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ','); }
  function pct(a, b) { return b ? Math.round(a / b * 100) : 0; }
  // Estado contra la proyección: cumple si va al ritmo, cerca si llega al 80% del ritmo, falta si no
  function juicio(real, proy) { if (!proy) return ''; var r = real / (proy * AVANCE); return r >= 1 ? 'cumple' : r >= 0.8 ? 'cerca' : 'falta'; }

  // ---- Íconos de trazo (duotono: relleno leve + trazo) ----
  var ICO = {
    casa: 'M3 11l9-7 9 7v9a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z',
    tendencia: 'M3 17l6-6 4 4 8-8M15 7h6v6',
    megafono: 'M3 10v4a1 1 0 0 0 1 1h3l7 4V5L7 9H4a1 1 0 0 0-1 1zM18 8.5a5 5 0 0 1 0 7',
    billetera: 'M4 7h15a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8l3-4h11M16 14h2',
    check: 'M5 4h14a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1zM8 12l3 3 5-6',
    ruta: 'M6 3a3 3 0 1 0 0 6 3 3 0 0 0 0-6zM18 15a3 3 0 1 0 0 6 3 3 0 0 0 0-6zM6 9v3a4 4 0 0 0 4 4h5',
    calendario: 'M5 5h14a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1zM4 10h16M8 3v4M16 3v4',
    chat: 'M5 4h14a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H9l-5 4V5a1 1 0 0 1 1-1z',
    personas: 'M9 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM3 20a6 6 0 0 1 12 0M16 5a3 3 0 0 1 0 6M21 20a6 6 0 0 0-4-5.6',
    reloj: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM12 7v5l3 2',
    trofeo: 'M8 4h8v5a4 4 0 0 1-8 0zM8 6H5a3 3 0 0 0 3 4M16 6h3a3 3 0 0 1-3 4M12 13v4M8 20h8',
    informe: 'M6 3h9l4 4v13a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1zM9 12h6M9 16h6M9 8h3',
    libro: 'M5 5a2 2 0 0 1 2-2h12v15H7a2 2 0 0 0-2 2zM5 20a2 2 0 0 0 2 1h12v-3',
    tarjeta: 'M4 6h16a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1zM3 10h18M7 15h4',
    ficha: 'M6 3h12a1 1 0 0 1 1 1v16a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1zM9 8h6M9 12h6M9 16h3',
    diana: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8zM12 12h.01',
    usuario: 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM4 21a8 8 0 0 1 16 0',
    guion: 'M6 3h9l4 4v13a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1zM9 13h6M9 17h4',
    tablero: 'M4 4h4v16H4zM10 4h4v10h-4zM16 4h4v6h-4z',
    video: 'M7 3h10a1 1 0 0 1 1 1v16a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1zM10 9.5v5l4-2.5z',
    paleta: 'M9 4a4 4 0 1 0 0 8 4 4 0 0 0 0-8zM15 4a4 4 0 1 0 0 8 4 4 0 0 0 0-8zM12 11a4 4 0 1 0 0 8 4 4 0 0 0 0-8z'
  };
  var ICO_EXTRA = { conversaciones: '#7BA7E8', semanal: '#93A9E2' };
  function ico(k) { return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="' + ICO[k] + '" fill="currentColor" fill-opacity=".16"/></svg>'; }
  var CHEV = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>';

  // ---- Menú lateral ----
  function lateral() {
    var cfg = NEGOCIOS[estado.negocio];
    var html = '<div class="lateral-cab"><div class="lateral-marca"><span class="lateral-logo">' + cfg.logo + '</span><span class="lateral-titulo">Panel de performance</span></div>' +
      '<button class="lateral-plegar" type="button" id="plegar" aria-label="Achicar el menú"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 17l-5-5 5-5M18 17l-5-5 5-5"/></svg></button></div>';
    html += '<div class="neg" data-pop="negocio"><button class="neg-btn" type="button" id="neg-btn" aria-haspopup="menu" aria-expanded="false" style="--ico:' + cfg.ico + '">' +
      '<span class="neg-sigla">' + cfg.sigla + '</span><span class="neg-txt"><strong>' + esc(cfg.nombre) + '</strong><span>' + esc(cfg.modeloTxt) + '</span></span><span class="neg-flecha">' + CHEV + '</span></button>' +
      '<div class="pop" role="menu" id="neg-menu" hidden>' + Object.keys(NEGOCIOS).map(function (k) {
        var n = NEGOCIOS[k];
        return '<button class="neg-op" type="button" role="menuitemradio" data-negocio="' + k + '" aria-checked="' + (k === estado.negocio) + '" style="--ico:' + n.ico + '"><span class="neg-sigla">' + n.sigla + '</span><span class="neg-txt"><strong>' + esc(n.nombre) + '</strong><span>' + esc(n.modeloTxt) + '</span></span></button>';
      }).join('') + '</div></div>';
    html += '<div class="lateral-cuerpo"><nav aria-label="Menús">';
    cfg.menus.forEach(function (g) {
      var links = g.items.map(function (it) {
        var activo = it[0] === estado.menu;
        var st = (activo ? 'background: var(--nav-activo); box-shadow: var(--nav-activo-sombra);' : '') + (ICO_EXTRA[it[0]] ? '--ico:' + ICO_EXTRA[it[0]] + ';' : '');
        return '<a href="#' + it[0] + '"' + (activo ? ' aria-current="page"' : '') + (st ? ' style="' + st + '"' : '') + '><span class="nav-ico">' + ico(it[2]) + '</span>' + esc(it[1]) + '</a>';
      }).join('');
      if (!g.grupo) { html += '<div class="nav-bloque">' + links + '</div>'; return; }
      var abierto = estado.grupos[g.grupo] !== 0;
      html += '<div class="nav-bloque"><button class="nav-grupo" type="button" data-grupo="' + esc(g.grupo) + '" aria-expanded="' + abierto + '">' + esc(g.grupo) + CHEV + '</button>' +
        '<div class="nav-sub"' + (abierto ? '' : ' hidden') + '>' + links + '</div></div>';
    });
    html += '</nav><div class="lateral-pie"><span class="fase">Datos de ejemplo</span><button class="sonido-btn" type="button" id="sonido" data-sin-sonido aria-pressed="' + SONIDO.activo() + '">' +
      '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 9v6h4l5 4V5L8 9zM17 9a4 4 0 0 1 0 6"/></svg>Sonidos</button></div></div>';
    document.getElementById('lateral').innerHTML = html;
  }

  // ---- Piezas comunes ----
  function tarjeta(o) {
    var cls = 'kpi' + (o.clave ? ' kpi--clave' : '') + (o.oro ? ' kpi--oro' : '');
    var h = '<article class="' + cls + '"><div class="kpi-cab"><span class="kpi-nombre">' + esc(o.nombre) + '</span>' + (o.vari ? '<span class="pill var ' + o.vari[1] + '">' + o.vari[0] + '</span>' : '') + '</div>';
    h += '<div class="kpi-cuerpo"><div class="kpi-valores"><div class="kpi-valor"' + (o.ambar ? ' style="color: var(--ambar-texto)"' : '') + '>' + esc(o.valor) + (o.pct != null ? ' <span class="kpi-pct">' + o.pct + '%</span>' : '') + '</div>';
    h += '<div class="kpi-sub">' + esc(o.sub || '') + '</div></div>';
    if (o.barra) {
      var b = o.barra, est = b.estado || '';
      h += '<div class="ini-meta"><span class="rend-barra ini-barra" data-estado="' + est + '"><span style="width:' + Math.max(2, Math.min(100, b.pct)) + '%"></span><i style="left:' + Math.round(AVANCE * 100) + '%"></i></span><span class="ini-proy">' + esc(b.txt) + '</span></div>';
    }
    h += '</div>';
    if (o.ir) h += '<button class="kpi-ir" type="button" data-ir="' + o.ir[1] + '">' + esc(o.ir[0]) + ' →</button>';
    return h + '</article>';
  }
  function secItem(nombre, valor, sub, p) {
    return '<li class="sec-item"><span class="sec-nombre">' + esc(nombre) + '</span><span class="sec-valor">' + esc(valor) + (p != null ? ' <span class="kpi-pct">' + p + '%</span>' : '') + '</span><span class="sec-sub">' + esc(sub) + '</span></li>';
  }
  function secundarias(clave, items, ir) {
    return '<section class="sec" data-sec="' + clave + '"><button class="sec-cab" type="button" aria-expanded="true">Métricas secundarias <span class="sec-n">' + items.length + '</span><span class="sec-flecha"></span></button>' +
      '<ul class="sec-lista">' + items.join('') + '</ul>' + (ir ? '<div class="sec-pie"><button class="rend-link kpi-ir" type="button" data-ir="' + ir[1] + '">' + esc(ir[0]) + ' →</button></div>' : '') + '</section>';
  }
  function bloque(titulo, cuerpo, ir, extra) {
    return '<section class="caja ini-bloque' + (extra || '') + '"><div class="ini-bloque-cab"><h3 class="fin-h3">' + esc(titulo) + '</h3>' + (ir ? '<button class="kpi-ir" type="button" data-ir="' + ir[1] + '">' + esc(ir[0]) + ' →</button>' : '') + '</div>' + cuerpo + '</section>';
  }
  function anillo(p, monto, txt, ritmo) {
    var r = 52, c = 2 * Math.PI * r, largo = Math.min(1, p / 100) * c;
    var ang = AVANCE * 2 * Math.PI - Math.PI / 2, x1 = 60 + Math.cos(ang) * 44, y1 = 60 + Math.sin(ang) * 44, x2 = 60 + Math.cos(ang) * 66, y2 = 60 + Math.sin(ang) * 66;
    return '<div class="ini-proy-cuerpo"><div class="ini-anillo-graf"><svg viewBox="0 0 120 120"><circle class="ini-anillo-fondo" cx="60" cy="60" r="' + r + '"/>' +
      '<circle class="ini-anillo-arco" cx="60" cy="60" r="' + r + '" stroke-dasharray="' + largo.toFixed(1) + ' ' + c.toFixed(1) + '" transform="rotate(-90 60 60)"/>' +
      '<line class="ini-anillo-marca" x1="' + x1.toFixed(1) + '" y1="' + y1.toFixed(1) + '" x2="' + x2.toFixed(1) + '" y2="' + y2.toFixed(1) + '"/></svg><span class="ini-anillo-pct">' + p + '%</span></div>' +
      '<div class="ini-proy-txt"><span class="ini-anillo-monto">' + esc(monto) + '</span><p class="ini-anillo-txt">' + esc(txt) + '</p><span class="ini-anillo-ritmo">' + esc(ritmo) + '</span></div></div>';
  }
  function lineas(filas) {
    return '<ul class="ini-lineas">' + filas.map(function (f) {
      var p = pct(f[1], f[2]), est = juicio(f[1], f[2]);
      return '<li><span class="ini-linea-n">' + esc(f[0]) + '</span><span class="ini-linea-v">' + (f[3] ? f[1] : us(f[1])) + ' <small>de ' + (f[3] ? f[2] : us(f[2])) + '</small></span>' +
        '<span class="rend-barra"><span style="width:' + Math.max(2, Math.min(100, p)) + '%"></span></span><strong class="ini-est" data-estado="' + est + '" style="text-align:right">' + p + '%</strong></li>';
    }).join('') + '</ul>';
  }
  var DONA_COLOR = { comisiones: '#2E9E6B', setup: '#8B6CC8', fees: '#B38A26', otros: '#6B7A72' };
  function dona(cats, centroTxt) {
    var total = cats.reduce(function (a, c) { return a + c[1]; }, 0), r = 80, C = 2 * Math.PI * r, ini = 0;
    var capas = '', dets = '';
    cats.forEach(function (c, i) {
      var len = total ? c[1] / total * C : 0;
      capas += '<svg class="fin-dona-capa" viewBox="0 0 200 200"><circle class="fin-dona-arco" data-i="' + i + '" cx="100" cy="100" r="' + r + '" stroke="' + DONA_COLOR[c[2]] + '" stroke-dasharray="' + Math.max(0, len - 3).toFixed(1) + ' ' + C.toFixed(1) + '" stroke-dashoffset="' + (-ini).toFixed(1) + '" transform="rotate(-90 100 100)"/></svg>';
      dets += '<div class="fin-dona-det" data-i="' + i + '"><span>' + esc(c[0]) + '</span><strong>' + us(c[1]) + '</strong><span>' + pct(c[1], total) + '%</span></div>';
      ini += len;
    });
    var ley = cats.map(function (c, i) { return '<li data-i="' + i + '" tabindex="0"><span class="fin-dona-color" style="background:' + DONA_COLOR[c[2]] + '"></span><span class="fin-dona-n">' + esc(c[0]) + '</span><span class="fin-dona-v">' + us(c[1]) + ' <small>' + pct(c[1], total) + '%</small></span></li>'; }).join('');
    return '<div class="fin-dona"><div class="fin-dona-graf"><svg viewBox="0 0 200 200"><circle class="fin-dona-fondo" cx="100" cy="100" r="' + r + '"/></svg>' + capas +
      '<div class="fin-dona-centro"><div class="fin-dona-total" style="display:flex;flex-direction:column;align-items:center;gap:2px"><span>' + esc(centroTxt) + '</span><strong>' + us(total) + '</strong></div>' + dets + '</div></div><ul class="fin-dona-ley">' + ley + '</ul></div>';
  }
  function meses(filas, actual) {
    var max = Math.max.apply(null, filas.map(function (f) { return Math.max(f[1], f[2]); }));
    return '<ul class="ini-meses">' + filas.map(function (f) {
      var es = f[0] === actual;
      return '<li data-actual="' + es + '" data-cumple="' + (!es && f[1] >= f[2]) + '"><span class="ini-mes-n">' + f[0] + '</span><span class="ini-mes-barra"><span style="width:' + Math.max(2, f[1] / max * 100) + '%"></span><i style="left:' + (f[2] / max * 100) + '%"></i></span><span class="ini-mes-v">' + us(f[1]) + '</span></li>';
    }).join('') + '</ul><p class="ini-nota">Últimos 5 meses · resaltado el período elegido · la marca blanca es la proyección del mes</p>';
  }
  function ranking(filas) {
    var max = Math.max.apply(null, filas.map(function (f) { return f[1]; })) || 1;
    return '<ol class="ini-ranking">' + filas.map(function (f, i) {
      return '<li><span class="rend-pos' + (i < 3 ? ' rend-pos--' + (i + 1) : '') + '">' + (i + 1) + '</span><div class="ini-ranking-cuerpo"><div class="ini-ranking-cab"><strong>' + esc(f[0]) + '</strong><span class="ini-ranking-total">' + f[2] + '</span></div>' +
        '<span class="rend-barra"><span style="width:' + Math.max(2, f[1] / max * 100) + '%"></span></span><span class="ini-ranking-sub">' + esc(f[3]) + '</span></div></li>';
    }).join('') + '</ol>';
  }
  function alertas(lista) {
    return '<ul class="rend-alertas">' + lista.map(function (a) {
      return '<li class="rend-alerta ini-alerta" data-nivel="' + a[0] + '"><div><strong>' + esc(a[1]) + '</strong><span>' + esc(a[2]) + '</span></div><button class="rend-link kpi-ir" type="button" data-ir="' + a[4] + '">' + esc(a[3]) + ' →</button></li>';
    }).join('') + '</ul>';
  }
  function tareas(lista) {
    if (!lista.length) return '<p class="vacio">Nada pendiente para hoy.</p>';
    return '<div>' + lista.map(function (t) { return '<div class="ini-pend"><span class="ini-pend-tipo" data-nivel="' + (t[1] === 'Vencida' ? 'falta' : '') + '">' + t[1] + '</span><span>' + esc(t[0]) + '</span></div>'; }).join('') + '</div>';
  }
  function actividad(d) {
    var EST = { 'Asistió': 'cumple', 'Sin marcar': 'cerca', 'Canceló': '' };
    return '<div class="ini-cuentas">' + d.conteoHoy.map(function (c) { return '<span class="ini-cuenta"><strong>' + c[0] + '</strong>' + esc(c[1]) + '</span>'; }).join('') + '</div>' +
      '<div class="ini-hoy">' + d.hoy.map(function (c) {
        return '<button class="ini-hoy-cita" type="button"' + (c[4] === 'Canceló' ? ' style="opacity:.55"' : '') + '><span class="ini-hoy-hora">' + c[0] + '</span><span class="ini-hoy-tipo">' + esc(c[1]) + '</span><span class="ini-hoy-nombre"><strong>' + esc(c[2]) + '</strong><span>' + esc(c[3]) + '</span></span><span class="ini-est" data-estado="' + EST[c[4]] + '">' + c[4] + '</span></button>';
      }).join('') + '</div>';
  }

  // ---- Cabecera con período y filtros ----
  function cabecera(titulo, sub) {
    var cfg = NEGOCIOS[estado.negocio], n = DEMO[estado.negocio].cuentas.length;
    var per = estado.vista === 'mes' ? MESES[estado.mes] + ' ' + estado.anio : String(estado.anio);
    var rango = estado.vista === 'mes' ? '1 ' + MESES[estado.mes].slice(0, 3).toLowerCase() + ' – ' + new Date(estado.anio, estado.mes + 1, 0).getDate() + ' ' + MESES[estado.mes].slice(0, 3).toLowerCase() : '1 ene – 31 dic';
    return '<header><div class="e19"><h1 class="titulo-1">' + esc(titulo) + '</h1><span class="e30">' + esc(sub.replace('{per}', per)) + '</span></div>' +
      '<div class="cab-filtros e36"><div class="seg" role="group" aria-label="Vista"><button type="button" data-vista="mes" aria-pressed="' + (estado.vista === 'mes') + '">Mes</button><button type="button" data-vista="anio" aria-pressed="' + (estado.vista === 'anio') + '">Año</button></div>' +
      '<button class="btn-sec btn-flecha" type="button" data-paso="-1" aria-label="Período anterior">‹</button><span class="periodo-txt">' + esc(per) + '</span><button class="btn-sec btn-flecha" type="button" data-paso="1" aria-label="Período siguiente">›</button>' +
      '<button class="btn-sec" type="button" data-paso="0">Este mes</button>' +
      '<button class="btn-sec" type="button" aria-haspopup="menu" aria-expanded="false">' + esc(cfg.voc.cuentas) + ': Todas (' + n + ') ' + CHEV + '</button>' +
      '<button class="btn-sec" type="button" aria-haspopup="dialog" aria-expanded="false"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 5h14v15H5zM5 10h14M9 3v4M15 3v4"/></svg>' + rango + ' ' + CHEV + '</button></div></header>';
  }

  // ---- Inicio: comisión (Plastia) ----
  function inicioComision(cfg, d) {
    var c = calcPlastia(d, cfg), t = c.t;
    var gastos = d.gastos.reduce(function (a, g) { return a + g[1]; }, 0), stripe = d.gastos.filter(function (g) { return /Stripe/.test(g[0]); })[0][1];
    var cash = c.setup + t.cobrado, cashNeto = cash - stripe, flujo = cashNeto - (gastos - stripe), porCobrar = t.comision - t.cobrado;
    var factura = c.setup + t.comision, comisionando = c.filas.filter(function (f) { return f.comision > 0; }).length;
    var closerPend = t.closer * (porCobrar / t.comision);
    var h = cabecera('Inicio', '{per} · Salud del negocio · USD');
    h += '<div class="grilla" style="--n:3">' +
      tarjeta({ nombre: 'Facturación', clave: true, valor: us(factura), sub: 'setups + comisiones generadas · ' + t.cirugias + ' cirugías', barra: { pct: pct(factura, d.proy.comisiones + d.proy.setups * cfg.cobro.setup), estado: juicio(factura, d.proy.comisiones + d.proy.setups * cfg.cobro.setup), txt: pct(factura, d.proy.comisiones + d.proy.setups * cfg.cobro.setup) + '% de ' + us(d.proy.comisiones + d.proy.setups * cfg.cobro.setup) + ' proyectado' }, ir: ['Ver ingresos', 'finanzas'] }) +
      tarjeta({ nombre: 'Cash collected neto', valor: us(cashNeto), pct: pct(cashNeto, cash), sub: 'sin ' + us(stripe) + ' de comisión de Stripe', ir: ['Ver finanzas', 'finanzas'] }) +
      tarjeta({ nombre: 'Flujo de caja neto', oro: true, valor: us(flujo), pct: pct(flujo, cashNeto), sub: 'cash neto menos ' + us(gastos - stripe) + ' de gastos', barra: { pct: pct(flujo, d.proy.flujo), txt: pct(flujo, d.proy.flujo) + '% de ' + us(d.proy.flujo) + ' proyectado' }, ir: ['Ver gastos', 'finanzas'] }) +
      tarjeta({ nombre: 'Comisiones por cobrar', clave: true, ambar: true, valor: us(porCobrar), sub: '25% del margen · ' + (c.filas.filter(function (f) { return f.comision > f.cobrado; }).length) + ' clínicas · margen = venta − costos de cirugía − pauta', ir: ['Ver cobros pendientes', 'bitacora'] }) +
      tarjeta({ nombre: 'Clínicas nuevas', valor: String(d.setups.length), sub: 'setup de ' + us(cfg.cobro.setup) + ' cada una', barra: { pct: pct(d.setups.length, d.proy.setups), estado: juicio(d.setups.length, d.proy.setups), txt: pct(d.setups.length, d.proy.setups) + '% de ' + d.proy.setups + ' proyectadas' }, ir: ['Ver incorporaciones', 'finanzas'] }) +
      tarjeta({ nombre: 'Clínicas comisionando', valor: String(comisionando), sub: 'con comisiones generadas · promedio ' + us(t.comision / (comisionando || 1)) + ' por clínica', barra: { pct: pct(comisionando, d.proy.cuentas), estado: juicio(comisionando, d.proy.cuentas), txt: pct(comisionando, d.proy.cuentas) + '% de ' + d.proy.cuentas + ' proyectadas' }, ir: ['Ver bitácora', 'bitacora'] }) +
      '</div>';
    h += secundarias('ini-plastia', [
      secItem('Gastos', us(gastos), 'pauta propia, herramientas, Stripe', pct(gastos, cash)),
      secItem('Ventas de cirugías', us(t.venta), t.cirugias + ' cirugías vendidas por las clínicas'),
      secItem('Margen de las clínicas', us(t.margen), 'venta − ' + us(t.costos) + ' de costos − ' + us(t.pauta) + ' de pauta'),
      secItem('Pauta de clínicas', us(t.pauta), 'campañas que corre Plastia para las clínicas · proyectado ' + us(d.proy.pautaCuentas)),
      secItem('Pauta propia (Plastia)', us(d.pautaPropia), 'para conseguir clínicas nuevas · proyectado ' + us(d.proy.pautaPropia)),
      secItem('Comisiones de closers por pagar', us(closerPend), '25% de la comisión de Plastia · generado ' + us(t.closer))
    ], ['Ver el detalle en Finanzas', 'finanzas']);
    var pc = pct(cash, d.proy.cash);
    h += '<div class="bloques">' +
      bloque('Proyección del mes', anillo(pc, us(cash) + ' de ' + us(d.proy.cash), 'Faltan ' + us(Math.max(0, d.proy.cash * AVANCE - cash)) + ' para ir al ritmo (la marca es dónde habría que estar hoy).', 'Pasó el ' + Math.round(AVANCE * 100) + '% del período') +
        lineas([['Cash collected', cash, d.proy.cash], ['Setups', c.setup, d.proy.setups * cfg.cobro.setup], ['Comisiones', t.comision, d.proy.comisiones], ['Flujo de caja neto', flujo, d.proy.flujo], ['Clínicas nuevas', d.setups.length, d.proy.setups, true], ['Pauta propia', d.pautaPropia, d.proy.pautaPropia], ['Pauta de clínicas', t.pauta, d.proy.pautaCuentas]]) +
        '<p class="ini-nota">Proyección de Indicadores · comisiones calculadas sobre la bitácora de cirugías.</p>', ['Ver proyección', 'indicadores'], ' ini-proyeccion" data-estado="' + juicio(cash, d.proy.cash)) +
      bloque('Ganancia por categoría', dona([['Comisiones de cirugías', t.comision, 'comisiones'], ['Setups de clínicas', c.setup, 'setup']], 'Facturado'), ['Ver finanzas', 'finanzas']) + '</div>';
    var mesesD = d.meses.slice(); mesesD[4] = [mesesD[4][0], cash, mesesD[4][2]];
    h += '<div class="bloques">' + bloque('Cash collected por mes', meses(mesesD, 'Nov 26'), ['Ver ingresos', 'finanzas']) +
      bloque('Ranking de clínicas según comisiones', ranking(c.filas.slice().sort(function (a, b) { return b.comision - a.comision; }).map(function (f) { return [f.n, f.comision, us(f.comision), 'cobrado ' + us(f.cobrado) + ' · ' + f.cirugias + ' cirugía' + (f.cirugias > 1 ? 's' : '')]; })), ['Ver bitácora', 'bitacora']) + '</div>';
    h += '<div class="bloques">' + bloque('Alertas y accionables', alertas(d.alertas), null) + bloque('Tareas de hoy', tareas(d.tareas), ['Ver tareas', 'tareas']) + '</div>';
    h += '<div class="bloques">' + bloque('Actividad de hoy', actividad(d), ['Ver calendario', 'calendario']) + '<div></div></div>';
    return h;
  }

  // ---- Inicio: fee mensual (TPA) ----
  function inicioFee(cfg, d) {
    var c = calcTpa(d, cfg);
    var gastos = d.gastos.reduce(function (a, g) { return a + g[1]; }, 0), stripe = d.gastos.filter(function (g) { return /Stripe/.test(g[0]); })[0][1];
    var cash = c.setup + c.pagado, cashNeto = cash - stripe, flujo = cashNeto - (gastos - stripe), porSocio = flujo / cfg.socios.length;
    var porCobrar = c.vencido + c.pendiente, ltv = cfg.cobro.setup + cfg.cobro.fee * 8;
    var h = cabecera('Inicio', '{per} · Salud del negocio · USD');
    h += '<div class="grilla" style="--n:3">' +
      tarjeta({ nombre: 'MRR', clave: true, valor: us(c.mrr), sub: c.activos + ' clientes × ' + us(cfg.cobro.fee) + ' de fee mensual', barra: { pct: pct(c.mrr, d.proy.mrr), estado: c.mrr >= d.proy.mrr ? 'cumple' : 'cerca', txt: pct(c.mrr, d.proy.mrr) + '% de ' + us(d.proy.mrr) + ' proyectado' }, ir: ['Ver suscripciones', 'cobros'] }) +
      tarjeta({ nombre: 'Cash collected neto', valor: us(cashNeto), pct: pct(cashNeto, cash), sub: 'setups + fees cobrados · sin ' + us(stripe) + ' de Stripe', ir: ['Ver finanzas', 'finanzas'] }) +
      tarjeta({ nombre: 'Flujo de caja neto', oro: true, valor: us(flujo), pct: pct(flujo, cashNeto), sub: 'cash neto menos ' + us(gastos - stripe) + ' de gastos', barra: { pct: pct(flujo, d.proy.flujo), txt: pct(flujo, d.proy.flujo) + '% de ' + us(d.proy.flujo) + ' proyectado' }, ir: ['Ver gastos', 'finanzas'] }) +
      tarjeta({ nombre: 'Fees por cobrar', clave: true, ambar: true, valor: us(porCobrar), sub: us(c.vencido) + ' vencido · ' + us(c.pendiente) + ' por vencer', ir: ['Ver suscripciones', 'cobros'] }) +
      tarjeta({ nombre: 'Clientes nuevos', valor: String(d.setups.length), sub: 'setup de ' + us(cfg.cobro.setup) + ' cada uno', barra: { pct: pct(d.setups.length, d.proy.setups), estado: juicio(d.setups.length, d.proy.setups), txt: pct(d.setups.length, d.proy.setups) + '% de ' + d.proy.setups + ' proyectados' }, ir: ['Ver ventas TPA', 'ag-ventas'] }) +
      tarjeta({ nombre: 'Clientes activos', valor: String(c.activos), sub: d.bajas + ' bajas este mes · churn ' + pct(d.bajas, c.activos) + '%', barra: { pct: pct(c.activos, d.proy.cuentas), estado: juicio(c.activos, d.proy.cuentas), txt: pct(c.activos, d.proy.cuentas) + '% de ' + d.proy.cuentas + ' proyectados' }, ir: ['Ver clientes', 'recursos'] }) +
      '</div>';
    h += secundarias('ini-tpa', [
      secItem('Gastos', us(gastos), 'pauta propia, herramientas, Stripe', pct(gastos, cash)),
      secItem('Ganancia por socio', us(porSocio), cfg.socios.map(function (s) { return s.nombre + ' ' + s.pct + '%'; }).join(' · ')),
      secItem('Pauta propia (TPA)', us(d.pautaPropia), 'Meta y YouTube · proyectado ' + us(d.proy.pautaPropia)),
      secItem('Saldo de pauta Mateo → Luis', us(pautaSocios(cfg, d).saldo), 'pauta cargada a la tarjeta de Luis · 50% cada uno'),
      secItem('LTV estimado', us(ltv), 'setup + 8 meses de fee promedio'),
      secItem('Churn del mes', d.bajas + ' bajas', 'sobre ' + c.activos + ' clientes activos', pct(d.bajas, c.activos))
    ], ['Ver el detalle en Finanzas', 'finanzas']);
    var pc = pct(cash, d.proy.cash);
    h += '<div class="bloques">' +
      bloque('Proyección del mes', anillo(pc, us(cash) + ' de ' + us(d.proy.cash), 'Faltan ' + us(Math.max(0, d.proy.cash * AVANCE - cash)) + ' para ir al ritmo (la marca es dónde habría que estar hoy).', 'Pasó el ' + Math.round(AVANCE * 100) + '% del período') +
        lineas([['Cash collected', cash, d.proy.cash], ['Setups', c.setup, d.proy.setups * cfg.cobro.setup], ['Fees cobrados', c.pagado, d.proy.mrr], ['Flujo de caja neto', flujo, d.proy.flujo], ['Clientes nuevos', d.setups.length, d.proy.setups, true], ['Pauta propia', d.pautaPropia, d.proy.pautaPropia]]) +
        '<p class="ini-nota">Proyección de Indicadores: clientes × fee, setups y churn esperado.</p>', ['Ver proyección', 'indicadores'], ' ini-proyeccion" data-estado="' + juicio(cash, d.proy.cash)) +
      bloque('Ingresos por categoría', dona([['Fees mensuales', c.pagado, 'fees'], ['Setups', c.setup, 'setup']], 'Cash collected'), ['Ver finanzas', 'finanzas']) + '</div>';
    var mesesD = d.meses.slice(); mesesD[4] = [mesesD[4][0], cash, mesesD[4][2]];
    h += '<div class="bloques">' + bloque('Cash collected por mes', meses(mesesD, 'Nov 26'), ['Ver ingresos', 'finanzas']) +
      bloque('Ranking de clientes por retorno', ranking(d.cuentas.slice().sort(function (a, b) { return b.roi - a.roi; }).slice(0, 5).map(function (x) { return [x.n, x.roi, x.roi ? x.roi.toFixed(1) + 'x' : '—', x.citas + ' citas en el mes · fee ' + ({ pagado: 'pagado', pendiente: 'pendiente', vencido: 'vencido' })[x.estado]]; })), ['Ver cierres', 'bitacora']) + '</div>';
    h += '<div class="bloques">' + bloque('Alertas y accionables', alertas(d.alertas), null) + bloque('Tareas de hoy', tareas(d.tareas), ['Ver tareas', 'tareas']) + '</div>';
    h += '<div class="bloques">' + bloque('Actividad de hoy', actividad(d), ['Ver calendario', 'calendario']) + '<div></div></div>';
    return h;
  }

  // ---- Finanzas con socios: pauta propia cargada a la tarjeta de un socio y transferencias del otro ----
  function pautaSocios(cfg, d) {
    var gasto = d.pautaMov.reduce(function (a, m) { return a + m[3]; }, 0);
    var parte = {}; cfg.socios.forEach(function (s) { parte[s.nombre] = gasto * s.pct / 100; });
    var puso = {}; cfg.socios.forEach(function (s) { puso[s.nombre] = 0; });
    puso[d.pagadorPauta] += gasto;
    d.transferencias.forEach(function (t) { puso[t[1]] += t[3]; puso[t[2]] -= t[3]; });
    var otro = cfg.socios.filter(function (s) { return s.nombre !== d.pagadorPauta; })[0].nombre;
    return { gasto: gasto, parte: parte, puso: puso, otro: otro, transferido: d.transferencias.reduce(function (a, t) { return a + t[3]; }, 0), saldo: Math.max(0, parte[otro] - puso[otro]) };
  }
  function finanzasSocios(cfg, d) {
    var p = pautaSocios(cfg, d), pag = d.pagadorPauta;
    var h = cabecera('Finanzas', '{per} · Ingresos, gastos y socios · USD');
    h += '<div class="grilla" style="--n:4">' +
      tarjeta({ nombre: 'Gasto en pauta propia', clave: true, valor: us(p.gasto), sub: 'Meta + YouTube · cargado a la tarjeta de ' + pag }) +
      tarjeta({ nombre: 'Parte de cada socio', valor: us(p.gasto / cfg.socios.length), sub: cfg.socios.map(function (s) { return s.nombre + ' ' + s.pct + '%'; }).join(' · ') }) +
      tarjeta({ nombre: 'Transferido por ' + p.otro, valor: us(p.transferido), sub: d.transferencias.length + ' transferencias a ' + pag, barra: { pct: pct(p.transferido, p.parte[p.otro]), estado: p.saldo ? 'cerca' : 'cumple', txt: pct(p.transferido, p.parte[p.otro]) + '% de su parte (' + us(p.parte[p.otro]) + ')' } }) +
      tarjeta({ nombre: 'Saldo ' + p.otro + ' → ' + pag, valor: us(p.saldo), ambar: p.saldo > 0, sub: p.saldo ? 'lo que falta transferir para quedar 50/50' : 'al día: cada socio puso su parte' }) +
      '</div>';
    var max = Math.max.apply(null, cfg.socios.map(function (s) { return Math.max(p.puso[s.nombre], p.parte[s.nombre]); })) || 1;
    var aportes = '<div class="e33">' + cfg.socios.map(function (s) {
      var est = p.puso[s.nombre] >= p.parte[s.nombre] - 0.5 ? 'repartido' : 'pendiente';
      return '<div class="fin-cat" data-est="' + est + '"><span class="fin-cat-n">' + esc(s.nombre) + (s.nombre === pag ? ' · paga con su tarjeta' : ' · le transfiere a ' + pag) + '</span><span class="rend-barra"><span style="width:' + Math.max(2, p.puso[s.nombre] / max * 100) + '%"></span></span><span class="fin-cat-v">' + us(p.puso[s.nombre]) + ' <small>de ' + us(p.parte[s.nombre]) + '</small></span></div>';
    }).join('') + '<p class="ini-nota">Aporte neto a la pauta del período: lo que pagó cada uno, descontando lo que se transfirieron entre ellos.</p></div>';
    var mov = '<div class="rend-scroll"><table class="rend-tabla"><thead><tr><th>Fecha</th><th>Plataforma</th><th>Campaña</th><th class="rend-num">Gasto</th></tr></thead><tbody>' +
      d.pautaMov.slice().reverse().map(function (m) { return '<tr><td>' + m[0] + '</td><td>' + esc(m[1]) + '</td><td>' + esc(m[2]) + '</td><td class="rend-num">' + us(m[3]) + '</td></tr>'; }).join('') + '</tbody></table></div>';
    var trans = '<div class="rend-scroll"><table class="rend-tabla"><thead><tr><th>Fecha</th><th>De → a</th><th>Nota</th><th class="rend-num">Monto</th></tr></thead><tbody>' +
      d.transferencias.slice().reverse().map(function (t) { return '<tr><td>' + t[0] + '</td><td>' + esc(t[1]) + ' → ' + esc(t[2]) + '</td><td>' + esc(t[4]) + '</td><td class="rend-num">' + us(t[3]) + '</td></tr>'; }).join('') + '</tbody></table></div>';
    var form = '<form class="e57" id="form-transf"><label class="e100">Monto (US$)<input class="e182" name="monto" type="number" min="1" step="1" required placeholder="' + Math.round(p.saldo || 100) + '"></label>' +
      '<label class="e101">Nota<input class="e182" name="nota" type="text" placeholder="Mi parte, semana 3"></label><button class="fin-boton" type="submit">Registrar transferencia</button></form>';
    h += '<div class="bloques">' + bloque('Aportes de cada socio a la pauta', aportes, null) + bloque('Transferencias ' + p.otro + ' → ' + pag, form + trans, null) + '</div>';
    h += bloque('Gasto de la cuenta publicitaria', mov + '<p class="ini-nota">En la fase 1 el gasto se lee solo de Meta y YouTube; las transferencias se guardan en la base de finanzas (fase 4). En esta vista de ejemplo no quedan guardadas.</p>', null);
    h += '<section class="caja ini-bloque"><div class="ini-bloque-cab"><h3 class="fin-h3">Resto de Finanzas</h3><span class="fase">Fase F4</span></div><p class="e52" style="margin:0">' + esc(MENU_INFO.finanzas[1]) + '</p></section>';
    return h;
  }

  function enConstruccion(cfg, id) {
    var item = null; cfg.menus.forEach(function (g) { g.items.forEach(function (it) { if (it[0] === id) item = it; }); });
    if (!item) { estado.menu = 'resumen'; return inicio(); }
    var info = MENU_INFO[id] || ['—', ''];
    return '<header><div class="e19"><h1 class="titulo-1">' + esc(item[1]) + '</h1><span class="e30">' + esc(cfg.nombre) + '</span></div></header>' +
      '<section class="caja ini-bloque"><div class="ini-bloque-cab"><h3 class="fin-h3">Qué va a mostrar</h3><span class="fase">Fase ' + info[0] + '</span></div><p class="e52" style="margin:0">' + esc(info[1]) + '</p>' +
      '<button class="kpi-ir" type="button" data-ir="resumen">Volver al Inicio →</button></section>';
  }
  function inicio() { var cfg = NEGOCIOS[estado.negocio], d = DEMO[estado.negocio]; return cfg.modelo === 'comision' ? inicioComision(cfg, d) : inicioFee(cfg, d); }

  function titulo() { var t = 'Inicio'; NEGOCIOS[estado.negocio].menus.forEach(function (g) { g.items.forEach(function (it) { if (it[0] === estado.menu) t = it[1]; }); }); return t; }
  function render() {
    var cfg = NEGOCIOS[estado.negocio];
    document.documentElement.setAttribute('data-negocio', estado.negocio);
    var tema = document.getElementById('tema'); if (tema.getAttribute('href') !== 'temas/' + estado.negocio + '.css') tema.setAttribute('href', 'temas/' + estado.negocio + '.css');
    document.title = titulo() + ' · ' + cfg.nombre;
    lateral();
    document.getElementById('movil-titulo').textContent = titulo();
    document.getElementById('principal').innerHTML = estado.menu === 'resumen' ? inicio() : (estado.menu === 'finanzas' && cfg.socios.length > 1) ? finanzasSocios(cfg, DEMO[estado.negocio]) : enConstruccion(cfg, estado.menu);
    window.dcPostRender();
  }

  // ---- Eventos ----
  document.addEventListener('click', function (e) {
    var t = e.target.closest ? e.target : null; if (!t) return;
    var b;
    if ((b = t.closest('#neg-btn'))) { var m = document.getElementById('neg-menu'), ab = m.hidden; m.hidden = !ab; b.setAttribute('aria-expanded', String(ab)); return; }
    if ((b = t.closest('.neg-op[data-negocio]'))) {
      var n = b.getAttribute('data-negocio');
      if (n !== estado.negocio) { estado.negocio = n; guardar('suite_negocio', n); SONIDO.sonar('menu'); }
      document.documentElement.classList.remove('movil-menu'); render(); return;
    }
    if (!t.closest('[data-pop]')) { var mm = document.getElementById('neg-menu'); if (mm && !mm.hidden) { mm.hidden = true; document.getElementById('neg-btn').setAttribute('aria-expanded', 'false'); } }
    if ((b = t.closest('[data-grupo]'))) { var g = b.getAttribute('data-grupo'); estado.grupos[g] = estado.grupos[g] === 0 ? 1 : 0; guardar('suite_grupos', JSON.stringify(estado.grupos)); lateral(); return; }
    if ((b = t.closest('[data-ir]'))) { location.hash = b.getAttribute('data-ir'); return; }
    if ((b = t.closest('[data-vista]'))) { estado.vista = b.getAttribute('data-vista') === 'anio' ? 'anio' : 'mes'; render(); return; }
    if ((b = t.closest('[data-paso]'))) {
      var p = +b.getAttribute('data-paso');
      if (p === 0) { estado.mes = HOY.getMonth(); estado.anio = HOY.getFullYear(); }
      else if (estado.vista === 'anio') estado.anio += p;
      else { estado.mes += p; if (estado.mes < 0) { estado.mes = 11; estado.anio--; } if (estado.mes > 11) { estado.mes = 0; estado.anio++; } }
      render(); return;
    }
    if (t.closest('#sonido')) { var on = SONIDO.alternar(); t.closest('#sonido').setAttribute('aria-pressed', String(on)); return; }
    if (t.closest('#plegar')) { document.documentElement.classList.toggle('lat-mini'); guardar('suite_lat_mini', document.documentElement.classList.contains('lat-mini') ? '1' : '0'); return; }
    if (t.closest('#movil-menu-btn')) { document.documentElement.classList.add('movil-menu'); return; }
    if (t.closest('.movil-velo') || t.closest('.lateral nav a')) { document.documentElement.classList.remove('movil-menu'); }
  });
  document.addEventListener('submit', function (e) {
    if (e.target.id !== 'form-transf') return;
    e.preventDefault();
    var f = e.target, monto = Math.round(+f.monto.value), d = DEMO[estado.negocio], cfg = NEGOCIOS[estado.negocio];
    if (!(monto > 0)) return;
    var p = pautaSocios(cfg, d);
    d.transferencias.push([HOY.getDate() + ' nov', p.otro, d.pagadorPauta, monto, f.nota.value || 'Transferencia de pauta']);
    SONIDO.sonar('listo'); render();
  });
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    var mm = document.getElementById('neg-menu'); if (mm && !mm.hidden) { mm.hidden = true; document.getElementById('neg-btn').setAttribute('aria-expanded', 'false'); }
    document.documentElement.classList.remove('movil-menu');
  });
  window.addEventListener('hashchange', function () { estado.menu = (location.hash || '#resumen').slice(1); render(); window.scrollTo(0, 0); });
  if (leer('suite_lat_mini', '0') === '1') document.documentElement.classList.add('lat-mini');
  render();
})();
