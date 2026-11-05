"""servidor.py — servidor TCP con hilo por cliente y mensajes estructurados (Semana 9).

Evoluciona el servidor de la semana 6/7. Cambia solo la forma de leer y
escribir mensajes. Antes, una línea de texto. Ahora, un mensaje enmarcado y
codificado con codec.py (JSON o binario según la variable CODEC).

El dominio de referencia es un inventario (LISTAR, AGREGAR, QUITAR). Cada
equipo reemplaza esas operaciones por las de su propio servicio.
"""
import json
import os
import socket
import struct
import threading
import time

import codec
from mensajes import Solicitud, VERSION, ok, error

HOST = "0.0.0.0"
PUERTO = int(os.environ.get("SERVIDOR_PUERTO", "5000"))
TIMEOUT = float(os.environ.get("TIMEOUT_SERVIDOR", "30"))

estado = {
    "vehiculos": {
        "moto1": (-41.47, -72.94),
        "moto2": (-41.46, -72.95),
    },
    "pedidos": {
        "p1": {
            "destino": (-41.45, -72.93),
            "asignado": None,
        },
    },
    "siguiente_id": 2,
    "operaciones": 0,
}
lock = threading.Lock()


def log(*args):
    print(time.strftime("%H:%M:%S"), f"[{threading.current_thread().name}]", *args, flush=True)


# ---------------------------------------------------------------- dominio
def procesar(sol):
    """Procesa una solicitud de geolocalización y despacho."""
    op = sol.operacion.upper()
    args = sol.argumentos

    if op == "HOLA":
        nombre = " ".join(args) or "anonimo"
        return ok(sol, ["HOLA", nombre])

    if op == "SALIR":
        return ok(sol, ["CHAO"])

    operaciones = (
        "POSICION", "DONDE", "PEDIDO",
        "TOMAR", "CERCANO", "ESPERA",
    )

    if op not in operaciones:
        return error(sol.id, "COMANDO_DESCONOCIDO")

    with lock:
        estado["operaciones"] += 1

    # Estas tres operaciones reciben coordenadas.
    if op in ("POSICION", "PEDIDO", "CERCANO"):
        cantidad = 3 if op == "POSICION" else 2

        if len(args) != cantidad:
            return error(
                sol.id,
                f"FORMATO {op} requiere {cantidad} argumentos",
            )

        try:
            lat = float(args[-2])
            lon = float(args[-1])
        except ValueError:
            return error(sol.id, "FORMATO coordenadas invalidas")

        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return error(
                sol.id,
                "FORMATO coordenadas fuera de rango",
            )

    if op == "POSICION":
        vehiculo = args[0].lower()

        with lock:
            estado["vehiculos"][vehiculo] = (lat, lon)

        return ok(sol, [vehiculo, str(lat), str(lon)])

    if op == "DONDE":
        if len(args) != 1 or not args[0].strip():
            return error(sol.id, "FORMATO DONDE vehiculo")

        vehiculo = args[0].strip().lower()

        with lock:
            posicion = estado["vehiculos"].get(vehiculo)

        if posicion is None:
            return error(sol.id, "VEHICULO_NO_EXISTE")

        return ok(
            sol,
            [vehiculo, str(posicion[0]), str(posicion[1])],
        )

    if op == "PEDIDO":
        with lock:
            id_pedido = f"p{estado['siguiente_id']}"
            estado["siguiente_id"] += 1
            estado["pedidos"][id_pedido] = {
                "destino": (lat, lon),
                "asignado": None,
            }

        return ok(sol, [id_pedido, "pendiente"])

    if op == "TOMAR":
        if len(args) != 2:
            return error(sol.id, "FORMATO TOMAR vehiculo pedido")

        vehiculo = args[0].lower()
        id_pedido = args[1].lower()

        with lock:
            if vehiculo not in estado["vehiculos"]:
                return error(sol.id, "VEHICULO_NO_EXISTE")

            pedido = estado["pedidos"].get(id_pedido)

            if pedido is None:
                return error(sol.id, "PEDIDO_NO_EXISTE")

            if pedido["asignado"] is not None:
                return error(
                    sol.id,
                    f"YA_ASIGNADO {pedido['asignado']}",
                )

            pedido["asignado"] = vehiculo

        return ok(sol, [vehiculo, id_pedido])

    if op == "CERCANO":
        with lock:
            if not estado["vehiculos"]:
                return error(sol.id, "SIN_VEHICULOS")

            vehiculo = min(
                estado["vehiculos"],
                key=lambda v: (
                    (estado["vehiculos"][v][0] - lat) ** 2
                    + (estado["vehiculos"][v][1] - lon) ** 2
                ),
            )

            posicion = estado["vehiculos"][vehiculo]
            distancia = (
                (posicion[0] - lat) ** 2
                + (posicion[1] - lon) ** 2
            ) ** 0.5

        return ok(
            sol,
            [vehiculo, f"distancia={distancia:.4f}"],
        )

    if op == "ESPERA":
        if len(args) != 1:
            return error(sol.id, "FORMATO ESPERA segundos")

        try:
            segundos = float(args[0])
            time.sleep(segundos)
        except (ValueError, OverflowError):
            return error(sol.id, "FORMATO segundos invalidos")

        return ok(sol, ["ESPERA", args[0]])


# ---------------------------------------------------------------- conexión
def atender(conn, addr):
    conn.settimeout(TIMEOUT)
    log("conectado", addr)
    try:
        while True:
            try:
                sol = codec.recibir(conn, Solicitud)
            except ConnectionError:
                break
            except (struct.error, json.JSONDecodeError, UnicodeDecodeError, ValueError, KeyError, IndexError) as e:
                # Mensaje mal formado. El servidor responde y cierra ESTA conexión, no muere.
                nombre = "struct.error" if isinstance(e, struct.error) else type(e).__name__
                log("mensaje mal formado desde", addr, "->", nombre, e)
                codec.enviar(conn, error(0, f"mensaje mal formado ({nombre})"))
                break
            if sol.version != VERSION:
                log("versión no soportada", sol.version, "desde", addr)
                codec.enviar(conn, error(sol.id, f"versión {sol.version} no soportada, use {VERSION}"))
                continue
            log("solicitud", sol.id, sol.operacion, sol.argumentos)
            resp = procesar(sol)
            codec.enviar(conn, resp)
            if sol.operacion.upper() == "SALIR":
                break
    except socket.timeout:
        log("timeout de", addr, "sin mensajes completos en", TIMEOUT, "s")
    except OSError as e:
        log("error de red con", addr, e)
    finally:
        conn.close()
        log("desconectado", addr)


def main():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, PUERTO))
    srv.listen(16)
    log(f"servidor inventario v{VERSION} en {HOST}:{PUERTO}  codec={codec.CODEC}  hilo por cliente")
    n = 0
    while True:
        conn, addr = srv.accept()
        n += 1
        threading.Thread(target=atender, args=(conn, addr), name=f"cli-{n}", daemon=True).start()


if __name__ == "__main__":
    main()
