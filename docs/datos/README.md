# Datos del proyecto

Catálogo de las fuentes de datos que usa el proyecto y de qué garantías ofrece cada una. Cada fuente tiene su propia ficha con el detalle del relevamiento.

| Fuente | Ficha | Para qué la usamos | Estado al 15/11/2026 |
|---|---|---|---|
| Cruces Semaforizados (BA Data) | [cruces-semaforizados.md](cruces-semaforizados.md) | Ubicar los cruces del corredor | Descargado y perfilado |
| GTFS de colectivos (BA Data) | [gtfs-colectivos.md](gtfs-colectivos.md) | Líneas por cruce y estimación de demoras | Descargado y perfilado; **dataset suspendido y desactualizado (2019)** |

## Qué entendemos por "garantías"

Para cada fuente respondemos las mismas preguntas, así podemos decidir si un dato sirve para calibrar el gemelo o sólo como referencia:

| Dimensión | Pregunta |
|---|---|
| Procedencia | ¿Quién lo publica y bajo qué licencia? |
| Vigencia | ¿De cuándo es el dato y cada cuánto se actualiza? |
| Completitud | ¿Qué porcentaje de los registros tiene el campo que necesitamos? |
| Exactitud | ¿El dato es observado, programado o estimado? |
| Consistencia | ¿Coinciden los distintos formatos de la misma fuente? ¿Hay duplicados o filas rotas? |
| Reproducibilidad | ¿Podemos trabajar todos con el mismo archivo? |

Cada dimensión se califica como:

- **Garantizado**: verificado por nosotros sobre el archivo descargado.
- **Declarado**: lo dice la metadata de la fuente, no lo verificamos.
- **No garantizado**: no hay dato o lo verificamos y no se cumple.

## Matriz resumen

| Dimensión | Cruces Semaforizados | GTFS colectivos |
|---|---|---|
| Procedencia | Declarado: Secretaría de Transporte y Obras Públicas, CC-BY-2.5-AR | Declarado: Secretaría de Transporte y Obras Públicas, CC-BY-2.5-AR |
| Vigencia | No garantizado: archivo de 2019, actualización "eventual" | No garantizado: feed de sep-2019, calendario vence el 31/12/2019 |
| Completitud | Garantizado para ubicación (100% con coordenadas en GeoJSON); `horario` sólo en 3,4% | Garantizado: 100% de `stop_times` con horario |
| Exactitud | Ubicación: garantizada. Tiempos de fase: **no existen en el dataset** | Horarios **programados**, no observados; 88% interpolados (`timepoint=0`) |
| Consistencia | No garantizado: CSV con encoding roto, coordenadas mal formateadas, filas corridas y duplicados | Garantizado a nivel estructura (archivos GTFS válidos) |
| Reproducibilidad | Garantizado: archivos versionados en el repo | Parcial: URL estable, pero el archivo no se versiona y la Ciudad podría reemplazarlo |

## Conclusiones para el MVP

1. **No hay tiempos de ciclo ni fases en ningún dataset abierto relevado.** La columna `horario` de cruces describe cuándo un semáforo pasa a modo titilante, no la duración de verde/rojo. Esto confirma que el plan actual hay que pedirlo a la Ciudad (tarea 4) o medirlo a mano (tarea 8).
2. **El GTFS estático no permite armar un mapa de demoras.** Tiene horarios programados, no tiempos reales de paso. Para demoras observadas necesitamos posiciones de colectivos en tiempo real (API de Transporte, tarea 3), que BA Data también marca como suspendida.
3. **Para ubicar cruces usar el GeoJSON, no el CSV.** El GeoJSON tiene coordenadas WGS84 correctas y 7 cruces más.
4. Los datos de 2019 son pre-pandemia: sirven para la red de paradas y recorridos, pero no para calibrar demanda actual sin validación.

## Archivos en el repo

| Fuente | Ubicación | ¿Versionado? |
|---|---|---|
| Cruces Semaforizados (CSV + GeoJSON) | [`data/cruces-semaforizados/`](../../data/cruces-semaforizados/) | Sí, como dataset de prueba (2,6 MB en total), descargado el 15/11/2026 |
| GTFS de colectivos | `data/raw/gtfs/` (local) | No: pesa 209 MB, más que el límite de 100 MB por archivo de GitHub. Cada uno lo baja con el comando de abajo |

`.gitattributes` marca `data/**` como binario para que git guarde los archivos byte a byte (el CSV viene con finales de línea CRLF). Así, al volver a bajarlos, `git status` sólo marca cambios si la Ciudad publicó algo distinto.

### Actualizar Cruces Semaforizados

Bajar la versión publicada encima de la versionada:

```bash
cd data/cruces-semaforizados
curl -fsSO https://cdn.buenosaires.gob.ar/datosabiertos/datasets/transporte-y-obras-publicas/cruces-semaforizados/cruces-semaforizados.csv
curl -fsSO https://cdn.buenosaires.gob.ar/datosabiertos/datasets/transporte-y-obras-publicas/cruces-semaforizados/cruces-semaforizados.geojson
git status --short .
```

- Si `git status` no muestra nada: la fuente no cambió, no hay nada que hacer.
- Si muestra algún archivo modificado: la Ciudad publicó una versión nueva. Hay que volver a perfilar y actualizar la ficha ([cruces-semaforizados.md](cruces-semaforizados.md)) en el mismo PR que los archivos.

Para ver si cambió la metadata (fecha, frecuencia, estado) sin bajar los archivos, abrir en el navegador `https://data.buenosaires.gob.ar/api/3/action/package_show?id=cruces-semaforizados` y mirar `metadata_modified` y el `last_modified` de cada recurso. Ese dominio rechaza `curl` sin user-agent de navegador; el CDN no.

### Bajar el GTFS de colectivos

```bash
mkdir -p data/raw/gtfs && cd data/raw/gtfs
curl -fsSO https://cdn.buenosaires.gob.ar/datosabiertos/datasets/transporte-y-obras-publicas/colectivos-gtfs/colectivos-gtfs.zip
```
