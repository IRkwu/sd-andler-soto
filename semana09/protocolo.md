# Protocolo del servicio — versión 3 (Semana 9)

> Reemplaza a protocolo.md v2 de semana06/. Lo que cambia es la **sección 2**
> (ya no es una línea de texto, es un mensaje estructurado) y se agregan las
> secciones 7 y 8. El resto se copia de la v2 y se actualiza donde corresponda.

## 1. Identificación

| Campo | Valor |
|---|---|
| Equipo | andler-soto |
| Dominio | Geolocalización y Despacho |
| Versión del protocolo | 2 (campo `version` del mensaje) |
| Versión del documento | 3 |
| Transporte | TCP, puerto 5000 dentro de `sd_net` |

## 2. Formato del mensaje

Cada mensaje viaja **enmarcado**: 4 bytes con el largo (entero sin signo, big-endian) seguidos del cuerpo.

```
+------------+------------------------+
| largo (4B) | cuerpo (largo bytes)   |
+------------+------------------------+
```

El cuerpo se codifica con uno de dos **codecs**, elegido por la variable `CODEC`. Cliente y servidor deben usar el mismo.

### 2.1 Solicitud (cliente → servidor)

| Campo | Tipo | Descripción |
|---|---|---|
| `version` | entero | Versión del protocolo. El servidor rechaza las distintas de 2 |
| `id` | entero | Correlativo del cliente. La respuesta trae el mismo id |
| `operacion` | texto | Nombre de la operación en mayúsculas |
| `argumentos` | lista de textos | Argumentos de la operación, puede ser vacía |

### 2.2 Respuesta (servidor → cliente)

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | entero | Mismo id de la solicitud (0 si no se pudo leer la solicitud) |
| `estado` | `OK` o `ERROR` | Resultado |
| `datos` | lista de textos | Resultado cuando estado es OK |
| `error` | texto | Mensaje legible cuando estado es ERROR |

### 2.3 Codec `json`

Cuerpo en JSON UTF-8 con los campos anteriores como claves.

```json
{"operacion": "POSICION", "argumentos": ["moto1", "-41.48", "-72.96"], "id": 7, "version": 2}
```

### 2.4 Codec `bin`

Cuerpo binario con `struct`, big-endian. Los textos van con largo prefijado de 2 bytes y las listas con cantidad prefijada de 1 byte.

```
Solicitud: version(1B) id(4B) operacion(2B+texto) n_args(1B) [arg(2B+texto)]*
Respuesta: id(4B) estado(1B: 0=OK 1=ERROR) n_datos(1B) [dato(2B+texto)]* error(2B+texto)
```

## 3. Operaciones

Las solicitudes contienen una operación y una lista de argumentos de texto.
Las respuestas correctas tienen `estado="OK"` y sus resultados en `datos`.
Las respuestas fallidas tienen `estado="ERROR"` y el código y detalle en `error`.
La respuesta conserva el mismo `id` de la solicitud.

| Operación | Argumentos | Respuesta OK (`datos`) | Errores posibles | Ejemplo de solicitud estructurada |
|---|---|---|---|---|
| `HOLA` | nombre opcional | `["HOLA", "equipo"]`; sin nombre usa `"anonimo"` | — | `Solicitud("HOLA", ["equipo"], id=1)` |
| `POSICION` | vehiculo, lat, lon | `["moto1", "-41.47", "-72.94"]` | `FORMATO` | `Solicitud("POSICION", ["moto1", "-41.47", "-72.94"], id=2)` |
| `DONDE` | vehiculo | `["moto1", "-41.47", "-72.94"]` | `FORMATO`, `VEHICULO_NO_EXISTE` | `Solicitud("DONDE", ["moto1"], id=3)` |
| `PEDIDO` | lat, lon | `["p2", "pendiente"]` | `FORMATO` | `Solicitud("PEDIDO", ["-41.45", "-72.93"], id=4)` |
| `TOMAR` | vehiculo, pedido | `["moto1", "p1"]` | `FORMATO`, `VEHICULO_NO_EXISTE`, `PEDIDO_NO_EXISTE`, `YA_ASIGNADO` | `Solicitud("TOMAR", ["moto1", "p1"], id=5)` |
| `CERCANO` | lat, lon | `["moto1", "distancia=0.0000"]` | `FORMATO`, `SIN_VEHICULOS` | `Solicitud("CERCANO", ["-41.47", "-72.94"], id=6)` |
| `ESPERA` | segundos | `["ESPERA", "2"]` | `FORMATO` | `Solicitud("ESPERA", ["2"], id=7)` |
| `SALIR` | — | `["CHAO"]`; cierra la conexión | — | `Solicitud("SALIR", [], id=8)` |

### Descripción y validaciones

- `HOLA` es opcional: se puede operar sin identificarse.
- `POSICION` registra o actualiza las coordenadas de un vehículo.
- `DONDE` consulta la posición registrada de un vehículo.
- `PEDIDO` crea un pedido pendiente con un identificador incremental.
- `TOMAR` asigna un pedido a un vehículo, siempre que todavía no esté asignado.
- `CERCANO` busca el vehículo más cercano mediante distancia euclidiana
  entre coordenadas; no representa kilómetros de recorrido.
- `ESPERA` simula una operación lenta sin mantener el `Lock` durante la espera.
- La latitud debe estar entre -90 y 90 y la longitud entre -180 y 180.
- Los identificadores de vehículos y pedidos se convierten a minúsculas.
- Una operación desconocida devuelve el error `COMANDO_DESCONOCIDO`.

Los resultados de los ejemplos dependen del estado del servidor.
Los ejemplos de posición y cercanía corresponden a los datos iniciales.

## 4. Errores de protocolo

| Situación | Reacción del servidor |
|---|---|
| `version` distinta de 2 | Responde `ERROR` con el texto `versión X no soportada, use 2` y mantiene la conexión |
| Cuerpo que no se puede decodificar | Responde `ERROR mensaje mal formado (...)` con id 0 y **cierra esa conexión** |
| Largo anunciado mayor a 1 MB | Responde `ERROR` y cierra esa conexión |
| Largo anunciado mayor a lo enviado | Espera hasta `TIMEOUT_SERVIDOR` (30 s) y cierra esa conexión |
| Operación desconocida | Responde `ERROR COMANDO_DESCONOCIDO` |

## 5. Concurrencia

El servidor atiende cada conexión mediante un hilo independiente. El estado compartido contiene los vehículos, los pedidos, el siguiente identificador de pedido y el contador de operaciones.

Un Lock protege las consultas y modificaciones del estado compartido. En TOMAR, comprobar si el pedido está asignado y registrar su asignación ocurre dentro de la misma sección crítica, evitando asignaciones simultáneas del mismo pedido.

ESPERA realiza la espera sin mantener el Lock.

## 6. Ejemplo de sesión

```text
> HOLA equipo                    ->  OK HOLA | equipo
> POSICION moto1 -41.48 -72.96   ->  OK moto1 | -41.48 | -72.96
> DONDE moto1                    ->  OK moto1 | -41.48 | -72.96
> CERCANO -41.48 -72.96          ->  OK moto1 | distancia=0.0000
> PEDIDO -41.45 -72.93           ->  OK p2 | pendiente
> TOMAR moto1 p2                 ->  OK moto1 | p2
> TOMAR moto2 p2                 ->  ERROR YA_ASIGNADO moto1
> SALIR                          ->  OK CHAO
```

## 7. Medición de codecs

Medición de 10.000 solicitudes y 10.000 respuestas de geolocalización y despacho mediante `python bench_codec.py 10000`.

| Mensaje   | Codec | Bytes promedio | Bytes totales | Codificar (ms) | Decodificar (ms) |
|-----------|-------|---------------:|--------------:|---------------:|-----------------:|
| Solicitud | json  |           87.5 |        874885 |           53.5 |             24.9 |
| Solicitud | bin   |           32.6 |        325983 |           12.4 |             15.5 |
| Respuesta | json  |           79.2 |        792378 |           50.2 |             24.2 |
| Respuesta | bin   |           30.6 |        305512 |           14.0 |             16.5 |

El formato binario ocupó aproximadamente un 63 % menos bytes en las solicitudes y un 61 % menos en las respuestas que JSON.
En esta ejecución también codificó y decodificó más rápido, a cambio, pierde legibilidad y exige respetar el orden y los tipos definidos en el formato.

## 8. Historial de cambios

| Versión doc | Fecha | Cambio |
| --- | --- |--- |
| 1 | sem. 4 | Protocolo de texto por líneas y servidor secuencial |
| 2 | sem. 6 | Servidor concurrente, operaciones de geolocalización y despacho, estado compartido, errores y timeout documentados |
| 3 | sem. 9 | Solicitudes y respuestas estructuradas para el dominio; campos version e id; enmarcado por largo y definición de codecs JSON y binario |
