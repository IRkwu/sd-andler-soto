# Bitácora individual — Semana 10

**Nombre:** Elías Soto  
**Equipo:** andler-soto  
**Archivo:** `semana10/bitacora_<apellido>.md` en el repositorio del equipo. **Entrega:** jueves 5 de noviembre de 2026, 18.00.

Esta bitácora es individual. Cada integrante escribe la suya con sus propias horas y sus propias palabras. No lleva nota, pero es un formativo obligatorio del programa y se revisa.

## Registro de sesiones

Una fila por sesión de trabajo. Las horas deben sumar al menos 8 entre los cuatro bloques.

| Fecha | Horas | Bloque | Qué estudié o hice | Qué me costó |
|---|---|---|---|---|
| 04/11/2026 | 2 | 1 Lecturas | Revisé la invocación remota, las referencias a objetos y las posibles consecuencias de un fallo de comunicación. | Entender por qué un timeout no permite saber si la operación se ejecutó. |
| 04/11/2026 | 2 | 2 RMI, CORBA, DCOM | Contrasté las características de RMI, CORBA y DCOM y revisé fuentes para el cuadro comparativo. | Separar las limitaciones de cada tecnología de sus aplicaciones todavía vigentes. |
| 04/11/2026 | 2 | 3 JSON-RPC 2.0 | Estudié los campos de las solicitudes y respuestas, los códigos de error y los parámetros por nombre y posición. | Distinguir una solicitud inválida de un JSON que ni siquiera puede interpretarse. |
| 04/11/2026 | 2 | 4 Prototipo | Revisé las operaciones de posiciones y ejecuté pruebas del endpoint, incluyendo parámetros como lista y objeto, notificaciones y batch. | Comprobar el HTTP 204 sin confundir la ausencia de cuerpo con una falla del servidor. |

## Tres preguntas de cierre (responder con sus palabras, 3 a 5 líneas cada una)

1. ¿Qué tienen en común JSON-RPC 2.0 y el protocolo v3 que escribieron en la semana 9? ¿Qué decisión tomó la especificación por ustedes?  
En ambos protocolos el cliente indica qué operación desea ejecutar y entrega los argumentos necesarios. También existe un identificador que permite reconocer a qué solicitud pertenece la respuesta. JSON-RPC proporciona una estructura común para representar llamadas, resultados y errores, incluyendo reglas para notificaciones y solicitudes por lotes. Estas decisiones ya están documentadas y deben respetarse.

2. ¿Por qué RMI, CORBA y DCOM casi no se usan en sistemas nuevos y qué los reemplazó?  
Estas tecnologías resolvieron la comunicación entre objetos desde entornos diferentes, pero sus dependencias y mecanismos de despliegue pueden complicar una integración entre plataformas. Las alternativas incluyen servicios HTTP con JSON y llamadas mediante gRPC. La elección depende del sistema: mantener una aplicación existente puede exigir compatibilidad, mientras que un desarrollo nuevo permite evaluar otras opciones.

3. ¿Qué parte del prototipo les costó más y cómo la resolvieron?  
La mayor dificultad fue comprobar las notificaciones, porque una respuesta sin contenido podía confundirse con una falla. Lo resolví revisando tanto el cuerpo como el estado HTTP mediante `curl`. También comprobé el procesamiento por lotes, verificando que las solicitudes normales generaran respuestas y que las notificaciones no agregaran elementos a la lista devuelta.

## Autoevaluación

| Afirmación | Sí | Parcial | No |
|---|---|---|---|
| Leí las secciones asignadas y puedo explicar la diferencia entre RPC y objetos distribuidos | | X | |
| Aporté al cuadro comparativo con fuentes propias | X | | |
| Puedo explicar el código del endpoint `/rpc` línea por línea | | X | |
| Probé los seis casos de error del prototipo con `curl` | X | | |
