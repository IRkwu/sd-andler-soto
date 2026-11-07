# Semana 10: JSON-RPC

## 1. Operación 1 válida con parámetros objeto

**Caso:** Enviar una solicitud válida a `posicion` con parámetros de tipo objeto.

**Resultado esperado:** La respuesta contiene `result`.

**Comando:**

```powershell
curl.exe -sS -X POST `
  "http://127.0.0.1:8000/rpc" `
  -H "Content-Type: application/json" `
  -d '{"jsonrpc":"2.0","method":"posicion","params":{"vehiculo":"moto1","lat":-41.48,"lon":-72.96},"id":1}'
```

**Respuesta:**

```text
{"jsonrpc":"2.0","result":{"vehiculo":"moto1","lat":-41.48,"lon":-72.96},"id":1}
```

## 2. Operación 2 válida con parámetros lista

**Caso:** Enviar una solicitud válida a `donde` con parámetros de tipo lista.

**Resultado esperado:** La respuesta contiene `result`.

**Comando:**

```powershell
curl.exe -sS -X POST `
  "http://127.0.0.1:8000/rpc" `
  -H "Content-Type: application/json" `
  -d '{"jsonrpc":"2.0","method":"donde","params":["moto1"],"id":2}'
```

**Respuesta:**

```text
{"jsonrpc":"2.0","result":{"vehiculo":"moto1","lat":-41.48,"lon":-72.96},"id":2}
```

## 3. Error de dominio

**Caso:** Enviar una solicitud que produce un error de dominio.

**Resultado esperado:** La respuesta contiene el código `-32000` y `data`.

**Comando:**

```powershell
curl.exe -sS -X POST `
  "http://127.0.0.1:8000/rpc" `
  -H "Content-Type: application/json" `
  -d '{"jsonrpc":"2.0","method":"donde","params":{"vehiculo":"moto_inexistente"},"id":3}'
```

**Respuesta:**

```text
{"jsonrpc":"2.0","error":{"code":-32000,"message":"Error del dominio","data":"VEHICULO_NO_EXISTE: moto_inexistente"},"id":3}
```

## 4. Método inexistente

**Caso:** Enviar una solicitud a un método inexistente.

**Resultado esperado:** La respuesta contiene el código `-32601`.

**Comando:**

```powershell
curl.exe -sS -X POST `
  "http://127.0.0.1:8000/rpc" `
  -H "Content-Type: application/json" `
  -d '{"jsonrpc":"2.0","method":"metodo_inexistente","params":[],"id":4}'
```

**Respuesta:**

```text
{"jsonrpc":"2.0","error":{"code":-32601,"message":"Method not found"},"id":4}
```

## 5. Parámetros incompletos o de tipo incorrecto

**Caso:** Enviar una solicitud con parámetros incompletos o de tipo incorrecto.

**Resultado esperado:** La respuesta contiene el código `-32602`.

**Comando:**

```powershell
curl.exe -sS -X POST `
  "http://127.0.0.1:8000/rpc" `
  -H "Content-Type: application/json" `
  -d '{"jsonrpc":"2.0","method":"posicion","params":{"vehiculo":"moto1","lat":-41.48},"id":5}'
```

**Respuesta:**

```text
{"jsonrpc":"2.0","error":{"code":-32602,"message":"Invalid params","data":"posicion() missing 1 required positional argument: 'lon'"},"id":5}
```

## 6. JSON inválido

**Caso:** Enviar un cuerpo que no contiene JSON válido.

**Resultado esperado:** La respuesta contiene el código `-32700`.

**Comando:**

```powershell
curl.exe -sS -X POST `
  "http://127.0.0.1:8000/rpc" `
  -H "Content-Type: application/json" `
  -d '{"jsonrpc":"2.0","method":'
```

**Respuesta:**

```text
{"jsonrpc":"2.0","error":{"code":-32700,"message":"Parse error"},"id":null}
```

## 7. Solicitud sin `jsonrpc`

**Caso:** Enviar una solicitud sin el campo `jsonrpc`.

**Resultado esperado:** La respuesta contiene el código `-32600`.

**Comando:**

```powershell
curl.exe -sS -X POST `
  "http://127.0.0.1:8000/rpc" `
  -H "Content-Type: application/json" `
  -d '{"method":"donde","params":["moto1"],"id":7}'
```

**Respuesta:**

```text
{"jsonrpc":"2.0","error":{"code":-32600,"message":"Invalid Request"},"id":7}
```

## 8. Notificación

**Caso:** Enviar una notificación JSON-RPC.

**Resultado esperado:** HTTP `204` sin cuerpo.

**Comando:**

```powershell
curl.exe -i -sS -X POST `
  "http://127.0.0.1:8000/rpc" `
  -H "Content-Type: application/json" `
  -d '{"jsonrpc":"2.0","method":"donde","params":["moto1"]}'
```

**Respuesta:**

```text
HTTP/1.1 204 No Content
date: Fri, 06 Nov 2026 00:29:13 GMT
server: uvicorn
```

## 9. Lote válido e inexistente

**Caso:** Enviar un lote con una solicitud válida y otra a un método inexistente.

**Resultado esperado:** La respuesta es una lista que contiene `result` y el código `-32601`.

**Comando:**

```powershell
curl.exe -sS -X POST `
  "http://127.0.0.1:8000/rpc" `
  -H "Content-Type: application/json" `
  -d '[{"jsonrpc":"2.0","method":"donde","params":["moto1"],"id":9},{"jsonrpc":"2.0","method":"metodo_inexistente","params":[],"id":10}]'
```

**Respuesta:**

```text
[{"jsonrpc":"2.0","result":{"vehiculo":"moto1","lat":-41.48,"lon":-72.96},"id":9},{"jsonrpc":"2.0","error":{"code":-32601,"message":"Method not found"},"id":10}]
```
