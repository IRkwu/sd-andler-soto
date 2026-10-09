"""Servidor TCP concurrente — plantilla de la Semana 6 (hilo por cliente).

Dominio de referencia: INVENTARIO (equipo E-commerce). Cada equipo reemplaza
las operaciones por las de su propio dominio, manteniendo la estructura:
  - un hilo por cliente
  - estado compartido protegido por un Lock
  - manejo explícito de errores y desconexión abrupta
  - logging con identificador del cliente en cada línea

Protocolo por líneas, UTF-8, terminador "\n". Ver protocolo.md.
"""
import logging
import os
import socket
import threading
import time

HOST = os.environ.get("HOST", "0.0.0.0")
PUERTO = int(os.environ.get("PUERTO", "5000"))
SIN_LOCK = os.environ.get("SIN_LOCK", "0") == "1"
TIMEOUT_CLIENTE = int(os.environ.get("TIMEOUT_CLIENTE", "60"))

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [servidor] %(threadName)s %(message)s")

# ----------------------------------------------------------------- estado compartido
estado = {
    "vehiculos": {"moto1": (-41.47, -72.94), "moto2": (-41.46, -72.95)},
    "pedidos": {"p1": {"destino": (-41.45, -72.93), "asignado": None}},
    "siguiente_id": 2,
    "operaciones": 0
}
lock = threading.Lock()


class SinLock:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def seccion_critica():
    return SinLock() if SIN_LOCK else lock


# ----------------------------------------------------------------- operaciones del dominio
def op_posicion(arg):
    partes = arg.split()
    if len(partes) != 3:
        return "ERROR FORMATO POSICION vehiculo lat lon"

    vehiculo = partes[0].lower()
    try:
        lat, lon = float(partes[1]), float(partes[2])
    except ValueError:
        return "ERROR FORMATO coordenadas invalidas"

    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return "ERROR FORMATO coordenadas fuera de rango"

    with seccion_critica():
        estado["vehiculos"][vehiculo] = (lat, lon)

    return f"OK {vehiculo} {lat} {lon}"


def op_donde(arg):
    vehiculo = arg.strip().lower()
    if not vehiculo or len(arg.split()) != 1:
        return "ERROR FORMATO DONDE vehiculo"

    with seccion_critica():
        posicion = estado["vehiculos"].get(vehiculo)

    if posicion is None:
        return "ERROR VEHICULO_NO_EXISTE"

    return f"OK {vehiculo} {posicion[0]} {posicion[1]}"


def op_pedido(arg):
    partes = arg.split()
    if len(partes) != 2:
        return "ERROR FORMATO PEDIDO lat lon"

    try:
        lat, lon = float(partes[0]), float(partes[1])
    except ValueError:
        return "ERROR FORMATO coordenadas invalidas"

    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return "ERROR FORMATO coordenadas fuera de rango"

    with seccion_critica():
        id_pedido = f"p{estado['siguiente_id']}"
        estado["siguiente_id"] += 1
        estado["pedidos"][id_pedido] = {
            "destino": (lat, lon),
            "asignado": None
        }

    return f"OK {id_pedido} pendiente"


def op_tomar(arg):
    partes = arg.split()
    if len(partes) != 2:
        return "ERROR FORMATO TOMAR vehiculo pedido"

    vehiculo, id_pedido = partes[0].lower(), partes[1].lower()

    with seccion_critica():
        if vehiculo not in estado["vehiculos"]:
            return "ERROR VEHICULO_NO_EXISTE"

        pedido = estado["pedidos"].get(id_pedido)
        if pedido is None:
            return "ERROR PEDIDO_NO_EXISTE"

        if pedido["asignado"] is not None:
            return f"ERROR YA_ASIGNADO {pedido['asignado']}"

        time.sleep(0.001)
        pedido["asignado"] = vehiculo

    return f"OK {vehiculo} {id_pedido}"


def op_cercano(arg):
    partes = arg.split()
    if len(partes) != 2:
        return "ERROR FORMATO CERCANO lat lon"

    try:
        lat, lon = float(partes[0]), float(partes[1])
    except ValueError:
        return "ERROR FORMATO coordenadas invalidas"

    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return "ERROR FORMATO coordenadas fuera de rango"

    with seccion_critica():
        if not estado["vehiculos"]:
            return "ERROR SIN_VEHICULOS"

        vehiculo = min(
            estado["vehiculos"],
            key=lambda v: (
                (estado["vehiculos"][v][0] - lat) ** 2
                + (estado["vehiculos"][v][1] - lon) ** 2
            )
        )

        pos = estado["vehiculos"][vehiculo]
        distancia = ((pos[0] - lat) ** 2 +
                     (pos[1] - lon) ** 2) ** 0.5

    return f"OK {vehiculo} distancia={distancia:.4f}"



def op_espera(arg):
    try:
        seg = float(arg)
    except ValueError:
        return "ERROR FORMATO ESPERA <segundos>"
    time.sleep(seg)                            # operación lenta, NO toma el Lock
    return f"OK ESPERA {arg}"


OPERACIONES = {
    "POSICION": op_posicion,
    "DONDE": op_donde,
    "PEDIDO": op_pedido,
    "TOMAR": op_tomar,
    "CERCANO": op_cercano,
    "ESPERA": op_espera,
}


def procesar(linea):
    """Devuelve (respuesta, seguir)."""
    partes = linea.strip().split(" ", 1)
    cmd = partes[0].upper() if partes and partes[0] else ""
    arg = partes[1] if len(partes) > 1 else ""
    if cmd == "HOLA":
        return f"OK HOLA {arg or 'anonimo'}", True
    if cmd == "SALIR":
        return "OK CHAO", False
    if cmd in OPERACIONES:
        with seccion_critica():
            estado["operaciones"] += 1
        return OPERACIONES[cmd](arg), True
    return "ERROR COMANDO_DESCONOCIDO", True


# ----------------------------------------------------------------- atención de un cliente
def atender(conn, addr):
    logging.info("conexion de %s", addr)
    conn.settimeout(TIMEOUT_CLIENTE)
    try:
        with conn, conn.makefile("r", encoding="utf-8", errors="replace") as entrada:
            for linea in entrada:
                respuesta, seguir = procesar(linea)
                conn.sendall((respuesta + "\n").encode("utf-8"))
                if not seguir:
                    break
    except (ConnectionResetError, BrokenPipeError) as e:
        logging.warning("cliente %s se desconecto abruptamente (%s)", addr, e.__class__.__name__)
    except socket.timeout:
        logging.warning("cliente %s inactivo %ss, cerrando", addr, TIMEOUT_CLIENTE)
    except Exception as e:  # noqa: BLE001  — un cliente nunca puede botar el servidor
        logging.error("error inesperado con %s: %r", addr, e)
    finally:
        logging.info("cierre de %s | operaciones=%s", addr, estado["operaciones"])


def main():
    logging.info("SIN_LOCK=%s timeout=%ss", SIN_LOCK, TIMEOUT_CLIENTE)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((HOST, PUERTO))
        srv.listen(64)
        logging.info("escuchando en %s:%s", HOST, PUERTO)
        while True:
            conn, addr = srv.accept()
            threading.Thread(target=atender, args=(conn, addr),
                             name=f"cli-{addr[1]}", daemon=True).start()


if __name__ == "__main__":
    main()
