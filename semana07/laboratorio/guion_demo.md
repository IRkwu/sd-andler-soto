# Guion de la demostración, Evaluación 3 (viernes 16-10)

Equipo andler-soto.  
Dominio: geolocalización y despacho.  
Integrantes: Álvaro Andler y Elías Soto.

## Antes de comenzar

```powershell
cd semana07/laboratorio
docker compose up -d --build
docker compose ps
```

Deben verse `sd_api1`, `sd_api2`, `sd_cliente`, `sd_nginx` y `sd_servidor` en up.  
Nginx debe mostrar el mapeo de puertos (`8080 -> 80`).

Definir el atajo `c` en la misma terminal.

PowerShell:

```powershell
function c { docker compose exec cliente @args }
```

Shell / Bash / Zsh:

```bash
c() { docker compose exec cliente "$@"; }
```

| Minuto | Qué mostramos | Quién habla | Comando o archivo en pantalla |
|---|---|---|---|
| 0 a 2 | Tres niveles: cliente, puerta sin estado y servidor con estado. Red, puertos y Lock | Elías | `diagramas/despliegue_geolocalización.png` |
| 2 a 4 | Actualizar y consultar la posición de `moto1` (200); consultar `fantasma` (404). Relación con `POSICION` y `DONDE` | Álvaro | `protocolo.md`, secciones 4 y 9.2; `c python cliente_http.py` con PUT y GET |
| 4 a 5 | Cinco contenedores y único puerto publicado. Cuatro consultas alternan entre `api1` y `api2` con la misma posición | Elías | `docker compose ps` y `c python cliente_http.py --repetir 4 GET /vehiculos/moto1/posicion` |
| 5 a 6 | 20 clientes: un OK y 19 `YA_ASIGNADO`. El intento con `moto2` devuelve 409 y confirma la asignación a `moto1`. Explicar el Lock | Álvaro | `c python cliente_carga.py --clientes 20 --comando "TOMAR moto1 p1"`, POST de asignación y `op_tomar` en `servidor.py` |
| 6 a 9 | Predecir y provocar dos fallas: sin `api1`, responde `api2` (200); sin servidor, 503. Recuperar y comprobar que volvió la posición inicial | Elías y Álvaro | `docker compose kill api1`, `docker compose kill servidor`, `docker compose start servidor api1` y consultas GET |

## Minuto 0 a 2

Abrir `diagramas/despliegue_geolocalización.png` y explicarlo:

- Cliente: el navegador llega a `nginx` por `HTTP 8080 -> 80`. El contenedor `cliente / sd_cliente` llega por la red interna al puerto 80.
- Puerta sin estado: Nginx reparte por `HTTP 8000` entre `api1` y `api2`. Ninguna guarda posiciones ni pedidos.
- Servidor con estado: las dos API hablan `TCP 5000` con `servidor`, un hilo por cliente. Ahí están las posiciones y los pedidos, en memoria y protegidos con Lock.

Cierre: si cae una API sigue la otra. Si cae Nginx no hay entrada HTTP. Si cae el servidor, la API responde 503 y se pierde el estado modificado.

## Minuto 2 a 4

Mostrar en `protocolo.md` los comandos `POSICION` y `DONDE` de la sección 4 y sus equivalentes HTTP en la sección 9.2.

Primera operación correcta, actualizar la posición:

```powershell
c python cliente_http.py PUT /vehiculos/moto1/posicion lat=-41.48 lon=-72.96
```

Esperado: HTTP 200 con la posición `(-41.48, -72.96)`.

Segunda operación correcta, consultar la posición:

```powershell
c python cliente_http.py GET /vehiculos/moto1/posicion
```

Esperado: HTTP 200 con la misma posición.

Error documentado:

```powershell
c python cliente_http.py GET /vehiculos/fantasma/posicion
```

Esperado: HTTP 404 con `VEHICULO_NO_EXISTE`.  
El servidor responde `ERROR VEHICULO_NO_EXISTE` y la API lo traduce a 404 porque el vehículo no existe.

## Minuto 4 a 5

Mostrar la topología levantada:

```powershell
docker compose ps
```

Señalar los cinco contenedores en `sd_net` y el único puerto expuesto, `8080 -> 80`.

```powershell
c python cliente_http.py --repetir 4 GET /vehiculos/moto1/posicion
```

Se esperan respuestas 200 desde `api1` y `api2`, identificadas por el campo `replica`, con la misma posición. Las API comparten el dato porque ambas consultan al servidor TCP.

## Minuto 5 a 6

Con `p1` todavía pendiente, lanzar 20 clientes que intenten asignarlo a `moto1`:

```powershell
c python cliente_carga.py --clientes 20 --comando "TOMAR moto1 p1"
```

Esperado: un `OK moto1 p1` y 19 `ERROR YA_ASIGNADO moto1`.

Comprobar el estado intentando asignar el mismo pedido a `moto2`:

```powershell
c python cliente_http.py POST /pedidos/p1/asignacion vehiculo=moto2
```

Esperado: HTTP 409 con `YA_ASIGNADO` y el detalle `moto1`. El pedido conserva la primera asignación.

Mostrar `op_tomar` en `servidor.py`: el Lock protege la comprobación de si el pedido está libre y la escritura de la asignación. Sin él, dos hilos podrían verlo libre y ambos responder éxito.

## Minuto 6 a 9

Antes de la primera falla, Elías predice: “Al detener api1, Nginx enviará las consultas a api2. Esperamos 200 y la misma posición, con una posible demora por el reintento”.

```powershell
docker compose kill api1
c python cliente_http.py --repetir 4 GET /vehiculos/moto1/posicion
```

Esperado: HTTP 200 desde `api2`, manteniendo latitud y longitud `(-41.48, -72.96)`. El servidor que guarda el estado sigue funcionando.

Antes de la segunda falla, Elías predice: “Al detener el servidor TCP, api2 seguirá activa pero no podrá consultar las posiciones. Esperamos HTTP 503”.

```powershell
docker compose kill servidor
c python cliente_http.py --repetir 2 GET /vehiculos/moto1/posicion
```

Esperado: HTTP 503 generado por la API. Si la conexión agota su tiempo de espera, puede responder 504. Explicar la salida observada: las réplicas de API dependen del mismo servidor.

Recuperar:

```powershell
docker compose start servidor api1
c python cliente_http.py GET /vehiculos/moto1/posicion
```

Cuando termine de arrancar, se espera HTTP 200 con `(-41.47, -72.94)`, la posición inicial. Se perdió la actualización porque estaba en memoria.

Cierre: las dos API toleran la caída de una réplica, pero el servidor TCP sigue siendo un punto único de falla. La mejora sería persistir los datos y replicar ese nivel con coordinación de las asignaciones.

## Plan B si algo no levanta

Mostrar el diagrama, el protocolo, `docker-compose.yml`, `nginx.conf` y [logs.txt](logs.txt) como respaldo del ensayo. Explicar el recorrido HTTP → API → TCP y aclarar que las salidas del archivo corresponden al ensayo previo.

Resultados registrados en `logs.txt`:

- Protocolo HTTP: actualización y consulta de `moto1` con 200; consulta de `fantasma` con 404 y `VEHICULO_NO_EXISTE`.
- Réplicas: cuatro consultas alternan entre `api1` y `api2`, manteniendo la posición `(-41.48, -72.96)`.
- Concurrencia: 20 clientes producen un `OK moto1 p1` y 19 `ERROR YA_ASIGNADO moto1`. El intento posterior con `moto2` devuelve 409 y confirma que el pedido sigue asignado a `moto1`.
- Caída de `api1`: las cuatro consultas responden 200 desde `api2` y conservan la posición.
- Caída del servidor: las dos consultas responden 503 con `SERVIDOR_NO_DISPONIBLE`.
- Recuperación: la consulta vuelve a responder 200, pero con la posición inicial `(-41.47, -72.94)`, mostrando que se perdió la actualización en memoria.
