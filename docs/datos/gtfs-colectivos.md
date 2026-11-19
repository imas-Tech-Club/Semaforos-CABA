# GTFS de colectivos (BA Data)

Tarea 2 de la reunión del 4/11: bajar el GTFS de colectivos y armar el mapa de demoras por franja horaria del corredor.

## Resumen

- El dataset está **marcado como suspendido** en BA Data, pero el archivo se sigue pudiendo descargar.
- El feed es de **septiembre de 2019** y su calendario **venció el 31/12/2019**.
- Tiene **horarios programados, no observados**. Con este dataset solo **no se puede** medir demora real: sirve para saber qué líneas pasan por cada cruce y con qué frecuencia programada.
- El mapa de demoras requiere posiciones en tiempo real (API de Transporte, tarea 3).

## Ficha

| Campo | Valor |
|---|---|
| Dataset | [Colectivos: GTFS](https://data.buenosaires.gob.ar/dataset/colectivos-gtfs) |
| Publica | Secretaría de Transporte y Obras Públicas, Jefatura de Gabinete |
| Licencia | CC-BY-2.5-AR (hay que citar la fuente) |
| Frecuencia de actualización declarada | Cada 2 años (`R/P2Y`) |
| Fecha del recurso | 08/08/2019 (`last_modified`); archivos internos del 30/09/2019 |
| Estado declarado | "Se informa a los usuarios de BA DATA que todos los datasets con Formato API y GTFS, están suspendidos. Se encuentran en revisión y corrección." |
| Variante | [Colectivos: GTFS Frequency](https://data.buenosaires.gob.ar/dataset/colectivos-gtfs-frequency): versión simplificada por frecuencias en lugar de horarios por parada (no relevada) |
| Fecha de descarga | 15/11/2026 |

### Archivo descargado

| URL | Tamaño |
|---|---|
| `https://cdn.buenosaires.gob.ar/datosabiertos/datasets/transporte-y-obras-publicas/colectivos-gtfs/colectivos-gtfs.zip` | 209.195.824 B (1,46 GB descomprimido) |

## Qué contiene

| Archivo | Registros | Columnas |
|---|---|---|
| `agency.txt` | 192 empresas | `agency_id`, `agency_name`, `agency_url`, `agency_timezone`, `agency_lang`, `agency_phone` |
| `routes.txt` | 1.052 ramales (todos `route_type=3`, bus) | `route_id`, `agency_id`, `route_short_name`, `route_long_name`, `route_desc`, `route_type` |
| `trips.txt` | 436.407 viajes | `route_id`, `service_id`, `trip_id`, `trip_headsign`, `trip_short_name`, `direction_id`, `block_id`, `shape_id`, `exceptional` |
| `stop_times.txt` | 1,4 GB (no se cargó completo) | `trip_id`, `arrival_time`, `departure_time`, `stop_id`, `stop_sequence`, `timepoint`, `shape_dist_traveled` |
| `stops.txt` | 43.594 paradas | `stop_id`, `stop_code`, `stop_name`, `stop_lat`, `stop_lon` |
| `shapes.txt` | 29 MB | `shape_id`, `shape_pt_lat`, `shape_pt_lon`, `shape_pt_sequence`, `shape_dist_traveled` |
| `calendar_dates.txt` | 95 fechas | `service_id`, `date`, `exception_type` |

No incluye `calendar.txt`, `feed_info.txt` ni `frequencies.txt`.

### Cobertura

- **Geográfica: AMBA, no sólo CABA.** Las paradas van de lat −35,18 a −34,04 y lon −60,98 a −57,73. Hay que recortar al corredor.
- **Temporal:** `calendar_dates` cubre del 28/09/2019 al 31/12/2019, con 4 `service_id` (1 a 4, presumiblemente día hábil / sábado / domingo / feriado; no está documentado).
- Los horarios pasan de 24:00 (hasta `32:53:54`) para viajes nocturnos, como permite la especificación GTFS.

### Exactitud de los horarios

En una muestra de 200.000 filas de `stop_times.txt` (3.553 viajes):

| `timepoint` | Filas | Significado GTFS |
|---|---|---|
| `1` | 24.749 (12%) | Horario exacto programado (cabeceras y puntos de control) |
| `0` | 175.251 (88%) | Horario aproximado, interpolado entre puntos de control |

Es decir: aun como programación, la hora de paso por una parada intermedia (como un cruce del corredor) es una estimación lineal.

## Por qué no alcanza para el mapa de demoras

La demora en un cruce es la diferencia entre el tiempo real de paso y el tiempo a flujo libre. El GTFS estático sólo da el tiempo **programado**, que además ya incorpora la demora promedio que la empresa estimó en 2019 al armar el cronograma. Lo que sí podemos sacar:

| Pregunta | ¿El GTFS la responde? |
|---|---|
| ¿Qué líneas pasan por cada cruce del corredor? | Sí (`shapes` + `stops` + `trips`) |
| ¿Cuántos colectivos por hora programados por franja? | Sí, con la salvedad de que es 2019 |
| Velocidad programada por tramo entre paradas | Aproximada (88% interpolado) |
| Demora real por cruce y franja | **No** |

Para demoras observadas hace falta GTFS-Realtime o posiciones de vehículos (API de Transporte, tarea 3). BA Data también la marca como suspendida, así que vale averiguar si la API de Transporte de Nación o la Ciudad publican hoy el feed por otra vía.

## Garantías

| Dimensión | Nivel | Detalle |
|---|---|---|
| Procedencia | Declarado | Publicación oficial GCBA, licencia CC-BY-2.5-AR. Las `agency_url` apuntan a la CNRT |
| Vigencia | **No garantizado** | Feed de sep-2019, calendario vencido, dataset suspendido. Recorridos, paradas y frecuencias pueden haber cambiado (pandemia, Metrobuses nuevos, traspaso de líneas a la Ciudad) |
| Completitud | Garantizado | Todos los archivos obligatorios de GTFS presentes; 0% de horarios vacíos en la muestra |
| Exactitud | **No garantizado** | Horarios programados, no observados; 88% interpolados |
| Consistencia | Garantizado a nivel estructura | Columnas según especificación GTFS; no se corrió un validador completo (ej. `gtfs-validator` de MobilityData) |
| Reproducibilidad | Parcial | URL estable, pero el archivo no se versiona en el repo y la Ciudad podría reemplazarlo en la misma URL |

## Cómo reproducir

No está versionado en el repo (209 MB, supera el límite de GitHub). Para bajarlo y verificarlo, ver el [README de datos](README.md#bajar-el-gtfs-de-colectivos).

`stop_times.txt` pesa 1,4 GB descomprimido: conviene leerlo en streaming o filtrarlo por `stop_id` del corredor antes de cargarlo en memoria.

## Próximos pasos

1. Elegido el corredor (tarea 6), recortar `stops` y `shapes` y listar las líneas que pasan por cada cruce.
2. Contrastar contra fuentes actuales (recorridos en OSM o en la API) para ver qué cambió desde 2019.
3. Para demoras observadas: depende de la tarea 3 (API de Transporte).
