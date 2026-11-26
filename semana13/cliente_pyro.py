"""
Cliente Pyro5 del servicio, semana 12.

Uso (dentro del contenedor cliente, o con Python local)
  python cliente_pyro.py uri
  python cliente_pyro.py listar
  python cliente_pyro.py agregar cafe 10
  python cliente_pyro.py quitar cafe 3
  python cliente_pyro.py quien --veces 3
  python cliente_pyro.py pedido cafe:2 te:1 [--esperar 30]
  python cliente_pyro.py vivos
  python cliente_pyro.py vigilar [--cada 1]

Variables
  NOMBRES_HOST (nombres)  NOMBRES_PUERTO (9090)  EQUIPO (referencia)
"""
import argparse
import os
import sys
import time

from Pyro5.api import Proxy, locate_ns, register_dict_to_class
from Pyro5.errors import (CommunicationError, DaemonError, NamingError,
                          SerializeError, get_pyro_traceback)

NS_HOST = os.environ.get("NOMBRES_HOST", "nombres")
NS_PUERTO = int(os.environ.get("NOMBRES_PUERTO", "9090"))
EQUIPO = os.environ.get("EQUIPO", "referencia")
NOMBRE = f"sd.{EQUIPO}.geolocalizacion"


# Las excepciones también viajan serializadas (por valor). Pyro5 solo sabe
# reconstruir las de Python. Las propias del dominio hay que enseñárselas.
import dominio  # noqa: E402


def _a_excepcion(nombre_clase, datos):
    clase = getattr(dominio, nombre_clase.split(".")[-1])
    return clase(*datos.get("args", ()))


for _nombre in ("ErrorDominio", "ErrorParametros"):
    register_dict_to_class(f"dominio.{_nombre}", _a_excepcion)


def log(msg):
    print(time.strftime("%H:%M:%S"), msg, flush=True)

def geolocalizacion():
    """Proxy al Geolocalizacion. La URI se resuelve en el servidor de nombres."""
    proxy = Proxy(f"PYRONAME:{NOMBRE}@{NS_HOST}:{NS_PUERTO}")
    proxy._pyroTimeout = 5
    return proxy


def cmd_uri(_):
    with locate_ns(host=NS_HOST, port=NS_PUERTO) as ns:
        log(f"{NOMBRE} -> {ns.lookup(NOMBRE)}")
        log(f"nombres registrados {sorted(ns.list().keys())}")


def cmd_listar(_):
    with geolocalizacion() as geo:
        log(f"vehiculos {geo.listar()}")


def cmd_posicion(a):
    with geolocalizacion() as geo:
        resultado = geo.posicion(a.vehiculo, a.lat, a.lon)
        log(f"posicion -> {resultado}")


def cmd_donde(a):
    with geolocalizacion() as geo:
        resultado = geo.donde(a.vehiculo)
        log(f"donde -> {resultado}")


def cmd_quien(a):
    """Mismo proxy varias veces y después un proxy nuevo. Muestra el modo."""
    for etiqueta in ("proxy A", "proxy B"):
        with geolocalizacion() as geo:
            for _ in range(a.veces):
                log(f"{etiqueta} -> {geo.quien_soy()}")


def cmd_vivos(_):
    """Muestra cuántos seguimientos remotos están activos."""
    with geolocalizacion() as geo:
        log(f"seguimientos vivos: {geo.seguimientos_vivos()}")


def reintentar_finalizar(uri, segundos):
    """Reintenta finalizar usando la misma referencia remota."""
    limite = time.monotonic() + segundos

    while True:
        try:
            with Proxy(uri) as seguimiento:
                seguimiento._pyroTimeout = 5
                return seguimiento.finalizar()
        except DaemonError:
            # El objeto ya no existe en el servidor.
            raise
        except CommunicationError:
            if time.monotonic() >= limite:
                raise
            time.sleep(1)


def cmd_seguimiento(a):
    """Crea, utiliza y finaliza un seguimiento remoto."""

    with geolocalizacion() as geo:
        seguimiento = geo.iniciar_seguimiento(a.vehiculo)
        seguimiento._pyroTimeout = 5

        log(
            f"recibí {type(seguimiento).__name__}, "
            f"referencia {seguimiento._pyroUri}"
        )

        resultado = seguimiento.registrar_posicion(a.lat, a.lon)
        log(f"posición registrada -> {resultado}")

        historial = seguimiento.ver_historial()
        log(f"historial en el servidor -> {historial}")

        if a.esperar:
            log(f"espero {a.esperar} segundos antes de finalizar")
            time.sleep(a.esperar)

        try:
            resultado = seguimiento.finalizar()
        except CommunicationError:
            log("Se perdió la conexión. Reintentando con la misma URI")
            resultado = reintentar_finalizar(
                seguimiento._pyroUri, 30
            )

        log(f"seguimiento finalizado -> {resultado}")

        # Experimento: referencia colgante.
        log("Intentando utilizar la referencia después de finalizar")

        try:
            seguimiento.ver_historial()
        except (DaemonError, CommunicationError) as e:
            log(
                f"REFERENCIA COLGANTE (esperado): "
                f"{type(e).__name__}: {e}"
            )
        else:
            log("AVISO: el objeto todavía responde")


def cmd_vigilar(a):
    """Llama listar() cada a.cada segundos con el MISMO proxy y reporta fallas."""
    geo = geolocalizacion()
    while True:
        try:
            log(f"ok, vehiculos {geo.listar()}  [{geo._pyroUri}]")
        except CommunicationError as e:
            log(f"FALLA de comunicación {type(e).__name__} {e}")
            try:
                geo._pyroReconnect(tries=1)
                log("reconectado")
            except (CommunicationError, NamingError) as e2:
                log(f"no pude reconectar {type(e2).__name__}")
        except NamingError as e:
            log(f"FALLA de nombres {e}")
        time.sleep(a.cada)


def main():
    p = argparse.ArgumentParser(description="Cliente Pyro5, semana 12")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("uri").set_defaults(f=cmd_uri)
    sub.add_parser("listar").set_defaults(f=cmd_listar)
    s = sub.add_parser("posicion")
    s.add_argument("vehiculo")
    s.add_argument("lat", type=float)
    s.add_argument("lon", type=float)
    s.set_defaults(f=cmd_posicion)

    s = sub.add_parser("donde")
    s.add_argument("vehiculo")
    s.set_defaults(f=cmd_donde)
    sub.add_parser("vivos").set_defaults(f=cmd_vivos)
    s = sub.add_parser("quien")
    s.add_argument("--veces", type=int, default=3)
    s.set_defaults(f=cmd_quien)
    s = sub.add_parser("seguimiento")
    s.add_argument("vehiculo")
    s.add_argument("lat", type=float)
    s.add_argument("lon", type=float)
    s.add_argument("--esperar", type=int, default=0)
    s.set_defaults(f=cmd_seguimiento)
    s = sub.add_parser("vigilar")
    s.add_argument("--cada", type=float, default=1)
    s.set_defaults(f=cmd_vigilar)
    a = p.parse_args()
    try:
        a.f(a)
    except KeyboardInterrupt:
        pass
    except NamingError as e:
        log(f"ERROR de nombres. No encuentro {NOMBRE}. {e}")
        sys.exit(2)
    except DaemonError as e:
        log(f"ERROR del daemon. La referencia apunta a un objeto que ya no existe. {e}")
        sys.exit(3)
    except SerializeError as e:
        log(f"ERROR de serialización. El servidor intentó enviar un objeto por valor. {e}")
        sys.exit(4)
    except CommunicationError as e:
        if "unknown object" in str(e):
            log("ERROR. El servidor responde, pero el objeto de esa referencia "
                f"ya no existe (referencia colgante). {e}")
            sys.exit(3)
        log(f"ERROR de comunicación. {type(e).__name__} {e}")
        sys.exit(5)
    except Exception as e:  # error del dominio que viene desde el servidor
        log(f"ERROR remoto {type(e).__name__} {e}")
        if os.environ.get("TRAZA") == "1":
            print("".join(get_pyro_traceback()))
        sys.exit(6)


if __name__ == "__main__":
    main()
