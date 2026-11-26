"""cola.py, utilidades minimas para hablar con RabbitMQ usando pika.

Se usa igual en la demo del jueves y en el laboratorio del viernes.
Variables de entorno
    RABBIT_HOST   nombre del servicio del broker en sd_net (por defecto rabbitmq)
    RABBIT_PUERTO puerto AMQP (por defecto 5672)
    RABBIT_USUARIO, RABBIT_CLAVE credenciales (por defecto guest / guest)
    PREFIJO       prefijo para los nombres de cola, solo si varios equipos
                  comparten un mismo broker (por defecto vacio)
"""
import json
import os
import socket
import sys
import time

import pika

RABBIT_HOST = os.environ.get("RABBIT_HOST", "rabbitmq")
RABBIT_PUERTO = int(os.environ.get("RABBIT_PUERTO", "5672"))
RABBIT_USUARIO = os.environ.get("RABBIT_USUARIO", "guest")
RABBIT_CLAVE = os.environ.get("RABBIT_CLAVE", "guest")
PREFIJO = os.environ.get("PREFIJO", "")


def nombre_cola(base):
    """Nombre real de la cola. Con PREFIJO=pagos_ la cola operaciones pasa a pagos_operaciones."""
    return f"{PREFIJO}{base}"


def nombre_nodo():
    """Nombre corto para los logs. En un servicio escalado es el id del contenedor."""
    return os.environ.get("NOMBRE_NODO") or socket.gethostname()[:6]


def log(*partes):
    hora = time.strftime("%H:%M:%S")
    print(f"[{hora}] [{nombre_nodo()}]", *partes, flush=True)


def conectar(intentos=30, espera=2.0):
    """Abre una conexion al broker con reintentos.

    El broker tarda varios segundos en arrancar, y si se reinicia a mitad de
    la demo los clientes tienen que volver a intentarlo. Sin reintentos el
    contenedor muere con ConnectionRefused y parece que el codigo esta malo.
    """
    parametros = pika.ConnectionParameters(
        host=RABBIT_HOST,
        port=RABBIT_PUERTO,
        credentials=pika.PlainCredentials(RABBIT_USUARIO, RABBIT_CLAVE),
        heartbeat=30,
        blocked_connection_timeout=30,
    )
    for i in range(1, intentos + 1):
        try:
            return pika.BlockingConnection(parametros)
        except pika.exceptions.AMQPConnectionError:
            log(f"broker no disponible en {RABBIT_HOST}:{RABBIT_PUERTO}, intento {i}/{intentos}")
            time.sleep(espera)
    log("no pude conectarme al broker, me rindo")
    sys.exit(1)


def declarar_cola(canal, nombre):
    """Declara una cola durable.

    Durable significa que la definicion de la cola sobrevive a un reinicio
    del broker. Los mensajes sobreviven solo si ademas se publican como
    persistentes. RabbitMQ 4 desaconseja las colas no durables y no exclusivas,
    por eso en el curso todas las colas compartidas son durables.
    """
    return canal.queue_declare(queue=nombre, durable=True)


def publicar(canal, cola, cuerpo, persistente=True):
    """Publica un diccionario como JSON en la cola indicada."""
    propiedades = pika.BasicProperties(
        content_type="application/json",
        delivery_mode=2 if persistente else 1,  # 2 persistente, 1 transiente
    )
    canal.basic_publish(
        exchange="",
        routing_key=cola,
        body=json.dumps(cuerpo).encode("utf-8"),
        properties=propiedades,
    )


def leer(cuerpo):
    return json.loads(cuerpo.decode("utf-8"))


def env_bool(nombre, defecto="0"):
    return os.environ.get(nombre, defecto).strip().lower() in ("1", "true", "si", "sí", "yes")
