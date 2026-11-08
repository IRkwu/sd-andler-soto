
"""
Cliente gRPC del servicio de geolocalización, semana 11.

Uso
    python cliente_grpc.py posicion moto1 -41.45 -72.90
    python cliente_grpc.py donde moto1
    python cliente_grpc.py posicion moto1 -41.45 -72.90 --reintentos 2

Variables
    SERVIDOR_HOST    (servidor)
    SERVIDOR_PUERTO  (50051)
    TIMEOUT_CLIENTE  (2) segundos por intento
    REINTENTOS       (0) intentos extra ante DEADLINE_EXCEEDED o UNAVAILABLE

Cada reintento de Posicion manda el MISMO id_solicitud.
"""

import argparse
import os
import uuid

import grpc

import servicio_pb2 as pb
import servicio_pb2_grpc as pb_grpc


HOST = os.getenv("SERVIDOR_HOST", "servidor")
PUERTO = os.getenv("SERVIDOR_PUERTO", "50051")

REINTENTABLES = {
    grpc.StatusCode.DEADLINE_EXCEEDED,
    grpc.StatusCode.UNAVAILABLE
}


def main():

    ap = argparse.ArgumentParser()

    ap.add_argument(
        "metodo",
        choices=["posicion", "donde"]
    )

    ap.add_argument("vehiculo")

    ap.add_argument("lat", nargs="?", type=float)
    ap.add_argument("lon", nargs="?", type=float)

    ap.add_argument(
        "--reintentos",
        type=int,
        default=int(os.getenv("REINTENTOS", "0"))
    )

    ap.add_argument(
        "--timeout",
        type=float,
        default=float(os.getenv("TIMEOUT_CLIENTE", "2"))
    )

    a = ap.parse_args()

    if a.reintentos < 0 or a.timeout <= 0:
        ap.error("Los reintentos no pueden ser negativos y el timeout debe ser mayor que cero.")

    canal = grpc.insecure_channel(f"{HOST}:{PUERTO}")

    stub = pb_grpc.GeolocalizacionStub(canal)

    if a.metodo == "posicion":

        if a.lat is None or a.lon is None:
            ap.error("posicion requiere vehículo, latitud y longitud.")

        solicitud = pb.PosicionSolicitud(
            id_solicitud=uuid.uuid4().hex[:8],
            vehiculo=a.vehiculo,
            lat=a.lat,
            lon=a.lon
        )

        llamada = stub.Posicion

    else:

        solicitud = pb.DondeSolicitud(
            vehiculo=a.vehiculo
        )

        llamada = stub.Donde

    for intento in range(1, a.reintentos + 2):

        ids = getattr(solicitud, "id_solicitud", "-")

        print(
            f"[cliente] intento {intento}, "
            f"id_solicitud={ids}, deadline {a.timeout:.0f} s"
        )

        try:

            resp = llamada(
                solicitud,
                timeout=a.timeout
            )

        except grpc.RpcError as e:

            print(f"[cliente] {e.code().name}, {e.details()}")

            if e.code() in REINTENTABLES:
                continue

            return 1

        if a.metodo == "posicion":

            print(
                f"[cliente] OK {resp.vehiculo} "
                f"lat={resp.lat} lon={resp.lon}"
            )

        else:

            print(
                f"[cliente] OK {resp.vehiculo} "
                f"lat={resp.lat} lon={resp.lon}"
            )

        return 0

    if a.metodo == "donde":

        print("[cliente] me rendí, sin respuesta del servidor")

    else:

        print(
            "[cliente] me rendí, "
            "la operación quedó en estado DESCONOCIDO"
        )

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
