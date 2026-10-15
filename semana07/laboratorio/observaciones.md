# Observaciones de la Semana 7

Equipo: andler-soto  
Integrantes: Álvaro Andler y Elías Soto  
Dominio del servicio: Geolocalización y despacho

## Paso 1  diagrama de despliegue v1 (el sistema de la semana 6)

Archivo entregado en `diagramas/`: está disponible `despliegue_base.drawio` como base v1; la exportación v1 propia está pendiente. El PNG `despliegue_geolocalización.png` ya representa los tres niveles de semana 7.

Cantidad de nodos, redes y puertos representados: en la base v1 hay tres contenedores locales (`cliente`, `carga`, `servidor`) y un cliente externo, una red `sd_net` y conexiones TCP al puerto 5000, publicado como `5000:5000`.

## Paso 2  revisión por pares

Equipo que revisó nuestro diagrama
Ítems de la pauta marcados como NO (copiar el número y el comentario)
Qué vamos a corregir primero y por qué

Equipo cuyo diagrama revisamos
Los dos hallazgos más importantes que les dejamos

## Paso 3  una operación como servicio REST

Operación del protocolo de texto elegida: `POSICION moto1 -41.48 -72.96`.

Método y ruta HTTP: `PUT /vehiculos/moto1/posicion`, con JSON `{"lat":-41.48,"lon":-72.96}`.

Salida de la prueba contra api1 (copiar la línea completa):

```text
200   0.04 s  {"vehiculo":"moto1","lat":-41.48,"lon":-72.96,"replica":"api1"}
```

Salida de un caso de error y su código HTTP: `GET /vehiculos/fantasma/posicion` contra api1 devolvió 404.

```text
404   0.01 s  {"detail":{"error":"VEHICULO_NO_EXISTE","detalle":"","replica":"api1"}}
```

## Paso 4  dos réplicas detrás de Nginx

Salida de `cliente_http.py --repetir 4`,  para `GET /vehiculos/moto1/posicion`:

```text
200   0.01 s  {"vehiculo":"moto1","lat":-41.47,"lon":-72.94,"replica":"api1"}
200   0.00 s  {"vehiculo":"moto1","lat":-41.47,"lon":-72.94,"replica":"api2"}
200   0.00 s  {"vehiculo":"moto1","lat":-41.47,"lon":-72.94,"replica":"api1"}
200   0.00 s  {"vehiculo":"moto1","lat":-41.47,"lon":-72.94,"replica":"api2"}
```

Esta salida corresponde a la prueba manual posterior al reinicio del servidor, por eso muestra la posición inicial de moto1. Los pasos 3 y 5 conservan los resultados del ensayo anterior.

**¿Qué réplica atendió cada petición?:**  
`api1`, `api2`, `api1`, `api2`, respectivamente.

**¿El dato es el mismo sin importar la réplica? ¿Por qué?**  
Sí, ambas devolvieron `(-41.47,-72.94)` porque consultan el mismo servidor TCP, que conserva las posiciones ya que la API no guarda estado.

## Paso 5  falla provocada en dos tiempos

### Tiempo 1, cae una réplica de la API
Predicción escrita ANTES de ejecutar: Nginx enviará las solicitudes a api2 y las lecturas seguirán respondiendo 200 con la misma posición. Alguna petición podría demorarse por el reintento al detectar la caída de api1.

Comando usado: `docker compose kill api1`, luego `docker compose exec cliente python cliente_http.py --repetir 4 GET /vehiculos/moto1/posicion`.

Qué respondió el sistema (copiar las líneas):

```text
200   1.01 s  {"vehiculo":"moto1","lat":-41.47,"lon":-72.94,"replica":"api2"}
200   1.01 s  {"vehiculo":"moto1","lat":-41.47,"lon":-72.94,"replica":"api2"}
200   1.01 s  {"vehiculo":"moto1","lat":-41.47,"lon":-72.94,"replica":"api2"}
200   1.01 s  {"vehiculo":"moto1","lat":-41.47,"lon":-72.94,"replica":"api2"}
```

**¿Cuánto tardó la primera petición después de la caída?:**   
1.01 s. Las cuatro peticiones tardaron 1.01 s y fueron atendidas por api2 con HTTP 200.

### Tiempo 2, cae el servidor TCP
Predicción escrita ANTES de ejecutar: api2 seguirá levantada, pero no podrá consultar las posiciones y devolverá 503. Al reiniciar el servidor se perderán los cambios en memoria y se recuperarán los valores iniciales.

Comando usado: `docker compose kill servidor`, luego `docker compose exec cliente python cliente_http.py --repetir 2 GET /vehiculos/moto1/posicion`. Recuperación con `docker compose start servidor` y, al terminar, `docker compose start api1`.

Qué respondió el sistema y con qué código HTTP:

```text
503   3.98 s  {"detail":{"error":"SERVIDOR_NO_DISPONIBLE","detalle":"gaierror","replica":"api1"}}
503   3.83 s  {"detail":{"error":"SERVIDOR_NO_DISPONIBLE","detalle":"gaierror","replica":"api1"}}
```

**¿Qué se perdió al volver a levantar el servidor?:**  
Se perdió la posición actualizada de moto1, que volvió a `(-41.47,-72.94)`. El pedido p2 creado durante el ensayo dejó de existir, p1 volvió a estar pendiente y el siguiente pedido creado volvió a recibir el ID p2. El servidor reinició sus diccionarios en memoria.

### Conclusión en tres líneas
**¿Qué nivel se pudo replicar sin problemas y cuál no? ¿Por qué?**  
Se pudo replicar el nivel de API porque sus instancias no guardan estado y consultan el mismo servidor TCP.\
El nivel de datos no se replicó: el servidor era la única copia de las posiciones, pedidos y asignaciones.\
Al reiniciarlo se perdieron los cambios; el Lock protege la concurrencia, pero no aporta persistencia.