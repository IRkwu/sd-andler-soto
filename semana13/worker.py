"""worker.py, worker del patron master-worker. Cuenta primos en un rango.

Toma una tarea de la cola tareas_primos, cuenta los primos en [inicio, fin),
publica el resultado en resultados_primos y recien ahi confirma (ack).
Con prefetch=1 cada worker tiene a lo mas una tarea a la vez, asi el reparto
es justo aunque los trozos cuesten distinto.

Se escala con
    docker compose up -d --scale worker=3 worker
"""
import os
import signal
import sys
import time

from cola import conectar, declarar_cola, leer, log, nombre_cola, nombre_nodo, publicar

COLA_TAREAS = nombre_cola("tareas_primos")
COLA_RESULTADOS = nombre_cola("resultados_primos")
PREFETCH = int(os.environ.get("PREFETCH", "1"))


def es_primo(n):
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    d = 3
    while d * d <= n:
        if n % d == 0:
            return False
        d += 2
    return True


def contar_primos(inicio, fin):
    return sum(1 for n in range(inicio, fin) if es_primo(n))


def main():
    conexion = conectar()
    canal = conexion.channel()
    declarar_cola(canal, COLA_TAREAS)
    declarar_cola(canal, COLA_RESULTADOS)
    canal.basic_qos(prefetch_count=PREFETCH)

    def al_recibir(ch, metodo, propiedades, cuerpo):
        tarea = leer(cuerpo)
        t0 = time.perf_counter()
        cantidad = contar_primos(tarea["inicio"], tarea["fin"])
        segundos = time.perf_counter() - t0
        publicar(ch, COLA_RESULTADOS, {
            "corrida": tarea["corrida"],
            "id": tarea["id"],
            "cantidad": cantidad,
            "worker": nombre_nodo(),
            "segundos": segundos,
        })
        ch.basic_ack(delivery_tag=metodo.delivery_tag)
        log(f"trozo {tarea['id']:>3} [{tarea['inicio']:>9},{tarea['fin']:>9}) -> {cantidad:>6} primos en {segundos:5.2f}s")

    def detener(*_):
        try:
            canal.stop_consuming()
        except Exception:
            pass

    signal.signal(signal.SIGTERM, detener)
    canal.basic_consume(queue=COLA_TAREAS, on_message_callback=al_recibir)
    log(f"worker listo, prefetch={PREFETCH}")
    try:
        canal.start_consuming()
    finally:
        try:
            conexion.close()
        except Exception:
            pass
        sys.exit(0)


if __name__ == "__main__":
    main()
