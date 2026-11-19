"""Gráfico de plan fijo vs. Q-learning por franja horaria (lee results/franjas/resumen.csv).

Uso:  python scripts/graficar_franjas.py [--entrada results/franjas] [--salida docs/franjas_fijo_vs_ql.png]
"""
import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
# Paleta categórica validada (slots 1 y 2): azul = plan fijo, naranja = Q-learning
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e1"
COLOR = {"fijo": "#2a78d6", "ql": "#eb6834"}
NOMBRE = {"fijo": "Plan fijo (relleno de netconvert)", "ql": "Q-learning"}
ORDEN = ["madrugada", "pico", "valle", "noche"]
ETIQ = {"madrugada": "Madrugada\n(4 h)", "pico": "Pico\n(12 h)", "valle": "Valle de tarde\n(17 h)", "noche": "Noche\n(20 h)"}


def panel(ax, res, ev, col, titulo, unidad):
    franjas = [f for f in ORDEN if f in set(res["franja"])]
    w, gap = 0.36, 0.03
    med = res[col + "_mediana"] if col + "_mediana" in res else res[col]
    tope = med.max() * 1.45  # lo que pase de acá se marca con un triángulo y su valor
    for j, plan in enumerate(["fijo", "ql"]):
        d = res[res["plan"] == plan].set_index("franja").loc[franjas]
        altura = d[col + "_mediana"] if col + "_mediana" in d else d[col]
        xs = [i + (j - 0.5) * (w + gap) for i in range(len(franjas))]
        ax.bar(xs, altura, width=w, color=COLOR[plan], alpha=0.55, label=NOMBRE[plan], zorder=3)
        for x, f, v in zip(xs, franjas, altura):
            pts = ev[(ev["franja"] == f) & (ev["plan"] == plan)][col].tolist()
            techo = max([v] + [y for y in pts if y <= tope])  # la etiqueta va sobre el punto más alto
            ax.annotate(f"{v:.2f}".replace(".", ","), (x, techo), xytext=(0, 8), textcoords="offset points",
                        ha="center", va="bottom", fontsize=8.5, color=INK)
            for k, y in enumerate(pts):
                dx = (k - (len(pts) - 1) / 2) * 0.045
                if y > tope:
                    ax.plot(x + dx, tope * 0.97, marker="^", ms=8, color=COLOR[plan], mec=SURFACE, mew=1.5, zorder=6)
                    ax.annotate(f"{y:.0f}".replace(".", ","), (x + dx, tope * 0.97), xytext=(8, -3), textcoords="offset points",
                                fontsize=8, color=INK, fontweight="bold")
                else:
                    ax.plot(x + dx, y, marker="o", ms=5, color=COLOR[plan], mec=SURFACE, mew=1.5, zorder=5)
    ax.set_xticks(range(len(franjas)), [ETIQ[f] for f in franjas], color=INK2, fontsize=9)
    ax.set_title(titulo, loc="left", fontsize=11, color=INK, fontweight="bold")
    ax.set_ylabel(unidad, color=INK2, fontsize=9)
    ax.set_facecolor(SURFACE)
    ax.grid(axis="y", color=GRID, linewidth=0.8, zorder=0)
    ax.tick_params(colors=INK2, length=0)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.set_ylim(0, tope * 1.06)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--entrada", default=str(ROOT / "results" / "franjas"))
    p.add_argument("--salida", default=str(ROOT / "docs" / "franjas_fijo_vs_ql.png"))
    a = p.parse_args()
    df = pd.read_csv(Path(a.entrada) / "resumen.csv")
    ev = pd.read_csv(Path(a.entrada) / "evaluaciones.csv")
    n = int(df["n_eval"].iloc[0]) if "n_eval" in df else 1

    fig, axs = plt.subplots(1, 2, figsize=(11.5, 5.2), facecolor=SURFACE)
    panel(axs[0], df, ev, "espera_media_s", "Espera media de los vehículos", "segundos (menos es mejor)")
    panel(axs[1], df, ev, "detenidos_medio", "Vehículos detenidos en promedio", "vehículos (menos es mejor)")
    h, l = axs[0].get_legend_handles_labels()
    fig.legend(h, l, loc="upper left", ncol=2, frameon=False, fontsize=9, labelcolor=INK2, bbox_to_anchor=(0.006, 0.925))
    fig.suptitle("Plan fijo vs. Q-learning por franja horaria — Av. Santa Fe × Av. Coronel Díaz", x=0.012, y=0.985,
                 ha="left", fontsize=12.5, color=INK, fontweight="bold")
    fig.text(0.012, 0.015,
             "PRUEBA TÉCNICA. Forma del tránsito real (zona, marzo 2020); nivel de demanda SUPUESTO; tiempos del semáforo de RELLENO (no son los de la Ciudad).\n"
             f"Barras: mediana de {n} demandas de evaluación distintas; puntos: cada demanda. Triángulo ▲: valor fuera de escala (la política colapsó en esa demanda).\nQ-learning entrenado en otra demanda y evaluado sin explorar.",
             ha="left", va="bottom", fontsize=8, color=INK2)
    fig.tight_layout(rect=(0, 0.095, 1, 0.88))
    Path(a.salida).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(a.salida, dpi=160, facecolor=SURFACE)
    print("Guardado", a.salida)


if __name__ == "__main__":
    main()
