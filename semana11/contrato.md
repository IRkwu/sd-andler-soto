# Contrato del servicio · trabajo autónomo semana 11

Plazo jueves 12-11-2026 a las 18.00, en `semana11/` del repositorio del equipo.

## Qué hay que hacer
1. Agregar al menos **una operación nueva** a `proto/servicio.proto` con sus mensajes, sin cambiar los números de campo existentes.
2. Implementarla en `dominio.py` y exponerla en `servidor_grpc.py` y en `cliente_grpc.py`.
3. Regenerar los stubs y probarla desde el contenedor cliente.
4. Completar este archivo.

## Operaciones

| Operación | Qué hace | Modifica estado | Idempotente | Lleva `id_solicitud` | Errores posibles (código gRPC) |
|---|---|---|---|---|---|
| `Posicion` | Registra o actualiza las coordenadas de un vehículo. | Sí | Sí, si se repiten las mismas coordenadas, el estado final no cambia. | Sí | `INVALID_ARGUMENT`, `DEADLINE_EXCEEDED`, `UNAVAILABLE` |
| `Donde` | Consulta las coordenadas actuales de un vehículo. | No | Sí, porque consultar no modifica el estado. | No | `INVALID_ARGUMENT`, `FAILED_PRECONDITION`, `UNAVAILABLE` |
| `ListarVehiculos` | Devuelve todos los vehículos registrados con sus coordenadas. | No | Sí, porque consultar la lista no modifica el estado. | No | `INTERNAL`, `DEADLINE_EXCEEDED`, `UNAVAILABLE` |

## Mensajes y campos

| Mensaje | Campo | Número | Tipo | Significado |
|---|---|---|---|---|
| `PosicionSolicitud` | `id_solicitud` | 1 | `string` | Identificador único de la solicitud para controlar duplicados. |
| `PosicionSolicitud` | `vehiculo` | 2 | `string` | Identificador del vehículo. |
| `PosicionSolicitud` | `lat` | 3 | `double` | Latitud de la posición del vehículo. |
| `PosicionSolicitud` | `lon` | 4 | `double` | Longitud de la posición del vehículo. |
| `DondeSolicitud` | `vehiculo` | 1 | `string` | Identificador del vehículo que se desea consultar. |
| `PosicionRespuesta` | `vehiculo` | 1 | `string` | Identificador del vehículo consultado o actualizado. |
| `PosicionRespuesta` | `lat` | 2 | `double` | Latitud del vehículo. |
| `PosicionRespuesta` | `lon` | 3 | `double` | Longitud del vehículo. |
| `ListarVehiculosSolicitud` | — | — | — | Mensaje vacío: no necesita parámetros para consultar todos los vehículos. |
| `Vehiculo` | `vehiculo` | 1 | `string` | Identificador del vehículo. |
| `Vehiculo` | `lat` | 2 | `double` | Latitud del vehículo. |
| `Vehiculo` | `lon` | 3 | `double` | Longitud del vehículo. |
| `ListaVehiculosRespuesta` | `vehiculos` | 1 | `repeated Vehiculo` | Lista de vehículos registrados con sus coordenadas. |

## Decisiones

- **¿Por qué la operación nueva es o no es idempotente?**

  `ListarVehiculos` es idempotente porque solamente consulta los vehículos registrados y sus coordenadas. Ejecutarla varias veces no modifica el estado del servidor.

- **¿Qué pasaría si un cliente antiguo, que no conoce la operación nueva, sigue llamando al servidor?**

  El cliente antiguo puede seguir utilizando `Posicion` y `Donde`, siempre que esas operaciones y sus mensajes mantengan su compatibilidad. Sin embargo, no podrá llamar a `ListarVehiculos` porque no conoce esa operación ni tiene los stubs necesarios. Si intenta invocarla, el servidor responderá con `UNIMPLEMENTED` para ese método desconocido desde el punto de vista del cliente.

  La incorporación de la nueva operación no impide que los clientes antiguos sigan utilizando las operaciones existentes.

- **Prueba realizada (comando y salida)**

  Comando ejecutado desde el contenedor cliente:

  ```bash
  docker exec sd_cliente python cliente_grpc.py listar
  ```

  Salida obtenida:

  ```text
  [cliente] intento 1, id_solicitud=-, deadline 2 s
  [cliente] Vehículos registrados:
  [cliente] moto1 lat=-41.47 lon=-72.94
  [cliente] moto2 lat=-41.46 lon=-72.95
  ```

  **Resultado:** prueba exitosa. El cliente recibió correctamente la lista de vehículos y sus coordenadas desde el servidor gRPC.