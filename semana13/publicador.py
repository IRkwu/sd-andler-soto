"""publicador.py, publica operaciones del dominio del equipo en una cola durable.

Uso (siempre a traves de docker compose run, desde la carpeta semana13)
    docker compose run --rm publicador AGREGAR tornillo 5
    docker compose run --rm publicador --n 20 AGREGAR tornillo 1
    docker compose run --rm -e PERSISTENTE=0 publicador --n 5 LISTAR

Cada mensaje es un JSON con la forma
    {"id": 7, "op": "AGREGAR", "args": ["tornillo", "1"], "origen": "a1b2c3", "t": 1731..}

Variables de entorno
    COLA         nombre de la cola (por defecto operaciones)
    PERSISTENTE  1 publica mensajes persistentes, 0 transientes (por defecto 1)
"""
import argparse
import os
import time

from cola import conectar, declarar_cola, env_bool, log, nombre_cola, nombre_nodo, publicar

COLA = nombre_cola(os.environ.get("COLA", "operaciones"))


def main():
    p = argparse.ArgumentParser(description="Publica operaciones en una cola")
    p.add_argument("--n", type=int, default=1, help="cuantas veces repetir la operacion")
    p.add_argument("op", help="nombre de la operacion, por ejemplo AGREGAR")
    p.add_argument("args", nargs="*", help="argumentos de la operacion")
    a = p.parse_args()

    persistente = env_bool("PERSISTENTE", "1")
    conexion = conectar()
    canal = conexion.channel()
    declarar_cola(canal, COLA)

    for i in range(1, a.n + 1):
        mensaje = {
            "id": i,
            "op": a.op.upper(),
            "args": a.args,
            "origen": nombre_nodo(),
            "t": time.time(),
        }
        publicar(canal, COLA, mensaje, persistente=persistente)
        log(f"publicado id={i} op={mensaje['op']} args={a.args} persistente={persistente}")

    conexion.close()
    log(f"listo, {a.n} mensaje(s) en la cola '{COLA}'")


if __name__ == "__main__":
    main()
