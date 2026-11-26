"""graficar.py, calcula speedup y eficiencia desde mediciones/mediciones.csv
y dibuja mediciones/speedup.svg. Solo usa la biblioteca estandar.

Uso
    docker compose run --rm graficar

Para cada cantidad de workers p se usa el promedio de las corridas validas.
    speedup     S(p) = T(1) / T(p)
    eficiencia  E(p) = S(p) / p
    Karp-Flatt  e(p) = (1/S - 1/p) / (1 - 1/p)   fraccion serial estimada
"""
import csv
import os
from collections import defaultdict

CARPETA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mediciones")
ENTRADA = os.path.join(CARPETA, "mediciones.csv")
SALIDA = os.path.join(CARPETA, "speedup.svg")


def cargar():
    tiempos = defaultdict(list)
    with open(ENTRADA, encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            if fila["ok"].strip().lower() != "true":
                continue
            tiempos[int(fila["workers"])].append(float(fila["segundos"]))
    return {p: sum(v) / len(v) for p, v in sorted(tiempos.items())}, tiempos


def svg(puntos, ruta):
    ancho, alto, m = 640, 420, 60
    pmax = max(max(p for p, _ in puntos), 4)
    smax = max(pmax, max(s for _, s in puntos)) * 1.05

    def x(p):
        return m + (p - 1) / (pmax - 1) * (ancho - 2 * m) if pmax > 1 else m

    def y(s):
        return alto - m - (s / smax) * (alto - 2 * m)

    partes = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{ancho}" height="{alto}" font-family="Calibri, Arial" font-size="13">',
        f'<rect width="{ancho}" height="{alto}" fill="white"/>',
        f'<text x="{ancho / 2}" y="28" text-anchor="middle" font-size="17" font-weight="bold">Speedup medido frente al ideal</text>',
        f'<line x1="{m}" y1="{alto - m}" x2="{ancho - m}" y2="{alto - m}" stroke="#333"/>',
        f'<line x1="{m}" y1="{alto - m}" x2="{m}" y2="{m}" stroke="#333"/>',
        f'<text x="{ancho / 2}" y="{alto - 18}" text-anchor="middle">workers (p)</text>',
        f'<text x="18" y="{alto / 2}" text-anchor="middle" transform="rotate(-90 18 {alto / 2})">speedup S(p)</text>',
    ]
    for p in range(1, pmax + 1):
        partes.append(f'<line x1="{x(p)}" y1="{alto - m}" x2="{x(p)}" y2="{alto - m + 5}" stroke="#333"/>')
        partes.append(f'<text x="{x(p)}" y="{alto - m + 20}" text-anchor="middle">{p}</text>')
    s = 0.0
    while s <= smax:
        partes.append(f'<line x1="{m - 5}" y1="{y(s)}" x2="{ancho - m}" y2="{y(s)}" stroke="#e5e5e5"/>')
        partes.append(f'<text x="{m - 10}" y="{y(s) + 4}" text-anchor="end">{s:.0f}</text>')
        s += 1.0
    # ideal
    partes.append(f'<line x1="{x(1)}" y1="{y(1)}" x2="{x(pmax)}" y2="{y(pmax)}" stroke="#999" stroke-dasharray="6 4" stroke-width="2"/>')
    partes.append(f'<text x="{x(pmax) - 6}" y="{y(pmax) - 8}" text-anchor="end" fill="#777">ideal S = p</text>')
    # medido
    camino = " ".join(f"{x(p)},{y(sp)}" for p, sp in puntos)
    partes.append(f'<polyline points="{camino}" fill="none" stroke="#C1272D" stroke-width="3"/>')
    for p, sp in puntos:
        partes.append(f'<circle cx="{x(p)}" cy="{y(sp)}" r="5" fill="#C1272D"/>')
        partes.append(f'<text x="{x(p) + 8}" y="{y(sp) + 16}" fill="#C1272D">{sp:.2f}</text>')
    partes.append("</svg>")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("\n".join(partes))


def main():
    if not os.path.exists(ENTRADA):
        print("No existe mediciones/mediciones.csv. Primero ejecuten master.py con 1, 2, 3 y 4 workers.")
        return
    promedios, todos = cargar()
    if 1 not in promedios:
        print("Falta al menos una corrida valida con 1 worker, que es la base T(1).")
        return
    t1 = promedios[1]
    print(f"{'p':>3}{'corridas':>10}{'T(p) s':>10}{'S(p)':>8}{'E(p)':>8}{'Karp-Flatt':>12}")
    puntos = []
    for p, tp in promedios.items():
        sp = t1 / tp
        ep = sp / p
        kf = (1 / sp - 1 / p) / (1 - 1 / p) if p > 1 else float("nan")
        kf_txt = "-" if p == 1 else f"{kf:.3f}"
        print(f"{p:>3}{len(todos[p]):>10}{tp:>10.2f}{sp:>8.2f}{ep:>8.2f}{kf_txt:>12}")
        puntos.append((p, sp))
    svg(puntos, SALIDA)
    print("Grafico guardado en mediciones/speedup.svg (se abre con el navegador)")


if __name__ == "__main__":
    main()
