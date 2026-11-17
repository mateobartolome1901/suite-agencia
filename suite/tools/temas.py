"""Genera un CSS por negocio a partir de marca.css (el de la suite original) y app.css.

Regla del kit: con otra marca cambian SOLO los colores. Radios, sombras, curvas, tamaños, animaciones y estructura
quedan idénticos. Como marca.css también tiene colores de marca escritos sueltos (rgba de la menta, del acento, del
dorado…), no alcanza con cambiar :root: este script reemplaza cada color de marca por su equivalente en cada negocio.
Los colores de estado (verde, rojo, ámbar), las categorías y los íconos del menú no se tocan.

Uso:  python tools/temas.py        (escribe temas/<negocio>.css)
"""
import os
import re

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)

# Original (Growth) -> cada negocio. Hex en mayúscula; los rgba se escriben como 'r,g,b'.
TEMAS = {
    # Plastia Partners: verde petróleo, menta y coral (presentación de Plastia)
    'plastia': {
        'hex': {
            '#0E1612': '#0B1715', '#121C17': '#0F1D1A', '#17231D': '#13231F', '#1D2B24': '#182C27', '#25362E': '#213A33',
            '#22302A': '#1D302B', '#2A3B33': '#263D37', '#3A4F44': '#355048', '#13201A': '#10221E', '#0B1712': '#0A1614',
            '#EDF2EF': '#EEF4F2', '#C7D4CC': '#C4D6D1', '#98A79F': '#93A8A2', '#80908A': '#7D918B', '#4A5650': '#46574F',
            '#4A7A63': '#1F7A66', '#8FC4AA': '#8FD6C1', '#D7ECE2': '#BFF3E2', '#EAF5EF': '#E6FAF3', '#0E2A1F': '#0B2620',
            '#6F9C86': '#5FA894',
            # especial (en el original, dorado): coral de Plastia
            '#D6A743': '#E08A58', '#EEC567': '#F6C3A3', '#8C6420': '#9A5530', '#1B2118': '#221A15',
        },
        'rgb': {
            '143,196,170': '143,214,193', '74,122,99': '31,122,102', '205,235,220': '191,243,226', '215,236,226': '191,243,226',
            '29,45,37': '24,44,39', '14,22,18': '11,23,21', '14,42,31': '11,38,32', '4,8,6': '3,8,7', '128,144,138': '125,145,139',
            '214,167,67': '224,138,88', '246,214,140': '246,195,163',
        },
        'luces': 'radial-gradient(900px 620px at 88% -8%, rgba(143, 214, 193, 0.15), transparent 62%), radial-gradient(760px 560px at 22% 4%, rgba(31, 122, 102, 0.22), transparent 64%), radial-gradient(820px 640px at 4% 92%, rgba(224, 138, 88, 0.06), transparent 60%), radial-gradient(700px 520px at 96% 78%, rgba(31, 122, 102, 0.1), transparent 62%), linear-gradient(180deg, #10221E, #0B1715 65%)',
    },
    # Top Producer Acquisition: negro, rojo y dorado (landing de Realtor Millonario)
    'tpa': {
        'hex': {
            '#0E1612': '#070707', '#121C17': '#0C0C0C', '#17231D': '#131313', '#1D2B24': '#1A1919', '#25362E': '#2A1515',
            '#22302A': '#1F1F1F', '#2A3B33': '#2B2A2A', '#3A4F44': '#433636', '#13201A': '#170808', '#0B1712': '#160505',
            '#EDF2EF': '#F3F3F3', '#C7D4CC': '#D2D2D2', '#98A79F': '#A6A6A6', '#80908A': '#8F8F8F', '#4A5650': '#555555',
            '#4A7A63': '#C40000', '#8FC4AA': '#FF4040', '#D7ECE2': '#FFB8B8', '#EAF5EF': '#FFE8E8', '#0E2A1F': '#1F0000',
            '#6F9C86': '#B85050',
            # especial: dorado de la landing
            '#D6A743': '#F2C230', '#EEC567': '#FFDC46', '#8C6420': '#8F6A00', '#1B2118': '#1C1708',
        },
        'rgb': {
            '143,196,170': '255,64,64', '74,122,99': '196,0,0', '205,235,220': '255,225,225', '215,236,226': '255,200,200',
            '29,45,37': '34,26,26', '14,22,18': '7,7,7', '14,42,31': '31,0,0', '4,8,6': '0,0,0', '128,144,138': '143,143,143',
            '214,167,67': '242,194,48', '246,214,140': '255,226,120',
        },
        'luces': 'radial-gradient(900px 620px at 88% -8%, rgba(255, 0, 0, 0.14), transparent 62%), radial-gradient(760px 560px at 22% 4%, rgba(185, 0, 0, 0.16), transparent 64%), radial-gradient(820px 640px at 4% 92%, rgba(255, 210, 0, 0.05), transparent 60%), radial-gradient(700px 520px at 96% 78%, rgba(255, 0, 0, 0.08), transparent 62%), linear-gradient(180deg, #170808, #070707 65%)',
    },
}

RGBA = re.compile(r'rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,')
HEX = re.compile(r'#[0-9A-Fa-f]{6}\b')


def tematizar(css, t):
    css = HEX.sub(lambda m: t['hex'].get(m.group(0).upper(), m.group(0)), css)
    # el ícono del divisor está en un data-uri (%238FC4AA)
    css = re.sub(r'%23([0-9A-Fa-f]{6})', lambda m: '%23' + t['hex'].get('#' + m.group(1).upper(), '#' + m.group(1)).lstrip('#'), css)

    def rgba(m):
        clave = ','.join(m.group(i) for i in (1, 2, 3))
        nuevo = t['rgb'].get(clave)
        return 'rgba(' + nuevo.replace(',', ', ') + ',' if nuevo else m.group(0)
    return RGBA.sub(rgba, css)


def main():
    marca = open(os.path.join(RAIZ, 'marca.css'), encoding='utf-8').read()
    app = open(os.path.join(RAIZ, 'app.css'), encoding='utf-8').read()
    os.makedirs(os.path.join(RAIZ, 'temas'), exist_ok=True)
    for nombre, t in TEMAS.items():
        salida = '/* Generado por tools/temas.py desde marca.css + app.css: solo cambian los colores. No editar a mano. */\n'
        salida += tematizar(marca, t) + '\n' + tematizar(app, t)
        salida += '\n/* Luces del fondo de este negocio (las del original usan el verde de estado como luz) */\n.app::before { background: ' + t['luces'] + '; }\n'
        with open(os.path.join(RAIZ, 'temas', nombre + '.css'), 'w', encoding='utf-8') as f:
            f.write(salida)
        print('temas/' + nombre + '.css')


if __name__ == '__main__':
    main()
