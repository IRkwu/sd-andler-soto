"""Puerta HTTP (API REST) delante del servidor TCP de la Semana 6.

Cada peticion HTTP se TRADUCE a una linea del protocolo de texto, se envia
al servidor TCP y la respuesta se traduce de vuelta a JSON y a un codigo HTTP.

    GET  /items                  ->  LISTAR
    GET  /items/{item}           ->  LISTAR (y se filtra)
    POST /items/{item}/entradas  ->  AGREGAR <item> <cantidad>
    POST /items/{item}/salidas   ->  QUITAR  <item> <cantidad>

Plantilla del laboratorio, dominio de referencia INVENTARIO. Cada equipo
reemplaza los recursos por los de su dominio y mantiene la estructura
    pedir()     habla con el servidor TCP  (no se toca)
    traducir()  convierte OK / ERROR en datos o en un codigo HTTP  (no se toca)
    ERRORES     tabla codigo del protocolo -> codigo HTTP  (se adapta)
    recursos    una funcion por operacion expuesta  (se adapta)

La API NO guarda nada. Todo el estado sigue viviendo en el servidor TCP.
"""
import os
import socket

from fastapi import FastAPI, HTTPException, Path, Query
from pydantic import BaseModel, Field

SERVIDOR_HOST = os.environ.get("SERVIDOR_HOST", "servidor")
SERVIDOR_PUERTO = int(os.environ.get("SERVIDOR_PUERTO", "5000"))
TIMEOUT_SERVIDOR = float(os.environ.get("TIMEOUT_SERVIDOR", "3"))
REPLICA = os.environ.get("REPLICA", socket.gethostname())

app = FastAPI(title="API de geolcalizacion y despacho", 
              version="1.0",
              description="Puerta HTTP del servicio de geolocalizacion y despacho. Semana 7.")

VEHICULO = Path(
    pattern=r"^[a-zA-Z0-9_]{1,30}$",
    description="Identificador del vehículo, sin espacios.",
)
PEDIDO = Path(
    pattern=r"^[pP][0-9]+$",
    description="Identificador del pedido, por ejemplo p1.",
)

# Codigo de error del protocolo de texto  ->  codigo de estado HTTP
ERRORES = {
    "FORMATO": 400,                 # la peticion esta mal armada
    "VEHICULO_NO_EXISTE": 404,      # el recurso no existe
    "PEDIDO_NO_EXISTE": 404,        # el recurso no existe
    "SIN_VEHICULOS": 404,           # no hay vehiculos disponibles para asignar
    "YA_ASIGNADO": 409,             # la peticion es valida pero choca con el estado actual
    "COMANDO_DESCONOCIDO": 501,     # el servidor no implementa esa operacion
}

class Coordenadas(BaseModel):
    lat: float = Field(ge=-90, le=90, allow_inf_nan=False, description="Latitud.")
    lon: float = Field(ge=-180, le=180, allow_inf_nan=False, description="Longitud.")

class Asignacion(BaseModel):
    vehiculo: str = Field(
        min_length=1,
        max_length=30,
        pattern=r"^[a-zA-Z0-9_]+$",
        description="Identificador del vehículo que tomará el pedido.",
    )

# Comunicación con el nivel de datos
def pedir(linea: str) -> str:
    """Envía una línea al servidor TCP y devuelve su respuesta."""
    try:
        with socket.create_connection(
            (SERVIDOR_HOST, SERVIDOR_PUERTO), timeout=TIMEOUT_SERVIDOR
        ) as conexion:
            conexion.sendall((linea + "\n").encode("utf-8"))
            respuesta = conexion.makefile("r", encoding="utf-8").readline().strip()
    except socket.timeout:
        raise HTTPException(
            504, {"error": "SERVIDOR_NO_RESPONDE", "replica": REPLICA}
        )
    except OSError as error:
        raise HTTPException(
            503,
            {
                "error": "SERVIDOR_NO_DISPONIBLE",
                "detalle": error.__class__.__name__,
                "replica": REPLICA,
            },
        )

    if not respuesta:
        raise HTTPException(
            503, {"error": "SERVIDOR_CERRO_LA_CONEXION", "replica": REPLICA}
        )
    return respuesta

def traducir(respuesta: str) -> list[str]:
    """Convierte OK en campos y los errores del protocolo en errores HTTP."""
    partes = respuesta.split()
    if partes and partes[0] == "OK":
        return partes[1:]

    codigo = partes[1] if len(partes) > 1 else "DESCONOCIDO"
    raise HTTPException(
        ERRORES.get(codigo, 500),
        {
            "error": codigo,
            "detalle": " ".join(partes[2:]),
            "replica": REPLICA,
        },
    )

def respuesta_posicion(vehiculo: str, datos: list[str]) -> dict:
    return {
        "vehiculo": vehiculo,
        "lat": float(datos[0]),
        "lon": float(datos[1]),
        "replica": REPLICA,
    }

# Recursos HTTP
@app.get("/salud")
def salud():
    """Indica qué réplica de la API atendió la petición."""
    return {"estado": "ok", "replica": REPLICA}


@app.put("/vehiculos/{vehiculo}/posicion")
def actualizar_posicion(coordenadas: Coordenadas, vehiculo: str = VEHICULO):
    """Registra o actualiza la posición de un vehículo (POSICION)."""
    nombre = vehiculo.lower()
    datos = traducir(
        pedir(f"POSICION {nombre} {coordenadas.lat} {coordenadas.lon}")
    )
    return respuesta_posicion(datos[0], datos[1:])


@app.get("/vehiculos/{vehiculo}/posicion")
def consultar_posicion(vehiculo: str = VEHICULO):
    """Consulta la última posición de un vehículo (DONDE)."""
    nombre = vehiculo.lower()
    datos = traducir(pedir(f"DONDE {nombre}"))
    return respuesta_posicion(datos[0], datos[1:])


@app.post("/pedidos", status_code=201)
def crear_pedido(coordenadas: Coordenadas):
    """Crea un pedido pendiente para el destino indicado (PEDIDO)."""
    datos = traducir(pedir(f"PEDIDO {coordenadas.lat} {coordenadas.lon}"))
    return {"pedido": datos[0], "estado": datos[1], "replica": REPLICA}


@app.post("/pedidos/{pedido}/asignacion", status_code=201)
def asignar_pedido(asignacion: Asignacion, pedido: str = PEDIDO):
    """Asigna un pedido pendiente a un vehículo (TOMAR)."""
    id_pedido = pedido.lower()
    vehiculo = asignacion.vehiculo.lower()
    datos = traducir(pedir(f"TOMAR {vehiculo} {id_pedido}"))
    return {"vehiculo": datos[0], "pedido": datos[1], "replica": REPLICA}


@app.get("/vehiculos/cercano")
def vehiculo_mas_cercano(
    lat: float = Query(ge=-90, le=90, allow_inf_nan=False),
    lon: float = Query(ge=-180, le=180, allow_inf_nan=False),
):
    """Devuelve el vehículo más cercano a unas coordenadas (CERCANO)."""
    datos = traducir(pedir(f"CERCANO {lat} {lon}"))
    vehiculo, distancia = datos[0], datos[1]
    return {
        "vehiculo": vehiculo,
        "distancia": float(distancia.split("=", 1)[1]),
        "replica": REPLICA,
    }
