"""Velocidad simulada por calle y franja, para compararla con datos observados.

Cuándo usarlo
    Validación del gemelo digital (entregable 2): ¿la simulación se parece a lo que
    se observa en la calle? Sirve con las velocidades/demoras por tramo que salgan
    del GTFS de colectivos (tarea 2) o de la API de Transporte (tarea 3).

Uso (desde la raíz del repo, con el venv activado)
    python scripts/validar_demoras.py santa-fe-coronel-diaz
    python scripts/validar_demoras.py santa-fe-coronel-diaz --periodo 900
    python scripts/validar_demoras.py santa-fe-coronel-diaz --observado datos/observado.csv

Qué hace
    Corre el plan de tiempo fijo del escenario (el real si hay plan-real.add.xml) con la
    demanda del escenario, mide la velocidad media en cada calle por franja de simulación y
    la agrupa por NOMBRE de calle. Escribe results/<escenario>/validacion_sim.csv.
    Con --observado, además compara contra ese CSV y calcula el error.

Formato de --observado (CSV con encabezado)
    calle,t_inicio_s,velocidad_kmh
    Avenida Santa Fe,0,22.5
    Avenida Coronel Díaz,0,18.0
  - `calle`: nombre exacto como sale en OSM (ver validacion_sim.csv).
  - `t_inicio_s`: inicio de la franja en segundos de simulación; tiene que coincidir con
    un inicio de franja de la simulación (0, periodo, 2*periodo, ...).
  - Ese formato lo fija este script; hay que acordarlo con quien arme el mapa de demoras.

LIMITACIONES (leer antes de sacar conclusiones)
    - La velocidad simulada es la de TODOS los autos de la calle. La del GTFS es la de los
      colectivos, que paran en paradas y comparten carril: no son directamente comparables.
      Un desvío sistemático (los colectivos más lentos) es esperable, no un error del modelo.
    - Con demanda aleatoria y plan por defecto (no reales), esta comparación no valida nada:
      solo comprueba que el procedimiento funciona.
"""
import argparse
import csv
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

import sumo

os.environ.setdefault("SUMO_HOME", sumo.SUMO_HOME)
os.environ.setdefault("PROJ_DATA", os.path.join(sumo.SUMO_HOME, "data", "proj"))
import sumolib  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
MS_A_KMH = 3.6


def simular(scen, periodo, salida_xml):
    """Corre sumo con un edgeData por franja y deja el XML en salida_xml."""
    adicionales = []
    plan = scen / "plan-real.add.xml"
    if plan.exists():
        adicionales.append(str(plan))
    with tempfile.NamedTemporaryFile("w", suffix=".add.xml", delete=False, encoding="utf-8") as f:
        f.write(
            f'<additional><edgeData id="v" file="{salida_xml}" period="{periodo}" '
            f'excludeEmpty="true"/></additional>\n'
        )
        tmp_add = f.name
    adicionales.append(tmp_add)
    try:
        subprocess.run(
            [sumolib.checkBinary("sumo"), "-c", str(scen / "cruce.sumocfg"),
             "-a", ",".join(adicionales), "--no-step-log", "true", "--no-warnings", "true"],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    finally:
        os.unlink(tmp_add)


def agrupar_por_calle(net, edgedata_xml):
    """{(calle, t_inicio): (velocidad_kmh, segundos_muestreados)} ponderando por tiempo de muestreo."""
    nombre = {e.getID(): e.getName() for e in net.getEdges()}
    acum = defaultdict(lambda: [0.0, 0.0])  # suma(vel*seg), suma(seg)
    for intervalo in ET.parse(edgedata_xml).getroot().iter("interval"):
        t0 = float(intervalo.get("begin"))
        for e in intervalo.iter("edge"):
            calle = nombre.get(e.get("id"), "") or "(sin nombre)"
            seg = float(e.get("sampledSeconds", 0))
            if seg <= 0 or e.get("speed") is None:
                continue
            acum[(calle, t0)][0] += float(e.get("speed")) * seg
            acum[(calle, t0)][1] += seg
    return {k: (v[0] / v[1] * MS_A_KMH, v[1]) for k, v in acum.items() if v[1] > 0}


def leer_observado(ruta):
    obs = {}
    with open(ruta, newline="", encoding="utf-8") as f:
        for i, fila in enumerate(csv.DictReader(f), start=2):
            try:
                obs[(fila["calle"].strip(), float(fila["t_inicio_s"]))] = float(fila["velocidad_kmh"])
            except (KeyError, ValueError) as e:
                sys.exit(f"{ruta} línea {i}: formato inválido ({e}). Se esperan las columnas calle,t_inicio_s,velocidad_kmh")
    return obs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scenario")
    ap.add_argument("--periodo", type=int, default=900, help="largo de cada franja de simulación, en segundos")
    ap.add_argument("--observado", help="CSV con velocidades observadas (ver formato en --help)")
    args = ap.parse_args()

    scen = ROOT / "scenarios" / args.scenario
    if not (scen / "cruce.sumocfg").exists():
        sys.exit(f"No existe {scen / 'cruce.sumocfg'}")
    out = ROOT / "results" / args.scenario
    out.mkdir(parents=True, exist_ok=True)
    xml = out / "edgedata.xml"

    obs = leer_observado(args.observado) if args.observado else {}  # validar el CSV antes de simular

    plan = (scen / "plan-real.add.xml").exists()
    dem = "demanda-real.rou.xml" in (scen / "cruce.sumocfg").read_text()
    print("Plan:", "REAL" if plan else "por defecto de netconvert (NO real)", "| Demanda:", "REAL" if dem else "aleatoria (NO calibrada)")
    simular(scen, args.periodo, xml)
    sim = agrupar_por_calle(sumolib.net.readNet(str(scen / "cruce.net.xml")), xml)
    if not sim:
        sys.exit("La simulación no produjo datos de velocidad.")

    destino = out / "validacion_sim.csv"
    filas, errores = [], []
    for (calle, t0), (v, seg) in sorted(sim.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        o = obs.get((calle, t0))
        fila = {"calle": calle, "t_inicio_s": int(t0), "vel_sim_kmh": round(v, 2), "vehiculo_segundos": round(seg)}
        if o is not None:
            fila.update(vel_obs_kmh=o, error_kmh=round(v - o, 2))
            errores.append(v - o)
        filas.append(fila)
    with open(destino, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["calle", "t_inicio_s", "vel_sim_kmh", "vehiculo_segundos", "vel_obs_kmh", "error_kmh"])
        w.writeheader()
        w.writerows(filas)

    print(f"\n{'calle':32} {'inicio_s':>8} {'sim km/h':>9} {'obs km/h':>9} {'error':>7}")
    for r in filas:
        print(f"{r['calle'][:32]:32} {r['t_inicio_s']:>8} {r['vel_sim_kmh']:>9.1f} "
              f"{r.get('vel_obs_kmh', ''):>9} {r.get('error_kmh', ''):>7}")
    print(f"\nEscrito: {destino}")
    if args.observado:
        sin_par = [k for k in obs if k not in sim]
        if errores:
            mae = sum(abs(e) for e in errores) / len(errores)
            sesgo = sum(errores) / len(errores)
            print(f"Comparadas {len(errores)} celdas. Error absoluto medio: {mae:.1f} km/h. Sesgo (sim - obs): {sesgo:+.1f} km/h")
        else:
            print("Ninguna fila del observado coincide con la simulación (revisar nombres de calle y t_inicio_s).")
        if sin_par:
            print(f"Sin par en la simulación ({len(sin_par)}): {sin_par[:5]}{' ...' if len(sin_par) > 5 else ''}")


if __name__ == "__main__":
    main()
