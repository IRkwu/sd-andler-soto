"""master.py, master del patron master-worker.

1. Vacia las colas de corridas anteriores.
2. Pregunta al broker cuantos workers hay conectados a tareas_primos.
3. Parte el rango [2, N) en TROZOS tareas del mismo ancho y las publica.
4. Junta los resultados, valida el total contra una criba local y mide el tiempo.
5. Agrega una fila a mediciones/mediciones.csv.

Uso
    docker compose up -d --scale worker=2 worker
    docker compose run --rm master

Variables de entorno
    N        limite superior del rango (por defecto 5000000)
    TROZOS   cantidad de tareas (por defecto 40)
"""
import csv
import os
import time
from collections import defaultdict

from cola import conectar, declarar_cola, leer, log, nombre_cola, publicar

COLA_TAREAS = nombre_cola("tareas_primos")
COLA_RESULTADOS = nombre_cola("resultados_primos")
N = int(os.environ.get("N", "5000000"))
TROZOS = int(os.environ.get("TROZOS", "40"))
ARCHIVO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mediciones", "mediciones.csv")


def criba(n):
    """Cuenta los primos menores que n con la criba de Eratostenes (referencia)."""
    marcas = bytearray([1]) * n
    marcas[0:2] = b"\x00\x00"
    i = 2
    while i * i < n:
        if marcas[i]:
            marcas[i * i::i] = bytearray(len(range(i * i, n, i)))
        i += 1
    return sum(marcas)


def esperar_workers(canal, limite=30):
    """Espera a que el numero de workers conectados se estabilice.

    Despues de un  docker compose up --scale  los workers nuevos tardan un par
    de segundos en conectarse. Se considera estable cuando la cuenta no cambia
    en tres consultas seguidas (unos 3 s) y hay al menos un worker.
    """
    previo, iguales = -1, 0
    for _ in range(limite):
        workers = declarar_cola(canal, COLA_TAREAS).method.consumer_count
        if workers == 0:
            log("todavia no hay workers conectados, espero...")
        iguales = iguales + 1 if workers == previo else 0
        if workers > 0 and iguales >= 2:
            return workers
        previo = workers
        time.sleep(1)
    return previo if previo > 0 else 0


def main():
    conexion = conectar()
    canal = conexion.channel()
    declarar_cola(canal, COLA_TAREAS)
    declarar_cola(canal, COLA_RESULTADOS)
    canal.queue_purge(COLA_TAREAS)
    canal.queue_purge(COLA_RESULTADOS)

    log(f"calculando la referencia con una criba local para N={N:,} ...")
    esperado = criba(N)

    workers = esperar_workers(canal)
    if workers == 0:
        log("no hay workers. Levantelos con  docker compose up -d --scale worker=2 worker")
        return
    log(f"workers conectados {workers}, trozos {TROZOS}")

    corrida = f"{int(time.time())}"
    ancho = (N - 2 + TROZOS - 1) // TROZOS
    t0 = time.perf_counter()
    for i in range(TROZOS):
        inicio = 2 + i * ancho
        fin = min(N, inicio + ancho)
        publicar(canal, COLA_TAREAS, {"corrida": corrida, "id": i, "inicio": inicio, "fin": fin})

    total = 0
    recibidos = set()
    por_worker = defaultdict(lambda: [0, 0.0])
    for metodo, _, cuerpo in canal.consume(COLA_RESULTADOS, inactivity_timeout=120):
        if metodo is None:
            log("pasaron 120 s sin resultados, corto la corrida")
            break
        r = leer(cuerpo)
        canal.basic_ack(metodo.delivery_tag)
        if r["corrida"] != corrida or r["id"] in recibidos:
            continue  # resultado viejo o duplicado por una reentrega
        recibidos.add(r["id"])
        total += r["cantidad"]
        por_worker[r["worker"]][0] += 1
        por_worker[r["worker"]][1] += r["segundos"]
        if len(recibidos) == TROZOS:
            break
    segundos = time.perf_counter() - t0
    canal.cancel()

    ok = total == esperado and len(recibidos) == TROZOS
    log("-" * 58)
    log(f"{'worker':<10}{'trozos':>8}{'seg ocupado':>14}")
    for w, (n_trozos, seg) in sorted(por_worker.items()):
        log(f"{w:<10}{n_trozos:>8}{seg:>14.2f}")
    log("-" * 58)
    log(f"workers={workers}  tiempo total={segundos:.2f}s  primos={total:,}  esperado={esperado:,}  ok={ok}")

    os.makedirs(os.path.dirname(ARCHIVO), exist_ok=True)
    nuevo = not os.path.exists(ARCHIVO)
    with open(ARCHIVO, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if nuevo:
            w.writerow(["fecha", "workers", "n", "trozos", "segundos", "primos", "ok"])
        w.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), workers, N, TROZOS, f"{segundos:.3f}", total, ok])
    log(f"fila agregada a mediciones/mediciones.csv")
    conexion.close()


if __name__ == "__main__":
    main()
