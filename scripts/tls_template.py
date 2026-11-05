"""Genera una PLANTILLA de plan semafórico para completar con tiempos reales.

Cuándo usarlo
    Cuando tengas tiempos de ciclo medidos (tarea 8) u oficiales (tarea 4) y quieras
    cargarlos en la simulación. La plantilla trae los `state` correctos de cada
    semáforo (cuáles carriles tienen verde en cada fase); vos solo cambiás las duraciones.

Uso (desde la raíz del repo, con el venv activado)
    python scripts/tls_template.py santa-fe-coronel-diaz
    python scripts/tls_template.py santa-fe-coronel-diaz --tls 437539849

Escribe scenarios/<nombre>/plan-real.plantilla.xml. Ese archivo NO se carga solo.
Cuando le pongas los tiempos reales y la fuente, renombralo a plan-real.add.xml:
desde ahí lo usan automáticamente la demo (baseline) y build_scenario.py.

Las duraciones que trae la plantilla son las inventadas por netconvert: hay que
reemplazarlas todas. Un plan con la duración por defecto NO debe llamarse "real".
"""
import argparse
import os
import sys
from pathlib import Path

import sumo

os.environ.setdefault("SUMO_HOME", sumo.SUMO_HOME)
os.environ.setdefault("PROJ_DATA", os.path.join(sumo.SUMO_HOME, "data", "proj"))
import sumolib  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scenario")
    ap.add_argument("--tls", action="append", help="id de semáforo (repetible); por defecto, todos los del escenario")
    ap.add_argument("--program-id", default="real", help="programID del plan (no puede ser 0, ya existe)")
    args = ap.parse_args()

    out = ROOT / "scenarios" / args.scenario
    net_file = out / "cruce.net.xml"
    if not net_file.exists():
        sys.exit(f"No existe {net_file}")
    net = sumolib.net.readNet(str(net_file), withPrograms=True)
    tls = [t for t in net.getTrafficLights() if not args.tls or t.getID() in args.tls]
    if not tls:
        sys.exit("No hay semáforos que coincidan.")

    lines = [
        "<!--",
        "  PLANTILLA. Completar antes de usar:",
        "  1) Reemplazar TODAS las duraciones por las medidas u oficiales (hoy son las de netconvert).",
        "  2) Anotar la fuente: quién midió o qué documento, fecha, franja horaria, cómo se midió.",
        "     Fuente: ",
        "     Fecha: ",
        "  3) Renombrar a plan-real.add.xml. Sin ese nombre no se carga.",
        "-->",
        "<additional>",
    ]
    for t in tls:
        prog = list(t.getPrograms().values())[0]
        lines.append(f'  <tlLogic id="{t.getID()}" type="static" programID="{args.program_id}" offset="0">')
        for ph in prog.getPhases():
            lines.append(f'    <phase duration="{ph.duration:g}" state="{ph.state}"/>')
        lines.append("  </tlLogic>")
    lines.append("</additional>")

    dest = out / "plan-real.plantilla.xml"
    dest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Plantilla escrita en {dest} ({len(tls)} semáforo(s))")


if __name__ == "__main__":
    main()
