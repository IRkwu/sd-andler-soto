# Mediciones — Laboratorio N°1 (Semana 2)

**Equipo:** andler-soto  
**Integrantes:** Álvaro Andler / Elías Soto  
**Fecha:** 28-08-2026  
**Entorno:** Docker Desktop (Windows)

## Paso 1 — Línea base
| Métrica | Valor |
|---|---|
| RTT ping (promedio) | 0.068 ms |
| Throughput iperf3 | 22.2 Gbit/s |

## Pasos 2 y 3 — Latencia inyectada (100 llamadas)
| Latencia `tc` | Total (s) | Promedio (ms) | Máx (ms) | ¿Esperado? (sí/no, por qué) |
|---|---|---|---|---|
| 0 ms (base) 0.011s | 0.1ms | 0.1ms | 0.3ms | Sí, sin latencia el RTT debería ser muy bajo |
| 50 ms 5.034s |50.3ms |50.3ms |50.7 |Sí, porque la latencia medida debería aproximarse a los 50 ms inyectados. |
| 200 ms 20.035ms |200.3ms |200.2ms |200.6ms |Sí, porque la latencia medida debería aproximarse a los 200 ms inyectados. |
| 500 ms 50.035ms |500.3ms |500.3ms |500.6ms |Sí, porque la latencia medida debería aproximarse a los 500 ms inyectados. |

## Paso 4 — Pérdida de paquetes
| Pérdida `tc` | Throughput iperf3 | Total cliente (s) | Observación |
|---|---|---|---|
| 1% | 7.13Gbit/s |0.216s | La comunicación funciona, pero la pérdida provoca retransmisiones y mayor variabilidad.|
| 5% | 223Mbits/sec| 1.468s| El throughput cayó fuertemente; el cliente siguió funcionando, pero con mayor tiempo total.|
| 20% | 604Kbits/sec| 5.016s | La conexión quedó casi inutilizable hubo muchas retransmisiones, todo esto debido a la alta perdida.|
| 100% (falla provocada) | — | — | El cliente no pudo establecer la comunicación y terminó con el error Errno 113: No route to host. Con TIMEOUT_S=3, el cliente debería abandonar la espera después de aproximadamente 3 s si el fallo se manifiesta como timeout.| 

## Falacia que asumimos sin advertirlo

El cliente asume que la red es confiable porque, por defecto, no tiene un timeout definido y espera que el servidor siempre responda. La prueba con pérdida del 100% muestra que el cliente puede quedar esperando o fallar después de varios segundos; al definir TIMEOUT_S=3, la aplicación detecta la falta de respuesta y aborta de forma controlada.
