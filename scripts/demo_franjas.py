"""Demo por franjas horarias: plan fijo vs. Q-learning con demanda escalada por el perfil horario.

Qué hace
    Para cada franja (madrugada, pico, valle, noche) genera una demanda con
    randomTrips cuyo caudal es proporcional al índice horario real de la zona
    (data/perfil_horario_zona_48Q3CH00.csv, semana 9-15/03/2020), entrena un
    Q-learning y lo compara con el plan fijo del escenario sobre una demanda
    NUEVA (otra semilla), para no evaluar sobre lo mismo que se entrenó.

Qué es real y qué es supuesto (se imprime también al correr)
    REAL      la red (OpenStreetMap) y la FORMA del tránsito a lo largo del día.
    SUPUESTO  el nivel de demanda: --base-period fija cada cuántos segundos entra
              un vehículo en la hora pico; el resto se escala con el índice.
    RELLENO   los tiempos del semáforo, salvo que exista plan-real.add.xml.
    => Los números son una PRUEBA TÉCNICA, no un hallazgo sobre la Ciudad.

Uso (desde la raíz del repo, con el venv activado)
    python scripts/demo_franjas.py
    python scripts/demo_franjas.py --episodes 10 --franjas pico valle
Salidas en results/franjas/ (o --salida): resumen.csv, evaluaciones.csv (una fila por demanda
    de evaluación) y aprendizaje.csv
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

import sumo  # paquete pip `eclipse-sumo`

os.environ.setdefault("SUMO_HOME", sumo.SUMO_HOME)
os.environ.setdefault("PROJ_DATA", os.path.join(sumo.SUMO_HOME, "data", "proj"))
sys.path.append(os.path.join(os.environ["SUMO_HOME"], "tools"))

import pandas as pd  # noqa: E402
from sumo_rl import SumoEnvironment  # noqa: E402
from sumo_rl.agents import QLAgent  # noqa: E402
from sumo_rl.exploration import EpsilonGreedy  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SCEN_DIR = ROOT / "scenarios"
PERFIL = ROOT / "data" / "perfil_horario_zona_48Q3CH00.csv"

# Hora del día (0-23) que representa a cada franja en el perfil horario
FRANJAS = {"madrugada": 4, "pico": 12, "valle": 17, "noche": 20}


def indices(columna):
    df = pd.read_csv(PERFIL).set_index("hora")
    return {f: float(df.loc[h, columna]) for f, h in FRANJAS.items()}


def gen_demanda(net, out_rou, period, seconds, seed):
    """Demanda aleatoria con randomTrips (misma configuración que build_scenario.py)."""
    trips = out_rou.with_suffix(".trips.xml")
    tools = Path(os.environ["SUMO_HOME"]) / "tools"
    subprocess.run(
        [sys.executable, str(tools / "randomTrips.py"), "-n", str(net), "-r", str(out_rou),
         "-o", str(trips), "-e", str(seconds), "-p", f"{period:.3f}", "--fringe-factor", "10",
         "--min-distance", "100", "--seed", str(seed), "--validate"],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    return sum(1 for ln in out_rou.read_text(encoding="utf-8").splitlines() if "<vehicle " in ln)


def make_env(args, route, out_csv, fixed):
    scen = SCEN_DIR / args.scenario
    plan = scen / "plan-real.add.xml"
    extra = ""
    if plan.exists() and not args.sin_plan_real:
        try:
            extra = f" -a {os.path.relpath(plan)}"
        except ValueError:
            extra = f" -a {plan}"
    return SumoEnvironment(
        net_file=str(scen / "cruce.net.xml"), route_file=str(route), out_csv_name=str(out_csv),
        use_gui=False, num_seconds=args.seconds, delta_time=5, yellow_time=3, min_green=5,
        fixed_ts=fixed, sumo_warnings=False, additional_sumo_cmd="--no-step-log true" + extra,
    )


def medias(csv_path):
    df = pd.read_csv(csv_path)
    return {"espera_media_s": df["system_mean_waiting_time"].mean(),
            "velocidad_media_ms": df["system_mean_speed"].mean(),
            "detenidos_medio": df["system_total_stopped"].mean()}


def run_fija(args, route, wd, tag=""):
    env = make_env(args, route, wd / f"fijo{tag}", fixed=True)
    env.reset()
    done = {"__all__": False}
    while not done["__all__"]:
        _, _, done, _ = env.step(action={})
    env.save_csv(str(wd / f"fijo{tag}"), 1)
    env.close()
    return medias(sorted(wd.glob(f"fijo{tag}_conn*_ep1.csv"))[-1])


def run_ql(args, route_train, routes_test, wd):
    """Entrena en route_train y evalúa sin explorar ni aprender en cada demanda de routes_test."""
    env = make_env(args, route_train, wd / "ql", fixed=False)
    agents, curva = None, []
    for ep in range(1, args.episodes + 1):
        obs = env.reset()
        if agents is None:
            agents = {ts: QLAgent(starting_state=env.encode(obs[ts], ts), state_space=env.observation_space,
                                  action_space=env.action_space, alpha=0.1, gamma=0.99,
                                  exploration_strategy=EpsilonGreedy(initial_epsilon=0.05, min_epsilon=0.005, decay=1.0))
                      for ts in env.ts_ids}
        else:
            for ts, a in agents.items():
                a.state = env.encode(obs[ts], ts)
        done = {"__all__": False}
        while not done["__all__"]:
            s, r, done, _ = env.step(action={ts: a.act() for ts, a in agents.items()})
            for ts in s:
                agents[ts].learn(next_state=env.encode(s[ts], ts), reward=r[ts])
        env.save_csv(str(wd / "ql"), ep)
        curva.append({"episodio": ep, **medias(sorted(wd.glob(f"ql_conn*_ep{ep}.csv"))[-1])})
    env.close()

    # Evaluación: política greedy, sin aprender, en demandas que no vio al entrenar
    evals = []
    for k, route_test in enumerate(routes_test):
        env = make_env(args, route_test, wd / f"ql_eval{k}", fixed=False)
        obs = env.reset()
        for ts, a in agents.items():
            a.exploration.epsilon = 0.0
            a.state = env.encode(obs[ts], ts)
        done = {"__all__": False}
        while not done["__all__"]:
            acts = {}
            for ts, a in agents.items():
                a.q_table.setdefault(a.state, [0] * a.action_space.n)  # estado no visto: acción 0
                acts[ts] = a.act()
            s, _, done, _ = env.step(action=acts)
            for ts in s:
                agents[ts].state = env.encode(s[ts], ts)
        env.save_csv(str(wd / f"ql_eval{k}"), 1)
        env.close()
        evals.append(medias(sorted(wd.glob(f"ql_eval{k}_conn*_ep1.csv"))[-1]))
    return evals, curva


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--scenario", default="santa-fe-coronel-diaz")
    p.add_argument("--franjas", nargs="+", default=list(FRANJAS), choices=list(FRANJAS))
    p.add_argument("--dia", default="habil", choices=["habil", "sabado", "domingo"], help="tipo de día del perfil")
    p.add_argument("--base-period", type=float, default=3.0,
                   help="SUPUESTO: segundos entre vehículos en la hora pico (el repo usa 3)")
    p.add_argument("--episodes", type=int, default=10, help="episodios de entrenamiento de Q-learning")
    p.add_argument("--seconds", type=int, default=3600, help="segundos simulados por episodio")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--eval-seeds", type=int, default=4, help="cantidad de demandas distintas de evaluación")
    p.add_argument("--salida", default="franjas", help="subcarpeta de results/ donde se guardan las salidas")
    p.add_argument("--sin-plan-real", action="store_true")
    args = p.parse_args()

    scen = SCEN_DIR / args.scenario
    idx = indices(f"{args.dia}_indice")
    out = ROOT / "results" / args.salida
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)

    plan_real = (scen / "plan-real.add.xml").exists() and not args.sin_plan_real
    print("== Qué es real y qué es supuesto ==")
    print("Red vial:", "REAL (OpenStreetMap)")
    print(f"Forma del tránsito: REAL pero de 2020 y a nivel zona ({args.dia}), índice por franja:", idx)
    print(f"Nivel de demanda: SUPUESTO (un vehículo cada {args.base_period:g} s en el pico)")
    print("Tiempos del semáforo:", "REALES (plan-real.add.xml)" if plan_real else "RELLENO de netconvert (NO es el real de la Ciudad)")
    print("Resultados: PRUEBA TÉCNICA, no un hallazgo.\n")

    filas, curvas, evrows = [], [], []
    for f in args.franjas:
        wd = out / f
        wd.mkdir()
        period = args.base_period / idx[f]
        net = scen / "cruce.net.xml"
        gen_demanda(net, wd / "train.rou.xml", period, args.seconds, args.seed)
        tests = []
        for k in range(args.eval_seeds):
            rt = wd / f"test{k}.rou.xml"
            n_te = gen_demanda(net, rt, period, args.seconds, args.seed + 1 + k)
            tests.append(rt)
        print(f"[{f}] índice {idx[f]:.2f} -> 1 vehículo cada {period:.1f} s (~{n_te} vehículos); {len(tests)} demandas de evaluación")
        fijas = [run_fija(args, rt, wd, tag=str(k)) for k, rt in enumerate(tests)]
        qls, curva = run_ql(args, wd / "train.rou.xml", tests, wd)
        for plan, ms in (("fijo", fijas), ("ql", qls)):
            d = pd.DataFrame(ms)
            fila = {"franja": f, "hora_ref": FRANJAS[f], "indice": idx[f], "veh_por_hora": round(3600 / period),
                    "plan": plan, "n_eval": len(ms)}
            for c in d.columns:
                fila[c] = round(d[c].mean(), 3)
                fila[c + "_desv"] = round(d[c].std(ddof=0), 3)
                fila[c + "_mediana"] = round(d[c].median(), 3)
            filas.append(fila)
            evrows += [{"franja": f, "plan": plan, "demanda_eval": k, **{c: round(v, 3) for c, v in m.items()}}
                       for k, m in enumerate(ms)]
        curvas += [{"franja": f, **c} for c in curva]
        mf, mq = pd.DataFrame(fijas)["espera_media_s"], pd.DataFrame(qls)["espera_media_s"]
        print(f"    espera media: fijo {mf.mean():.2f} s | ql {mq.mean():.2f} s (promedio de {len(tests)} demandas)\n")

    res = pd.DataFrame(filas)
    res.to_csv(out / "resumen.csv", index=False)
    pd.DataFrame(curvas).to_csv(out / "aprendizaje.csv", index=False)
    pd.DataFrame(evrows).to_csv(out / "evaluaciones.csv", index=False)
    print(res.to_string(index=False))
    print(f"\nGuardado en {out}")


if __name__ == "__main__":
    main()
