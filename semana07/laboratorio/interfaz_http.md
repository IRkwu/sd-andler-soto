# Interfaz HTTP del servicio (anexo de protocolo.md)

> Plantilla de la Semana 7. Este documento se agrega a `protocolo.md` v2 como sección 9.
> Regla de oro, la misma de la semana 6. Otro equipo debe poder usar la API leyendo SOLO este documento.

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
