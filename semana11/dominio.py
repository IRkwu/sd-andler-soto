
"""
Dominio del servicio, sin nada de red. Semana 11.

Este archivo contiene la lógica del negocio, independiente del transporte.
Lo utilizan rpc.py (JSON-RPC, semana 10) y servidor_grpc.py (gRPC, semana 11).
"""

import threading

_lock = threading.Lock()

_vehiculos = {
    "moto1": (-41.47, -72.94),
    "moto2": (-41.46, -72.95)
}


class ErrorDominio(Exception):
    """Error relacionado con las reglas del negocio."""


class ErrorParametros(Exception):
    """Error cuando un parámetro tiene un valor inválido."""


def _validar_vehiculo(vehiculo):
    if not isinstance(vehiculo, str) or not vehiculo.strip():
        raise ErrorParametros("El identificador del vehículo es inválido.")

    return vehiculo.strip()


def posicion(vehiculo, lat, lon):
    vehiculo = _validar_vehiculo(vehiculo)

    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        raise ErrorParametros("La latitud y longitud deben ser numéricas.")

    if not -90 <= lat <= 90:
        raise ErrorParametros("La latitud debe estar entre -90 y 90.")

    if not -180 <= lon <= 180:
        raise ErrorParametros("La longitud debe estar entre -180 y 180.")

    with _lock:
        _vehiculos[vehiculo] = (lat, lon)

        return {
            "vehiculo": vehiculo,
            "lat": lat,
            "lon": lon
        }


def donde(vehiculo):
    vehiculo = _validar_vehiculo(vehiculo)

    with _lock:
        if vehiculo not in _vehiculos:
            raise ErrorDominio(f"El vehículo '{vehiculo}' no existe.")

        lat, lon = _vehiculos[vehiculo]

        return {
            "vehiculo": vehiculo,
            "lat": lat,
            "lon": lon
        }
