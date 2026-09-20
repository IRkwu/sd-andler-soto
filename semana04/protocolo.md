# Protocolo de aplicación — Equipo andler-soto

Versión 0.1 · semana 4 · Este archivo evoluciona cada semana junto con el servicio.

## 1. Transporte

- Protocolo de transporte: TCP
- Puerto del servidor: 5000
- Codificación: UTF-8
- Delimitador de mensaje: una línea terminada en `\n`
- Quién inicia: el cliente. El servidor solo responde.

## 2. Mensajes

Completen la tabla. Una fila por comando. La operación propia del equipo va al final.

| Comando (cliente → servidor) | Argumentos | Respuesta (servidor → cliente) | ¿Cambia el estado de la conexión? |
|---|---|---|---|
| `HOLA <nombre>` | nombre, texto libre | `OK hola <nombre>` | Sí, guarda el nombre |
| `ECO <texto>` | texto libre | `ECO <texto>` | No |
| `CONTAR` | - | `OK <n>` | Sí, aumenta el contador |
| `SALIR` | - | `ADIOS` | Sí, termina la conexión |
| (cualquier otro) | | `ERROR comando desconocido` | No |
| `SUMA <a> <b>` | dos enteros | `OK <resultado>` | No |
| `HORA` | ninguno | `OK HH:MM:SS` | No |

## 3. Estado

- ¿Qué recuerda el servidor de cada conexión?  
**R:** El servidor recuerda el **nombre del cliente** y la **cantidad de mensajes recibidos** durante esa conexión.

- ¿Qué pasa con ese estado cuando el cliente se desconecta?  
**R:** El estado se pierde, porque existe solamente mientras dura esa conexión.

- Si el servidor se reinicia mientras un cliente está conectado, ¿qué pierde el cliente?
**R:** Pierde el nombre y el contador asociados a la sesión. Al volver a conectarse, comienza una nueva sesión con el estado reiniciado.

## 4. Secuencia típica

Dibujen o describan una sesión completa, desde `connect` hasta `ADIOS`.

```text
cliente                 servidor
   |---- connect ---------->|
   |---- HOLA equipo ------>|
   |<--- OK hola equipo ----|
   |---- SUMA 2 3 --------->|
   |<--- OK 5 --------------|
   |---- CONTAR ----------->|
   |<--- OK 3 --------------|
   |---- SALIR ------------>|
   |<--- ADIOS -------------|
   |---- close ------------>|
```

## 5. Errores

| Situación | Qué ve el cliente | Qué ve el servidor |
|---|---|---|
| Comando desconocido | `ERROR comando desconocido` | Registra el comando recibido y responde `ERROR comando desconocido` |
| Servidor caído durante la sesión | `CONEXIÓN PERDIDA: ConnectionError: el servidor cerró la conexión sin responder` | El proceso queda detenido (`Exited 137`) y deja de recibir mensajes |
| Cliente sin red durante la sesión | `TIMEOUT: el servidor no respondió en 5 s. ¿Caído, sin red o lento? No se puede saber.` | Durante el corte no recibe el mensaje; al reconectar la red, el `ECO` pendiente puede llegar después |
| Cliente corta sin `SALIR` (Ctrl+C) | `corte abrupto desde el cliente (sin SALIR)` | Registra el cierre de la conexión sin haber recibido `SALIR` |
