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
| Reproducibilidad | ¿Podemos volver a bajar exactamente el mismo archivo? (URL + SHA-256) |

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
| Reproducibilidad | Garantizado: URL estable + SHA-256 registrado | Garantizado: URL estable + SHA-256 registrado |

## Conclusiones para el MVP

1. **No hay tiempos de ciclo ni fases en ningún dataset abierto relevado.** La columna `horario` de cruces describe cuándo un semáforo pasa a modo titilante, no la duración de verde/rojo. Esto confirma que el plan actual hay que pedirlo a la Ciudad (tarea 4) o medirlo a mano (tarea 8).
2. **El GTFS estático no permite armar un mapa de demoras.** Tiene horarios programados, no tiempos reales de paso. Para demoras observadas necesitamos posiciones de colectivos en tiempo real (API de Transporte, tarea 3), que BA Data también marca como suspendida.
3. **Para ubicar cruces usar el GeoJSON, no el CSV.** El GeoJSON tiene coordenadas WGS84 correctas y 7 cruces más.
4. Los datos de 2019 son pre-pandemia: sirven para la red de paradas y recorridos, pero no para calibrar demanda actual sin validación.

## Cómo se registran los archivos

Los archivos crudos no se versionan en el repo (el GTFS pesa 209 MB comprimido). Cada ficha documenta la URL de descarga, la fecha y el SHA-256 del archivo usado, para que cualquiera pueda verificar que trabaja con la misma versión:

```bash
shasum -a 256 <archivo>
```

Si el hash no coincide, la fuente cambió: hay que volver a perfilar y actualizar la ficha.
