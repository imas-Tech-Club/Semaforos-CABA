"""Demo de SUMO-RL con un solo cruce: semáforo de tiempo fijo vs. Q-learning.

Uso (desde la raíz del repo, con el venv activado):
    python scripts/run_sumo_rl_demo.py                 # fijo + Q-learning, sin GUI
    python scripts/run_sumo_rl_demo.py --gui           # abre sumo-gui
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
sys.path.append(os.path.join(os.environ["SUMO_HOME"], "tools"))

import pandas as pd  # noqa: E402
from sumo_rl import SumoEnvironment  # noqa: E402
from sumo_rl.agents import QLAgent  # noqa: E402
from sumo_rl.exploration import EpsilonGreedy  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SCEN = ROOT / "scenarios" / "cruce-sintetico"
OUT = ROOT / "results" / "demo"


def make_env(args, out_csv, fixed):
    return SumoEnvironment(
        net_file=str(SCEN / "cruce.net.xml"),
        route_file=str(SCEN / "cruce.rou.xml"),
        out_csv_name=str(out_csv),
        use_gui=args.gui,
        num_seconds=args.seconds,
        delta_time=5,
        yellow_time=3,
        min_green=5,
        fixed_ts=fixed,
        sumo_warnings=False,
        additional_sumo_cmd="--no-step-log true",
    )


def run_fixed(args):
    """Plan que trae la red (tiempo fijo). Es el baseline."""
    env = make_env(args, OUT / "fijo", fixed=True)
    env.reset()
    done = {"__all__": False}
    while not done["__all__"]:
        _, _, done, _ = env.step(action={})
    env.save_csv(str(OUT / "fijo"), 1)
    env.close()


def run_ql(args):
    """Q-learning independiente por semáforo (un solo cruce acá)."""
    env = make_env(args, OUT / "ql", fixed=False)
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
        env.save_csv(str(OUT / "ql"), ep)
        print(f"  episodio {ep}/{args.episodes} listo")
    env.close()


def summarize():
    rows = []
    for name in ("fijo", "ql"):
        for f in sorted(OUT.glob(f"{name}_conn*_ep*.csv")):
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
    p.add_argument("--gui", action="store_true", help="abrir sumo-gui")
    p.add_argument("--episodes", type=int, default=3, help="episodios de Q-learning")
    p.add_argument("--seconds", type=int, default=3600, help="segundos simulados por episodio")
    args = p.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.csv"):
        old.unlink()
    print("Baseline (tiempo fijo)...")
    run_fixed(args)
    print("Q-learning...")
    run_ql(args)
    summarize()


if __name__ == "__main__":
    main()
