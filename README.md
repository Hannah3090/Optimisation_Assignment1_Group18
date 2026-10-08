# Active Distribution Network with Flexible Residential Consumers

This repository contains the implementation of the optimisation models developed for the assignment on active distribution networks and flexible residential consumers.

The project investigates the behaviour of a residential consumer equipped with:

- Flexible electrical load
- Rooftop photovoltaic (PV) generation
- Grid import/export capability
- Alternative comfort/disutility models
- Minimum daily energy requirements
- Battery energy storage

All optimisation problems are implemented in Python using Gurobi.

---

# Repository Structure

```text
.
├── data/
│   ├── params_Q1_caseA.json
│   ├── params_Q1_caseB.json
│   ├── params_Q2_linear.json
│   ├── params_Q2_quadratic.json
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
│   │
│   ├── Q3_energy/
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
└──requirements.txt

```

---

# Installation

## Option 1: Conda Environment (Recommended)

Create the environment from the provided file:

```bash
conda env create -f environment.yaml
conda activate <environment-name>
```

## Option 2: pip

```bash
pip install -r requirements.txt
```

---

# Solver

The optimisation models are implemented using **Gurobi**.

A valid Gurobi licence is required to solve the optimisation problems.

---

# Questions and Models

## Question 1

### Case A

Price-elastic consumer model with low PV marginal cost.

Implementation:

```text
src/Q1/model.py
```

Run:

```bash
python main.py --question Q1_caseA
```

### Case B

Same formulation as Case A with different PV economics.

Implementation:

```text
src/Q1/model.py
```

Run:

```bash
python main.py --question Q1_caseB
```

---

## Question 2(b): Linear Disutility

Disutility represented by:

\[
D_t = c^L |L_t - \ell_t^{ref}|
\]

Implementation:

```text
src/Q2_linear/model.py
```

Run base case:

```bash
python main.py --question Q2_linear
```

---

### Sensitivity Analysis: Linear Disutility

Parameter varied:

\[
c^L
\]

Sweep values:

```text
0.00
0.20
0.50
0.80
1.00
1.43
2.00
2.50
3.50
```

Run:

```bash
python main.py --question Q2_linear --scenarios --analysis linear_disutility
```

Metrics reported:

- Procurement cost
- Total disutility
- Objective value
- Daily energy consumed
- Absolute deviation
- Number of binding hours

---

## Question 2(c): Quadratic Disutility

Disutility represented by:

\[
D_t = c^Q(L_t-\ell_t^{ref})^2
\]

Implementation:

```text
src/Q2_quadratic/model.py
```

Run base case:

```bash
python main.py --question Q2_quadratic
```

---

### Sensitivity Analysis: Quadratic Disutility

Parameter varied:

\[
c^Q
\]

Sweep values:

```text
0.01
0.05
0.10
0.25
0.50
1.00
2.00
5.00
10.00
20.00
50.00
```

Run:

```bash
python main.py --question Q2_quadratic --scenarios --analysis quadratic_disutility
```

Metrics reported:

- Procurement cost
- Total disutility
- Objective value
- Daily energy consumed
- Absolute deviation

---

## Question 3(f): Minimum Daily Energy Requirement

Quadratic disutility model with an additional minimum daily energy requirement:

\[
\sum_t L_t \ge E^{min}
\]

Implementation:

```text
src/Q3_energy/model.py
```

Run base case:

```bash
python main.py --question Q3
```

---

### Sensitivity Analysis: Daily Energy Requirement

Parameter varied:

\[
E^{min}
\]

Sweep values:

```text
20 kWh
30 kWh
40 kWh
50 kWh
60 kWh
```

Run:

```bash
python main.py --question Q3 --scenarios --analysis energy_requirement
```

---

### Sensitivity Analysis: Electricity Price Spread

Run:

```bash
python main.py --question Q3 --scenarios --analysis price_spread
```

---

## Question 3(g): Battery Storage

Extension of Question 3 with battery storage.

Additional features:

- State of charge dynamics
- Charging/discharging efficiencies
- Energy capacity limits
- Charging/discharging power limits

Implementation:

```text
src/Q3g/model.py
```

Run base case:

```bash
python main.py --question Q3_battery
```

---

### Sensitivity Analysis: Price Spread

Run:

```bash
python main.py --question Q3_battery --scenarios --analysis price_spread
```

---

### Sensitivity Analysis: Battery Capacity

Battery capacities investigated:

```text
2 kWh
Base Case
8 kWh
```

Run:

```bash
python main.py --question Q3_battery --scenarios --analysis battery_capacity
```

---

# Outputs

For each optimisation run, the code generates:

- Optimal primal variables
- Objective value
- Procurement cost
- Utility / disutility values
- Grid imports and exports
- Load consumption
- PV generation
- Dual variables (where applicable)
- Figures (.png)
- Hourly result tables (.csv)

All outputs are written automatically to:

```text
results/<question>/
```

---

# Notes

- Each optimisation formulation is implemented in its own folder.
- Every formulation uses a file named `model.py`.
- Sensitivity analyses reuse the corresponding model and only modify input parameters.
- Models are selected automatically by `main.py` through dynamic imports.

---

DTU – Optimization in Modern Power Systems Assignment I
