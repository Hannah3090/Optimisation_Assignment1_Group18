"""Optimisation model of a single flexible consumer with non-separable 
cumulative state disutility (Question 2e), implemented with gurobipy.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import gurobipy as gp
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from gurobipy import GRB

from src.data_loader import InputData, load_question
from src.plotting import plot_schedule


@dataclass
class Results:
    """Primal and dual solution of one model run."""

    question: str
    status: str
    objective: float
    hourly: pd.DataFrame
    duals: dict[str, float] = field(default_factory=dict)
    meta: dict = field(default_factory=dict)

    def save(self, folder: Path | str, tag: str = "") -> None:
        """Write hourly data to CSV and scalar values to a text summary file."""
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        stem = f"{self.question}{'_' + tag if tag else ''}"
        self.hourly.to_csv(folder / f"{stem}_hourly.csv", index_label="hour")
        with open(folder / f"{stem}_summary.txt", "w", encoding="utf-8") as f:
            f.write(f"status   : {self.status}\nobjective : {self.objective:.4f} DKK\n")
            for k, v in self.meta.items():
                if v is not None:
                    f.write(f"{k} : {v:.4f}\n")
            for k, v in self.duals.items():
                f.write(f"dual[{k}] : {v:.4f}\n")

    def __str__(self) -> str:
        cols = [c for c in self.hourly.columns if not c.startswith("dual_")]
        return (
            f"status: {self.status} | objective: {self.objective:.2f} DKK\n"
            f"daily totals (kWh): " + ", ".join(f"{c}={self.hourly[c].sum():.1f}" for c in cols if c in ("import", "export", "load", "pv", "S", "S_abs"))
        )


def _dual(c) -> float:
    """Dual value of a linear (Pi) or quadratic (QCPi) constraint."""
    return c.QCPi if isinstance(c, gp.QConstr) else c.Pi


class FlexibleConsumerModel:
    """Consumption problem with quadratic hourly disutility and cumulative state penalties (Question 2e)."""

    def __init__(
        self, 
        data: InputData, 
        name: str = "flexible_consumer_nonseparable", 
        verbose: bool = False
    ):
        self.data = data
        self.T = range(data.n_hours)
        
        # Read coefficients from data object, falling back to defaults if not set by scenarios
        self.c_Q = getattr(data, "quadratic_disutility", 0.5)
        self.c_accum = getattr(data, "accum_disutility", 0.25)
        self.c_L = getattr(data, "linear_disutility", 0.0)

        self.m = gp.Model(name)
        self.m.Params.OutputFlag = 1 if verbose else 0
        self.m.Params.QCPDual = 1
        self.var: dict[str, gp.tupledict | gp.Var] = {}
        self.con: dict[str, gp.tupledict | gp.Constr] = {}

    # ------------------------------------------------------------------ 2. build
    def build(self) -> "FlexibleConsumerModel":
        d, m, T = self.data, self.m, self.T
        c_Q, c_accum, c_L = self.c_Q, self.c_accum, self.c_L

        # --- Decision variables ---
        self.var["import"] = m.addVars(T, lb=0.0, vtype=GRB.CONTINUOUS, name="import")
        self.var["export"] = m.addVars(T, lb=0.0, vtype=GRB.CONTINUOUS, name="export")
        self.var["load"]   = m.addVars(T, lb=-GRB.INFINITY, vtype=GRB.CONTINUOUS, name="load")
        self.var["pv"]     = m.addVars(T, lb=0.0, vtype=GRB.CONTINUOUS, name="pv")

        self.var["load_abs"] = m.addVars(T, lb=0.0, vtype=GRB.CONTINUOUS, name="load_abs")

        # Cumulative state variables and absolute value linearization
        self.var["S"]        = m.addVars(T, lb=-GRB.INFINITY, ub=GRB.INFINITY, vtype=GRB.CONTINUOUS, name="S")
        self.var["S_abs"]    = m.addVars(T, lb=0.0, vtype=GRB.CONTINUOUS, name="S_abs")

        # --- Objective ---
        m.setObjective(
            gp.quicksum(
                # 1. Quadratic hourly disutility
                c_Q * (self.var["load"][t] - d.reference_load[t])**2
                # 2. Cumulative state penalty (absolute accumulated drift/deficit)
                + c_accum * self.var["S_abs"][t]
                # 3. Linear hourly disutility
                + c_L * self.var["load_abs"][t]
                # 4. Financial procurement and generation costs
                + (d.energy_price[t] + d.import_tariff) * self.var["import"][t] 
                - (d.energy_price[t] - d.export_tariff) * self.var["export"][t]
                - d.pv_marginal_cost * self.var["pv"][t]
                for t in T
            ),
            GRB.MINIMIZE
        )

        # --- Constraints ---
        # 1. Hourly Energy Balance
        self.con["balance"] = m.addConstrs(
            (self.var["load"][t] + self.var["export"][t] - self.var["pv"][t] - self.var["import"][t] == 0 for t in T),
            name="balance"
        )
        self.con["load_abs_1"] = m.addConstrs(
            (self.var["load_abs"][t] >= self.var["load"][t] - d.reference_load[t] for t in T), 
            name="load_abs_1"
        )
        self.con["load_abs_2"] = m.addConstrs(
            (self.var["load_abs"][t] >= -(self.var["load"][t] - d.reference_load[t]) for t in T), 
            name="load_abs_2"
        )

        # 2. Load Bounds
        self.con["load_min"] = m.addConstrs((d.load_min_kWh - self.var["load"][t] <= 0 for t in T), name="load_min")
        self.con["load_max"] = m.addConstrs((self.var["load"][t] - d.load_max_kWh <= 0 for t in T), name="load_max")

        # 3. PV Bounds
        self.con["pv_min"] = m.addConstrs((-self.var["pv"][t] <= 0 for t in T), name="pv_min")
        self.con["pv_max"] = m.addConstrs((self.var["pv"][t] - d.pv_available[t] <= 0 for t in T), name="pv_max")

        # 4. State Accumulation Dynamics
        def state_rule(m, t):
            if t == 0:
                return self.var["S"][t] == self.var["load"][t] - d.reference_load[t]
            else:
                return self.var["S"][t] == self.var["S"][t-1] + (self.var["load"][t] - d.reference_load[t])

        self.con["state_dynamics"] = m.addConstrs((state_rule(m, t) for t in T), name="state_dynamics")

        # 5. Absolute Value Linearization for S[t]
        self.con["s_abs_1"] = m.addConstrs((self.var["S_abs"][t] >= self.var["S"][t] for t in T), name="s_abs_1")
        self.con["s_abs_2"] = m.addConstrs((self.var["S_abs"][t] >= -self.var["S"][t] for t in T), name="s_abs_2")

        m.update()
        return self

    # ------------------------------------------------------------------ 3. solve
    def solve(self) -> Results:
        m = self.m
        m.update()
        m.optimize()
        
        status = "OPTIMAL" if m.Status == GRB.OPTIMAL else f"STATUS_{m.Status}"
        if m.Status != GRB.OPTIMAL:
            raise RuntimeError(f"Optimisation ended with status {status}.")
            
        return self._extract_results(status)

    # --------------------------------------------------------------- extraction
    def _extract_results(self, status: str) -> Results:
        d, T = self.data, list(self.T)
        hourly = pd.DataFrame(index=pd.Index(T, name="hour"))
        hourly["price"] = d.energy_price
        hourly["pv_available"] = d.pv_available
        if d.reference_load is not None:
            hourly["reference_load"] = d.reference_load

        for name, v in self.var.items():
            if isinstance(v, gp.tupledict) and len(v) == len(T):
                hourly[name] = [v[t].X for t in T]

        procurement_cost = sum(
            (d.energy_price[t] + d.import_tariff) * hourly.loc[t, "import"] -
            (d.energy_price[t] - d.export_tariff) * hourly.loc[t, "export"] -
            d.pv_marginal_cost * hourly.loc[t, "pv"]
            for t in T
        )
        
        quad_dis = self.c_Q * ((hourly["load"] - d.reference_load) ** 2).sum()
        accum_dis = self.c_accum * hourly["S_abs"].sum()
        lin_dis = self.c_L * hourly["load_abs"].sum()
        total_disutility = quad_dis + accum_dis + lin_dis

        meta = {
            "procurement_cost": procurement_cost,
            "utility": None,
            "total_disutility": total_disutility,
        }

        duals: dict[str, float] = {}
        for name, c in self.con.items():
            try:
                if isinstance(c, gp.tupledict):
                    hourly[f"dual_{name}"] = [_dual(c[t]) for t in T]
                else:
                    duals[name] = _dual(c)
            except (AttributeError, gp.GurobiError):
                pass

        return Results(
            question=d.question,
            status=status,
            objective=self.m.ObjVal,
            hourly=hourly,
            duals=duals,
            meta=meta,
        )


def run_price_experiment(question: str = "Q2_quadratic", out_dir: str = "results/Q2_nonseparable_experiment", show: bool = False) -> None:
    """Run the price structure experiment comparing alternating vs. persistent prices."""
    data = load_question(question)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    
    print(f"--- Running Price Structure Experiment ({question}) ---")
    
    base_prices = data.energy_price.copy()
    mean_price = np.mean(base_prices)
    T_hours = range(data.n_hours)

    delta = 0.75
    profile_a = np.array([mean_price + delta if (t // 2) % 2 == 0 else mean_price - delta for t in T_hours])
    half_t = data.n_hours // 2
    profile_b = np.array([mean_price - delta if t < half_t else mean_price + delta for t in T_hours])

    experiments = [
        ("Alternating_Profile_A", profile_a),
        ("Persistent_Profile_B", profile_b)
    ]

    summary_records = []

    for name, price_profile in experiments:
        print(f"Solving model under {name}...")
        data.energy_price = price_profile

        model = FlexibleConsumerModel(data, verbose=False).build()
        res = model.solve()
        res.save(out, tag=name)

        df = res.hourly
        procurement_cost = sum(
            (price_profile[t] + data.import_tariff) * df.loc[t, "import"] -
            (price_profile[t] - data.export_tariff) * df.loc[t, "export"] -
            data.pv_marginal_cost * df.loc[t, "pv"]
            for t in T_hours
        )

        total_disutility = res.meta.get("total_disutility", 0.0)
        binding_hours = int(
            ((df["load"] - data.load_min_kWh).abs() < 1e-4).sum() +
            ((df["load"] - data.load_max_kWh).abs() < 1e-4).sum()
        )

        summary_records.append({
            "Price_Profile": name,
            "Procurement Cost (DKK)": round(procurement_cost, 2),
            "Total Disutility (DKK)": round(total_disutility, 2),
            "Total Objective (DKK)": round(res.objective, 2),
            "Daily Energy Consumed (kWh)": round(df["load"].sum(), 2),
            "Abs. Deviation (kWh)": round(df["S_abs"].sum(), 2),
            "Binding Hours": binding_hours
        })

        plot_schedule(res, data, save_to=str(out / f"schedule_{name.lower()}.png"))
        plt.close()

    summary_df = pd.DataFrame(summary_records)
    summary_df.to_csv(out / "price_experiment_summary.csv", index=False)
    print("\n--- Price Experiment Summary ---")
    print(summary_df.to_string(index=False))
    print(f"\nAll experiment files saved to: {out}")
    if show:
        plt.show()
