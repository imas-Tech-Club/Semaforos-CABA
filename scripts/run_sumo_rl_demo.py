"""Demo de SUMO-RL con un solo cruce: semáforo de tiempo fijo vs. Q-learning.

Uso (desde la raíz del repo, con el venv activado):
    python scripts/run_sumo_rl_demo.py                 # fijo + Q-learning, sin GUI
    python scripts/run_sumo_rl_demo.py --gui           # abre sumo-gui
    python scripts/run_sumo_rl_demo.py --scenario santa-fe-coronel-diaz
    python scripts/run_sumo_rl_demo.py --episodes 10 --seconds 3600

Funciona igual en Windows y Linux/WSL: SUMO_HOME se define acá, antes de
importar sumo_rl (que lo exige).
"""
import argparse
import os
import sys
from pathlib import Path

import sumo  # paquete pip `eclipse-sumo`

# sumo_rl falla al importarse si SUMO_HOME no existe; el paquete pip no lo define.
os.environ.setdefault("SUMO_HOME", sumo.SUMO_HOME)
# Evita el aviso "Cannot find proj.db" de las herramientas de SUMO.
os.environ.setdefault("PROJ_DATA", os.path.join(sumo.SUMO_HOME, "data", "proj"))
sys.path.append(os.path.join(os.environ["SUMO_HOME"], "tools"))

import pandas as pd  # noqa: E402
from sumo_rl import SumoEnvironment  # noqa: E402
from sumo_rl.agents import QLAgent  # noqa: E402
from sumo_rl.exploration import EpsilonGreedy  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SCEN_DIR = ROOT / "scenarios"


def make_env(args, out_csv, fixed):
    scen = SCEN_DIR / args.scenario
    # Si el escenario tiene plan-real.add.xml (tiempos medidos/oficiales) se carga:
    # lo usa el baseline de tiempo fijo. El agente de RL arma sus propias fases.
    plan = scen / "plan-real.add.xml"
    # Conteos reales (demanda-real.rou.xml) reemplazan a la demanda aleatoria.
    route_name = "demanda-real.rou.xml" if (scen / "demanda-real.rou.xml").exists() and not args.sin_demanda_real else "cruce.rou.xml"
    extra = ""
    if plan.exists() and not args.sin_plan_real:
        # sumo-rl parte este texto por espacios: preferir ruta relativa (sin espacios).
        try:
            plan_arg = os.path.relpath(plan)
        except ValueError:  # Windows: otro disco
            plan_arg = str(plan)
        extra = f" -a {plan_arg}"
    return SumoEnvironment(
        net_file=str(scen / "cruce.net.xml"),
        route_file=str(scen / route_name),
        out_csv_name=str(out_csv),
        use_gui=args.gui,
        num_seconds=args.seconds,
        delta_time=5,
        yellow_time=3,
        min_green=5,
        fixed_ts=fixed,
        sumo_warnings=False,
        additional_sumo_cmd="--no-step-log true" + extra,
    )


def run_fixed(args):
    """Plan que trae la red (tiempo fijo). Es el baseline."""
    env = make_env(args, args.out / "fijo", fixed=True)
    env.reset()
    done = {"__all__": False}
    while not done["__all__"]:
        _, _, done, _ = env.step(action={})
    env.save_csv(str(args.out / "fijo"), 1)
    env.close()


def run_ql(args):
    """Q-learning independiente por semáforo (un solo cruce acá)."""
    env = make_env(args, args.out / "ql", fixed=False)
    agents = None
    for ep in range(1, args.episodes + 1):
        obs = env.reset()
        if agents is None:
            agents = {
                ts: QLAgent(
                    starting_state=env.encode(obs[ts], ts),
                    state_space=env.observation_space,
                    action_space=env.action_space,
                    alpha=0.1,
                    gamma=0.99,
                    exploration_strategy=EpsilonGreedy(initial_epsilon=0.05, min_epsilon=0.005, decay=1.0),
                )
                for ts in env.ts_ids
            }
        else:
            for ts, a in agents.items():
                a.state = env.encode(obs[ts], ts)
        done = {"__all__": False}
        while not done["__all__"]:
            actions = {ts: a.act() for ts, a in agents.items()}
            s, r, done, _ = env.step(action=actions)
            for ts in s:
                agents[ts].learn(next_state=env.encode(s[ts], ts), reward=r[ts])
        env.save_csv(str(args.out / "ql"), ep)
        print(f"  episodio {ep}/{args.episodes} listo")
    env.close()


def summarize(out):
    rows = []
    for name in ("fijo", "ql"):
        for f in sorted(out.glob(f"{name}_conn*_ep*.csv")):
            df = pd.read_csv(f)
            rows.append(
                {
                    "plan": name,
                    "archivo": f.name,
                    "espera_media_s": df["system_mean_waiting_time"].mean(),
                    "velocidad_media": df["system_mean_speed"].mean(),
                    "vehiculos_detenidos_medio": df["system_total_stopped"].mean(),
                }
            )
    if rows:
        print("\n" + pd.DataFrame(rows).round(2).to_string(index=False))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--scenario", default="cruce-sintetico", help="carpeta dentro de scenarios/ (cruce-sintetico, santa-fe-coronel-diaz)")
    p.add_argument("--sin-plan-real", action="store_true", help="ignorar plan-real.add.xml y usar el plan por defecto de la red")
    p.add_argument("--sin-demanda-real", action="store_true", help="ignorar demanda-real.rou.xml y usar la demanda aleatoria")
    p.add_argument("--gui", action="store_true", help="abrir sumo-gui")
    p.add_argument("--episodes", type=int, default=3, help="episodios de Q-learning")
    p.add_argument("--seconds", type=int, default=3600, help="segundos simulados por episodio")
    args = p.parse_args()
    args.out = ROOT / "results" / args.scenario

    args.out.mkdir(parents=True, exist_ok=True)
    for old in args.out.glob("*.csv"):
        old.unlink()
    plan_real = (SCEN_DIR / args.scenario / "plan-real.add.xml").exists() and not args.sin_plan_real
    print("Plan del baseline:", "REAL (plan-real.add.xml)" if plan_real else "por defecto de netconvert (NO es el real de la Ciudad)")
    dem_real = (SCEN_DIR / args.scenario / "demanda-real.rou.xml").exists() and not args.sin_demanda_real
    print("Demanda:", "REAL (demanda-real.rou.xml)" if dem_real else "aleatoria con randomTrips (NO calibrada)")
    print("Baseline (tiempo fijo)...")
    run_fixed(args)
    print("Q-learning...")
    run_ql(args)
    summarize(args.out)


if __name__ == "__main__":
    main()
