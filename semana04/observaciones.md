# Observaciones — fallas provocadas · semana 4 · Equipo Álvaro Andler - Álvaro Soto
Anoten lo que vieron, no lo que esperaban ver. Un tiempo sin unidad no sirve.

## Falla 1 — servidor muerto con el cliente conectado

Comando usado: `docker compose kill servidor`

| Pregunta | Respuesta |
|---|---|
| ¿Qué mensaje mostró el cliente? | `CONEXIÓN PERDIDA: ConnectionError: el servidor cerró la conexión sin responder` |
| ¿Cuánto tardó en aparecer desde que enviaron el comando? (ms o s) | Aproximadamente `0.17 ms` desde que se envió el comando hasta detectar el cierre de la conexión |
| ¿El cliente supo que el servidor estaba muerto o solo que la conexión se cerró? | Solo supo que la conexión se cerró |
| Al levantar el servidor de nuevo, ¿se recuperó la sesión anterior (nombre, contador)? | No. La sesión anterior se perdió y el contador volvió a comenzar desde `OK 1` |

## Falla 2 — cliente sin red con el servidor vivo

Comando usado: `docker network disconnect sd_net cliente`

| Pregunta | Respuesta |
|---|---|
| ¿Qué mensaje mostró el cliente? | `TIMEOUT: el servidor no respondió en 5 s. ¿Caído, sin red o lento? No se puede saber.` |
| ¿Cuánto tardó en aparecer? | Aproximadamente `5 s` |
| ¿Qué mostró el log del servidor en ese momento? | Durante el corte no mostró ningún mensaje nuevo. Solo estaba registrado `HOLA equipo`. Al reconectar la red, recibió posteriormente `ECO prueba-red`. |
| Desde el punto de vista del cliente, ¿en qué se diferencia esta falla de la falla 1? | En la falla 1 detectó inmediatamente que la conexión se cerró; en esta falla esperó 5 s hasta alcanzar el timeout, sin poder saber si el servidor estaba caído, ocupado o si había un problema de red. |

## Segundo cliente mientras el primero está conectado (paso 3)

| Pregunta | Respuesta |
|---|---|
| ¿El segundo cliente logró conectarse (`connect`)? | Sí. La conexión TCP se estableció correctamente. |
| ¿Recibió respuesta a su primer comando? ¿Qué mostró? | No. El servidor estaba ocupado con el primer cliente y el segundo terminó en `TIMEOUT` después de 5 s. |
| ¿Qué mostró el log del servidor cuando el primer cliente hizo `SALIR`? | Cerró la conexión del primer cliente y recién después procesó la conexión del segundo. El servidor recibió `HOLA equipo`, pero el segundo cliente ya había terminado por timeout. |

## Conclusión del equipo (3 a 5 líneas)

Un programador asumiría la falacia 1: “la red es confiable”.
Aunque nuestro cliente tiene un timeout de 5 segundos, este solo limita cuánto espera.
Si no llega una respuesta, el cliente no puede saber con certeza si el servidor está ocupado
o si la red está cortada; en ambos casos observamos un `TIMEOUT`.
