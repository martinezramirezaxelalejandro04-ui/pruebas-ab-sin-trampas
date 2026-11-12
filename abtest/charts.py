"""Charts for the README. Text in Spanish: the audience is small businesses in Mexico."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

SURFACE, INK, INK_SECONDARY, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, AXIS, BLUE, LIGHT_BLUE = "#e1e0d9", "#c3c2b7", "#2a78d6", "#9ec5f4"
SOURCE = "Simulación propia. Código y supuestos en el repositorio."


def _figure(title: str, subtitle: str, figsize=(8, 4.2)):
    fig, ax = plt.subplots(figsize=figsize, facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    height = figsize[1]
    fig.text(0.02, 1 - 0.22 / height, title, fontsize=13, fontweight="bold", color=INK, va="top")
    fig.text(0.02, 1 - 0.55 / height, subtitle, fontsize=9.5, color=INK_SECONDARY, va="top")
    fig.text(0.02, 0.12 / height, SOURCE, fontsize=8, color=MUTED, va="bottom")
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(AXIS)
    ax.tick_params(colors=MUTED, labelsize=9.5, length=0)
    ax.yaxis.set_visible(False)
    return fig, ax


def peeking(report: pd.DataFrame, path: Path) -> None:
    fig, ax = _figure(
        "Mirar la prueba antes de tiempo multiplica las falsas alarmas",
        "Pruebas donde A y B son idénticas y aun así se declara un ganador. "
        "Lo aceptable es 5%.",
    )
    labels = [f"{row.schedule}\n({row.looks} revisiones)" if row.looks > 1
              else f"{row.schedule}\n(1 revisión)" for row in report.itertuples()]
    bars = ax.bar(labels, report["false_alarm_pct"], width=0.55, color=BLUE)
    for bar, value in zip(bars, report["false_alarm_pct"]):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 0.6, f"{value:.0f}%",
                ha="center", fontsize=11, color=INK)
    ax.axhline(5, color=MUTED, linewidth=1, linestyle=(0, (4, 3)))
    ax.text(2.42, 5.6, "5% aceptable", fontsize=8.5, color=MUTED, ha="right")
    ax.set_ylim(0, report["false_alarm_pct"].max() * 1.2)
    fig.subplots_adjust(left=0.04, right=0.97, top=0.74, bottom=0.20)
    fig.savefig(path, dpi=160, facecolor=SURFACE)
    plt.close(fig)


def exaggerated_winners(report: pd.DataFrame, path: Path) -> None:
    true_lift = report["true_lift_pct"].iloc[0]
    fig, ax = _figure(
        "Con pocos visitantes, las pruebas que \"ganan\" exageran la mejora",
        f"Mejora que reportan las pruebas ganadoras. Línea punteada: la mejora real, "
        f"{true_lift:.0f}%.",
    )
    labels = [f"{row.share_of_needed_visitors_pct}% de los\nvisitantes necesarios"
              for row in report.itertuples()]
    colors = [LIGHT_BLUE if share < 100 else BLUE
              for share in report["share_of_needed_visitors_pct"]]
    bars = ax.bar(labels, report["lift_reported_by_winners_pct"], width=0.55, color=colors)
    for bar, row in zip(bars, report.itertuples()):
        ax.text(bar.get_x() + bar.get_width() / 2, row.lift_reported_by_winners_pct + 0.8,
                f"+{row.lift_reported_by_winners_pct:.0f}%", ha="center", fontsize=11, color=INK)
    ax.axhline(true_lift, color=MUTED, linewidth=1, linestyle=(0, (4, 3)))
    ax.set_ylim(0, report["lift_reported_by_winners_pct"].max() * 1.2)
    fig.subplots_adjust(left=0.04, right=0.97, top=0.74, bottom=0.20)
    fig.savefig(path, dpi=160, facecolor=SURFACE)
    plt.close(fig)
