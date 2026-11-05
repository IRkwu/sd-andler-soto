# Observaciones — Semana 9, serialización explícita

**Equipo:** andler-soto  
**Integrantes:** Álvaro Andler y Elías Soto  
**Fecha:** 23-10-2026

## Paso 2 — Ida y vuelta de los codecs

Salida de `python codec.py`:

```text
json  solicitud  93 bytes  b'{"operacion": "POSICION", "argumentos": ["moto1", "-41.48", "-72.96"], "id": 7, "version": 2}'
json  respuesta  78 bytes  b'{"id": 7, "estado": "OK", "datos": ["moto1", "-41.48", "-72.96"], "error": ""}'
bin   solicitud  39 bytes  b'\x02\x00\x00\x00\x07\x00\x08POSICION\x03\x00\x05moto1\x00\x06-41.48\x00\x06-72.96'
bin   respuesta  31 bytes  b'\x00\x00\x00\x07\x00\x03\x00\x05moto1\x00\x06-41.48\x00\x06-72.96\x00\x00'
ida y vuelta OK en los dos codecs
```

Tamaño de la misma solicitud en JSON **93 bytes** y en bin **39 bytes**.

## Paso 3 — Medición

Salida de `python bench_codec.py 10000`:

```
| Mensaje   | Codec | Bytes promedio | Bytes totales | Codificar (ms) | Decodificar (ms) |
|-----------|-------|---------------:|--------------:|---------------:|-----------------:|
| Solicitud | json  |           87.5 |        874885 |           53.5 |             24.9 |
| Solicitud | bin   |           32.6 |        325983 |           12.4 |             15.5 |
| Respuesta | json  |           79.2 |        792378 |           50.2 |             24.2 |
| Respuesta | bin   |           30.6 |        305512 |           14.0 |             16.5 |
```

**Conclusión en dos líneas (cuánto ahorra el binario, cuál es más rápido, qué sacrificamos a cambio):**  
El formato binario ocupó aproximadamente un 63 % menos bytes en las solicitudes y un 61 % menos en las respuestas que JSON.
En esta ejecución también codificó y decodificó más rápido, a cambio, pierde legibilidad y exige respetar el orden y los tipos definidos en el formato.

## Paso 4 — Integración

| Prueba | codec=json | codec=bin |
|---|---|---|
| `HOLA equipo` | OK HOLA equipo | OK HOLA equipo |
| `POSICION moto1 -41.48 -72.96` | OK moto1 -41.48 -72.96 | OK moto1 -41.48 -72.96 |
| `DONDE moto1` | OK moto1 -41.48 -72.96 | OK moto1 -41.48 -72.96 |
| `CERCANO -41.48 -72.96` | OK moto1 distancia=0.0000 | OK moto1 distancia=0.0000 |
| `PEDIDO -41.45 -72.93` | OK p2 pendiente | OK p2 pendiente |
| `TOMAR moto1 p2` | OK moto1 p2 | OK moto1 p2 |
| `TOMAR moto2 p2` — error del dominio | ERROR YA_ASIGNADO moto1 | ERROR YA_ASIGNADO moto1 |

## Paso 5 — Falla provocada

| Modo de `cliente_malo.py` | Qué vio el cliente | Qué dice el log del servidor | ¿El servidor siguió atendiendo? |
|---|---|---|---|
| `version` | ERROR versión 1 no soportada, use 2 | Registró `versión no soportada 1` | Sí, respondió correctamente a `HOLA equipo` |
| `largo` | Sin respuesta en 5.0 s | Registró la conexión y desconexión, sin procesar una solicitud | Sí, respondió correctamente a `HOLA equipo` |
| `basura` (codec json) | ERROR mensaje mal formado (UnicodeDecodeError), con id 0 | Registró `UnicodeDecodeError` al decodificar UTF-8 y cerró esa conexión | Sí, respondió correctamente a `HOLA equipo` |
| `basura` (codec bin) | ERROR mensaje mal formado (UnicodeDecodeError), con id 0 | Registró `UnicodeDecodeError` al decodificar UTF-8 y cerró esa conexión | Sí, respondió correctamente a `HOLA equipo` |
| `cruzado` | ERROR mensaje mal formado (JSONDecodeError), con id 0 | Registró `JSONDecodeError` y cerró esa conexión | Sí, respondió correctamente a `HOLA equipo` |

**¿Cuál de los dos codecs falló de forma más clara ante la basura y por qué?**  
En esta ejecución ambos fallaron de forma igualmente clara: respondieron «mensaje mal formado (UnicodeDecodeError)» porque encontraron bytes que no podían decodificarse como UTF-8. En ambos casos se cerró la conexión afectada y el servidor siguió atendiendo. No observamos una diferencia de claridad entre los dos codecs en estas pruebas.

## Para la semana autónoma

Una pregunta que nos quedó sobre serialización o protocolos:

_(escribir)_
