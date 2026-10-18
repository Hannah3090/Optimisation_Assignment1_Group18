# =============================================================================
# 2.b.iv (Parametric Sweep over c_L)
# =============================================================================

# =============================================================================
# SEPARATE SCRIPT FOR QUESTION 2.b.iv (Parametric Sweep over c_L)
# =============================================================================

import gurobipy as gp
from gurobipy import GRB
import numpy as np
import pandas as pd
from src.data_loader import load_question
from src.model import FlexibleConsumerModel

# 1. Load baseline dataset
data = load_question("Q2_linear")

# 2. Define c_L sweep range (spanning low, medium, and high disutility regimes)
cL_range = [0.0, 0.2, 0.5, 0.8, 1.0, 1.43, 2.0, 2.5, 3.5]

results_list = []

for cL_val in cL_range:
  # Temporarily override linear disutility parameter
  data.linear_disutility = cL_val

  # Define optimization model for current c_L
  class ModelSweep(FlexibleConsumerModel):

    def build(self):
      d, m, T = self.data, self.m, self.T

      import_price = d.energy_price + d.import_tariff
      export_price = d.energy_price - d.export_tariff

      # Decision Variables
      self.var["load"] = m.addVars(
          T,
          lb=d.load_min_kWh,
          ub=d.load_max_kWh,
          vtype=GRB.CONTINUOUS,
          name="load",
      )
      self.var["import"] = m.addVars(
          T, lb=0.0, vtype=GRB.CONTINUOUS, name="import"
      )
      self.var["export"] = m.addVars(
          T, lb=0.0, vtype=GRB.CONTINUOUS, name="export"
      )
      self.var["pv"] = m.addVars(
          T, lb=0.0, ub=d.pv_available, vtype=GRB.CONTINUOUS, name="pv"
      )
      self.var["d"] = m.addVars(T, lb=0.0, vtype=GRB.CONTINUOUS, name="d")

      # Objective: Minimise Total Cost = Procurement Cost + Disutility Penalty
      obj_expr = gp.quicksum(
          import_price[t] * self.var["import"][t]
          - export_price[t] * self.var["export"][t]
          + d.linear_disutility * self.var["d"][t]
          for t in T
      )
      m.setObjective(obj_expr, GRB.MINIMIZE)

      # Constraints
      self.con["balance"] = m.addConstrs(
          (
              self.var["load"][t] + self.var["export"][t]
              == self.var["pv"][t] + self.var["import"][t]
              for t in T
          ),
          name="balance",
      )
      self.con["disut_pos"] = m.addConstrs(
          (
              self.var["load"][t] - self.var["d"][t] <= d.reference_load[t]
              for t in T
          ),
          name="disut_pos",
      )
      self.con["disut_neg"] = m.addConstrs(
          (
              -self.var["load"][t] - self.var["d"][t] <= -d.reference_load[t]
              for t in T
          ),
          name="disut_neg",
      )

      m.update()
      return self

  # Solve model
  model = ModelSweep(data).build()
  res = model.solve()

  # Extract solution arrays directly from model decision variables
  imp = np.array([model.var["import"][t].X for t in data.hours])
  exp = np.array([model.var["export"][t].X for t in data.hours])
  load = np.array([model.var["load"][t].X for t in data.hours])
  dev = np.array([model.var["d"][t].X for t in data.hours])

  import_price = data.energy_price + data.import_tariff
  export_price = data.energy_price - data.export_tariff

  # Compute requested metrics
  procurement_cost = np.sum(import_price * imp - export_price * exp)
  total_disutility_cost = cL_val * np.sum(dev)
  total_energy_consumed = np.sum(load)
  total_abs_deviation = np.sum(dev)

  # Hours where deviation bound is binding (d_t > 0)
  binding_hours = int(np.sum(dev > 1e-4))

  results_list.append({
      "cL [DKK/kWh]": cL_val,
      "Procurement Cost [DKK]": round(procurement_cost, 2),
      "Total Disutility [DKK]": round(total_disutility_cost, 2),
      "Total Objective [DKK]": round(
          procurement_cost + total_disutility_cost, 2
      ),
      "Daily Consumed [kWh]": round(total_energy_consumed, 2),
      "Abs Deviation [kWh]": round(total_abs_deviation, 2),
      "Binding Hours": binding_hours,
  })

# Convert to pandas DataFrame and output table
df_results = pd.DataFrame(results_list)

print("\n=== PARAMETRIC SWEEP RESULTS (Q2.b.iv) ===")
print(df_results.to_string(index=False))

# Save summary table to CSV
out_path = f"results/{data.question}/sweep_q2b_iv.csv"
df_results.to_csv(out_path, index=False)
print(f"\nResults successfully saved to {out_path}")
