# Observaciones, taller semana 12 (objetos distribuidos con Pyro5)

**Equipo:** andler-soto  
**Integrantes:** Álvaro Andler y Elías Soto  
**Fecha:** 13-11-2026

## Paso 1, nombres y servidor arriba

URI que entregó el servidor de nombres para `sd.andler-soto.geolocalizacion`
(pegar la salida de `python cliente_pyro.py uri`)

```text
15:16:32 sd.andler-soto.geolocalizacion -> PYRO:geolocalizacion@servidor:9100
15:16:32 nombres registrados ['Pyro.NameServer', 'sd.andler-soto.geolocalizacion']
```

**¿Qué partes de la URI reconocen? (protocolo, identificador del objeto, nodo, puerto)**

La referencia remota utiliza el protocolo `PYRO`, identifica al objeto como `geolocalizacion` y señala que se encuentra en el nodo `servidor`, utilizando el puerto `9100`. Además, el servidor de nombres está disponible en `nombres:9090`, lo que permite al cliente localizar el servicio y comunicarse con él.

## Paso 2, su dominio como objeto remoto

El dominio usado es la geolocalización de vehículos. `Geolocalizacion` es la clase remota de entrada, y delega la lógica del negocio a `dominio.py` reutilizado de la semana 11. 

| Clase | Método remoto | Función de dominio / finalidad | ¿Cambia estado? |
|---|---|---|---|
| `Geolocalizacion` | `listar()` | `dominio.listar_vehiculos()` | No; consulta posiciones |
| `Geolocalizacion` | `donde(vehiculo)` | `dominio.donde(vehiculo)` | No; consulta una posición |
| `Geolocalizacion` | `posicion(vehiculo, lat, lon)` | `dominio.posicion(...)` | Sí; actualiza una posición |
| `Geolocalizacion` | `quien_soy()` | Contador de llamadas de la instancia Pyro5 | Sí; incrementa el contador de la instancia |
| `Geolocalizacion` | `iniciar_seguimiento(vehiculo)` | Fábrica de objetos de seguimiento | Sí; crea/registra un objeto remoto |
| `Geolocalizacion` | `seguimientos_vivos()` | Cuenta objetos de seguimiento registrados | No respecto al dominio, aunque incrementa el contador de llamadas |
| `SeguimientoVehiculo` | `registrar_posicion(lat, lon)` | Actualiza la posición y añade al historial propio | Sí |
| `SeguimientoVehiculo` | `ver_historial()` | Devuelve una copia del historial | No |
| `SeguimientoVehiculo` | `finalizar()` / `cancelar()` | Desregistra el objeto remoto | Sí; termina su ciclo de vida |

**Pruebas exitosas:**

```text
15:16:33 vehiculos [{'vehiculo': 'moto1', 'lat': -41.47, 'lon': -72.94}, {'vehiculo': 'moto2', 'lat': -41.46, 'lon': -72.95}]
15:16:33 posicion -> {'vehiculo': 'moto1', 'lat': -41.45, 'lon': -72.9}
15:16:34 donde -> {'vehiculo': 'moto1', 'lat': -41.45, 'lon': -72.9}
```

## Paso 3, paso por referencia

**Referencia que recibió el cliente al abrir el objeto con estado (`pedido` o el suyo):**

Se creó un objeto `SeguimientoVehiculo` para `moto1`, devolviendo al cliente un proxy con una URI del daemon.

```text
15:25:09 recibí Proxy, referencia PYRO:obj_8e40127492204799a68646dd1574d411@servidor:9100
15:25:09 posición registrada -> {'vehiculo': 'moto1', 'lat': -41.45, 'lon': -72.9}
15:25:09 historial en el servidor -> {'vehiculo': 'moto1', 'creado': '15:25:09', 'posiciones': [{'vehiculo': 'moto1', 'lat': -41.45, 'lon': -72.9}]}
15:25:09 seguimiento finalizado -> {'vehiculo': 'moto1', 'creado': '15:25:09', 'posiciones': [{'vehiculo': 'moto1', 'lat': -41.45, 'lon': -72.9}]}
15:25:09 REFERENCIA COLGANTE (esperado): DaemonError: unknown object
15:25:18 seguimientos vivos: 0
```

**¿Qué pasó con `POR_VALOR=1`? ¿Por qué el cliente rechaza el objeto?**

La fábrica devolvió el objeto sin registrarlo en el daemon. Pyro5 intentó serializarlo por valor, pero su clase no estaba soportada para reconstrucción en el cliente:

```text
15:26:44 ERROR de serialización. El servidor intentó enviar un objeto por valor. unsupported serialized class: objetos.SeguimientoVehiculo
```

**¿Qué pasó al usar la referencia después de confirmar?**

El objeto se registró y se devolvió por referencia (`Proxy`). Tras llamar a `finalizar()`, el daemon dejó de reconocer la URI (`unknown object`): una referencia colgante. Se restauró `POR_VALOR=0` y se confirmó que quedaban 0 seguimientos vivos.

## Paso 4, modo de instancia

| Modo | Instancia del proxy A | Instancia del proxy B | ¿Comparten el contador? |
|---|---|---|---|
| `single` | 1; llamadas 4 y 5 | 1; llamadas 6 y 7 | Sí |
| `session` | 1; llamadas 1 y 2 | 2; llamadas 1 y 2 | No |

**¿En cuál de los dos modos guardarían estado de un cliente?**

En el modo `session`, porque cada cliente conectado tiene su propia instancia de `Geolocalizacion`, lo que permite mantener su estado de forma independiente sin compartirlo con otros clientes.

**¿Por qué el stock no cambia entre modos?**

Porque los datos de los vehículos se almacenan en el módulo `dominio.py`, que es compartido por todas las instancias. Por eso, tanto en `single` como en `session`, los clientes acceden a las mismas posiciones, aunque cada instancia tenga su propio contador de llamadas.

## Paso 5, falla en tres tiempos

| Tiempo | Qué hicimos | Qué vio `vigilar` | Qué vio un cliente nuevo | Qué pasó con el estado |
|---|---|---|---|---|
| 1. Servidor muerto | `docker compose kill servidor` | Apareció `ConnectionClosedError` y luego falló un intento de reconexión. | No se realizó una prueba con un cliente nuevo mientras el servidor estaba caído. | El estado del proceso dejó de estar disponible. |
| 2. Servidor vuelve | `docker compose start servidor` | Reanudó las consultas `ok` sin necesidad de reiniciar `vigilar`. | `donde moto1` respondió correctamente. | Al actualizar `moto1` antes de una nueva caída y reiniciar el servidor, su posición pasó de `(-41.45, -72.90)` a los valores iniciales `(-41.47, -72.94)`. Esto confirmó que los cambios no persistían. |
| 3. Nombres muerto y de vuelta | `docker compose kill nombres`, después `docker compose start nombres` y, finalmente, `docker compose restart servidor` | Siguió realizando consultas porque ya tenía establecida la conexión al servicio. | Con el servidor de nombres caído apareció `Failed to locate the nameserver`; al reiniciarlo sin volver a registrar el servicio, apareció `unknown name`. Después de reiniciar el servidor de geolocalización, la URI y las consultas volvieron a funcionar. | El servidor de geolocalización permaneció activo al caer el servidor de nombres, pero se perdió el registro del nombre cuando este último se reinició. |

### Falla durante un seguimiento remoto

También se probó una caída mientras el cliente mantenía una referencia a un objeto `SeguimientoVehiculo`. Primero se inició el seguimiento de `moto1`, se registró una posición y se dejó al cliente esperando 20 segundos antes de finalizar. Durante la espera, se detuvo y volvió a iniciar el servidor. Cuando el cliente intentó finalizar el seguimiento utilizando la misma URI, se encontró con una referencia colgante: el servidor ya estaba disponible, pero no conservaba el objeto remoto creado antes de la caída.

**Evidencia obtenida en el cliente:**

```text
15:37:30 recibí Proxy, referencia PYRO:obj_f38ff6c4afb94c4eb76da10d75d257af@servidor:9100
15:37:30 posición registrada -> {'vehiculo': 'moto1', 'lat': -41.45, 'lon': -72.9}
15:37:30 historial en el servidor -> {'vehiculo': 'moto1', 'creado': '15:37:30', 'posiciones': [{'vehiculo': 'moto1', 'lat': -41.45, 'lon': -72.9}]}
15:37:30 espero 20 segundos antes de finalizar
15:37:50 Se perdió la conexión. Reintentando con la misma URI
15:38:20 ERROR. El servidor responde, pero el objeto de esa referencia ya no existe (referencia colgante). connection to ('servidor', 9100) rejected: unknown object
```

**Comprobación después del reinicio:**

```text
15:38:04 seguimientos vivos: 0
15:38:04 donde -> {'vehiculo': 'moto1', 'lat': -41.47, 'lon': -72.94}
```

Esto demuestra que el objeto remoto y su historial estaban almacenados en memoria: tras la caída, el cliente conservó la referencia, pero el servidor ya no reconocía su identificador. También se perdieron las actualizaciones de posición que no estaban guardadas de forma persistente.

### Preguntas de cierre

**¿Qué nodo es punto único de falla en esta arquitectura?**

El servidor de nombres (`nombres`) es un punto único de falla para los clientes nuevos, porque, si deja de funcionar, no pueden localizar el servicio de geolocalización por su nombre. El nodo `servidor` también es un punto único de falla, ya que su caída interrumpe las operaciones y provoca la pérdida del estado almacenado en memoria.

**¿Cómo lo resolverían?**

Implementaríamos servidores de respaldo y mecanismos de recuperación automática para mantener la disponibilidad. Además, utilizaríamos almacenamiento persistente para conservar las posiciones, los seguimientos y la información necesaria para recuperarlos después de un reinicio. Para el servidor de nombres, también habilitaríamos el registro periódico del servicio, de modo que pueda volver a anunciarse automáticamente después de una caída.

**¿Qué hace `REREGISTRO=5` y qué costo tiene?**

Con `REREGISTRO=5`, el servidor intenta registrar su servicio en el servidor de nombres cada cinco segundos. Esto permitiría recuperar el registro automáticamente después de reiniciar `nombres`, sin tener que reiniciar el servidor de geolocalización. A cambio, genera solicitudes periódicas y un pequeño consumo adicional de red y procesamiento, incluso cuando el nombre ya está registrado. Esta explicación corresponde al comportamiento previsto por el código; la prueba realizada utilizó `REREGISTRO=0`.
