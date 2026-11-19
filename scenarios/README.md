# Escenarios

Cada carpeta es un escenario de SUMO: una red vial, una demanda de vehículos y un `.sumocfg` que los une.

| Carpeta | Qué es | Origen |
|---|---|---|
| `cruce-sintetico/` | Cruce de 4 brazos inventado. Solo valida que el entorno funciona. | Archivos `.nod.xml` / `.edg.xml` escritos a mano |
| `santa-fe-coronel-diaz/` | Av. Santa Fe × Av. Coronel Díaz (Palermo), un semáforo. | OpenStreetMap, **generado con `scripts/build_scenario.py`** |

## Regenerar un escenario

`santa-fe-coronel-diaz/` se puede reconstruir con el script, sin pasos manuales:

```
python scripts/build_scenario.py --list                       # escenarios definidos
python scripts/build_scenario.py santa-fe-coronel-diaz        # reconstruye usando el OSM guardado
python scripts/build_scenario.py santa-fe-coronel-diaz --period 2   # más tránsito (un auto cada 2 s)
python scripts/build_scenario.py santa-fe-coronel-diaz --download   # baja OSM de nuevo
```

**Cuándo usarlo**
- Cambiar la demanda (`--period`, `--seed`, `--end`) sin tocar la red.
- Agregar un cruce o corredor nuevo: sumar una entrada en `SCENARIOS` dentro del script.
- Comprobar que lo que está versionado se puede reproducir.

**Cuándo NO usarlo**
- Si editaste la red a mano con `netedit` (por ejemplo para cargar tiempos de semáforo medidos): regenerar pisa esos cambios. Guardar esos datos en un archivo aparte (ver `docs/integracion.md`).

`cruce-sintetico/` no tiene script: es chico y se arma con `netconvert` a partir de `nodes.nod.xml` y `edges.edg.xml`.

## Archivos de datos reales (opcionales)

Si existen en la carpeta de un escenario, se usan solos y no se pisan al regenerar:

| Archivo | Qué es | Cómo se crea |
|---|---|---|
| `plan-real.add.xml` | Tiempos del semáforo medidos u oficiales | `python scripts/tls_template.py <nombre>`, completar y renombrar |
| `demanda-real.rou.xml` | Flujos de vehículos desde conteos reales | A mano, ver `docs/integracion.md` |

Los dos llevan su fuente anotada en un comentario. `plan-real.plantilla.xml` es solo la plantilla: no se carga.

## Datos que NO son reales todavía

- Los **tiempos del semáforo** los inventa `netconvert` (ciclo de 90 s). OSM no tiene tiempos.
- La **demanda** es aleatoria, no calibrada con conteos.

Cualquier resultado que dependa de eso es una prueba técnica, no un hallazgo.
