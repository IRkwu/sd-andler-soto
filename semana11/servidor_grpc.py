
"""
Servidor gRPC del servicio de geolocalización, semana 11.

Usa el dominio de dominio.py sin modificarlo.
Lo único nuevo es el transporte.

Variables
    SERVIDOR_PUERTO  (50051)
    FALLA            no | primera | siempre
    DEMORA           (3) segundos de demora cuando hay falla
    DEDUP            0 | 1

Requiere haber generado servicio_pb2.py y servicio_pb2_grpc.py desde proto/.
"""

import os
import signal
import threading
import time
from concurrent import futures

import grpc

import dominio
import servicio_pb2 as pb
import servicio_pb2_grpc as pb_grpc


PUERTO = os.getenv("SERVIDOR_PUERTO", "50051")
FALLA = os.getenv("FALLA", "no")
DEMORA = float(os.getenv("DEMORA", "3"))
DEDUP = os.getenv("DEDUP", "0") == "1"

_dedup_lock = threading.Lock()
_vistas = {}  # id_solicitud -> respuesta o error ya entregado
_ya_fallo = False


def log(msg):
    print(f"[servidor] {msg}", flush=True)


def demorar_si_corresponde():
    global _ya_fallo

    if FALLA == "no" or (FALLA == "primera" and _ya_fallo):
        return

    _ya_fallo = True
    log(f"FALLA={FALLA}, cambio YA aplicado, demoro la respuesta {DEMORA:.0f} s")
    time.sleep(DEMORA)


class Geolocalizacion(pb_grpc.GeolocalizacionServicer):

    def Posicion(self, request, context):
        return self._modificar(
            "Posicion",
            request,
            context,
            aplicar=lambda: dominio.posicion(
                request.vehiculo,
                request.lat,
                request.lon
            ),
            respuesta=pb.PosicionRespuesta
        )

    def Donde(self, request, context):
        try:
            resultado = dominio.donde(request.vehiculo)
            log(f"Donde -> {resultado}")
            return pb.PosicionRespuesta(**resultado)

        except dominio.ErrorParametros as e:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(e))

        except dominio.ErrorDominio as e:
            context.abort(grpc.StatusCode.FAILED_PRECONDITION, str(e))

    # Toda operación que modifica estado pasa por aquí.
    # aplicar: función que llama al dominio y devuelve un diccionario.
    # respuesta: clase del mensaje de respuesta generado desde el .proto.

    def _modificar(self, nombre, request, context, aplicar, respuesta):

        ids = request.id_solicitud

        if not ids:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "falta id_solicitud")

        repetido = False

        with _dedup_lock:

            if DEDUP and ids in _vistas:
                log(f"{nombre} id={ids} repetido, devuelvo lo guardado SIN aplicar de nuevo")
                resultado = _vistas[ids]
                repetido = True

            else:
                try:
                    resultado = ("ok", aplicar())

                except dominio.ErrorParametros as e:
                    resultado = ("error", grpc.StatusCode.INVALID_ARGUMENT, str(e))

                except dominio.ErrorDominio as e:
                    resultado = ("error", grpc.StatusCode.FAILED_PRECONDITION, str(e))

                detalle = resultado[1] if resultado[0] == "ok" else resultado[2]

                log(f"{nombre} id={ids} -> {detalle}")

                if DEDUP:
                    _vistas[ids] = resultado

        if resultado[0] == "error":
            context.abort(resultado[1], resultado[2])

        if not repetido:
            demorar_si_corresponde()

        return respuesta(**resultado[1])


def main():

    servidor = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10)
    )

    pb_grpc.add_GeolocalizacionServicer_to_server(
        Geolocalizacion(),
        servidor
    )

    servidor.add_insecure_port(f"0.0.0.0:{PUERTO}")

    servidor.start()

    log(
        f"gRPC escuchando en {PUERTO} "
        f"con FALLA={FALLA} DEMORA={DEMORA:.0f} DEDUP={int(DEDUP)}"
    )

    signal.signal(signal.SIGTERM, lambda *_: servidor.stop(1))

    servidor.wait_for_termination()


if __name__ == "__main__":
    main()
