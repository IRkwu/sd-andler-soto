# Bitácora del proyecto integrador

Una entrada por semana, la más reciente arriba. Cada entrada se sube a más tardar el jueves siguiente a las 18.00.

---

## Entrada 1, semana 12 (13-11-2026)

**Presentes:** Álvaro Andler y Elías Soto

**Qué decidimos**  

- Crear un objeto `SeguimientoVehiculo` que se devuelve al cliente por referencia, con un historial propio de posiciones.
- Usar el modo de instancia `single`.
- Registrar el servicio en el servidor de nombres como `sd.andler-soto.geolocalizacion`.

**Por qué lo decidimos y qué alternativa descartamos**  

- Descartamos devolver el seguimiento por valor (`POR_VALOR=1`). Pyro5 intentó serializarlo por valor, pero su clase no estaba soportada para reconstrucción en el cliente: `unsupported serialized class: objetos.SeguimientoVehiculo`.
- Elegimos `single` y descartamos `session` para `Geolocalizacion`. Los datos de los vehículos se almacenan en `dominio.py`, que es compartido por todas las instancias, así que en ambos modos los clientes acceden a las mismas posiciones. Usaríamos `session` solo para guardar estado de un cliente.

**Qué hicimos**  

- Levantamos `nombres`, `servidor` y `cliente`, y comprobamos la URI `PYRO:geolocalizacion@servidor:9100`.
- Probamos el paso por referencia. Tras llamar a `finalizar()`, el daemon dejó de reconocer la URI (`unknown object`): una referencia colgante.
- Comparamos los modos `single` y `session`.
- Provocamos la falla en tres tiempos: servidor muerto, servidor que vuelve, y nombres muerto y de vuelta (`semana12/observaciones.md`).

**Problemas encontrados y cómo los abordamos**  

- Al reiniciar el servidor, `moto1` volvió a sus valores iniciales y el seguimiento quedó como referencia colgante: los cambios no persistían. Utilizaríamos almacenamiento persistente para conservar las posiciones y los seguimientos.
- Al reiniciar el servidor de nombres sin volver a registrar el servicio, apareció `unknown name`. Después de reiniciar el servidor de geolocalización, la URI y las consultas volvieron a funcionar. Habilitaríamos el registro periódico (`REREGISTRO=5`).

**Próximo paso y responsable**  

| Tarea | Responsable | Para cuándo |
|---|---|---|
| `ALCANCE.md` aprobado | | |
| Cola de mensajes integrada al proyecto | | Jue 26-11, 18.00 |
| Entrada de la semana 13 en la bitácora | | Jue 26-11, 18.00 |

