# Observaciones Semana 13

**Equipo:** andler-soto  
**Integrantes:** Álvaro Andler y Elías Soto  
**Fecha:** 26-11-2026

## Entorno

- **CPU asignadas a Docker en el notebook donde se midió:** 16
- **Sistema operativo:** Windows 11

## Paso 2. Persistencia

- **Mensajes publicados con el procesador apagado:** 20
- **Mensajes que llegaron después de reiniciar el broker:** 20

**¿Por qué no se perdieron? Nombren las dos condiciones que tuvieron que cumplirse.**  
Los mensajes no se perdieron porque la cola fue declarada como durable (`durable=True`) y los mensajes fueron publicados como persistentes (`delivery_mode=2`). Al reiniciar el broker, se conservaron los 20 mensajes y fueron procesados correctamente al levantar nuevamente el procesador

## Paso 3. Reentrega

**Réplica que mataron:** `semana13-procesador-2`

**id del mensaje que tenía a medio procesar:** 7

**¿En qué réplica reapareció y con qué marca?**  
Reapareció en la réplica `semana13-procesador-3` con la marca `(REENTREGADO)`.

**Con AUTO_ACK=1, de 12 mensajes ¿cuántos terminaron?**  
Terminaron 8 de los 12 mensajes

**¿Dónde quedaron los otros?**  
Los otros 4 se perdieron al matar la réplica `semana13-procesador-1`, ya que RabbitMQ los consideraba confirmados desde su entrega, aunque todavía no habían terminado de procesarse

**¿Qué semántica de la semana 11 (maybe, at-least-once, at-most-once) vieron en cada caso?**  
AUTO_ACK=0: at-least-once, ya que el mensaje que no fue confirmado se entregó nuevamente a otra réplica  
AUTO_ACK=1: at-most-once, ya que los mensajes se confirmaron automáticamente y no fueron reentregados al caer la réplica

## Paso 4 y 5. Speedup

Peguen la tabla que imprime `graficar.py`.

```text
  p  corridas    T(p) s    S(p)    E(p)  Karp-Flatt
  1         2     18.94    1.00    1.00           -
  2         2     10.12    1.87    0.94       0.069
  3         2      7.02    2.70    0.90       0.056
  4         2      5.64    3.36    0.84       0.064
```

**¿Con cuántos workers deja de mejorar el tiempo?**  
En las pruebas realizadas el tiempo sigue mejorando hasta los 4 workers, aunque cada vez la mejora es menor

**¿Coincide con la cantidad de CPU de Docker?**  
No. Docker tiene asignadas 16 CPU y solamente se realizaron pruebas con un máximo de 4 workers, por lo que no se llegó a determinar el punto en que deja de mejorar el tiempo