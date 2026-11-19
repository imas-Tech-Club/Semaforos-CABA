# Cruces Semaforizados (BA Data)

Tarea 1 de la reunión del 4/11: descargar el CSV de Cruces Semaforizados y revisar sus columnas, en especial `horario`.

## Ficha

| Campo | Valor |
|---|---|
| Dataset | [Cruces Semaforizados](https://data.buenosaires.gob.ar/dataset/cruces-semaforizados) |
| Publica | Secretaría de Transporte y Obras Públicas (autor declarado: Secretaría de Desarrollo Urbano, Jefatura de Gabinete) |
| Licencia | CC-BY-2.5-AR (hay que citar la fuente) |
| Frecuencia de actualización declarada | Eventual |
| Fecha de los archivos | 24/09/2019 (`last_modified` de los recursos) |
| Última modificación de metadata | 18/06/2026 (sólo metadata, los archivos no cambiaron) |
| Formatos | CSV, XLSX, GeoJSON, SHP (zip) |
| Fecha de descarga | 15/11/2026 |

### Archivos descargados

| Formato | URL | Tamaño |
|---|---|---|
| CSV | `https://cdn.buenosaires.gob.ar/datosabiertos/datasets/transporte-y-obras-publicas/cruces-semaforizados/cruces-semaforizados.csv` | 683.007 B |
| GeoJSON | `https://cdn.buenosaires.gob.ar/datosabiertos/datasets/transporte-y-obras-publicas/cruces-semaforizados/cruces-semaforizados.geojson` | 1.958.498 B |

## Qué contiene

Un registro por cruce semaforizado de CABA. Incluye semáforos tradicionales, titiladores y titilantes. **No incluye duraciones de verde/rojo, fases ni planes horarios.**

| Archivo | Registros | Notas |
|---|---|---|
| CSV | 3.940 filas | 22 columnas, separador `;` |
| GeoJSON | 3.946 features | 16 propiedades, CRS84 (WGS84 lon/lat) |

### Columnas del CSV

| Columna | Descripción (según metadata) | Completitud | Observaciones |
|---|---|---|---|
| `long`, `lat` | Coordenadas del cruce | 99,9% | **Mal formateadas**, ver problemas |
| `n_cruce` | Número de cruce, extraído del código | 99,9% | 4 cruces con valor `0` (entradas a demanda: bomberos, premetro, usina) |
| `id_codigo` | Código del registro (`B-CR-NNNNN`) | 99,9% | 1 código duplicado |
| `fecha_inau`, `anio_inau` | Inauguración | 1,1% | Sólo 2017–2018, texto libre ("Febrero", "2-feb") |
| `dom_orig` | Domicilio original | 99,9% | Texto libre, ej. "Paseo Colón Av. y La Rábida" |
| `dom_norma` | Domicilio normalizado | 3,8% | Casi siempre vacío |
| `origen` | Cómo se geolocalizó | 99,9% | `Coordenada` 3.786, `Domicilio` 133, mixto 14, listado titilantes 4 |
| `observ` | Observaciones | 3,6% | 13 registros dicen "NO GEOCODIFICADO" |
| `nro_nva` | Número de instalaciones | 99,9% | `4` en el 96% |
| `instala` | Tipo de instalación | 3,8% | Ver tabla de `instala` |
| `horario` | "Horario en que funciona la instalación" | 3,4% | Ver análisis de `horario` |
| `fecha_fina` | Fin de obra | 0,4% | Referencias a obra del Paseo del Bajo (2018–2020) |
| `id_usig` | ID USIG | 99,9% | Correlativo, sirve como clave |
| `objeto` | Tipo de elemento | 99,7% | Siempre "CRUCE SEMAFORIZADO" |
| `calle_nombre` | Calle principal | 95,5% | |
| `calle_altura` | Altura | 2,3% | |
| `barrio`, `comuna` | Ubicación administrativa | 99,8% | 49 barrios, 15 comunas |
| `codigo_postal`, `codigo_postal_argentino` | CP | ~2% | |

## La columna `horario`

Era la pregunta abierta de la reunión: si `horario` traía los tiempos semafóricos. **No los trae.** Describe **en qué franja el cruce funciona en modo titilante (o apagado)**, no la duración de las fases.

Sólo 135 de 3.940 registros (3,4%) la tienen cargada. Valores encontrados:

| Valor | Registros |
|---|---|
| Todos los días de 22:00 a 06:00 hs. | 77 |
| Titilante 24 hs. | 20 |
| Titilante por obra | 14 |
| Todos los días de 21:00 a 07:00 hs. | 5 |
| Todos los días de 23:00 a 06:00 hs. | 3 |
| Todos los días de 19:00 a 07:00 hs. | 3 |
| Apagado por obra | 2 |
| Otros horarios nocturnos (18–23 h a 05–08 h) | 5 |
| Horarios por día de semana / escolar / eventos | 4 |
| "CRUCE SEMAFORIZADO" (fila corrida, ver abajo) | 2 |

Y la columna relacionada `instala`:

| Valor | Registros |
|---|---|
| TITILANTE NOCTURNO | 95 |
| TITILANTE CON DEMANDA | 15 |
| CRUCE | 13 |
| TITILANTE A PEDIDO DE GCBA (con variantes) | 11 |
| TITILANTE POR OBRA | 6 |
| APAGADO A PEDIDO DE GCBA | 2 |
| TITILANTE 24 HS EXCEPTO EN HORARIO ESCOLAR / EN EVENTOS | 2 |
| `-`, `2635`, `2636` (basura o filas corridas) | 4 |

**Para qué sirve igual:** identifica cruces que ya tienen un "plan por franja horaria" rudimentario (normal de día, titilante de noche). Si el corredor piloto incluye alguno, el plan actual no es de tiempo fijo las 24 h y hay que modelarlo así.

## Problemas de calidad encontrados

| # | Problema | Alcance | Cómo lo tratamos |
|---|---|---|---|
| 1 | **Coordenadas del CSV con separador de miles**: `-583.693.183.994.195` en lugar de `-58.3693183994195`. Además la metadata dice "coordenadas planas", pero son grados WGS84. | Todas las filas | Usar el GeoJSON. Si hace falta el CSV: quitar los puntos y poner el decimal después de los 2 primeros dígitos. Verificado: las 3.934 coordenadas reconstruidas coinciden con el GeoJSON (diferencia < 1e-4°). |
| 2 | **Doble codificación UTF-8** (mojibake): "Paseo ColÃ³n" en vez de "Paseo Colón". | 1.675 filas (42%) | Re-codificar como cp1252 y decodificar como UTF-8. 4 valores tienen bytes que cp1252 no define (`\x81`, `\x8d`) y van como latin-1. Ver [Cómo cargarlo](#cómo-cargarlo). |
| 3 | **Filas corridas**: los cruces "Melian y Pico" y "Melian y Vedia" tienen las columnas desplazadas (el nombre quedó en `id_codigo`, "Saavedra" en `objeto`, etc.). | 2 filas | Corregir a mano o tomar del GeoJSON (son `B-CR-03591` y `B-CR-03592`). |
| 4 | **Código duplicado**: `B-CR-03592` aparece 2 veces con coordenadas casi iguales (~2 m). | 1 código | Deduplicar por `id_codigo`, quedarse con la fila con domicilio normalizado. |
| 5 | **Registros sin código**. | 4 filas CSV, 4 features GeoJSON | Descartar o revisar a mano si caen en el corredor. |
| 6 | **IDs con `\r\n` al final** en el GeoJSON (`B-CR-03591\r\n`, `B-CR-03592\r\n`). | 2 features | `strip()` al leer. |
| 7 | **CSV y GeoJSON no tienen los mismos cruces**: el GeoJSON tiene 7 que no están en el CSV (`B-CR-04100`, `04175`, `04179`, `04195`, `04197`, `04198`, `07237`). | 7 cruces | Tomar el GeoJSON como fuente de verdad de ubicación. |
| 8 | **13 cruces "NO GEOCODIFICADO"** y 133 geolocalizados por domicilio (menos precisos que por coordenada). | 146 cruces | Si caen en el corredor, validar ubicación contra OSM. |
| 9 | **Archivos de 2019**: cruces instalados después no figuran. | Todo el dataset | Validar el corredor elegido contra OSM (`highway=traffic_signals`) y en campo. |

## Garantías

| Dimensión | Nivel | Detalle |
|---|---|---|
| Procedencia | Declarado | Publicación oficial GCBA, licencia CC-BY-2.5-AR |
| Vigencia | **No garantizado** | Archivos del 24/09/2019, actualización "eventual". Puede faltar cualquier cruce posterior |
| Completitud — ubicación | Garantizado | 100% de los features del GeoJSON tienen geometría; bbox dentro de CABA (lat −34,70 a −34,54; lon −58,53 a −58,36) |
| Completitud — horario/instalación | **No garantizado** | 3,4% / 3,8%. Que esté vacío **no** significa que el cruce no titile de noche |
| Exactitud — ubicación | Garantizado (con salvedades) | CSV y GeoJSON coinciden; 146 cruces geolocalizados por domicilio o sin geocodificar |
| Exactitud — tiempos de fase | **No existe** | El dataset no tiene duraciones de verde/rojo ni fases |
| Consistencia | **No garantizado** | Ver problemas 1–7 |
| Reproducibilidad | Garantizado | Archivos versionados en `data/cruces-semaforizados/` |

## Dónde están los archivos

Los dos archivos están versionados en [`data/cruces-semaforizados/`](../../data/cruces-semaforizados/), tal cual los publica la Ciudad (sin corregir). No se editan: las correcciones se aplican al cargarlos. Cómo actualizarlos: [README de datos](README.md#actualizar-cruces-semaforizados).

## Cómo cargarlo

Probado sobre los archivos versionados (descarga del 15/11/2026), desde la raíz del repo y sin dependencias externas.

GeoJSON, la fuente recomendada para ubicación. Devuelve un diccionario por `id_codigo`, con el ID limpio, sin registros sin código y sin duplicados:

```python
import json
from pathlib import Path

DATA_DIR = Path("data/cruces-semaforizados")


def load_crossings():
    features = json.loads((DATA_DIR / "cruces-semaforizados.geojson").read_text(encoding="utf-8"))["features"]
    crossings = {}
    for feature in features:
        code = (feature["properties"]["ID_Codigo"] or "").strip()
        if not code:
            continue
        longitude, latitude = feature["geometry"]["coordinates"]
        crossings.setdefault(code, {**feature["properties"], "id_codigo": code, "lon": longitude, "lat": latitude})
    return crossings
```

Resultado esperado: 3.940 cruces (de 3.946 features: 4 sin código y 2 que repiten un ID una vez limpiado el `\r\n`).

CSV, sólo si hacen falta columnas que el GeoJSON no tiene (`barrio`, `comuna`, `calle_nombre`, etc.). Arregla el encoding y las coordenadas; **no** arregla las 2 filas corridas ni el duplicado:

```python
import csv
from pathlib import Path

DATA_DIR = Path("data/cruces-semaforizados")
BYTES_UNDEFINED_IN_CP1252 = "\x81\x8d\x8f\x90\x9d"


def fix_mojibake(text):
    if "Ã" not in text and "Â" not in text:
        return text
    raw = b"".join(
        character.encode("latin-1") if character in BYTES_UNDEFINED_IN_CP1252 else character.encode("cp1252")
        for character in text
    )
    return raw.decode("utf-8")


def parse_csv_coordinate(raw):
    digits = raw.replace(".", "").replace("-", "")
    return -float(f"{digits[:2]}.{digits[2:]}") if digits else None


def load_crossings_csv():
    with open(DATA_DIR / "cruces-semaforizados.csv", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter=";"))
    return [
        {
            **{column: fix_mojibake(value) for column, value in row.items()},
            "lon": parse_csv_coordinate(row["long"]),
            "lat": parse_csv_coordinate(row["lat"]),
        }
        for row in rows
    ]
```

Resultado esperado: 3.940 filas; `Paseo Colón Av. y La Rábida` en `dom_orig` de la primera fila; coordenadas iguales a las del GeoJSON con una diferencia menor a 1e-4°.
