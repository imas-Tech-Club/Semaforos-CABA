# Instalación de SUMO y SUMO-RL

SUMO se instala con `pip` dentro de un entorno virtual (paquete `eclipse-sumo`). Trae `sumo`, `sumo-gui`, `netconvert` y las herramientas (`osmWebWizard`, `randomTrips`), así que no hace falta el instalador oficial. Probado con Python 3.12 en Ubuntu 24.04 (WSL2). Pendiente de probar en Windows nativo.

## Windows (PowerShell)

Requiere Python 3.10 o superior (python.org o Microsoft Store).

```powershell
git clone https://github.com/imas-Tech-Club/Semaforos-CABA.git
cd Semaforos-CABA
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Si PowerShell bloquea el script de activación, ejecutar una vez
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, o usar `cmd` con `.venv\Scripts\activate.bat`.

## Linux / WSL Ubuntu

```bash
git clone https://github.com/imas-Tech-Club/Semaforos-CABA.git
cd Semaforos-CABA
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`sumo-gui` necesita WSLg (Windows 11 o Windows 10 reciente). Sin eso, correr sin `--gui`.

## Verificar

```
sumo --version
python scripts/run_sumo_rl_demo.py
```

El script corre un cruce sintético de 4 brazos, primero con el plan fijo de la red (baseline) y después con Q-learning, y imprime una tabla con espera media, velocidad media y vehículos detenidos. Los CSV quedan en `results/demo/` (no se versiona). Con `--gui` abre `sumo-gui`.

## Escenarios

| Carpeta | Qué es |
|---|---|
| `scenarios/cruce-sintetico` | Cruce de 4 brazos inventado, solo para validar el entorno. |
| `scenarios/santa-fe-coronel-diaz` | Av. Santa Fe × Av. Coronel Díaz (Palermo), importado de OpenStreetMap. Un solo semáforo (`437539849`), unos 100 m de calles alrededor. |

Correr uno u otro: `python scripts/run_sumo_rl_demo.py --scenario santa-fe-coronel-diaz`.

Para reconstruir el cruce real o crear uno nuevo: `python scripts/build_scenario.py --list`. Detalles en [scenarios/README.md](../scenarios/README.md).

Para ver el escenario sin Python:

```
sumo-gui -c scenarios/cruce-sintetico/cruce.sumocfg
```

## Cosas a tener en cuenta

- **`SUMO_HOME`:** `sumo-rl` exige esta variable para importarse y el paquete pip no la define. `run_sumo_rl_demo.py` la setea solo a partir de `sumo.SUMO_HOME`. En scripts nuevos, hacer lo mismo antes de `import sumo_rl`.
- **NumPy:** `sumo-rl 1.4.5` falla con NumPy 2.4 o superior, por eso `requirements.txt` fija `numpy<2.4`.
- **"Retrying in 1 seconds":** es TraCI esperando que SUMO arranque. No es un error.
- **Planes semafóricos del cruce real:** OSM solo dice que hay semáforo, no sus tiempos. `netconvert` genera un plan de tiempo fijo por defecto (ciclo de 90 s, dos fases de 41 s y amarillos de 4 s). **No es el plan real de la Ciudad.** Hasta tener tiempos medidos o datos oficiales (tareas 4 y 8), el baseline es solo un punto de partida.
- **Demanda del cruce real:** generada al azar con `randomTrips` (un vehículo cada 3 s entrando por los bordes). No está calibrada con conteos reales.
- **Aviso `Cannot find proj.db`:** inofensivo. Se evita con `PROJ_DATA=<SUMO_HOME>/data/proj` (el script de la demo ya lo define).
- **Alcance de la demo:** con pocos episodios y demanda inventada, los resultados no permiten sacar conclusiones. Sirve solo para comprobar que el entorno funciona.
