import datetime as dt

from servidor import metricas

HOY = dt.date(2026, 11, 17)
CUENTAS = [{'id': 1, 'nombre': 'A', 'objetivo_costo_cita': None}, {'id': 2, 'nombre': 'B', 'objetivo_costo_cita': 30}]
DATOS = {
    'anuncios': [
        {'id': 'a1', 'nombre': 'Video 1', 'campana': 'C1', 'conjunto': '', 'cuenta_id': 1, 'plataforma': 'meta'},
        {'id': 'a2', 'nombre': 'Video 1', 'campana': 'C1', 'conjunto': '', 'cuenta_id': 1, 'plataforma': 'meta'},  # copia: se suma
        {'id': 'b1', 'nombre': 'Caro', 'campana': 'C2', 'conjunto': '', 'cuenta_id': 2, 'plataforma': 'youtube'},
    ],
    'gasto': [
        ['2026-11-16', 0, 100.0, 1000, 20, 10],
        ['2026-11-16', 1, 50.0, 500, 10, 5],
        ['2026-11-15', 2, 300.0, 3000, 30, 6],
        ['2026-11-08', 0, 100.0, 1000, 20, 10],  # período anterior (7 días)
    ],
    'citas': [
        # fecha_cita, minuto, creada, cuenta, tipo, estado, anuncio
        ['2026-11-16', 600, '2026-11-15', 1, 'calificacion', 'asistio', 0],
        ['2026-11-16', 630, '2026-11-16', 1, 'calificacion', 'no_asistio', 1],
        ['2026-11-15', 660, '2026-11-14', 1, 'calificacion', 'cancelada', 0],
        ['2026-11-14', 700, '2026-11-13', 1, 'calificacion', 'confirmada', 0],   # pasó y sigue sin marcar
        ['2026-11-19', 700, '2026-11-16', 1, 'calificacion', 'confirmada', 0],   # futura: no entra en tasas
        ['2026-11-16', 700, '2026-11-16', 1, 'calificacion', 'asistio', -1],     # sin anuncio: no cuenta como creada
        ['2026-11-16', 700, '2026-11-16', 1, 'principal', 'asistio', 0],         # otro paso del embudo
        ['2026-11-16', 700, '2026-11-15', 2, 'calificacion', 'asistio', 2],
        ['2026-11-09', 700, '2026-11-09', 1, 'calificacion', 'asistio', 0],      # período anterior
    ],
}


def test_numeros_base_y_tasas():
    r = metricas.panel(DATOS, CUENTAS, dt.date(2026, 11, 11), HOY, 'calificacion', 50, HOY)
    k = r['kpi']
    assert k['gasto']['valor'] == 450
    assert k['leads']['valor'] == 21
    assert k['citas']['valor'] == 6  # creadas en el período con anuncio, del paso medido
    assert round(k['costo_cita']['valor'], 2) == 75
    assert round(k['costo_lead']['valor'], 2) == round(450 / 21, 2)
    # asistencia sobre pasadas: asistio(1 + sin anuncio 1 + B 1) / (3 asistio + 1 no + 1 cancelada)
    assert k['pct_asistencia']['valor'] == 60
    assert r['agenda']['sin_marcar'] == 1


def test_comparacion_contra_periodo_anterior():
    r = metricas.panel(DATOS, CUENTAS, dt.date(2026, 11, 11), HOY, 'calificacion', 50, HOY)
    assert r['anterior'] == {'desde': '2026-11-04', 'hasta': '2026-11-10'}
    assert r['kpi']['gasto']['anterior'] == 100
    assert round(r['kpi']['gasto']['cambio']) == 350


def test_semaforo_y_objetivo_por_cuenta():
    r = metricas.panel(DATOS, CUENTAS, dt.date(2026, 11, 11), HOY, 'calificacion', 50, HOY)
    est = {f['nombre']: f['estado'] for f in r['cuentas']}
    assert est['A'] == 'bien'      # 150 / 5 = 30 <= 50
    assert est['B'] == 'critico'   # 300 / 1 = 300 > 30 * 1.3 (objetivo propio de la cuenta)


def test_veredictos():
    assert metricas.veredicto(100, 5, 50) == 'escalar'
    assert metricas.veredicto(100, 2, 60) == 'mantener'
    assert metricas.veredicto(160, 2, 50) == 'revisar'
    assert metricas.veredicto(300, 1, 50) == 'pausar'
    assert metricas.veredicto(80, 0, 50) == 'pausar'
    assert metricas.veredicto(20, 0, 50) == 'sin_datos'


def test_trazabilidad_suma_copias_y_filtra_accionables():
    t = metricas.trazabilidad(DATOS, CUENTAS, dt.date(2026, 11, 11), HOY, 'calificacion', 50)
    nombres = {(a['cuenta'], a['anuncio']): a for a in t['anuncios']}
    # con dos cuentas solo aparece lo accionable: "Video 1" (30 por cita, 5 citas) escala; "Caro" se pausa
    assert nombres[('A', 'Video 1')]['gasto'] == 150 and nombres[('A', 'Video 1')]['citas'] == 5
    assert nombres[('A', 'Video 1')]['veredicto'] == 'escalar'
    assert nombres[('B', 'Caro')]['veredicto'] == 'pausar'
    assert t['sin_anuncio'] == 1
    assert t['mejor']['anuncio'] == 'Video 1'


def test_rango_que_llega_al_futuro_compara_solo_lo_pasado():
    r = metricas.panel(DATOS, CUENTAS, dt.date(2026, 11, 11), dt.date(2026, 11, 24), 'calificacion', 50, HOY)
    assert r['anterior'] == {'desde': '2026-11-04', 'hasta': '2026-11-10'}


def test_sin_datos_no_rompe():
    vacio = {'anuncios': [], 'gasto': [], 'citas': []}
    r = metricas.panel(vacio, CUENTAS, dt.date(2026, 11, 11), HOY, 'calificacion', 50, HOY)
    assert r['kpi']['costo_cita']['valor'] is None
    assert all(f['estado'] == 'sin_datos' for f in r['cuentas'])
