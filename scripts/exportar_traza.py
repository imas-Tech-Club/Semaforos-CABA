"""Graba la simulación (plan fijo vs. Q-learning) para reproducirla en la página docs/demo/.

Qué hace
    Por cada franja: genera la demanda (igual que demo_franjas.py), entrena Q-learning y
    corre UNA evaluación de cada plan sobre la misma demanda nueva, grabando la posición
    de cada vehículo por segundo y el estado del semáforo. Escribe docs/demo/trazas.js
    (geometría de la red + trazas), que lee docs/demo/index.html sin servidor.

Real / supuesto / relleno: igual que demo_franjas.py (ver ese archivo y el README).
    Es una PRUEBA TÉCNICA: la demanda es supuesta y el plan fijo es de relleno.

Uso (desde la raíz del repo, con el venv activado)
    python scripts/exportar_traza.py
    python scripts/exportar_traza.py --franjas pico --episodes 10 --ventana 1200 480
"""
import argparse
import json
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import demo_franjas as df  # noqa: E402  (también define SUMO_HOME y el path de sumolib)
import sumolib  # noqa: E402

ROOT = df.ROOT


def geometria(net_path):
    net = sumolib.net.readNet(str(net_path), withInternal=False)
    tls = net.getTrafficLights()[0]
    carriles = []
    for e in net.getEdges():
        for ln in e.getLanes():
            carriles.append({"s": [[round(x, 1), round(y, 1)] for x, y in ln.getShape()], "w": ln.getWidth()})
    juncs = [[[round(x, 1), round(y, 1)] for x, y in n.getShape()] for n in net.getNodes() if n.getShape()]
    lineas = []  # una línea de detención por cada enlace controlado (índice = posición en el string de estado)
    for i, enlaces in sorted(tls.getLinks().items()):
        ln = enlaces[0][0]
        (x1, y1), (x2, y2) = ln.getShape()[-2], ln.getShape()[-1]
        lineas.append({"i": i, "p": [round(x2, 1), round(y2, 1)], "d": [round(x2 - x1, 2), round(y2 - y1, 2)], "w": ln.getWidth()})
    xmin, ymin, xmax, ymax = net.getBoundary()
    return tls.getID(), {"caja": [xmin, ymin, xmax, ymax], "carriles": carriles, "juncs": juncs, "lineas": lineas}


def grabar(fcd_xml, tls_xml, t0, dur):
    """Lee la salida de SUMO y la recorta a la ventana [t0, t0+dur)."""
    pasos = []
    for _, el in ET.iterparse(fcd_xml, events=("end",)):
        if el.tag != "timestep":
            continue
        t = float(el.get("time"))
        if t0 <= t < t0 + dur:
            fila = []
            for v in el.findall("vehicle"):
                fila += [round(float(v.get("x")) * 10), round(float(v.get("y")) * 10),
                         round(float(v.get("angle"))), round(float(v.get("speed")) * 10)]
            pasos.append(fila)
        el.clear()
    estados = [(float(e.get("time")), e.get("state")) for _, e in ET.iterparse(tls_xml) if e.tag == "tlsState"]
    previo = [s for t, s in estados if t <= t0]
    ini = previo[-1] if previo else estados[0][1]
    cambios, ult = [], ini
    for t, s in estados:
        if t0 < t < t0 + dur and s != ult:  # solo cuando cambia el estado
            cambios.append([round(t - t0, 1), s])
            ult = s
    return {"v": pasos, "tls0": ini, "tls": cambios}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--scenario", default="santa-fe-coronel-diaz")
    p.add_argument("--franjas", nargs="+", default=list(df.FRANJAS), choices=list(df.FRANJAS))
    p.add_argument("--base-period", type=float, default=3.0, help="SUPUESTO: segundos entre vehículos en la hora pico")
    p.add_argument("--episodes", type=int, default=10)
    p.add_argument("--seconds", type=int, default=3600)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--ventana", type=int, nargs=2, default=[1200, 480], metavar=("INICIO", "DURACION"),
                   help="segundos simulados que se graban (inicio y duración)")
    p.add_argument("--salida", default=str(ROOT / "docs" / "demo" / "trazas.js"))
    p.add_argument("--sin-plan-real", action="store_true")
    args = p.parse_args()

    scen = df.SCEN_DIR / args.scenario
    net = scen / "cruce.net.xml"
    tls_id, geo = geometria(net)
    idx = df.indices("habil_indice")
    plan = scen / "plan-real.add.xml"
    plan_real = plan.exists() and not args.sin_plan_real
    out = ROOT / "results" / "traza"
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    t0, dur = args.ventana

    datos = {"escenario": args.scenario, "semaforo": tls_id, "base_period_s": args.base_period,
             "plan_real": plan_real, "geo": geo, "franjas": {}}
    for f in args.franjas:
        wd = out / f
        wd.mkdir()
        period = args.base_period / idx[f]
        df.gen_demanda(net, wd / "train.rou.xml", period, args.seconds, args.seed)
        n_veh = df.gen_demanda(net, wd / "test.rou.xml", period, args.seconds, args.seed + 1)
        print(f"[{f}] índice {idx[f]:.2f} -> 1 vehículo cada {period:.1f} s (~{n_veh} vehículos)", flush=True)

        def extra(nombre):
            tls_add = wd / f"{nombre}.tls.add.xml"
            tls_add.write_text(
                f'<additional><timedEvent type="SaveTLSStates" source="{tls_id}" dest="{wd / (nombre + ".tls.xml")}"/></additional>')
            adds = f"{plan.resolve()},{tls_add}" if plan_real else str(tls_add)
            return f" -a {adds} --fcd-output {wd / (nombre + '.fcd.xml')}"

        # plan fijo (la política "fija" de SUMO-RL corre el plan que trae la red)
        env = df.make_env(args, wd / "test.rou.xml", wd / "fijo", fixed=True, extra_cmd=extra("fijo"))
        env.reset()
        done = {"__all__": False}
        while not done["__all__"]:
            _, _, done, _ = env.step(action={})
        env.save_csv(str(wd / "fijo"), 1)
        env.close()
        m_fijo = df.medias(sorted(wd.glob("fijo_conn*_ep1.csv"))[-1])

        agents, _ = df.entrenar(args, wd / "train.rou.xml", wd)
        m_ql = df.evaluar(args, agents, wd / "test.rou.xml", wd, 0, extra_cmd=extra("ql"))

        datos["franjas"][f] = {
            "hora_ref": df.FRANJAS[f], "indice": round(idx[f], 3), "veh_por_hora": round(3600 / period),
            "fijo": {**grabar(wd / "fijo.fcd.xml", wd / "fijo.tls.xml", t0, dur),
                     **{k: round(v, 3) for k, v in m_fijo.items()}},
            "ql": {**grabar(wd / "ql.fcd.xml", wd / "ql.tls.xml", t0, dur),
                   **{k: round(v, 3) for k, v in m_ql.items()}},
        }
        print(f"    espera media (hora completa): fijo {m_fijo['espera_media_s']:.2f} s | ql {m_ql['espera_media_s']:.2f} s", flush=True)

    datos["ventana"] = {"inicio_s": t0, "duracion_s": dur}
    dest = Path(args.salida)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("window.TRAZAS = " + json.dumps(datos, separators=(",", ":")) + ";\n", encoding="utf-8")
    print(f"Guardado {dest} ({dest.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
