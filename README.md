# Active Distribution Network with Flexible Residential Consumers

This repository contains the implementation of the optimisation models developed for the assignment on active distribution networks and flexible residential consumers.

The project investigates the behaviour of a residential consumer equipped with:

- Flexible electrical load
- Rooftop photovoltaic (PV) generation
- Grid import/export capability
- Linear and quadratic consumer disutility models
- Minimum daily energy requirements
- Battery energy storage

All optimisation problems are formulated and solved using **Python** and **Gurobi**.

---

# Repository Structure

```text
.
├── data/
│   ├── params_Q1_caseA.json
│   ├── params_Q1_caseB.json
│   ├── params_Q2_linear.json
│   ├── params_Q2_quadratic.json
│   ├── params_Q2_nonseparable.json
│   ├── params_Q3.json
│   └── params_Q3_battery.json
│
├── results/
│
├── src/
│   ├── data_loader.py
│   ├── plotting.py
│   ├── scenarios.py
│   │
│   ├── Q1/
│   │   └── model.py
│   │
│   ├── Q2_linear/
│   │   └── model.py
│   │
│   ├── Q2_quadratic/
│   │   └── model.py
├── Q2_nonseparable/
│   └── model.py
│   │
│   ├── Q3/
│   │   └── model.py
│   │
│   └── Q3g/
│       └── model.py
│
├── .gitignore
├── LICENSE
├── README.md
├── environment.yaml
├── main.py
└── requirements.txt
```

---

# Before Running the Code

After downloading or cloning the repository, navigate to the project root directory:

```bash
cd <path-to-repository>
```

# Installation

## Option 1: Conda Environment

Create the environment from the provided file:

```bash
conda env create -f environment.yaml
conda activate 46750-a1
```

## Option 2: pip

```bash
pip install -r requirements.txt
```

---

# Solver

The optimisation models are implemented using **Gurobi**.

A valid Gurobi licence is required to run the models.

---

# Code Structure

The code is organised into four stages:

1. Data loading (`src/data_loader.py`)
2. Model construction (`src/ /model.py`)
3. Optimisation and result extraction
4. Plotting and result visualisation (`src/plotting.py`)

Each optimisation formulation is implemented in a separate directory:

```text
src/Q1/model.py
src/Q2_linear/model.py
src/Q2_quadratic/model.py
src/Q2_nonseparable/model.py
src/Q3/model.py
src/Q3g/model.py
```

Sensitivity analyses reuse the same optimisation model and only modify input parameters through functions defined in:

```text
src/scenarios.py

```
# Reproducing Results

All figures and tables presented in the report can be reproduced directly from the command line. Each run automatically creates the corresponding results directory if it does not already exist!

## Base Cases

### Question 1 Case A

```bash
python main.py --question Q1_caseA
```

### Question 1 Case B

```bash
python main.py --question Q1_caseB
```

### Question 2(b) Linear Disutility

```bash
python main.py --question Q2_linear
```

### Question 2(c) Quadratic Disutility

```bash
python main.py --question Q2_quadratic
```
### Question 2(e) Non-Separable Disutility

```bash
python main.py --question Q2_nonseparable
```

### Question 3(f) Minimum Daily Energy Requirement

```bash
python main.py --question Q3
```
### Question 3(g) Battery Model

```bash
python main.py --question Q3_battery
```

---

## Sensitivity Analyses

### Q2(b) Linear Disutility Sweep

```bash
python main.py --question Q2_linear --scenarios --analysis linear_disutility
```

--- 

Example:

```bash
results/Q1_caseA/
results/Q1_caseB/
results/Q2_linear/
results/Q2_quadratic/
results/Q2_nonseparable/
results/Q3/
results/Q3_battery/
```

Parameter varied:

- Linear disutility coefficient `cL` (DKK/kWh)

Metrics reported:

- Procurement cost
- Total disutility
- Objective value
- Daily energy consumed
- Absolute deviation

---
### Q2(c) Quadratic Disutility Sweep

```bash
python main.py --question Q2_quadratic --scenarios --analysis quadratic_disutility
```

Parameter varied:

- Quadratic disutility coefficient `cQ` (DKK/kWh²)

Metrics reported:

- Procurement cost
- Total disutility
- Objective value
- Daily energy consumed
- Absolute deviation

---
### Q2(e) Aggregated Disutility Sweep

```bash
python main.py --question Q2_quadratic --scenarios --analysis accum_disutility
```

Parameter varied:

-  Aggregated disutility coefficient `c_agg` (DKK/kWh²)

Metrics reported: 

- Procurement cost
- Total disutility
- Objective value
- Daily energy consumed
- Absolute deviation
- Number of binding hours

### Q3(f) Daily Energy Requirement Sweep

```bash
python main.py --question Q3 --scenarios --analysis energy_requirement
```

Parameter varied:

- Minimum daily energy requirement `E_min` (kWh)

### Q3(f) Price Spread Sweep

```bash
python main.py --question Q3 --scenarios --analysis price_spread
```

Parameter varied:

- Electricity price spread

---

### Q3(g) Battery Price Spread Sweep

```bash
python main.py --question Q3_battery --scenarios --analysis price_spread
```

Parameter varied:

- Electricity price spread

---

### Q3(g) Battery Capacity Sweep

```bash
python main.py --question Q3_battery --scenarios --analysis battery_capacity
```

Parameter varied:

- Battery energy capacity

---

# Outputs

Each optimization run generates:

- Optimal primal variables
- Objective value
- Procurement cost
- Utility/disutility values
- Grid imports and exports
- Load consumption
- PV generation
- Battery schedules (when applicable)
- Dual variables (where applicable)
- CSV result files
- Figures and plots

Outputs are automatically saved to:

```text
results/<question>/
```

---

# Main Packages

```text
gurobipy
numpy
pandas
matplotlib
```

Full environment specifications are available in:

```text
requirements.txt
```

and

```text
environment.yaml
```

---

# Model Overview

| Question | Formulation | Implementation |
|-----------|------------|----------------|
| Q1 Case A | Price-elastic consumer | `src/Q1/model.py` |
| Q1 Case B | Price-elastic consumer (different price regime) | `src/Q1/model.py` |
| Q2(b) | Linear disutility | `src/Q2_linear/model.py` |
| Q2(c) | Quadratic_disutility | `src/Q2_quadratic/model.py` |
| Q2(e) | Nonseparable_disutility | `src/Q2_nonseperable/model.py` |
| Q3(f) | Minimum daily energy requirement | `src/Q3/model.py` |
| Q3(g) | Battery storage model | `src/Q3g/model.py` |

----
# Notes

- Each optimisation formulation is implemented in a separate `model.py`.
- Sensitivity analyses do not use separate optimisation models. They repeatedly solve the same formulation with modified parameter values.
- The `main.py` script dynamically loads the correct optimisation model based on the --question argument.
- No manual modification of source files is required to run different questions or sensitivity analyses.
- All figures and tables in the report can be reproducedising the commands listed above.

---
Optimization in Modern Power Systems (46750) Assingment I [Technical University of Denmark (DTU)]
