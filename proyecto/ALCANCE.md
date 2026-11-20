# Alcance del proyecto integrador

Se completa en clase el viernes 13-11 y el docente lo aprueba en la mesa.

**Equipo:** andler-soto  
**Integrantes:** Álvaro Andler - Elías Soto
**Dominio:** Geólocalización y despacho

## 1. Qué problema resuelve la aplicación

El sistema necesita una ubicación reciente y suficientemente precisa de cada vehículo para tomar decisiones de despacho. Se registra o actualiza la posición de cada vehículo, se crean pedidos pendientes y se asigna cada pedido al vehículo más cercano, siempre que todavía no esté asignado.

## 2. Objetos remotos

| Clase | Nodo donde vive | ¿Tiene estado propio? | Métodos principales |
|---|---|---|---|
| `Geolocalizacion` | `servidor` | No; los datos de los vehículos se almacenan en `dominio.py`, que es compartido por todas las instancias | `listar()`, `donde(vehiculo)`, `posicion(vehiculo, lat, lon)`, `iniciar_seguimiento(vehiculo)` |
| `SeguimientoVehiculo` | `servidor` | Sí; vehículo e historial de posiciones | `registrar_posicion(lat, lon)`, `ver_historial()`, `finalizar()`, `cancelar()` |
| `Central` | `central` | No | `pedido(lat, lon)`, `cercano(lat, lon)` |
| `Despacho` | `central` | Sí; repartidor, posición y estado (`pendiente` o asignado) | `tomar(vehiculo)`, `ver_estado()`, `finalizar()`, `cancelar()` |

`Central.cercano(lat, lon)` llama a `Geolocalizacion.listar()`, que vive en el nodo `servidor`, y busca el vehículo más cercano mediante distancia euclidiana entre coordenadas, como `CERCANO` en `semana09/protocolo.md`.

**Objeto que viaja por referencia y su ciclo de vida (cómo se crea, cómo se usa, cómo termina)**  

`Despacho`, con el mismo patrón que `SeguimientoVehiculo` en la semana 12.
- **Cómo se crea:** `Central.pedido(lat, lon)` crea un pedido pendiente, registra el objeto `Despacho` en el daemon y devuelve al cliente un proxy con una URI del daemon.
- **Cómo se usa:** el cliente llama a `tomar(vehiculo)` para asignar el pedido a un vehículo, siempre que todavía no esté asignado (si ya lo está, responde `YA_ASIGNADO`), y a `ver_estado()` para consultarlo.
- **Cómo termina:** `finalizar()` o `cancelar()` desregistran el objeto del daemon. Después de eso, el daemon deja de reconocer la URI (`unknown object`): la referencia queda colgante.

## 3. Nodos

| Nodo (servicio de compose) | Rol | Se comunica con |
|---|---|---|
| nombres | Servidor de nombres | todos |
| servidor | Daemon con `Geolocalizacion` y `SeguimientoVehiculo` (puerto 9100) | nombres, central, workers |
| central | Daemon con `Central` y `Despacho` | nombres, servidor, cola |
| cola | RabbitMQ (semana 13) | central, workers |
| worker1, worker2 | Toman pedidos pendientes de la cola y los asignan | cola, nombres, servidor, central |
| cliente | Contenedor para ejecutar `cliente_pyro.py` | nombres, servidor, central |

## 4. Primera idea de cola y coordinación

**Qué trabajo podría repartirse por cola entre workers (semana 13)**  

Cada pedido pendiente que crea `Central.pedido(lat, lon)` va a la cola. Los workers toman los pedidos, buscan el vehículo más cercano con `cercano` y lo asignan con `tomar`.

**Qué recurso o decisión necesitaría coordinación (semana 16)**  

La asignación de pedidos a vehículos. Hoy, en `TOMAR`, comprobar si el pedido está asignado y registrar su asignación ocurre dentro de la misma sección crítica, protegida con un `Lock`, lo que evita asignaciones simultáneas del mismo pedido (`semana09/protocolo.md`). Con dos workers en nodos distintos, ese `Lock` ya no basta y se necesita exclusión mutua distribuida.

## 5. Falla que van a demostrar el 18-12

**Qué nodo se cae, qué ve el usuario y cómo se recupera**  

- **Qué nodo se cae:** `nombres`, con `docker compose kill nombres` y después `docker compose start nombres`.
- **Qué ve el usuario:** quien ya tenía establecida la conexión al servicio sigue realizando consultas. Un cliente nuevo ve `Failed to locate the nameserver`. Cuando el servidor de nombres vuelve sin que se registre de nuevo el servicio, aparece `unknown name` (`semana12/observaciones.md`, paso 5).
- **Cómo se recupera:** con `REREGISTRO=5`, el servidor intenta registrar su servicio en el servidor de nombres cada cinco segundos. Así se recupera el registro automáticamente después de reiniciar `nombres`, sin tener que reiniciar el servidor de geolocalización.

## 6. Fuera de alcance

- Distancia real de recorrido. `CERCANO` mide distancia euclidiana entre pares de coordenadas, no kilómetros de recorrido.
- Persistencia de posiciones, pedidos y seguimientos. El estado vive en memoria y se pierde al reiniciar un nodo.
- P2P entre vehículos. La asignación no la negocian directamente los vehículos: la decide la central.
- `ESPERA`, `HOLA` y `SALIR`, que eran operaciones de prueba y de sesión TCP.

## 7. Riesgos

| Riesgo | Qué haremos si ocurre |
|---|---|
| El servidor de nombres es un punto único de falla para los clientes nuevos | Habilitar el registro periódico del servicio (`REREGISTRO=5`) para que vuelva a anunciarse automáticamente después de una caída |
| El nodo `servidor` cae y se pierde el estado almacenado en memoria | Utilizar almacenamiento persistente para conservar las posiciones, los seguimientos y la información necesaria para recuperarlos después de un reinicio |
| Un reintento sin `id_solicitud` repite la asignación de un vehículo a un despacho | Usar `id_solicitud` para reconocer solicitudes repetidas y evitar ejecutar la misma operación más de una vez, como en la semana 11 |
| Dos workers asignan el mismo pedido a la vez | Exclusión mutua distribuida en `tomar` (semana 16) |

**Aprobación docente**

Fecha                Aprobado / Aprobado con cambios / Rehacer

Observaciones
