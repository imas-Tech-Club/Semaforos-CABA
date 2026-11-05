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

Para ver el escenario sin Python:

```
sumo-gui -c scenarios/cruce-sintetico/cruce.sumocfg
```

## Cosas a tener en cuenta

- **`SUMO_HOME`:** `sumo-rl` exige esta variable para importarse y el paquete pip no la define. `run_sumo_rl_demo.py` la setea solo a partir de `sumo.SUMO_HOME`. En scripts nuevos, hacer lo mismo antes de `import sumo_rl`.
- **NumPy:** `sumo-rl 1.4.5` falla con NumPy 2.4 o superior, por eso `requirements.txt` fija `numpy<2.4`.
- **"Retrying in 1 seconds":** es TraCI esperando que SUMO arranque. No es un error.
- **Alcance de la demo:** el escenario es sintético y 3 episodios no alcanzan para sacar conclusiones. Sirve solo para comprobar que el entorno funciona.
