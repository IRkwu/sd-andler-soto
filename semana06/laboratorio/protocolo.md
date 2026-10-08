# Protocolo de aplicación — versión 2

## 1. Identificación

| Campo | Valor |
|---|---|
| Equipo | andler-soto |
| Dominio del servicio | geolocalización |
| Versión del protocolo | 2.0 |
| Transporte | TCP, puerto 5000 |
| Codificación | UTF-8, un mensaje por línea, terminador `\n` |
| Modelo de concurrencia del servidor | hilo por cliente |
| Timeout de inactividad | 60 s (el servidor cierra la conexión) |

## 2. Formato general

- Petición `COMANDO [argumentos separados por espacio]\n`
- Respuesta correcta `OK [datos]\n`
- Respuesta de error `ERROR CODIGO [detalle]\n`
- El servidor responde una línea por cada petición procesada.
- Los comandos no distinguen mayúsculas de minúsculas.
- Los identificadores de vehículos y pedidos se convierten a minúsculas.

## 3. Secuencia de una sesión

```
cliente                          servidor
   |--- HOLA <nombre> ------------->|
   |<-- OK HOLA <nombre> -----------|
   |--- <operaciones...> ---------->|
   |<-- OK ... / ERROR ... ---------|
   |--- SALIR --------------------->|
   |<-- OK CHAO --------------------|   (el servidor cierra)
```

¿Es obligatorio HOLA antes de operar? (indicar sí o no y qué pasa si no se envía)
No, el cliente puede enviar operaciones sin identificarse.

## 4. Operaciones

| Comando | Argumentos | Respuesta OK | Errores posibles | ¿Modifica estado compartido? |
|---|---|---|---|---|
| HOLA | nombre | `OK HOLA nombre` | — | no |
| POSICION | vehiculo lat lon | `OK moto1 -41.47 -72.94` | `ERROR FORMATO …` | sí |
| DONDE | vehiculo | `OK moto1 -41.47 -72.94` | `ERROR FORMATO …`, `ERROR VEHICULO_NO_EXISTE` | no |
| PEDIDO | lat lon | `OK p2 pendiente` | `ERROR FORMATO …` | sí |
| TOMAR | vehiculo id_pedido | `OK moto1 p1` | `ERROR FORMATO …`, `ERROR VEHICULO_NO_EXISTE`, `ERROR PEDIDO_NO_EXISTE`, `ERROR YA_ASIGNADO moto1` | sí |
| CERCANO | lat lon | `OK moto1 distancia=0.0000` | `ERROR FORMATO …`, `ERROR SIN_VEHICULOS` | no |
| ESPERA | segundos | `OK ESPERA 2` | `ERROR FORMATO …` | no |
| SALIR | — | `OK CHAO` | — | no |

### Descripción de las operaciones y validación de coordenadas

- `POSICION` registra o actualiza las coordenadas de un vehículo.
- `DONDE` consulta la posición registrada de un vehículo.
- `PEDIDO` crea un pedido pendiente con un identificador nuevo.
- `TOMAR` asigna un pedido a un vehículo, siempre que todavía no esté asignado.
- `CERCANO` calcula qué vehículo está más cerca de las coordenadas indicadas, usando distancia euclidiana entre pares de coordenadas (no kilómetros de recorrido).
- `ESPERA` simula una operación lenta; no mantiene el Lock durante la espera.
- Latitud y longitud son números; latitud entre -90 y 90 y longitud entre -180 y 180.

## 5. Códigos de error

| Código | Cuándo se produce |
|---|---|
| COMANDO_DESCONOCIDO | el comando no está en la tabla |
| FORMATO | faltan o sobran argumentos, las coordenadas no son válidas o el tipo es incorrecto |
| VEHICULO_NO_EXISTE | se consulta o utiliza un vehículo que no está registrado |
| PEDIDO_NO_EXISTE | se intenta tomar un pedido que no existe |
| YA_ASIGNADO | se intenta tomar un pedido que ya fue asignado (el detalle indica el vehículo asignado) |
| SIN_VEHICULOS | se solicita CERCANO cuando no hay vehículos registrados |

## 6. Comportamiento ante situaciones anómalas

| Situación | Qué hace el servidor |
|---|---|
| Línea vacía | responde `ERROR COMANDO_DESCONOCIDO` |
| Cliente inactivo 60 s | cierra la conexión sin mensaje |
| Cliente se desconecta a mitad de una operación | registra la desconexión y sigue atendiendo a los demás |
| Dos clientes modifican el mismo dato a la vez | las operaciones se serializan con un Lock; el resultado es el mismo que si hubieran llegado una tras otra |
| Bytes no decodificables en UTF-8 | los sustituye por el carácter de reemplazo durante la lectura (`errors="replace"`) |

## 7. Estado compartido

| Dato | Tipo | Valor inicial | Quién lo modifica |
|---|---|---|---|
| vehiculos | dict vehículo → (latitud, longitud) | moto1: (-41.47, -72.94), moto2: (-41.46, -72.95) | POSICION |
| pedidos | dict pedido → {destino, asignado} | p1: destino (-41.45, -72.93), asignado `None` | PEDIDO, TOMAR |
| siguiente_id | int | 2 | PEDIDO |
| operaciones | int | 0 | cada comando registrado en `OPERACIONES` (incluye ESPERA) |

## 8. Historial de cambios

| Versión | Fecha | Cambio |
|---|---|---|
| 1.0 | semana 4 | protocolo inicial, servidor secuencial |
| 2.0 | semana 6 | servidor concurrente, operaciones de geolocalización, estado compartido, errores y timeout documentados |
