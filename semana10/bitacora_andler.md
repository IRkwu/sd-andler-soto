# Bitácora individual — Semana 10

**Nombre:** Álvaro Andler  
**Equipo:** andler-soto  
**Archivo:** `semana10/bitacora_<apellido>.md` en el repositorio del equipo. **Entrega:** jueves 5 de noviembre de 2026, 18.00.

Esta bitácora es individual. Cada integrante escribe la suya con sus propias horas y sus propias palabras. No lleva nota, pero es un formativo obligatorio del programa y se revisa.

## Registro de sesiones

Una fila por sesión de trabajo. Las horas deben sumar al menos 8 entre los cuatro bloques.

| Fecha | Horas | Bloque | Qué estudié o hice | Qué me costó |
|---|---|---|---|---|
| 03/11/2026 | 2 | 1 Lecturas | Estudié RPC, stubs, paso de parámetros e IDL. Relacioné estos conceptos con el protocolo de semana 09. | Diferenciar la correlación de respuestas de la detección de solicitudes duplicadas. |
| 03/11/2026 | 2 | 2 RMI, CORBA, DCOM | Investigué las tres tecnologías y comparé sus contratos, plataformas, transportes y manejo de errores. | Distinguir la función del IDL de la función del ORB en CORBA. |
| 03/11/2026 | 2 | 3 JSON-RPC 2.0 | Revisé la especificación, preparé ejemplos del dominio y completé la comparación con nuestro protocolo. | Comprender que una notificación no recibe respuesta, incluso cuando ocurre un error. |
| 03/11/2026 | 2 | 4 Prototipo | Adapté el registro y la consulta de posiciones al prototipo. Probé llamadas válidas, errores, notificaciones y batch. | Diferenciar los parámetros incorrectos de los errores propios del dominio. |


## Tres preguntas de cierre (responder con sus palabras, 3 a 5 líneas cada una)

1. ¿Qué tienen en común JSON-RPC 2.0 y el protocolo v3 que escribieron en la semana 9? ¿Qué decisión tomó la especificación por ustedes?  
Ambos permiten enviar una operación con argumentos, identificar la versión y relacionar cada respuesta con su solicitud mediante un identificador. En semana 09 definimos nuestros propios campos y JSON-RPC establece `method`, `params`, `id`, `result` y `error`, además de sus reglas y códigos de error. Al utilizarlo sobre HTTP, ese transporte proporciona el enmarcado.

2. ¿Por qué RMI, CORBA y DCOM casi no se usan en sistemas nuevos y qué los reemplazó?  
Su elección puede implicar dependencias y configuración específicas: RMI está vinculado con Java, CORBA utiliza infraestructura como ORB e IDL y DCOM pertenece al entorno COM de Microsoft. Para una integración nueva entre plataformas evaluaría HTTP/JSON o gRPC. Estas alternativas facilitan otros modelos de comunicación, aunque las tecnologías anteriores siguen presentes y no fueron reemplazadas universalmente.

3. ¿Qué parte del prototipo les costó más y cómo la resolvieron?  
Lo que más me costó fue distinguir los parámetros incorrectos de los errores propios del dominio. Una solicitud incompleta debía producir `-32602`, mientras que consultar un vehículo inexistente correspondía a un error del dominio. Lo resolví revisando las validaciones y comparando solicitudes válidas, incompletas y dirigidas a vehículos no registrados.

## Autoevaluación

| Afirmación | Sí | Parcial | No |
|---|---|---|---|
| Leí las secciones asignadas y puedo explicar la diferencia entre RPC y objetos distribuidos | X | | |
| Aporté al cuadro comparativo con fuentes propias | X | | |
| Puedo explicar el código del endpoint `/rpc` línea por línea | | X | |
| Probé los seis casos de error del prototipo con `curl` | X | | |
