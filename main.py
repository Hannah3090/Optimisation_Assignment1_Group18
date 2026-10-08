"""
Entry point: load one question's data, build and solve the model, save results and figures.

    python main.py
    python main.py --question Q2_linear
    python main.py --question Q3_energy --scenarios --analysis energy_requirement
    python main.py --question Q3_battery --scenarios --analysis battery_capacity

Results (CSV, TXT, PNG) are written to results/<question>/.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

from src.data_loader import load_question, list_questions
from src.plotting import plot_duals, plot_inputs, plot_scenario_comparison, plot_schedule
from src.scenarios import scale_prices, scale_pv, set_tariffs, set_load_preferences # set_load_preferences is added!
from importlib import import_module

RESULTS_DIR = Path(__file__).resolve().parent / "results"

def run_base_case(question: str, out: Path, show: bool): 
    
    FlexibleConsumerModel, Results = load_model_class(question)

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
        print(f"Utility: " f"{results.meta['utility']:.2f} DKK")

    if results.meta["total_disutility"] is not None:
        print(f"Total Disutility: " f"{results.meta['total_disutility']:.2f} DKK")

    print(f"Objective value: " f"{results.objective:.2f} DKK")

    print("-----------------------------------------------------------------------")

    print(results.hourly.head()) 

    results.save(out)
    plot_schedule(results, data, save_to=out / "schedule.png")
    
    if question != "Q3_battery":
        plot_duals(results, data, save_to=out / "duals.png")

    if show:
        matplotlib.pyplot.show()
    return results

def get_scenarios(question: str, analysis: str, base):

    # ---------------- Q2(b) ----------------
    if question == "Q2_linear":

        if analysis == "linear_disutility":

            return {"cL_0.00": set_linear_disutility(base, 0.00),
                    "cL_0.20": set_linear_disutility(base, 0.20),
                    "cL_0.50": set_linear_disutility(base, 0.50),
                    "cL_0.80": set_linear_disutility(base, 0.80),
                    "cL_1.00": set_linear_disutility(base, 1.00),
                    "cL_1.43": set_linear_disutility(base, 1.43),
                    "cL_2.00": set_linear_disutility(base, 2.00),
                    "cL_2.50": set_linear_disutility(base, 2.50),
                    "cL_3.50": set_linear_disutility(base, 3.50),}
            
    # ---------------- Q2(c) ----------------
    elif question == "Q2_quadratic":

        if analysis == "quadratic_disutility":

            return {"cQ_0.01": set_quadratic_disutility(base, 0.01),
                   "cQ_0.05": set_quadratic_disutility(base, 0.05),
                   "cQ_0.10": set_quadratic_disutility(base, 0.10),
                   "cQ_0.25": set_quadratic_disutility(base, 0.25),
                   "cQ_0.50": set_quadratic_disutility(base, 0.50),
                   "cQ_1.00": set_quadratic_disutility(base, 1.00),
                   "cQ_2.00": set_quadratic_disutility(base, 2.00),
                   "cQ_5.00": set_quadratic_disutility(base, 5.00),
                   "cQ_10.00": set_quadratic_disutility(base, 10.00),
                   "cQ_20.00": set_quadratic_disutility(base, 20.00),
                   "cQ_50.00": set_quadratic_disutility(base, 50.00),}

    elif question == "Q3_energy":
    
        if analysis == "energy_requirement":

            return {"E20": set_load_preferences(base, min_daily_energy_kWh=20),
                    "E30": set_load_preferences(base, min_daily_energy_kWh=30),
                    "E40": set_load_preferences(base, min_daily_energy_kWh=40),
                    "E50": set_load_preferences(base, min_daily_energy_kWh=50),
                    "E60": set_load_preferences(base, min_daily_energy_kWh=60),}

        elif analysis == "price_spread":

            return {"half_spread": scale_prices(base, factor=0.5, keep_mean=True),
                    "base": base,
                     "double_spread": scale_prices(base, factor=2.0, keep_mean=True),}

    elif question == "Q3_battery":

        if analysis == "price_spread":

            return {"half_spread": scale_prices(base, factor=0.5, keep_mean=True),
                    "base": base,
                    "double_spread": scale_prices(base, factor=2.0, keep_mean=True),}

        elif analysis == "battery_capacity":

            return {"BatCap2": set_load_preferences(base, battery_capacity_kWh=2),
                    "base": base,
                    "BatCap8": set_load_preferences(base, battery_capacity_kWh=8),}

    return {}

def run_scenarios(question: str, analysis: str, out: Path):

    FlexibleConsumerModel, Results = load_model_class(question)
    base = load_question(question)
    scenarios = get_scenarios(question, analysis, base)

    if not scenarios:
        print(f"No sensitivity analysis defined for " f"question={question}, analysis={analysis}")
        return {}

    runs: dict[str, Results] = {}

    for name, data in scenarios.items():
        results = FlexibleConsumerModel(data).build().solve()
        results.save(out, tag=name)
        runs[name] = results

    plot_scenario_comparison(runs, "objective", save_to=out / f"{analysis}.png")
    return runs

def load_model_class(question: str):
    """
    Load the correct model implementation based on the question name dynamically!
    """
    model_map = {"Q1_caseA": "src.Q1.model",
                 "Q1_caseB": "src.Q1.model",
                 "Q2_linear": "src.Q2_linear.model",
                 "Q2_quadratic": "src.Q2_quadratic.model",
                 "Q3": "src.Q3.model",
                 "Q3_battery": "src.Q3g.model",}

    module = import_module(model_map[question])

    return module.FlexibleConsumerModel, module.Results

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--question", default="Q3_battery", choices=list_questions(), help="data case to use")

    parser.add_argument("--analysis", default=None, choices=["linear_disutility", "quadratic_disutility", "energy_requirement", "price_spread", "battery_capacity",], help="sensitivity analysis type")

    parser.add_argument("--scenarios", action="store_true", help="run sensitivity analysis scenarios")
    parser.add_argument("--show", action="store_true", help="open the figures in a window")

    args = parser.parse_args()

    if args.scenarios and args.analysis is None:
        parser.error("--analysis must be specified when using --scenarios")

    out = RESULTS_DIR / args.question
    out.mkdir(parents=True, exist_ok=True)

    if not args.show:
        matplotlib.use("Agg")

    base = run_base_case(args.question, out, args.show)

    if args.scenarios and base is not None:
        run_scenarios(args.question, args.analysis, out,)
     
    print(f"\nOutputs written to {out}")

if __name__ == "__main__":
    main()
