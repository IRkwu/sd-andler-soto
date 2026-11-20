# Reporte de Servicios Cliente-Servidor

**Equipo:** andler-soto  
**Integrantes:** Álvaro Andler y Elías Soto  
**Dominio:** Geolocalización y despacho  
**Repositorio:** <https://github.com/IRkwu/sd-andler-soto>  
**Fecha:** 20-11-2026

## 1. El servicio y su dominio

El servicio guarda y entrega la posición de los vehículos de una plataforma de despacho, como las que estudiamos en la investigación de la Evaluación 1 (Uber y Cornershop, `docs/investigacion/investigacion.pdf`). El sistema necesita una ubicación reciente y suficientemente precisa de cada vehículo para tomar decisiones de despacho en tiempo real.

Lo usan los conductores o repartidores, que reportan su posición, y el despacho, que consulta dónde está cada vehículo para asignarle un pedido. En nuestra investigación, los teléfonos no hablan directo con los servicios internos: entran por un nodo Edge/API. Nuestro servicio está en esa parte interna.

La clase remota de entrada es `Geolocalizacion`, que delega la lógica del negocio a `dominio.py`, reutilizado de la semana 11 (`semana12/objetos.py`):

| Clase | Método remoto | Función de dominio / finalidad | ¿Cambia estado? |
|---|---|---|---|
| `Geolocalizacion` | `listar()` | `dominio.listar_vehiculos()` | No; consulta posiciones |
| `Geolocalizacion` | `donde(vehiculo)` | `dominio.donde(vehiculo)` | No; consulta una posición |
| `Geolocalizacion` | `posicion(vehiculo, lat, lon)` | `dominio.posicion(...)` | Sí; actualiza una posición |
| `Geolocalizacion` | `iniciar_seguimiento(vehiculo)` | Fábrica de objetos de seguimiento | Sí; crea y registra un objeto remoto |
| `SeguimientoVehiculo` | `registrar_posicion(lat, lon)` | Actualiza la posición y la añade al historial propio | Sí |
| `SeguimientoVehiculo` | `ver_historial()` | Devuelve una copia del historial | No |
| `SeguimientoVehiculo` | `finalizar()` / `cancelar()` | Desregistra el objeto remoto | Sí; termina su ciclo de vida |

Las posiciones viven en memoria y parten con `moto1 (-41.47, -72.94)` y `moto2 (-41.46, -72.95)`. Las operaciones de despacho (`PEDIDO`, `TOMAR` y `CERCANO`) existieron en el protocolo de texto (`semana09/protocolo.md`), pero todavía no las pasamos a objetos remotos.

## 2. Arquitectura y topología

![Topología del servicio con Pyro5 (`docs/informe/img/topologia_pyro5.png`)](img/topologia_pyro5.png)

El diagrama corresponde a `semana12/docker-compose.yml`. Son tres contenedores en la red `sd_net` y ningún puerto se publica hacia el host. La configuración sale de `semana12/.env` (`EQUIPO=andler-soto`, `MODO=single`, `POR_VALOR=0` y `REREGISTRO=0`).

| Nodo | Qué hace | Puerto y protocolo |
|---|---|---|
| `nombres` (`sd_nombres`) | Servidor de nombres de Pyro5 (`python -m Pyro5.nameserver -n nombres -p 9090 -x`). Guarda qué URI corresponde a cada nombre lógico | `nombres:9090`, TCP con el protocolo de Pyro5 |
| `servidor` (`sd_servidor`) | `servidor_pyro.py` crea el daemon, registra `Geolocalizacion` con el id `geolocalizacion` y la publica como `sd.andler-soto.geolocalizacion`. Los objetos `SeguimientoVehiculo` se registran en el mismo daemon con ids `obj_…` | `servidor:9100`, TCP con el protocolo de Pyro5 y serialización `serpent` |
| `cliente` (`sd_cliente`) | Contenedor para ejecutar `cliente_pyro.py` y `medir.py`. Usa un proxy `PYRONAME:sd.andler-soto.geolocalizacion` con `_pyroTimeout = 5` | Se conecta a `nombres:9090` y después a `servidor:9100` |

**¿En qué orden se comunican?**

0. Al arrancar, `servidor` se registra en `nombres`. Si `nombres` todavía no está listo, `registrar()` reintenta hasta 30 veces.
1. El cliente le pregunta a `nombres` por `sd.andler-soto.geolocalizacion` y recibe la URI `PYRO:geolocalizacion@servidor:9100`.
2. El cliente llama los métodos directamente en `servidor:9100`. Con `iniciar_seguimiento` recibe un proxy nuevo a un objeto `obj_…`.

Después del paso 1, el cliente ya no necesita a `nombres`. Eso explica la tercera falla de la sección 6.

## 3. Evolución del contrato

Usamos como ejemplo la misma consulta en todas las etapas: dónde está `moto1`. En la semana 4 el servicio todavía no era de geolocalización, así que mostramos el formato del protocolo base.

| Etapa | Semana | Dónde está el contrato | Ejemplo de la misma operación |
|---|---|---|---|
| Protocolo de texto sobre TCP | 4 y 6 | `protocolo.md` (`semana04/` y `semana06/laboratorio/`) | S4: `ECO <texto>` → `ECO <texto>`. S6: `DONDE moto1` → `OK moto1 -41.47 -72.94` |
| REST | 7 | `interfaz_http.md` (`semana07/laboratorio/`) | `GET /vehiculos/moto1/posicion` → `200 {"vehiculo":"moto1","lat":-41.47,"lon":-72.94,"replica":"api1"}` |
| Mensajes estructurados | 9 | `protocolo.md` v3 (`semana09/`) | 4 bytes de largo + `{"operacion":"DONDE","argumentos":["moto1"],"id":3,"version":2}` → `{"id":3,"estado":"OK","datos":["moto1","-41.47","-72.94"],"error":""}` |
| JSON-RPC | 10 | `rpc.py` (`semana10/`) | `{"jsonrpc":"2.0","method":"donde","params":["moto1"],"id":2}` → `{"jsonrpc":"2.0","result":{"vehiculo":"moto1","lat":-41.48,"lon":-72.96},"id":2}` |
| gRPC | 11 | `.proto` y `contrato.md` (`semana11/`) | `stub.Donde(DondeSolicitud(vehiculo="moto1"), timeout=2)` → `PosicionRespuesta{vehiculo:"moto1", lat:-41.47, lon:-72.94}` |
| Objetos remotos | 12 | `objetos.py` (`semana12/`) | `proxy.donde("moto1")` → `{'vehiculo': 'moto1', 'lat': -41.45, 'lon': -72.9}` |

Los valores cambian según el estado del servidor en cada prueba. Las respuestas de las semanas 10 y 12 están copiadas de `semana10/pruebas.md` y `semana12/observaciones.md`.

**¿Qué ganaron y qué perdieron en cada cambio?**

- **Texto sobre TCP (semanas 4 y 6).** Ganamos un protocolo que se lee y se prueba a mano y, en la semana 6, un servidor concurrente con `Lock` y códigos de error propios (`VEHICULO_NO_EXISTE`, `FORMATO`). Perdimos los tipos, porque todo viaja como texto. Tampoco hay id ni versión, y el contrato existe solo en el `.md`.
- **Texto → REST (semana 7).** Ganamos una entrada única por Nginx, dos réplicas de la API sin estado y códigos HTTP estándar. Al caer `api1`, `api2` siguió respondiendo 200 (`semana07/laboratorio/observaciones.md`). Perdimos simplicidad: cada petición da un salto extra, la primera después de la caída tardó 1,01 s, y el estado siguió en un único servidor TCP, que al caer devolvió 503.
- **REST → mensajes estructurados (semana 9).** Ganamos un enmarcado por largo, los campos `version` e `id` y un codec binario. El binario ocupó aproximadamente un 63 % menos de bytes en las solicitudes y un 61 % menos en las respuestas que JSON (`semana09/observaciones.md`). Perdimos legibilidad, y cliente y servidor tienen que mantener el codec a mano.
- **Estructurados → JSON-RPC (semana 10).** Ganamos un estándar con códigos de error definidos (-32601, -32602 y -32000), lotes y notificaciones (`semana10/pruebas.md`). Perdimos la validación de tipos: no hay IDL, así que `rpc.py` revisa a mano que `lat` y `lon` sean números.
- **JSON-RPC → gRPC (semana 11).** Ganamos un contrato tipado (`double lat = 3`), stubs generados, deadlines, códigos de estado y `id_solicitud` para deduplicar `Posicion`. Además, `ListarVehiculos` se agregó sin romper a los clientes antiguos (`semana11/contrato.md`). Perdimos legibilidad, porque ya no se puede probar con `curl`, y hay que regenerar los stubs cada vez que cambia el `.proto`.
- **gRPC → objetos remotos (semana 12).** Ganamos objetos con estado que viajan por referencia (`SeguimientoVehiculo`), llamadas que parecen locales (`proxy.donde("moto1")`) y un servidor de nombres para no escribir `host:puerto`. Perdimos el contrato independiente del lenguaje (Pyro5 es solo Python), los deadlines del servidor y la deduplicación. También apareció un nodo crítico nuevo (`nombres`) y el riesgo de referencias colgantes (`unknown object`).

## 4. Mecanismo elegido y justificación

**Mecanismo elegido:** objetos remotos con Pyro5 (`semana12/`), para la presentación del 4-12.

**¿Por qué?**

- **Un seguimiento es un objeto con estado y ciclo de vida.** Un viaje o pedido se sigue desde que empieza hasta que termina, con su propio historial de posiciones. Con Pyro5 eso es `SeguimientoVehiculo`: se crea con `iniciar_seguimiento`, se usa con `registrar_posicion` y `ver_historial`, y termina con `finalizar` o `cancelar` (`semana12/observaciones.md`, paso 3). En gRPC o JSON-RPC tendríamos que inventar un `id_seguimiento` y mantener una tabla a mano.
- **El despacho no necesita conocer `host:puerto`.** Pide `sd.andler-soto.geolocalizacion` y el servidor de nombres le dice dónde está. Si el servidor se mueve de nodo, basta con volver a registrarlo.
- **Fue la consulta más rápida que medimos.** El despacho consulta posiciones muchas veces para decidir. `listar` tardó 0,28 ms de mediana en Pyro5 y 0,63 ms en gRPC (sección 5).
- **Lo de "solo Python" no nos afecta aquí.** El servicio vive detrás del Edge/API, donde todos nuestros nodos son Python y comparten el mismo `dominio.py`. Además, el proyecto integrador sigue con objetos remotos y el nodo `nombres` (`proyecto/ALCANCE.md`).

| Criterio | Mecanismo elegido | Alternativa 1 | Alternativa 2 |
|---|---|---|---|
| Mecanismo | **Pyro5** (semana 12) | gRPC (semana 11) | JSON-RPC 2.0 (semana 10) |
| Modelo | Objetos remotos con estado y referencias | Procedimientos remotos agrupados en un servicio | Procedimientos remotos por nombre |
| Contrato o IDL | La clase Python expuesta (`objetos.py`), sin IDL | `.proto` con tipos, compilado a stubs | No hay IDL; los métodos se registran en `METODOS` |
| Transporte y formato | TCP con el protocolo de Pyro5, `serpent` | HTTP/2 sobre TCP, Protobuf binario | HTTP, JSON en texto |
| Lenguajes | Solo Python | Multilenguaje | Cualquiera que maneje JSON |
| Referencias y estado (seguimiento de un viaje) | `SeguimientoVehiculo` por referencia, con historial y ciclo de vida | Sin referencias; habría que crear un `id_seguimiento` | Sin referencias ni sesión |
| Manejo de errores | Excepciones remotas; `ErrorDominio` llega con su nombre (`register_dict_to_class`) | Códigos de estado (`FAILED_PRECONDITION`) | Objeto `error` (-32000) |
| Cómo encuentra el cliente al servidor | Por nombre en `nombres`; es punto único de falla para clientes nuevos | `servidor:50051` fijo | URL fija |
| Latencia de `listar` (p50) | 0,28 ms | 0,63 ms | No medido |
| Bytes de la respuesta de `listar` | 121 | 54 | No medido |
| Plazo de la llamada | Timeout del proxy (`_pyroTimeout = 5`), solo en el cliente | Deadline que viaja al servidor | Timeout del cliente HTTP |
| Reintento seguro de `posicion` | No implementado | `id_solicitud` y `DEDUP` probados en la semana 11 | No implementado |

**¿Qué perdemos al elegir Pyro5?**

Tres cosas que gRPC sí tenía. La primera es la deduplicación: en la semana 11, reintentar sin `id_solicitud` aplicó la misma `Posicion` tres veces, y en Pyro5 eso todavía no está resuelto. La segunda es el deadline que viaja al servidor, porque en Pyro5 solo existe el timeout del cliente. La tercera es el tamaño: la misma respuesta ocupa unas 2,2 veces más bytes. Lo aceptamos porque esos bytes viajan por la red interna, no por los datos móviles del conductor. La deduplicación es lo primero que tendríamos que llevar a `posicion` desde la semana 11.

## 5. Evidencia de funcionamiento y medición

**Evidencia obtenida en el cliente** (`semana12/observaciones.md`, pasos 1 y 2). El cliente corre en `sd_cliente`, resuelve el nombre en `sd_nombres` y llama al objeto en `sd_servidor`:

```text
15:16:32 sd.andler-soto.geolocalizacion -> PYRO:geolocalizacion@servidor:9100
15:16:32 nombres registrados ['Pyro.NameServer', 'sd.andler-soto.geolocalizacion']
15:16:33 vehiculos [{'vehiculo': 'moto1', 'lat': -41.47, 'lon': -72.94}, {'vehiculo': 'moto2', 'lat': -41.46, 'lon': -72.95}]
15:16:33 posicion -> {'vehiculo': 'moto1', 'lat': -41.45, 'lon': -72.9}
15:16:34 donde -> {'vehiculo': 'moto1', 'lat': -41.45, 'lon': -72.9}
```

**Paso por referencia entre contenedores** (`semana12/observaciones.md`, paso 3):

```text
15:25:09 recibí Proxy, referencia PYRO:obj_8e40127492204799a68646dd1574d411@servidor:9100
15:25:09 posición registrada -> {'vehiculo': 'moto1', 'lat': -41.45, 'lon': -72.9}
15:25:09 seguimiento finalizado -> {'vehiculo': 'moto1', 'creado': '15:25:09', 'posiciones': [{'vehiculo': 'moto1', 'lat': -41.45, 'lon': -72.9}]}
```

**Comandos usados para medir:**

```bash
# Pyro5, dentro de semana12/
docker compose up -d --build
docker compose exec cliente python medir.py pyro --metodo listar --nombre sd.andler-soto.geolocalizacion
# gRPC, dentro de semana11/ (medir.py con las tres líneas EDITAR ajustadas)
docker compose up -d --build
docker compose exec cliente python medir.py grpc --metodo listar
```

Medición con `medir.py`, la misma operación de consulta sobre el mecanismo elegido y sobre una alternativa

| Mecanismo | Operación | n | p50 ms | p95 ms | media ms | máx ms | respuesta bytes |
|---|---|---|---|---|---|---|---|
| pyro | listar | 200 | 0.28 | 0.35 | 0.28 | 0.6 | 121 |
| grpc | listar | 200 | 0.63 | 0.67 | 0.65 | 4.12 | 54 |

En los dos casos `listar` llama a `dominio.listar_vehiculos()` y no cambia estado. La fila de gRPC también quedó en `semana11/mediciones.csv`.

**¿Qué explica la diferencia?**

Pyro5 fue unas 2,3 veces más rápido: 0,28 ms de mediana contra 0,63 ms de gRPC. También fue más estable, con un máximo de 0,6 ms contra 4,12 ms. En bytes pasó lo contrario: Pyro5 mandó 121 y gRPC 54.

- **Latencia.** gRPC tardó más aunque mandó menos bytes, así que su costo extra está en el protocolo y no en los datos. Creemos que se debe a que `grpcio` arma en cada llamada los frames de HTTP/2 (cabeceras, datos y trailers), mientras que Pyro5 escribe un mensaje simple sobre un socket ya abierto. Es una hipótesis, porque no medimos cada parte por separado.
- **Bytes.** `serpent` escribe la lista como texto y repite `'vehiculo'`, `'lat'` y `'lon'` en cada vehículo. Protobuf usa números de campo y binario. Es la misma tendencia de la semana 9. `medir.py` cuenta solo los datos útiles, no las cabeceras de ninguno de los dos protocolos.

**¿Importa esa diferencia para su dominio?**

En la parte interna, donde está nuestro servicio, importa más la latencia que el tamaño, porque el despacho consulta posiciones muchas veces para decidir. Aun así, 0,35 ms es poco: la medición apoya la elección, pero no la decide. El tamaño sí importaría si las posiciones llegaran directo desde los teléfonos, porque gastarían datos móviles. En nuestro diseño entran por el Edge/API.

## 6. Análisis de fallos

| Falla provocada | Qué esperaban según la teoría | Qué observaron | Qué harían para tolerarla |
|---|---|---|---|
| Servidor cae a mitad de una llamada (semana 11) | El cliente no puede saber si el servidor no recibió la petición, si la ejecutó y no alcanzó a responder, o si la respuesta se perdió. El resultado queda desconocido | Con `docker compose kill servidor` durante la llamada, el cliente recibió `UNAVAILABLE` y el resultado quedó desconocido (caso 5). Con `FALLA=siempre`, el servidor aplicó el cambio, pero el cliente vio `DEADLINE_EXCEEDED` (caso 2). Al reintentar sin `DEDUP`, el cambio se aplicó tres veces (caso 3); con `DEDUP=1`, una vez (caso 4) | Reintentar siempre con el mismo `id_solicitud` y deduplicar en el servidor, guardando la tabla de deduplicación de forma persistente |
| Servidor cae y vuelve (semana 12) | Un cliente con proxy puede reconectarse a la misma URI, pero se pierde lo que estaba en memoria: posiciones y objetos registrados en el daemon | `vigilar` mostró `ConnectionClosedError` y luego retomó las consultas sin reiniciarse. `moto1` volvió de `(-41.45, -72.90)` a `(-41.47, -72.94)`. El seguimiento creado antes de la caída quedó como referencia colgante (`unknown object`) y `seguimientos vivos` quedó en 0 | Utilizar almacenamiento persistente para conservar las posiciones, los seguimientos y la información necesaria para recuperarlos después de un reinicio |
| Servidor de nombres cae (semana 12) | Los clientes que ya tienen la URI siguen funcionando. Los clientes nuevos no pueden localizar el servicio. Si `nombres` vuelve vacío, el nombre no existe hasta que alguien lo vuelva a registrar | Tal como esperábamos: `vigilar` siguió consultando, un cliente nuevo vio `Failed to locate the nameserver` y, al volver `nombres`, apareció `unknown name` hasta que reiniciamos `servidor` | Habilitar el registro periódico (`REREGISTRO=5`), que no probamos, o replicar el servidor de nombres |

**¿Qué semántica de fallo (como máximo una vez, al menos una vez) ofrece hoy su servicio?**

Como máximo una vez. Con Pyro5, cada llamada se envía una sola vez. Si la conexión se corta, el cliente recibe `ConnectionClosedError` o `CommunicationError` y no sabe si el método se ejecutó. Si el cliente vuelve a llamar después de reconectarse, como hace `vigilar` con `_pyroReconnect`, pasa a ser al menos una vez, porque Pyro5 no deduplica. Para una consulta no es un problema, pero con `posicion` o `registrar_posicion` sí lo es: es lo mismo que vimos en gRPC sin `DEDUP`, donde la misma `Posicion` se aplicó tres veces.

**¿Cuál necesita su dominio?**

Depende de la operación.

- **`posicion`:** le basta al menos una vez, porque sobrescribe coordenadas absolutas y repetirla deja el mismo estado. Es mejor que el despacho vea la posición a que no la vea. Hay un riesgo: un reintento atrasado puede llegar después de una posición más nueva y hacer que el marcador "salte" a un punto viejo.
- **`registrar_posicion`:** necesita más cuidado, porque además agrega al historial y un reintento lo duplicaría.
- **Despacho (`TOMAR`, asignar un pedido):** no es idempotente, porque asignar dos veces es un error. Necesita exactamente una vez en efecto, es decir, `id_solicitud` más deduplicación persistente.

Esa es la mejora pendiente más importante del servicio en Pyro5. Ya sabemos cómo hacerla, porque la probamos en gRPC (`semana11/observaciones.md`, caso 4).

## 7. Referencias

1. van Steen, M. y Tanenbaum, A. S. (2017). *Distributed Systems* (3.ª ed.). Capítulo 4 (Communication), capítulo 5 (Naming) y capítulo 8, §8.3 (Reliable client-server communication). Bibliografía del curso.
2. Coulouris, G., Dollimore, J. y Kindberg, T. (2001). *Sistemas distribuidos: conceptos y diseño* (3.ª ed.). Addison-Wesley. Capítulo 5 (Objetos distribuidos e invocación remota). Bibliografía del curso.
3. de Jong, I. (s. f.). *Pyro5 documentation*. <https://pyro5.readthedocs.io/>
4. gRPC Authors. (s. f.). *Core concepts, architecture and lifecycle* y *Status codes*. <https://grpc.io/docs/guides/concepts/> y <https://grpc.io/docs/guides/status-codes/>
5. JSON-RPC Working Group. (2013). *JSON-RPC 2.0 Specification*. <https://www.jsonrpc.org/specification>
6. Brodsky, I. (2018). *H3: Uber's Hexagonal Hierarchical Spatial Index*. Uber Engineering Blog. Citada en nuestra investigación (`docs/investigacion/investigacion.pdf`).
