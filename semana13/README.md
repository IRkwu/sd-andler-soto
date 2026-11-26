# Semana 13, Guía de laboratorio N°5. Colas de mensajes y master-worker

Viernes 20-11-2026. Parten del estado de su carpeta `semana12/`. No se parte de cero.
Todos los comandos funcionan igual en PowerShell, bash y zsh.

## 0. Preparación (antes de empezar)

1. Copien `semana12/` como `semana13/` y entren a la carpeta.
2. Copien dentro de `semana13/` todos los archivos de esta carpeta `laboratorio/`
   (`cola.py`, `publicador.py`, `procesador.py`, `worker.py`, `master.py`, `graficar.py`,
   `Dockerfile.colas`, `requirements-colas.txt`, `observaciones_semana13.md`, `analisis_speedup.md`).
3. Docker Desktop abierto. Revisen en Settings, Resources cuántas CPU le dan a Docker y anótenlo.

## Paso 1. Broker en el compose

- Peguen el contenido de `fragmento_compose.yml` dentro de `services:` de su `docker-compose.yml`.
- Agreguen al final de su `.env` las líneas de `fragmento_env.txt`.

```
docker compose config -q
docker compose up -d --build rabbitmq
docker compose ps
```

Esperado, `sd_rabbitmq` aparece como `healthy` (tarda unos 15 s). Abran http://localhost:15672
con usuario `guest` y clave `guest`.

## Paso 2. Persistencia con su propio dominio

Editen en `procesador.py` la lista `OPERACIONES_VALIDAS` con las operaciones de su `protocolo.md`.

```
docker compose up -d procesador
docker compose run --rm publicador AGREGAR tornillo 5
docker compose logs procesador
```

Falla provocada, consumidor apagado.

```
docker compose stop procesador
docker compose run --rm publicador --n 20 AGREGAR tornillo 1
```

Miren la pestaña Queues de la consola, la cola `operaciones` tiene 20 mensajes en Ready.
Reinicien el broker con los mensajes adentro y después levanten el procesador.

```
docker compose restart rabbitmq
docker compose start procesador
docker compose logs procesador
```

Esperado, llegan los 20. Anoten en `observaciones_semana13.md` por qué no se perdieron.

## Paso 3. Cola de trabajo, ack manual y reentrega

```
docker compose up -d --scale procesador=3 procesador
docker compose run --rm publicador --n 12 AGREGAR tornillo 1
docker compose logs -f procesador
```

Mientras una réplica dice `procesando id=...`, en otra terminal

```
docker compose ps procesador
docker kill semana13-procesador-2
```

(usen el nombre que les muestra `ps`). Esperado, el mensaje que estaba a medio procesar
aparece en otra réplica con la marca `(REENTREGADO)`. Eso es at-least-once.

Ahora repitan con `AUTO_ACK=1` en el `.env`, luego `docker compose up -d --scale procesador=3 procesador`,
publiquen 12 y maten una réplica. Cuenten cuántos `terminado` aparecen. Vuelvan a dejar `AUTO_ACK=0`.

## Paso 4. Paralelización master-worker

```
docker compose stop procesador
docker compose up -d --scale worker=1 worker
docker compose run --rm master
docker compose up -d --scale worker=2 worker
docker compose run --rm master
docker compose up -d --scale worker=3 worker
docker compose run --rm master
docker compose up -d --scale worker=4 worker
docker compose run --rm master
```

Cada corrida agrega una fila a `mediciones/mediciones.csv` y debe terminar con `ok=True`.
Si les sobra tiempo, hagan una segunda pasada de 1 a 4 para promediar.

## Paso 5. Gráfico de speedup

```
docker compose run --rm graficar
```

Abran `mediciones/speedup.svg` en el navegador. Anoten en `observaciones_semana13.md`
la tabla que imprime y cuántas CPU tiene Docker.

## Limpieza y entrega

```
docker compose down -v
git add semana13
git commit -m "semana13, colas y master-worker"
git push
```

Antes de las 16.00 debe estar en el repositorio `semana13/` con el compose actualizado,
`observaciones_semana13.md`, `mediciones/mediciones.csv` y `mediciones/speedup.svg`.

## Trabajo autónomo, plazo jueves 26-11 a las 18.00

1. `analisis_speedup.md`, por qué su speedup no es lineal (plantilla incluida).
2. `proyecto/topologia_colas.drawio`, topología del proyecto integrador con la cola
   (productores, broker, workers, servidor y protocolo de cada flecha) antes de integrarla.
3. Integrar una cola de mensajes al proyecto integrador. El procesador debe dejar de simular
   y llamar a su servidor real, así el estado vive en un solo lugar.
4. Bitácora del proyecto en `proyecto/bitacora.md`.
