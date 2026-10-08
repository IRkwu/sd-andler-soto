# Observaciones — Semana 6

Equipo: andler-soto
Integrantes: Álvaro Andler - Elías Soto
Dominio del servicio: Geolocalización

## Paso 1 — servidor secuencial bajo carga

Comando ejecutado: docker compose exec -e SERVIDOR_HOST=cliente carga python cliente_carga.py --clientes 5 --comando "ESPERA 2"
Tiempo por cliente: Aproximadamente 2, 4, 6 ,8 y 10 segundos.
TOTAL: 10.01 s
¿Qué esperaban? ¿Qué observaron?
Se esperaba un tiempo total cercano a 10 segundos.
Se observó que los clientes eran atendidos en cola, uno a la vez.

## Paso 2 — hilo por cliente bajo carga

Comando ejecutado: docker compose exec carga python cliente_carga.py --clientes 5 --comando "ESPERA 2"
TOTAL: 2.01 s
Diferencia respecto al Paso 1 y explicación:
En el paso 1, el servidor tardó 10.01 segundos, mientras que en el paso 2 tardó 2.01.
Esto ocurre porque el servidor secuencial atiende a los clientes uno por uno, mientras que el concurrente atiende a varios simultaneamente.

## Paso 3 — condición de carrera

Operación que modifica estado compartido usada: TOMAR moto1 p1.
Valor esperado: 1 asignación OK y 19 rechazadas.
Valor observado SIN Lock: 3 asignaciones OK y 17 rechazadas.
Valor observado CON Lock: 1 asignación OK y 19 rechazadas.
¿Dónde exactamente está la sección crítica en su código?
En la función op_tomar(), dentro del bloque with seccion_critica(), donde se comprueba si el pedido está disponible y se actualiza su asignación.

## Paso 4 — despliegue con docker compose

Salida de `docker compose ps`: 
NAME          IMAGE                  COMMAND                SERVICE    CREATED          STATUS          PORTS
sd_carga      laboratorio-carga      "sleep infinity"       carga      36 minutes ago   Up 36 minutes   
sd_cliente    laboratorio-cliente    "sleep infinity"       cliente    36 minutes ago   Up 28 minutes   
sd_servidor   laboratorio-servidor   "python servidor.py"   servidor   5 minutes ago    Up 5 minutes    0.0.0.0:5000->5000/tcp, [::]:5000->5000/tcp
IP del host publicada para la prueba cruzada: 192.168.1.18 (Falta hacerlo en clases creo)

## Paso 5 — prueba cruzada

Equipo cuyo servidor probamos:
¿Su protocolo.md alcanzó para conectarse sin preguntar? (sí / no, qué faltó)
Mensajes enviados y respuestas obtenidas:
Qué falló y por qué:

Equipo que probó nuestro servidor:
Qué reportaron:

## Falla provocada — desconexión abrupta

Comando usado para provocarla:
Qué registró el log del servidor:
¿El servidor siguió atendiendo a los demás? Evidencia:
