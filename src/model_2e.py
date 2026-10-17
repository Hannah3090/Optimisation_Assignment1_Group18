"""Optimisation model of a single flexible consumer with non-separable 
cumulative state disutility (Question 2e), implemented with gurobipy.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import gurobipy as gp
import numpy as np
import pandas as pd
from gurobipy import GRB

from .data_loader import InputData


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

    def build(self) -> "FlexibleConsumerModel":
        d, m, T = self.data, self.m, self.T
        c_Q, c_accum, c_L = self.c_Q, self.c_accum, self.c_L

        # --- Decision variables ---
        self.var["import"] = m.addVars(T, lb=0.0, vtype=GRB.CONTINUOUS, name="import")
        self.var["export"] = m.addVars(T, lb=0.0, vtype=GRB.CONTINUOUS, name="export")
        self.var["load"]   = m.addVars(T, lb=-GRB.INFINITY, vtype=GRB.CONTINUOUS, name="load")
        self.var["pv"]     = m.addVars(T, lb=0.0, vtype=GRB.CONTINUOUS, name="pv")

        self.var["load_abs"] = m.addVars(T, lb=0.0, vtype=GRB.CONTINUOUS, name="load_abs")
        self.var["S"]        = m.addVars(T, lb=-GRB.INFINITY, ub=GRB.INFINITY, vtype=GRB.CONTINUOUS, name="S")
        self.var["S_abs"]    = m.addVars(T, lb=0.0, vtype=GRB.CONTINUOUS, name="S_abs")

        # --- Objective ---
        m.setObjective(
            gp.quicksum(
                c_Q * (self.var["load"][t] - d.reference_load[t])**2
                + c_accum * self.var["S_abs"][t]
                + c_L * self.var["load_abs"][t]
                + (d.energy_price[t] + d.import_tariff) * self.var["import"][t] 
                - (d.energy_price[t] - d.export_tariff) * self.var["export"][t]
                - d.pv_marginal_cost * self.var["pv"][t]
                for t in T
            ),
            GRB.MINIMIZE
        )

        # --- Constraints ---
        self.con["balance"] = m.addConstrs(
            (self.var["load"][t] + self.var["export"][t] - self.var["pv"][t] - self.var["import"][t] == 0 for t in T),
            name="balance"
        )
        self.con["load_abs_1"] = m.addConstrs((self.var["load_abs"][t] >= self.var["load"][t] - d.reference_load[t] for t in T), name="load_abs_1")
        self.con["load_abs_2"] = m.addConstrs((self.var["load_abs"][t] >= -(self.var["load"][t] - d.reference_load[t]) for t in T), name="load_abs_2")

        self.con["load_min"] = m.addConstrs((d.load_min_kWh - self.var["load"][t] <= 0 for t in T), name="load_min")
        self.con["load_max"] = m.addConstrs((self.var["load"][t] - d.load_max_kWh <= 0 for t in T), name="load_max")

        self.con["pv_min"] = m.addConstrs((-self.var["pv"][t] <= 0 for t in T), name="pv_min")
        self.con["pv_max"] = m.addConstrs((self.var["pv"][t] - d.pv_available[t] <= 0 for t in T), name="pv_max")

        def state_rule(m, t):
            if t == 0:
                return self.var["S"][t] == self.var["load"][t] - d.reference_load[t]
            else:
                return self.var["S"][t] == self.var["S"][t-1] + (self.var["load"][t] - d.reference_load[t])

        self.con["state_dynamics"] = m.addConstrs((state_rule(m, t) for t in T), name="state_dynamics")
        self.con["s_abs_1"] = m.addConstrs((self.var["S_abs"][t] >= self.var["S"][t] for t in T), name="s_abs_1")
        self.con["s_abs_2"] = m.addConstrs((self.var["S_abs"][t] >= -self.var["S"][t] for t in T), name="s_abs_2")

        m.update()
        return self

    def solve(self) -> Results:
        m = self.m
        m.update()
        m.optimize()
        
        status = "OPTIMAL" if m.Status == GRB.OPTIMAL else f"STATUS_{m.Status}"
        if m.Status != GRB.OPTIMAL:
            raise RuntimeError(f"Optimisation ended with status {status}.")
            
        return self._extract_results(status)

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

        # Calculate metrics required for main.py print output
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
