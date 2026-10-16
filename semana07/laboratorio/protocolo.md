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

## 9. Interfaz HTTP del servicio

## 9.1 Identificación

| Campo | Valor |
|---|---|
| Equipo | andler-soto |
| Entrada única | `http://localhost:8080` (Nginx) |
| Formato | JSON, UTF-8; `Content-Type: application/json` para enviar cuerpos |
| Documentación interactiva | `http://localhost:8080/docs` |
| Réplicas de la API | api1, api2 |
| Dónde vive el estado | en el servidor TCP, la API no guarda nada |

## 9.2 Tabla de traducción, operación por operación

| Comando del protocolo de texto | Método y ruta HTTP | Cuerpo JSON | Respuesta correcta | Código |
|---|---|---|---|---|
| `POSICION <vehiculo> <lat> <lon>` | `PUT /vehiculos/{vehiculo}/posicion` | `{"lat": -41.48, "lon": -72.96}` | `{"vehiculo": "moto1", "lat": -41.48, "lon": -72.96, "replica": "api1"}` | 200 |
| `DONDE <vehiculo>` | `GET /vehiculos/{vehiculo}/posicion` | (sin cuerpo) | `{"vehiculo": "moto1", "lat": -41.48, "lon": -72.96, "replica": "api2"}` | 200 |
| `PEDIDO <lat> <lon>` | `POST /pedidos` | `{"lat": -41.45, "lon": -72.93}` | `{"pedido": "p2", "estado": "pendiente", "replica": "api1"}` | 201 |
| `TOMAR <vehiculo> <pedido>` | `POST /pedidos/{pedido}/asignacion` | `{"vehiculo": "moto1"}` | `{"vehiculo": "moto1", "pedido": "p2", "replica": "api1"}` | 201 |
| `CERCANO <lat> <lon>` | `GET /vehiculos/cercano?lat=-41.48&lon=-72.96` | (sin cuerpo) | `{"vehiculo": "moto1", "distancia": 0.0, "replica": "api2"}` | 200 |
| (sin comando TCP) | `GET /salud` | (sin cuerpo) | `{"estado": "ok", "replica": "api1"}` | 200 |

`PUT` registra o actualiza la posición. Cada `POST /pedidos` crea un pedido nuevo; el ID y la réplica de los ejemplos pueden variar. `CERCANO` mide distancia euclidiana entre coordenadas, no kilómetros. `/salud` comprueba solo la API, sin consultar al servidor TCP.

## 9.3 Tabla de errores

| Situación | Respuesta del protocolo de texto | Código HTTP | Quién responde |
|---|---|---|---|
| El vehículo no existe | `ERROR VEHICULO_NO_EXISTE` | 404 | la API |
| El pedido no existe | `ERROR PEDIDO_NO_EXISTE` | 404 | la API |
| No hay vehículos registrados | `ERROR SIN_VEHICULOS` | 404 | la API |
| El pedido ya está asignado | `ERROR YA_ASIGNADO <vehiculo>` | 409 | la API |
| El servidor rechaza el formato del comando | `ERROR FORMATO ...` | 400 | la API |
| El servidor no reconoce el comando | `ERROR COMANDO_DESCONOCIDO` | 501 | la API |
| Cuerpo o parámetros mal formados | (no llega al servidor) | 422 | la API, antes de traducir |
| El servidor TCP no está disponible | (sin respuesta) | 503 | la API |
| El servidor TCP no responde a tiempo | (sin respuesta) | 504 | la API |
| No queda ninguna réplica de la API | (sin respuesta) | 502 | Nginx |

## 9.4 Decisiones de diseño (dos o tres líneas cada una)

- **¿Por qué esos sustantivos como recursos?**  
`vehiculos` y `pedidos` representan las entidades del servicio de geolocalización y despacho. La posición pertenece a un vehículo y la asignación vincula un pedido con el vehículo que lo atenderá.

- **¿Qué operación NO expusieron por HTTP y por qué?**  
`ESPERA`, porque solo sirve para probar operaciones lentas. Tampoco `HOLA` ni `SALIR`, porque gestionan la sesión TCP y no hacen falta para las peticiones HTTP independientes.

- **¿Qué valida la API antes de traducir, y qué pasaría si no lo validara?**  
Vehículos de 1 a 30 letras ASCII, números o `_`; pedidos con `p` o `P` seguido de dígitos; latitud finita entre -90 y 90 y longitud finita entre -180 y 180. Los identificadores se convierten a minúsculas. Sin validar, podrían enviarse coordenadas inválidas o argumentos ambiguos al servidor.
