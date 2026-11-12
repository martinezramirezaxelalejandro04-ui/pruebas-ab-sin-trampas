"""Command line for the A/B test kit.

    python -m abtest size --baseline 0.03 --lift 0.10
    python -m abtest test --a 120/4000 --b 151/4000
    python -m abtest simulate
"""
from __future__ import annotations

import argparse
from pathlib import Path

from . import charts, simulation
from .stats import compare, sample_size

OUTPUT = Path(__file__).resolve().parent.parent / "output"


def _fraction(text: str) -> tuple[int, int]:
    conversions, visitors = text.split("/")
    return int(conversions), int(visitors)


def main() -> None:
    parser = argparse.ArgumentParser(description="A/B tests without the usual traps")
    commands = parser.add_subparsers(dest="command", required=True)

    size = commands.add_parser("size", help="visitors needed per variant")
    size.add_argument("--baseline", type=float, required=True, help="e.g. 0.03 for 3%%")
    size.add_argument("--lift", type=float, required=True, help="e.g. 0.10 for +10%%")

    test = commands.add_parser("test", help="did B really beat A?")
    test.add_argument("--a", type=_fraction, required=True, help="conversions/visitors")
    test.add_argument("--b", type=_fraction, required=True, help="conversions/visitors")

    commands.add_parser("simulate", help="rebuild the reports and charts")
    arguments = parser.parse_args()

    if arguments.command == "size":
        needed = sample_size(arguments.baseline, arguments.lift)
        print(f"Necesitas {needed:,} visitantes en cada variante "
              f"({2 * needed:,} en total) antes de leer el resultado.")
    elif arguments.command == "test":
        result = compare(*arguments.a, *arguments.b)
        verdict = ("La diferencia es estadísticamente significativa."
                   if result["significant"]
                   else "No hay evidencia suficiente: la diferencia puede ser azar.")
        print(f"A: {result['rate_a']:.2%}   B: {result['rate_b']:.2%}   "
              f"cambio: {result['relative_lift']:+.1%}")
        print(f"Valor p: {result['p_value']:.3f}. {verdict}")
        print(f"Diferencia plausible: de {result['difference_low']:+.2%} "
              f"a {result['difference_high']:+.2%} (puntos porcentuales).")
    else:
        (OUTPUT / "charts").mkdir(parents=True, exist_ok=True)
        peeking = simulation.peeking()
        winners = simulation.exaggerated_winners()
        peeking.to_csv(OUTPUT / "peeking.csv", index=False, encoding="utf-8-sig")
        winners.to_csv(OUTPUT / "exaggerated_winners.csv", index=False)
        charts.peeking(peeking, OUTPUT / "charts" / "peeking.png")
        charts.exaggerated_winners(winners, OUTPUT / "charts" / "exaggerated_winners.png")
        print(peeking.to_string(index=False))
        print(winners.to_string(index=False))


if __name__ == "__main__":
    main()
