"""Regenera un escenario de SUMO a partir de OpenStreetMap.

Cuándo usarlo
    - Querés recrear `scenarios/<nombre>/` desde cero (o verificar que es reproducible).
    - Querés un cruce o corredor nuevo: agregá una entrada en SCENARIOS y corré el script.
    - Querés cambiar la demanda (--period, --seed, --end) sin tocar la red.

Uso (desde la raíz del repo, con el venv activado)
    python scripts/build_scenario.py santa-fe-coronel-diaz
    python scripts/build_scenario.py santa-fe-coronel-diaz --period 2 --seed 7
    python scripts/build_scenario.py santa-fe-coronel-diaz --download   # vuelve a bajar OSM
    python scripts/build_scenario.py --list
    python scripts/build_scenario.py santa-fe-coronel-diaz --list-tls   # ids de semáforos del recorte

Pasos: (1) baja OSM con osmGet.py, solo si falta el archivo o se pide --download;
(2) netconvert recorta la zona y arma la red; (3) deja un solo semáforo (el que se
quiere estudiar) y desactiva el resto; (4) randomTrips genera la demanda;
(5) escribe el .sumocfg. Los pasos 2 a 5 no usan internet.

LIMITACIONES (importante para la investigación)
    - OSM no trae tiempos de semáforo: netconvert inventa un plan de tiempo fijo.
      NO es el plan real de la Ciudad. Reemplazarlo cuando haya datos oficiales o
      mediciones a mano (ver docs/integracion.md).
    - La demanda es aleatoria, no calibrada con conteos reales.
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

import sumo  # paquete pip `eclipse-sumo`

SUMO_HOME = sumo.SUMO_HOME
os.environ.setdefault("SUMO_HOME", SUMO_HOME)
os.environ.setdefault("PROJ_DATA", os.path.join(SUMO_HOME, "data", "proj"))

import sumolib  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TOOLS = Path(SUMO_HOME) / "tools"
PLAN_REAL = "plan-real.add.xml"
DEMANDA_REAL = "demanda-real.rou.xml"

# Para sumar un escenario: copiar una entrada y cambiar los datos.
#   bbox       : zona a descargar de OSM (lon_min, lat_min, lon_max, lat_max)
#   crop       : recorte de la red, más chico que bbox (mismo orden)
#   keep_tls   : lista de ids de los semáforos que se estudian (los demás se desactivan).
#                Un cruce = 1 id; un corredor = varios. Los ids se ven con --list-tls.
SCENARIOS = {
    "santa-fe-coronel-diaz": {
        "descripcion": "Av. Santa Fe x Av. Coronel Díaz (Palermo)",
        "bbox": (-58.4125, -34.5900, -58.4085, -34.5868),
        "crop": (-58.4113, -34.5898, -58.4089, -34.5882),
        "keep_tls": ["437539849"],
    },
}


def run(cmd, **kw):
    cmd = [str(c) for c in cmd]
    print("  $", " ".join(cmd))
    subprocess.run(cmd, check=True, **kw)


def netconvert(osm, out, cfg, unset=()):
    cmd = [
        sumolib.checkBinary("netconvert"), "--osm-files", osm, "-o", out,
        "--output.street-names", "--geometry.remove", "--roundabouts.guess",
        "--junctions.join", "--tls.join", "--tls.default-type", "static",
        "--remove-edges.isolated", "--keep-edges.by-vclass", "passenger",
        "--keep-edges.in-geo-boundary=" + ",".join(map(str, cfg["crop"])),
        "--no-warnings",
    ]
    if unset:
        cmd += ["--tls.unset", ",".join(unset)]
    run(cmd)


def build(name, args):
    cfg = SCENARIOS[name]
    out = Path(args.out_dir) if args.out_dir else ROOT / "scenarios" / name
    out.mkdir(parents=True, exist_ok=True)
    osm = out / "osm_bbox.osm.xml"
    net = out / "cruce.net.xml"

    print(f"[1/5] OSM: {cfg['descripcion']}")
    if args.download or not osm.exists():
        bbox = ",".join(map(str, cfg["bbox"]))
        # "=" es obligatorio: la longitud negativa se confunde con otra opción.
        run([sys.executable, TOOLS / "osmGet.py", f"--bbox={bbox}", "--prefix", "osm", "-d", out])
    else:
        print("  usando el archivo OSM existente (usar --download para bajarlo de nuevo)")

    print("[2/5] Red completa del recorte")
    netconvert(osm, net, cfg)

    print("[3/5] Dejar solo los semáforos elegidos (keep_tls)")
    keep = [cfg["keep_tls"]] if isinstance(cfg["keep_tls"], str) else list(cfg["keep_tls"])
    tls_ids = [t.getID() for t in sumolib.net.readNet(str(net)).getTrafficLights()]
    missing = [k for k in keep if k not in tls_ids]
    if missing:
        sys.exit(f"Semáforos {missing} no están en el recorte. Disponibles: {tls_ids} (ver --list-tls)")
    netconvert(osm, net, cfg, unset=[t for t in tls_ids if t not in keep])

    print("[4/5] Demanda")
    demanda_real = out / DEMANDA_REAL
    if demanda_real.exists():
        # Conteos reales: no se genera nada aleatorio. Este archivo tampoco se pisa.
        print(f"  usando {DEMANDA_REAL} (demanda real); se omite randomTrips")
        route_name = DEMANDA_REAL
    else:
        print("  demanda ALEATORIA con randomTrips (no calibrada)")
        run([
            sys.executable, TOOLS / "randomTrips.py", "-n", net, "-r", out / "cruce.rou.xml",
            "-o", out / "trips.trips.xml", "-e", args.end, "-p", args.period,
            "--fringe-factor", 10, "--min-distance", 100, "--seed", args.seed, "--validate",
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        route_name = "cruce.rou.xml"

    print("[5/5] .sumocfg")
    # Si existe plan-real.add.xml (tiempos medidos u oficiales) se carga solo.
    # Ese archivo NO lo genera este script ni se pisa al regenerar.
    plan = out / PLAN_REAL
    extra = f'    <additional-files value="{PLAN_REAL}"/>\n' if plan.exists() else ""
    (out / "cruce.sumocfg").write_text(
        '<configuration>\n  <input>\n    <net-file value="cruce.net.xml"/>\n'
        f'    <route-files value="{route_name}"/>\n{extra}  </input>\n'
        f'  <time><begin value="0"/><end value="{args.end}"/></time>\n</configuration>\n'
    )
    print("  plan real:", "cargado desde " + PLAN_REAL if plan.exists() else "no hay (se usa el plan por defecto de netconvert)")
    n = sumolib.net.readNet(str(net))
    print(f"Listo: {out}\n  calles: {len(n.getEdges())}, semáforos: {[t.getID() for t in n.getTrafficLights()]}")


def list_tls(name, args):
    """Muestra los semáforos del recorte (sin desactivar ninguno) para elegir keep_tls."""
    cfg = SCENARIOS[name]
    out = Path(args.out_dir) if args.out_dir else ROOT / "scenarios" / name
    osm = out / "osm_bbox.osm.xml"
    if not osm.exists():
        sys.exit(f"Falta {osm}. Correr primero: python scripts/build_scenario.py {name} --download")
    tmp = out / "_tmp_listar.net.xml"
    netconvert(osm, tmp, cfg)
    net = sumolib.net.readNet(str(tmp))
    for t in net.getTrafficLights():
        calles = sorted({c[0].getEdge().getName() for c in t.getConnections() if c[0].getEdge().getName()})
        print(f"{t.getID():>30}  conexiones: {len(t.getConnections()):2}  calles: {', '.join(calles)}")
    tmp.unlink()


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("scenario", nargs="?", help="nombre del escenario (ver --list)")
    p.add_argument("--list", action="store_true", help="listar escenarios definidos")
    p.add_argument("--list-tls", action="store_true", help="con un escenario: listar TODOS los semáforos del recorte, con sus calles, para elegir keep_tls")
    p.add_argument("--download", action="store_true", help="bajar OSM de nuevo aunque ya exista")
    p.add_argument("--period", type=float, default=3, help="segundos entre vehículos generados (menor = más tránsito)")
    p.add_argument("--end", type=int, default=3600, help="duración de la demanda en segundos")
    p.add_argument("--seed", type=int, default=42, help="semilla del generador aleatorio")
    p.add_argument("--out-dir", help="carpeta de salida (por defecto scenarios/<nombre>)")
    args = p.parse_args()

    if args.list or not args.scenario:
        for k, v in SCENARIOS.items():
            print(f"{k}: {v['descripcion']}")
        return
    if args.scenario not in SCENARIOS:
        sys.exit(f"Escenario desconocido: {args.scenario}. Usar --list.")
    if args.list_tls:
        list_tls(args.scenario, args)
        return
    build(args.scenario, args)


if __name__ == "__main__":
    main()
