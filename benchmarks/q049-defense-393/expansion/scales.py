import json
from pathlib import Path
from math import pi

G = 6.67430e-11
C = 299792458.0
MS = 1.98847e30


def circular(name, m1, m2, separation):
    power = 32 / 5 * G**4 * m1**2 * m2**2 * (m1 + m2) / (C**5 * separation**5)
    time = 5 / 256 * C**5 * separation**4 / (G**3 * m1 * m2 * (m1 + m2))
    return {'system': name, 'masses_kg': [m1, m2], 'separation_m': separation,
            'gw_frequency_Hz': (G * (m1 + m2) / separation**3)**0.5 / pi,
            'power_W': power, 'formal_inspiral_s': time, 'formal_inspiral_years': time / 31557600,
            'separation_over_GM_c2': separation * C**2 / (G * (m1 + m2))}


if __name__ == '__main__':
    separation = (G * 60 * MS / (pi * 2)**2)**(1 / 3)
    result = {'approximation': 'isolated circular binary; leading quadrupole; fixed masses',
              'systems': [circular('Sun-Earth', MS, 5.9722e24, 149597870700.0),
                          circular('30+30 solar masses at 2 Hz', 30 * MS, 30 * MS, separation)],
              'limits': 'formal integration extrapolates the approximation beyond its valid range; excludes solar evolution and strong-field merger'}
    Path('/work/scales.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
