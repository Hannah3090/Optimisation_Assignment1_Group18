"""Entry point: load one question's data, build and solve the model, save results and figures.

    python main.py                          # base case of Q1_caseA
    python main.py --question Q2_linear     # another case
    python main.py --scenarios              # also run the example sensitivity scenarios

Results (CSV, TXT, PNG) are written to ``results/<question>/``. Extend ``run_scenarios``
with your own scenarios, or add a new function per question, as your analysis grows.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

from src.data_loader import load_question, list_questions
from src.model import FlexibleConsumerModel, Results
from src.plotting import plot_duals, plot_inputs, plot_scenario_comparison, plot_schedule
from src.scenarios import scale_prices, scale_pv, set_tariffs, set_load_preferences # set_load_preferences is added!

RESULTS_DIR = Path(__file__).resolve().parent / "results"

def run_base_case(question: str, out: Path, show: bool) -> Results | None:
    data = load_question(question)
    print(data.summary(), "\n")
    plot_inputs(data, save_to=out / "inputs.png")

    model = FlexibleConsumerModel(data).build()
    try:
        results = model.solve()
    except NotImplementedError as e:
        print(f"[skipped] {e}")
        return None

    print(results, "\n")

    # print summary of results!!
    print("-----------------------------------------------------------------------")

    print(f"Procurement cost: " f"{results.meta['procurement_cost']:.2f} DKK")

    if results.meta["utility"] is not None:
        print(f"Utility: " f"{results.meta['utility']:.2f} DKKK")

    if results.meta["total_disutility"] is not None:
        print(f"Total Disutility: " f"{results.meta['total_disutility']:.2f} DKK")

    print(f"Objective value: " f"{results.objective:.2f} DKK")

    print("-----------------------------------------------------------------------")

    print(results.hourly.head()) 

    results.save(out)
    plot_schedule(results, data, save_to=out / "schedule.png")
    plot_duals(results, data, save_to=out / "duals.png")
    if show:
        matplotlib.pyplot.show()
    return results

def run_scenarios(question: str, out: Path) -> dict[str, Results]:
    """Example sensitivity analysis. Replace with the scenarios you design in Question 1.g."""
    base = load_question(question)

    # scenarios = {"base": base, "flat_prices": scale_prices(base, factor=0.0, keep_mean=True), "double_spread": scale_prices(base, factor=2.0, keep_mean=True), "no_tariffs": set_tariffs(base, import_tariff=0.0, export_tariff=0.0), "no_pv": scale_pv(base, factor=0.0),}

    # added for Q3(f) sensitivity analysis_1
    #scenarios = {"E20": set_load_preferences(base, min_daily_energy_kWh=20), "E30": set_load_preferences(base, min_daily_energy_kWh=30), "E40": set_load_preferences(base, min_daily_energy_kWh=40), "E50": set_load_preferences(base, min_daily_energy_kWh=50), "E60": set_load_preferences(base, min_daily_energy_kWh=60),}
    
    # added for Q3(f) sensitivity analysis_2
    scenarios = {"half_spread": scale_prices(base, factor=0.5, keep_mean=True), "base": base, "double_spread": scale_prices(base, factor=2.0, keep_mean=True),}

    runs: dict[str, Results] = {}
    for name, data in scenarios.items():
        results = FlexibleConsumerModel(data).build().solve()
        results.save(out, tag=name)
        runs[name] = results
        #print(f"{name:>14}: cost {results.objective:8.2f} DKK | import {results.hourly['import'].sum():5.1f} kWh"
              #f" | export {results.hourly['export'].sum():5.1f} kWh")
        print(f"{name:>14}: " f"objective={results.objective:8.2f} DKK | " f"procurement={results.meta['procurement_cost']:8.2f} DKK | " f"disutility={results.meta['total_disutility']:8.2f} DKK | "
              f"load={results.hourly['load'].sum():6.2f} kWh | " f"import={results.hourly['import'].sum():6.2f} kWh | " f"export={results.hourly['export'].sum():6.2f} kWh")
    plot_scenario_comparison(runs, "objective", save_to=out / "scenarios_cost.png")
    return runs

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--question", default="Q3", choices=list_questions(), help="data case to use")
    parser.add_argument("--scenarios", action="store_true", help="also run the example sensitivity scenarios")
    parser.add_argument("--show", action="store_true", help="open the figures in a window")
    args = parser.parse_args()

    out = RESULTS_DIR / args.question
    out.mkdir(parents=True, exist_ok=True)
    if not args.show:
        matplotlib.use("Agg")

    base = run_base_case(args.question, out, args.show)

    #if args.scenarios and base is not None:
        #run_scenarios(args.question, out)
    
    #Changed for Q3(f) sensitivity analysis 
    if base is not None:
        run_scenarios(args.question, out)   
    print(f"\nOutputs written to {out}")

if __name__ == "__main__":
    main()
