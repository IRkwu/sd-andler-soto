"""bench_codec.py — medición comparada JSON vs binario (Semana 9, paso 3).

Codifica y decodifica N solicitudes del dominio del equipo con cada codec y
reporta tamaño promedio y tiempo total. No usa la red, mide solo el costo de
serializar. Copien la tabla resultante en observaciones.md.

Uso:  python bench_codec.py [N]
"""
import random
import sys
import time

from mensajes import Solicitud, Respuesta, OPERACIONES
import codec

N = int(sys.argv[1]) if len(sys.argv) > 1 else 10_000
random.seed(9)

# Argumentos de ejemplo. Cambien PRODUCTOS por los datos de su dominio.
VEHICULOS = ["moto1", "moto2"]
OPS = [o for o in OPERACIONES if o not in ("HOLA", "SALIR", "ESPERA")]

def solicitud_aleatoria(i):
    op = random.choice(OPS)
    vehiculo = random.choice(VEHICULOS)
    lat = f"{random.uniform(-41.50, -41.40):.5f}"
    lon = f"{random.uniform(-73.00, -72.90):.5f}"

    if op == "POSICION":
        args = [vehiculo, lat, lon]
    elif op == "DONDE":
        args = [vehiculo]
    elif op in ("PEDIDO", "CERCANO"):
        args = [lat, lon]
    elif op == "TOMAR":
        args = [vehiculo, f"p{random.randint(1, 100)}"]

    return Solicitud(
        operacion=op,
        argumentos=args,
        id=i,
    )

def respuesta_aleatoria(sol):
    if sol.operacion == "POSICION":
        datos = list(sol.argumentos)

    elif sol.operacion == "DONDE":
        datos = [
            sol.argumentos[0],
            f"{random.uniform(-41.50, -41.40):.5f}",
            f"{random.uniform(-73.00, -72.90):.5f}",
        ]

    elif sol.operacion == "PEDIDO":
        datos = [f"p{sol.id + 2}", "pendiente"]

    elif sol.operacion == "TOMAR":
        datos = list(sol.argumentos)

    elif sol.operacion == "CERCANO":
        datos = [
            random.choice(VEHICULOS),
            f"distancia={random.uniform(0, 0.1):.4f}",
        ]

    return Respuesta(
        id=sol.id,
        estado="OK",
        datos=datos,
    )


def medir(nombre, mensajes, clase):
    cod, dec = codec.CODECS[nombre]
    t0 = time.perf_counter()
    cuerpos = [cod(m) for m in mensajes]
    t1 = time.perf_counter()
    for c in cuerpos:
        dec(c, clase)
    t2 = time.perf_counter()
    bytes_total = sum(len(c) for c in cuerpos)
    return {
        "bytes_prom": bytes_total / len(mensajes),
        "bytes_total": bytes_total,
        "t_cod_ms": (t1 - t0) * 1000,
        "t_dec_ms": (t2 - t1) * 1000,
    }


def main():
    sols = [solicitud_aleatoria(i) for i in range(N)]
    resps = [respuesta_aleatoria(sol) for sol in sols]
    print(f"N = {N} solicitudes y {N} respuestas del dominio\n")
    print("| Mensaje   | Codec | Bytes promedio | Bytes totales | Codificar (ms) | Decodificar (ms) |")
    print("|-----------|-------|---------------:|--------------:|---------------:|-----------------:|")
    filas = {}
    for etiqueta, msgs, clase in (("Solicitud", sols, Solicitud), ("Respuesta", resps, Respuesta)):
        for nombre in ("json", "bin"):
            r = medir(nombre, msgs, clase)
            filas[(etiqueta, nombre)] = r
            print(f"| {etiqueta:9s} | {nombre:5s} | {r['bytes_prom']:14.1f} | {r['bytes_total']:13d} | {r['t_cod_ms']:14.1f} | {r['t_dec_ms']:16.1f} |")
    print()
    for etiqueta in ("Solicitud", "Respuesta"):
        j, b = filas[(etiqueta, "json")], filas[(etiqueta, "bin")]
        ahorro = 100 * (1 - b["bytes_total"] / j["bytes_total"])
        print(f"{etiqueta}: el binario ocupa {ahorro:.0f}% menos bytes que JSON "
              f"(JSON {j['bytes_prom']:.0f} B vs bin {b['bytes_prom']:.0f} B por mensaje)")
    print("\nEjemplo de una misma solicitud en cada codec")
    s = sols[0]
    for nombre in ("json", "bin"):
        c = codec.codificar(s, nombre)
        print(f"  {nombre:5s} {len(c):3d} B  {c!r}")


if __name__ == "__main__":
    main()
