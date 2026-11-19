# AGENTS.md

Guía para agentes de IA (Claude Code, Codex, Cursor, Copilot, etc.) que trabajen en este repo. Los humanos también pueden leerla: es el resumen operativo del proyecto.

## Proyecto

Evaluar, con un **gemelo digital en SUMO** calibrado con datos reales de CABA, si adaptar los tiempos de los semáforos a cada franja horaria (con métodos clásicos y con aprendizaje por refuerzo) reduce demoras y colas frente al plan actual, en un **corredor piloto de 5 a 10 cruces**. No se tocan semáforos reales.

Flujo: datos de colectivos + conteos + red vial (OpenStreetMap) → diagnóstico de demoras por cruce y franja → gemelo en SUMO calibrado → comparación de planes (actual, por franjas, adaptativo) → recomendación con métricas.

Entregables: (1) diagnóstico de datos, (2) gemelo digital base, (3) baseline de comparación, (4) prototipo de control adaptativo con SUMO-RL, (5) informe final.

### Estado actual (15/11/2026)

- Etapa: MVP de 4 semanas (4/11 al 2/12/2026), semana 3. Cruce piloto de la demo: Santa Fe × Coronel Díaz; el corredor de 5 a 10 cruces sigue sin definir.
- Relevados: Cruces Semaforizados y GTFS de colectivos (ver `docs/datos/`).
- **Sin definir todavía:** el corredor piloto. No asumas uno; si una tarea lo necesita, pedilo o dejalo como parámetro.
- **Sin datos todavía:** tiempos de ciclo/fases de los semáforos y conteos vehiculares. No existen en ningún dataset abierto relevado.

## Stack

| Herramienta | Uso |
|---|---|
| Python | Análisis de datos y scripts |
| SUMO + sumo-gui | Simulación microscópica de tránsito |
| osmWebWizard / netconvert / netedit | Importar y editar la red desde OpenStreetMap |
| TraCI | Controlar la simulación desde Python |
| SUMO-RL (`pip install sumo-rl`) | Entornos de RL para semáforos |
| Notion | Actas, tareas y documentación del equipo (fuera del repo) |

## Estructura del repo

```
AGENTS.md                         esta guía
README.md                         presentación del proyecto, demo y convención real/supuesto/relleno
scenarios/                        escenarios SUMO (cruce-sintetico, santa-fe-coronel-diaz)
scripts/                          build_scenario, run_sumo_rl_demo, demo_franjas, graficar_franjas, etc.
docs/setup-sumo.md                instalación; docs/prototipo-franjas.md: prototipo de franjas
results_ejemplo/                  CSV de una corrida de ejemplo (results/ no se versiona)
docs/datos/README.md              catálogo de fuentes, matriz de garantías, cómo actualizar datos
docs/datos/cruces-semaforizados.md  ficha: columnas, problemas de calidad, cómo cargarlo
docs/datos/gtfs-colectivos.md     ficha: contenido, limitaciones, cómo bajarlo
data/perfil_horario_zona_48Q3CH00.csv  forma horaria del tránsito (zona, marzo 2020)
data/cruces-semaforizados/        CSV y GeoJSON originales de BA Data (dataset de prueba, versionado)
data/raw/                         descargas locales grandes, ignorado por git (ej. GTFS)
```

## Datos: lo que tenés que saber antes de usarlos

Leé la ficha de la fuente antes de escribir código que la use. Resumen de lo que más fácil se hace mal:

| Fuente | Regla |
|---|---|
| Cruces Semaforizados | Usar el **GeoJSON** como fuente de ubicación (WGS84, 3.946 features). El CSV tiene coordenadas con puntos de miles, encoding roto, filas corridas y le faltan 7 cruces |
| Cruces Semaforizados | Clave: `ID_Codigo` (GeoJSON) / `id_codigo` (CSV), formato `B-CR-NNNNN`. Hacer `strip()`: hay IDs con `\r\n`. Hay 4 sin ID y un duplicado (`B-CR-03592`) |
| Cruces Semaforizados | La columna `horario` **no** son tiempos de semáforo: indica cuándo el cruce está titilante o apagado. Sólo cargada en 3,4% de los registros; vacío no significa "sin titilante" |
| Cruces Semaforizados | Los datos son de 2019: pueden faltar cruces nuevos. Validar el corredor contra OSM (`highway=traffic_signals`) |
| GTFS colectivos | Feed de sep-2019 con calendario vencido (31/12/2019), dataset suspendido en BA Data. Cubre todo el AMBA: recortar al corredor |
| GTFS colectivos | Horarios **programados**, 88% interpolados (`timepoint=0`). No sirve para medir demora real |
| GTFS colectivos | `stop_times.txt` pesa 1,4 GB descomprimido: leerlo en streaming desde el zip y filtrar por `stop_id`; nunca cargarlo entero en memoria |
| GTFS colectivos | Horarios mayores a 24:00 (hasta `32:53:54`) son válidos en GTFS: viajes que cruzan la medianoche |

Código probado para cargar cruces: [docs/datos/cruces-semaforizados.md#cómo-cargarlo](docs/datos/cruces-semaforizados.md#cómo-cargarlo).

## Reglas de trabajo

- **Idioma:** documentación, commits y PRs en español.
- **No modificar los archivos de `data/`**: son los originales de la Ciudad. Las correcciones se hacen al cargarlos, en código.
- **No commitear archivos de más de 100 MB** (límite de GitHub). Las descargas grandes van a `data/raw/`, que está ignorado.
- **Si se actualiza un dataset**, actualizar en el mismo PR su ficha en `docs/datos/` (conteos, problemas de calidad, fecha de descarga) y la matriz de garantías de `docs/datos/README.md`. El procedimiento está en `docs/datos/README.md#actualizar-cruces-semaforizados`.
- **Si se suma una fuente nueva**, crear su ficha en `docs/datos/` con la misma estructura (ficha, contenido, problemas, garantías, cómo bajarla) y agregarla al catálogo.
- **No inventar datos.** Si falta un dato (tiempos de fase, conteos), dejarlo explícito como supuesto o parámetro y avisar; no completarlo con valores "típicos" sin marcarlo.
- Priorizar un cruce bien medido antes que muchos estimados a ciegas.
- Todo cambio va por PR a `main`.

## Fuentes externas

- `data.buenosaires.gob.ar` (CKAN de BA Data) rechaza `curl` sin user-agent de navegador ("Request Rejected"). La metadata se consulta en `https://data.buenosaires.gob.ar/api/3/action/package_show?id=<dataset>` desde un navegador.
- Los archivos se descargan sin problema desde `cdn.buenosaires.gob.ar`.
- BA Data marca como **suspendidos** todos los datasets en formato GTFS y API, incluida la API de Transporte (tiempo real).
