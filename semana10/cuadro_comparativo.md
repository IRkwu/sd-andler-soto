# Cuadro comparativo — RMI, CORBA, DCOM y JSON-RPC

**Equipo:** andler-soto  
**Integrantes:** Álvaro Andler y Elías Soto  
**Semana 10, trabajo autónomo**

Completen cada celda con una o dos frases propias (no copiar y pegar). Donde una tecnología no aplique, escriban "no aplica" y por qué.

| Criterio | Java RMI | CORBA | DCOM | JSON-RPC 2.0 |
|---|---|---|---|---|
| Año y origen (quién lo creó y para qué) | Sun Microsystems, 1997. Creado para comunicar objetos Java remotamente. | OMG, 1991. Creado para conectar objetos de distintos lenguajes. | Microsoft, 1996. Extendió COM para comunicación en red. | JSON-RPC Working Group, 2010. Estandarizó llamadas remotas mediante JSON. |
| Modelo (objetos remotos o procedimientos remotos) | Métodos sobre objetos Java remotos. | Objetos distribuidos con referencias remotas. | Componentes COM accesibles remotamente. | Procedimientos identificados por nombre. |
| Contrato o IDL (cómo se declara la interfaz) | Interfaces Java que extienden `Remote`. | Interfaces definidas mediante OMG IDL. | Interfaces IDL compiladas con MIDL. | No exige IDL; cada aplicación define sus métodos. |
| Transporte y formato de los mensajes | JRMP sobre TCP y serialización Java. | GIOP/IIOP y formato binario CDR. | ORPC y formato binario NDR. | JSON sobre HTTP, sockets u otros transportes. |
| Lenguajes y plataformas que soporta | Java y sistemas con JVM. | Varios lenguajes y plataformas mediante ORB. | Principalmente Windows y lenguajes compatibles con COM. | Cualquier lenguaje y plataforma compatibles con JSON. |
| Referencias remotas y estado (¿el servidor recuerda al cliente?) | Utiliza stubs y permite objetos con estado. | Referencias remotas a objetos que pueden mantener estado. | Referencias a componentes y objetos con estado. | No define referencias remotas ni requiere sesiones. |
| Manejo de errores (cómo viaja un fallo al cliente) | Excepciones como `RemoteException`. | Excepciones del sistema y del usuario. | Códigos `HRESULT` y errores RPC. | Objeto `error` con código y mensaje. |
| Relación con las cinco decisiones de la semana 9 (enmarcado, versión, id, errores, tipos) | JRMP gestiona mensajes y versión; el sistema relaciona llamadas y respuestas. Java define tipos y excepciones. | GIOP gestiona mensajes, versión e ID; IDL/CDR define tipos y las excepciones comunican errores. | RPC/ORPC gestiona mensajes, versiones y correlación; IDL/NDR define tipos y los errores usan códigos. | Define versión, ID, errores y tipos JSON; el transporte gestiona el enmarcado. |
| Estado actual (vigente, legado, reemplazado por qué) | Sigue vigente en Java, especialmente en JMX. | Uso especializado y en sistemas heredados. | Sigue presente en servicios de Windows. | Vigente en distintas APIs y servicios. |
| Caso de uso típico, real o histórico | Administración remota mediante JMX. | Sistemas de telecomunicaciones. | Administración remota con WMI. | API JSON-RPC de Ethereum. |

## Conclusión del equipo (5 a 8 líneas)

¿Cuál de las cuatro se parece más a lo que construyeron en la semana 9 y por qué? ¿Cuál elegirían hoy para un servicio interno y cuál para una API pública?

JSON-RPC 2.0 es la tecnología más parecida al protocolo que construimos en semana 09, porque organiza llamadas mediante operaciones, argumentos, versiones e identificadores.
La diferencia principal es que JSON-RPC proporciona reglas comunes para las solicitudes, las respuestas y los errores, mientras que nosotros definimos nuestro propio contrato.
RMI, CORBA y DCOM están orientados a objetos o componentes remotos y requieren mecanismos adicionales para representar interfaces y referencias.
Entre las cuatro alternativas, elegiríamos JSON-RPC para nuestro servicio interno por su sencillez y compatibilidad con Python y FastAPI.
Para una API pública también consideraríamos JSON-RPC sobre HTTPS, documentando los métodos y parámetros y definiendo controles de acceso.
La elección final dependería de los clientes, la compatibilidad requerida y las necesidades de mantenimiento, seguridad y rendimiento.

## Fuentes consultadas

1. Oracle. (s. f.). *Java Remote Method Invocation Specification*. https://docs.oracle.com/en/java/javase/11/docs/specs/rmi/index.html

2. Object Management Group. (2021). *CORBA, versión 3.4*. https://www.omg.org/spec/CORBA/3.4/About-CORBA

3. Microsoft. (2024). *Distributed Component Object Model Remote Protocol*. https://learn.microsoft.com/openspecs/windows_protocols/ms-dcom

4. JSON-RPC Working Group. (2013). *JSON-RPC 2.0 Specification*. https://www.jsonrpc.org/specification
