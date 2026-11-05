# Integración con las otras tareas

Cómo se conecta el resultado de cada tarea del equipo con la simulación. Las tareas y los números son los del Excel "Asignación de Tareas" del 4/11.

## El modelo: tres entradas reales que faltan

La simulación ya corre de punta a punta (red de OSM → demanda → plan fijo vs. Q-learning → métricas), pero con tres valores **de relleno**. Cada tarea del equipo reemplaza alguno:

| Entrada | Hoy | Se reemplaza con | Cómo se carga |
|---|---|---|---|
| **Dónde** (cruce o corredor) | Av. Santa Fe × Coronel Díaz, elegido por nosotros | La zona que defina el equipo (tareas 1, 5, 6) | Entrada nueva en `SCENARIOS` de `scripts/build_scenario.py` |
| **Tiempos del semáforo** | Plan inventado por `netconvert` (ciclo de 90 s) | Tiempos oficiales o medidos (tareas 4, 8) | Archivo `plan-real.add.xml` en la carpeta del escenario |
| **Demanda de vehículos** | Viajes aleatorios (`randomTrips`) | Conteos reales (tarea 4) | Archivo `demanda-real.rou.xml` en la carpeta del escenario |

**Regla de diseño:** los datos reales viven en archivos con nombre fijo dentro de `scenarios/<nombre>/`. Si el archivo existe, `build_scenario.py` y `run_sumo_rl_demo.py` lo usan solos y lo avisan por pantalla. Si no existe, se usan los valores de relleno y la salida lo dice ("NO es el real de la Ciudad"). Esos archivos **no se pisan** al regenerar el escenario. Para ignorarlos en una corrida: `--sin-plan-real` y `--sin-demanda-real`.

```
Tareas 1,5,6 ─► zona          ─► SCENARIOS en build_scenario.py ─► cruce.net.xml
Tareas 4,8   ─► tiempos       ─► plan-real.add.xml  ─────────────┐
Tarea 4      ─► conteos       ─► demanda-real.rou.xml ───────────┼─► run_sumo_rl_demo.py ─► métricas
Tareas 2,3   ─► demoras reales ─► (validación, ver abajo) ◄──────┘
```

## Paso a paso por tarea

### Tarea 1: CSV de Cruces Semaforizados (Karo)
**Aporta:** coordenadas de los cruces y la columna "horario".
**Se integra en:** la definición de la zona.
1. Ubicar en el CSV los cruces de la zona elegida y tomar sus coordenadas.
2. En `SCENARIOS` sumar una entrada con `bbox` (zona a bajar de OSM), `crop` (recorte, más chico) y `keep_tls`.
3. `python scripts/build_scenario.py <nombre> --download` baja OSM y arma la red.
4. `python scripts/build_scenario.py <nombre> --list-tls` lista los semáforos que quedaron, con sus calles. Elegir los ids que corresponden a los cruces del CSV y ponerlos en `keep_tls`.
5. Volver a correr el paso 3, esta vez sin `--download`.

La columna "horario", si indica que un cruce tiene planes distintos por franja, anticipa que hará falta el plan por franjas (ver tarea 5).

### Tarea 2: GTFS y mapa de demoras (Karo)
**Aporta:** velocidad y demora por tramo y franja, calculadas desde los colectivos.
**Se integra en:** la **validación**, no como entrada. Sirve para comprobar que el gemelo se parece a lo observado (entregable 2).
- Hay que correr la simulación del corredor, sacar la velocidad media por calle y franja, y compararla con la del GTFS.
- **No existe todavía** el script que exporta velocidades por calle desde SUMO. Es trabajo nuevo: sería `scripts/validar_demoras.py`, que lee el resultado de SUMO (opción `--edgedata-output`) y lo cruza con el CSV de demoras de Karo. Conviene definir con ella el formato (calle, franja, velocidad) antes de escribirlo.
- Limitación a tener presente: el GPS de los colectivos no da los tiempos exactos del semáforo, solo demoras.

### Tarea 3: API de Transporte (Daniel)
**Aporta:** posiciones de colectivos en tiempo real y, según la descripción, quizá datos de semáforos.
- Si trae posiciones: mismo uso que el GTFS (validación).
- Si el endpoint de semáforos trae tiempos: es una fuente del plan real. Seguir los pasos de la tarea 8.
- Si no se puede verificar, anotarlo en Notion para que no quede como supuesto.

### Tarea 4: Gobierno Abierto (Daniel)
**Aporta, si responden:** planes semafóricos y conteos vehiculares.

*Planes semafóricos* → `plan-real.add.xml` (los mismos pasos que la tarea 8).

*Conteos* → `demanda-real.rou.xml`:
1. Convertir los conteos a flujos de SUMO, uno por origen-destino o por tramo de entrada, con `vehsPerHour` y la franja (`begin`, `end`, en segundos de simulación):
   ```xml
   <routes>
     <flow id="coronel_diaz_entrada" begin="0" end="3600" vehsPerHour="900"
           from="548646544#0" to="47088480#0"/>
   </routes>
   ```
   Los ids de calles salen de `cruce.net.xml` (o de `netedit`). Si los conteos son por tramo y no por origen-destino, se puede usar `routeSampler.py` de SUMO.
2. Guardarlo como `scenarios/<nombre>/demanda-real.rou.xml`.
3. Correr `python scripts/build_scenario.py <nombre>`: omite `randomTrips` y apunta el `.sumocfg` a ese archivo.
4. **Anotar la fuente** (organismo, fecha, tramo y franja del conteo) al principio del archivo, en un comentario XML.

Si no existen conteos abiertos, la demanda sigue siendo aleatoria y hay que decirlo en el informe como limitación.

### Tarea 5: Estado del sistema en Av. de Mayo (Lu)
**Aporta:** si los cruces son coordinados o tienen planes por horario.
**Se integra en:** qué significa "plan actual" para el baseline.
- Si cada cruce tiene **un solo plan**: un `plan-real.add.xml` con un programa.
- Si tiene **planes por franja horaria**: un programa por franja y un `WAUT` que los activa por hora (ejemplo abajo). Es el "plan por franjas" del entregable 3.
- Si los cruces están **coordinados** (ondas verdes): hace falta el desfase entre cruces (`offset` en cada `tlLogic`). Sin ese dato, no se puede modelar la coordinación.

### Tarea 6: Corredor de 5 a 10 cruces (sin asignar)
**Aporta:** la lista de cruces.
**Se integra en:** igual que la tarea 1, con una diferencia: `keep_tls` lleva **varios ids** (ya está soportado y probado con 2 semáforos).
- La demo corre en modo multiagente: un agente de Q-learning por semáforo. **Son independientes**: ninguno sabe qué hace el vecino, así que no hay coordinación aprendida. Si el equipo quiere coordinación, es un cambio de enfoque (un agente que controle varios semáforos) y hay que decidirlo.
- Un corredor más largo aumenta el tiempo de cada corrida y el de entrenamiento.

### Tarea 7: SUMO y SUMO-RL con un cruce (Guille)
**Hecha.** Es la base de todo lo anterior: `docs/setup-sumo.md`, `scenarios/`, `scripts/`.

### Tarea 8: Medir ciclos a mano (sin asignar)
**Aporta:** duración de verde, amarillo y rojo por fase y franja, de 2 o 3 cruces.
**Se integra en:** `plan-real.add.xml`.
1. `python scripts/tls_template.py <nombre>` genera `plan-real.plantilla.xml` con los `state` correctos de cada fase (qué carriles tienen verde). Quien mide solo necesita que el protocolo de medición corresponda a esas fases.
2. Reemplazar **todas** las duraciones por las medidas. Las que trae la plantilla son las inventadas.
3. Completar `Fuente` y `Fecha` en el comentario del archivo.
4. Renombrarlo a `plan-real.add.xml`. Desde ahí lo usan solos la demo y el build.

El `programID` del plan debe ser distinto de `0` (que ya existe en la red); la plantilla usa `real`. Probado: con `0` SUMO da error, con otro ID el plan queda activo.

**Plan por franjas** (varias duraciones según la hora), probado:
```xml
<additional>
  <tlLogic id="437539849" type="static" programID="manana" offset="0"> ... </tlLogic>
  <tlLogic id="437539849" type="static" programID="tarde"  offset="0"> ... </tlLogic>
  <WAUT startProg="manana" refTime="0" id="franjas">
    <wautSwitch time="1000" to="tarde"/>
  </WAUT>
  <wautJunction wautID="franjas" junctionID="437539849"/>
</additional>
```
`time` está en **segundos de simulación**, no hora del reloj: hay que decidir a qué hora real corresponde el segundo 0 y ajustar la duración de cada corrida.

> **Qué hace el baseline y qué no:** el plan real lo usa el baseline de tiempo fijo. El agente de Q-learning **ignora** las duraciones (arma sus propias fases con los `state`) y decide cuándo cambiar. Por eso comparar contra el plan real es lo que da sentido a las métricas.

### Tarea 9: Notion, actas e informe (Daniel)
**Aporta:** la documentación y el informe de estado.
- Lo que hay que copiar a Notion está en `docs/` y `scenarios/README.md`; no hace falta reescribirlo.
- Para el informe de estado, la salida de la demo ya dice si el baseline y la demanda son reales o de relleno. Usar esa línea tal cual para no sobreestimar resultados.

## Qué falta para el informe final

| Falta | Depende de | Estado |
|---|---|---|
| Tiempos de semáforo reales | Tareas 4 y 8 | Sin datos. Punto de entrada listo |
| Conteos reales | Tarea 4 | Sin datos. Punto de entrada listo |
| Corredor elegido | Tareas 1, 5, 6 | Soporta varios semáforos, sin zona elegida |
| Validación contra demoras | Tarea 2 | Falta `scripts/validar_demoras.py` |
| Gráficos de resultados | — | No existen todavía |
| Entrenamiento serio de RL | Plan y demanda reales | Hoy 1 a 5 episodios, solo como prueba técnica |

## Convenciones

- **Un escenario por carpeta** en `scenarios/`.
- **Todo dato real lleva su fuente** (quién, cuándo, cómo) en un comentario del archivo. Los chicos se versionan; los pesados (GTFS completo, CSV grandes) no se suben: se documenta de dónde bajarlos.
- **Todo dato inventado o por defecto se rotula** como tal. Los scripts lo hacen en pantalla.
- **`results/` no se versiona.** Lo que se muestre al equipo se guarda como tabla o gráfico en `docs/`.
- **Probar en Windows nativo** cualquier script nuevo antes de darlo por terminado: casi todo lo probado hasta ahora fue en WSL.
