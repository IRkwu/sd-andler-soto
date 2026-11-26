"""procesador.py, consume operaciones de la cola y las procesa.

Es un consumidor sin estado. Si se escala a varias replicas, cada una toma
mensajes de la misma cola y RabbitMQ reparte el trabajo entre ellas.

Variables de entorno
    COLA         nombre de la cola (por defecto operaciones)
    PREFETCH     cuantos mensajes sin confirmar puede tener cada replica (por defecto 1)
    AUTO_ACK     1 confirma al recibir (at-most-once), 0 confirma al terminar (at-least-once)
    TRABAJO_SEG  segundos de trabajo simulado por mensaje (por defecto 0)

TODO del equipo (paso 2)
    Completar OPERACIONES_VALIDAS con las operaciones de su protocolo.md
    y ajustar procesar() para que el log muestre algo propio de su dominio.
"""
import os
import signal
import sys
import time

from cola import conectar, declarar_cola, env_bool, leer, log, nombre_cola

COLA = nombre_cola(os.environ.get("COLA", "operaciones"))
PREFETCH = int(os.environ.get("PREFETCH", "1"))
AUTO_ACK = env_bool("AUTO_ACK", "0")
TRABAJO_SEG = float(os.environ.get("TRABAJO_SEG", "0"))

# TODO equipo, reemplazar por las operaciones de su protocolo.md (listo)
OPERACIONES_VALIDAS = {"POSICION", "DONDE", "LISTAR"}

def procesar(mensaje):
    """Procesa una operacion del dominio de geolocalizacion."""
    op = mensaje.get("op")
    args = mensaje.get("args", [])

    if TRABAJO_SEG > 0:
        time.sleep(TRABAJO_SEG)

    if op == "POSICION":
        return f"Posicion de {args[0]} actualizada a ({args[1]}, {args[2]})"

    if op == "DONDE":
        return f"Consulta de posicion de {args[0]} procesada"

    if op == "LISTAR":
        return "Consulta de vehiculos registrados procesada"


def main():
    conexion = conectar()
    canal = conexion.channel()
    declarar_cola(canal, COLA)
    canal.basic_qos(prefetch_count=PREFETCH)

    procesados = 0

    def al_recibir(ch, metodo, propiedades, cuerpo):
        nonlocal procesados
        mensaje = leer(cuerpo)
        marca = " (REENTREGADO)" if metodo.redelivered else ""
        log(f"recibido id={mensaje.get('id')} op={mensaje.get('op')}{marca}")

        if mensaje.get("op") not in OPERACIONES_VALIDAS:
            log(f"operacion desconocida {mensaje.get('op')!r}, se descarta sin reintentar")
            if not AUTO_ACK:
                ch.basic_nack(delivery_tag=metodo.delivery_tag, requeue=False)
            return

        log(f"procesando id={mensaje.get('id')} ...")
        resultado = procesar(mensaje)
        procesados += 1
        if not AUTO_ACK:
            ch.basic_ack(delivery_tag=metodo.delivery_tag)
        log(f"terminado id={mensaje.get('id')} -> {resultado} (total {procesados})")

    def detener(*_):
        log("recibi SIGTERM, cierro ordenadamente")
        try:
            canal.stop_consuming()
        except Exception:
            pass

    signal.signal(signal.SIGTERM, detener)

    canal.basic_consume(queue=COLA, on_message_callback=al_recibir, auto_ack=AUTO_ACK)
    modo = "AUTO_ACK (at-most-once)" if AUTO_ACK else "ack manual (at-least-once)"
    log(f"esperando en '{COLA}', prefetch={PREFETCH}, {modo}, trabajo={TRABAJO_SEG}s")
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
