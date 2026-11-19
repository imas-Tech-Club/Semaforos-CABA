# Prototipo: plan fijo vs. Q-learning por franja horaria

> **Prueba técnica, no un hallazgo.** La forma del tránsito a lo largo del día es real (zona, marzo de 2020). El nivel de demanda es un **supuesto** y los tiempos del semáforo son de **relleno** (los inventa `netconvert`). Nada de esto describe cómo funciona hoy el cruce real.

## Qué hace

Para el cruce Av. Santa Fe × Av. Coronel Díaz simula cuatro franjas del día con una demanda proporcional al perfil horario real de la zona (`data/perfil_horario_zona_48Q3CH00.csv`, día hábil), y en cada una compara:

- **Plan fijo:** el plan que trae la red (hoy el de relleno de `netconvert`, ciclo de 90 s).
- **Q-learning (SUMO-RL):** un agente entrenado 10 episodios de 1 hora, **evaluado sin explorar ni aprender** en 4 demandas nuevas (otras semillas) que no vio al entrenar.

| Franja | Hora de referencia | Índice del perfil | Vehículos por hora (supuesto) |
|---|---|---|---|
| Madrugada | 4 h | 0,06 | 77 |
| Pico | 12 h | 1,00 | 1.200 |
| Valle de tarde | 17 h | 0,43 | 515 |
| Noche | 20 h | 0,77 | 918 |

El caudal del pico (1 vehículo cada 3 s) es el que ya usaba el repo. Se cambia con `--base-period`. El resto se escala con el índice.

## Cómo correrlo

Desde la raíz del repo, con el entorno activado (ver `docs/setup-sumo.md`):

```
pip install matplotlib
python scripts/demo_franjas.py                      # las 4 franjas
python scripts/demo_franjas.py --franjas pico valle --episodes 10 --eval-seeds 4
python scripts/graficar_franjas.py                  # genera docs/franjas_fijo_vs_ql.png
```

La corrida completa de las 4 franjas (sin `--franjas`) tardó unos 8 minutos en un contenedor de 2 núcleos. Las salidas quedan en `results/franjas/` (no se versiona): `resumen.csv`, `evaluaciones.csv` (una fila por demanda de evaluación) y `aprendizaje.csv`. Una corrida de ejemplo, ya lista para mirar, está en `results_ejemplo/`.

## Resultados de la corrida del 19/11 (mediana de 4 demandas de evaluación)

| Franja | Espera media, fijo (s) | Espera media, Q-learning (s) | Detenidos, fijo | Detenidos, Q-learning |
|---|---|---|---|---|
| Madrugada | 3,21 | 0,06 | 0,21 | 0,02 |
| Pico | 3,68 | 0,20 | 3,46 | 0,60 |
| Valle de tarde | 3,49 | 0,11 | 1,34 | 0,17 |
| Noche | 3,51 | 0,15 | 2,45 | 0,36 |

En esta corrida las 16 evaluaciones de Q-learning (4 franjas × 4 demandas) dieron valores bajos y **no hubo colapso**.

**Inestabilidad ya observada:** en la corrida del 14/11, con la misma configuración, 1 de las 4 demandas del valle hizo colapsar a Q-learning (espera media de 351 s y 28 vehículos detenidos en promedio, con picos de 56). Que una corrida no colapse no prueba que el agente sea estable: el resultado depende de la semilla y del entrenamiento.

Gráfico: `docs/franjas_fijo_vs_ql.png`. La "espera media" es la métrica `system_mean_waiting_time` de SUMO-RL: sirve para comparar planes entre sí, no para decir cuántos minutos pierde cada conductor.

## Cómo leer los resultados

- **Qué sí muestran:** el pipeline completo funciona (red real, demanda por franja, entrenamiento, evaluación en demandas nuevas, gráfico). Un controlador adaptativo, con demanda moderada, puede reducir mucho las esperas frente a un plan fijo genérico.
- **Qué no muestran:** que Q-learning mejore el plan real del cruce. El plan fijo es de relleno (ciclo de 90 s) y la demanda es supuesta. La diferencia es grande en parte porque ese plan no está pensado para este cruce.
- **El colapso del 14/11 es un hallazgo en sí mismo:** el agente es tabular, no explora al evaluar y puede encontrar estados que no vio al entrenar (el script usa la acción 0 en esos casos). En esa corrida el colapso empezó cerca del segundo 1.000 de la hora simulada. No confirmé la causa exacta. Un controlador que falla algunas veces no sirve sin una salvaguarda (por ejemplo, un tiempo máximo de verde).

## Limitaciones

- Un solo cruce. Sin peatones, colectivos ni coordinación con otros cruces.
- Cuatro demandas de evaluación por franja: sirve para detectar fallos, no para estimar incertidumbres finas.
- El perfil horario es de 2020 y de una zona de unos 5 km, no del cruce.
- Q-learning ignora las duraciones de un plan real: decide cuándo cambiar. El plan medido lo usa solo el baseline.

## Cómo reemplazar lo supuesto por datos reales

| Dato | Cómo se carga |
|---|---|
| Tiempos del semáforo medidos | `plan-real.add.xml` en `scenarios/santa-fe-coronel-diaz/` (ver `docs/integracion.md` y el Protocolo de medición en Notion). El script lo usa solo y lo avisa por pantalla. Para ignorarlo: `--sin-plan-real` |
| Nivel de demanda | `--base-period` (segundos entre vehículos en el pico) o, si hay conteos por acceso, un `demanda-real.rou.xml` |
| Perfil horario más reciente | Reemplazar `data/perfil_horario_zona_48Q3CH00.csv` manteniendo las columnas `hora` y `habil_indice` |

Fuente del perfil horario: API de Transporte del GCBA, endpoint `/datos/movilidad/transito/semanaTipica`, datos del 9 al 15 de marzo de 2020, zona `48Q3CH00+` (obtenidos el 14/11/2026).
