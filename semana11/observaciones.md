# Observaciones semana 11 · Migración a gRPC

Equipo Soto-Andler · Dominio ……………… · Fecha 06-11-2026

## 1. Contrato
- Archivo `proto/servicio.proto` con 3 operaciones.
- Operaciones que modifican estado y llevan `id_solicitud`: **`Posicion`**.
- Operaciones idempotentes (se pueden repetir sin efecto extra): **`Posicion`, `Donde` y `ListarVehiculos`**.

## 2. Stubs generados
- Clase del stub en el cliente `GeolocalizacionStub`. (nombre exacto en `servicio_pb2_grpc.py`)
- Clase base del servidor `GeolocalizacionServicer`.
- Qué hace el stub cuando llamamos `stub.Agregar(...)`, en dos líneas, con sus palabras El stub recibe la solicitud del cliente, la envía al servidor mediante gRPC y luego devuelve la respuesta, permitiendo establecer un tiempo máximo de espera.
## 3. Equivalencia de errores JSON-RPC → gRPC

| Caso | JSON-RPC (semana 10) | gRPC (hoy) | Comando usado |
|---|---|---|---|
| Método inexistente | `-32601` | `UNIMPLEMENTED` | `docker exec sd_cliente python -c "import grpc; grpc.insecure_channel('servidor:50051').unary_unary('/geolocalizacion.v1.Geolocalizacion/Borrar')(b'', timeout=2)"` |
| Parámetros inválidos | `-32602` | `INVALID_ARGUMENT` | `docker exec sd_cliente python cliente_grpc.py posicion moto1 100 200` |
| Error del dominio | `-32000` | `FAILED_PRECONDITION` | `docker exec sd_cliente python cliente_grpc.py donde camion99` |
| Servidor caído | Sin conexión | `UNAVAILABLE` (esperado; en nuestra prueba observamos `DEADLINE_EXCEEDED`) | `docker exec sd_cliente python cliente_grpc.py donde moto1` |
| Respuesta lenta | Timeout del cliente | `DEADLINE_EXCEEDED` | `$env:FALLA="siempre"; $env:DEMORA="5"; docker compose up -d servidor` y luego `docker exec sd_cliente python cliente_grpc.py posicion moto1 -41.45 -72.90` |

Pistas. Parámetros inválidos con `agregar tornillo 0`. El cliente no deja llamar a un método inexistente, usen esta línea (cambien la ruta por la de su servicio).

```
docker compose exec cliente python -c "import grpc; grpc.insecure_channel('servidor:50051').unary_unary('/inventario.v1.Inventario/Borrar')(b'', timeout=2)"
```

El error muestra `status = StatusCode.UNIMPLEMENTED`.

## 4. Falla intermedia · semántica teórica frente a la observada

| # | Configuración | Qué vio el cliente | Coordenadas finales con `listar` | Semántica observada |
|---|---|---|---|---|
| 1 | `FALLA=no`, sin reintentos | `OK` en el primer intento. | `moto1 (-41.45, -72.90)` | La operación se ejecutó y el cliente recibió la respuesta correctamente. |
| 2 | `FALLA=siempre`, sin reintentos | `DEADLINE_EXCEEDED`. | `moto1 (-41.40, -72.80)` | El servidor aplicó el cambio, pero demoró la respuesta más que el tiempo límite del cliente. |
| 3 | `FALLA=siempre`, `--reintentos 2`, sin `DEDUP` | Tres intentos con `DEADLINE_EXCEEDED`. | `moto1 (-41.35, -72.70)` | El servidor ejecutó la misma operación tres veces porque no tenía deduplicación activada. |
| 4 | `FALLA=siempre`, `DEDUP=1`, `--reintentos 2` | Primer intento `DEADLINE_EXCEEDED`; segundo intento `OK`. | `moto1 (-41.30, -72.60)` | El servidor reconoció el mismo `id_solicitud` y devolvió el resultado guardado sin aplicar nuevamente el cambio. |
| 5 | `docker compose kill servidor` durante una llamada | `UNAVAILABLE`, conexión cerrada. | No se pudo consultar. | El servidor se detuvo durante la llamada. El cliente perdió la conexión y el resultado de la operación quedó desconocido. |

### Registros del servidor

**Caso 3 — Sin deduplicación (`DEDUP=0`):**

```text
[servidor] Posicion id=72a26067 -> {'vehiculo': 'moto1', 'lat': -41.35, 'lon': -72.7}
[servidor] FALLA=siempre, cambio YA aplicado, demoro la respuesta 5 s
[servidor] Posicion id=72a26067 -> {'vehiculo': 'moto1', 'lat': -41.35, 'lon': -72.7}
[servidor] FALLA=siempre, cambio YA aplicado, demoro la respuesta 5 s
[servidor] Posicion id=72a26067 -> {'vehiculo': 'moto1', 'lat': -41.35, 'lon': -72.7}
[servidor] FALLA=siempre, cambio YA aplicado, demoro la respuesta 5 s
```

**Caso 4 — Con deduplicación (`DEDUP=1`):**

```text
[servidor] Posicion id=fbb63a6d -> {'vehiculo': 'moto1', 'lat': -41.3, 'lon': -72.6}
[servidor] FALLA=siempre, cambio YA aplicado, demoro la respuesta 5 s
[servidor] Posicion id=fbb63a6d repetido, devuelvo lo guardado SIN aplicar de nuevo
```


## 5. Conclusión (cinco líneas como máximo)
¿Qué operaciones de su dominio serían peligrosas de reintentar sin `id_solicitud`? ¿Qué pasaría en la vida real?
En nuestro sistema, registrar posiciones o asignar vehículos a despachos podría ser peligroso si se repite una operación sin `id_solicitud`, ya que podría generar registros duplicados o asignaciones repetidas. En la vida real, esto podría causar confusiones al ubicar vehículos o coordinar despachos. Por eso, usamos `id_solicitud` para reconocer solicitudes repetidas y evitar ejecutar la misma operación más de una vez.