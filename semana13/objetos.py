"""
Objetos remotos del servicio, semana 12.

Aquí el dominio deja de exponerse como funciones sueltas (gRPC, JSON-RPC) y
pasa a exponerse como OBJETOS que viven en el servidor.

  Inventario  objeto de entrada, se registra en el servidor de nombres.
              Delega en dominio.py y además fabrica objetos Pedido.
  Pedido      objeto con estado propio (sus líneas). No se registra con
              nombre, el cliente lo recibe POR REFERENCIA desde
              Inventario.abrir_pedido().

Variables
  MODO       single | session | percall   modo de instancia del Inventario
  POR_VALOR  0 | 1   con 1, abrir_pedido devuelve el Pedido sin registrarlo
             en el daemon (experimento, el cliente recibe un error)

El equipo reemplaza Inventario y Pedido por los objetos de su dominio.
"""
import os
import threading
import time

from Pyro5.api import behavior, current_context, expose

import dominio

MODO = os.environ.get("MODO", "single")
POR_VALOR = os.environ.get("POR_VALOR", "0") == "1"

_contador_instancias = 0
_lock_contador = threading.Lock()


def _nueva_instancia():
    global _contador_instancias
    with _lock_contador:
        _contador_instancias += 1
        return _contador_instancias



@expose
class SeguimientoVehiculo:
    """Seguimiento remoto de un vehículo.

    Mantiene un historial de posiciones en el servidor.
    El cliente accede mediante una referencia Pyro5.
    """

    def __init__(self, vehiculo):
        self.vehiculo = vehiculo
        self.historial = []
        self.creado = time.strftime("%H:%M:%S")

    def registrar_posicion(self, lat, lon):
        """Actualiza la posición y modifica el historial."""
        resultado = dominio.posicion(self.vehiculo, lat, lon)
        self.historial.append(resultado.copy())
        return resultado

    def ver_historial(self):
        """Consulta el historial sin modificar el estado."""
        return {
            "vehiculo": self.vehiculo,
            "creado": self.creado,
            "posiciones": [p.copy() for p in self.historial]
        }

    def finalizar(self):
        """Devuelve el historial y termina la vida del objeto."""
        resultado = self.ver_historial()
        self._terminar()
        return resultado

    def cancelar(self):
        """Termina el seguimiento sin modificar las posiciones."""
        self._terminar()
        return "seguimiento cancelado"

    def _terminar(self):
        """Desregistra el objeto del daemon Pyro5."""
        self._pyroDaemon.unregister(self)


@expose
@behavior(instance_mode=MODO)
class Geolocalizacion:
    """Servicio remoto para consultar y actualizar vehículos."""
    
    def __init__(self):
        self.numero = _nueva_instancia()
        self.llamadas = 0

    def _contar(self):
        self.llamadas += 1

    def listar(self):
        """Consulta todos los vehículos. No modifica estado."""
        self._contar()
        return dominio.listar_vehiculos()

    def posicion(self, vehiculo, lat, lon):
        """Actualiza la ubicación de un vehículo. Modifica estado."""
        self._contar()
        return dominio.posicion(vehiculo, lat, lon)

    def donde(self, vehiculo):
        """Consulta la ubicación de un vehículo. No modifica estado."""
        self._contar()
        return dominio.donde(vehiculo)

    def quien_soy(self):
        """Cuenta qué instancia atendió la llamada y cuántas lleva.

        Sirve para ver el modo de instancia. El stock vive en dominio.py y
        es el mismo para todas las instancias.
        """
        self._contar()
        return {"modo": MODO, "instancia": self.numero, "llamadas": self.llamadas,
                "cliente": str(current_context.client_sock_addr)}

    
    def seguimientos_vivos(self):
        """Consulta cuántos seguimientos remotos están activos."""
        self._contar()
        return sum(
            1 for objeto in self._pyroDaemon.objectsById.values()
            if isinstance(objeto, SeguimientoVehiculo)
        )

    def iniciar_seguimiento(self, vehiculo):
        """Crea un seguimiento y devuelve su referencia remota."""
        self._contar()

        # Verifica que el vehículo exista en nuestro dominio.
        dominio.donde(vehiculo)

        seguimiento = SeguimientoVehiculo(vehiculo)

        if POR_VALOR:
            # Experimento: devolver sin registrar en el daemon.
            return seguimiento

        self._pyroDaemon.register(seguimiento)
        return seguimiento

