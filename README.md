# Active Distribution Network with Flexible Residential Consumers

This repository contains the implementation and analysis of the optimisation models developed for the assignment on active distribution networks with flexible residential consumers.

The project investigates the decision-making process of a residential consumer equipped with:

- A flexible electrical load
- Rooftop photovoltaic (PV) generation
- Grid import/export capability
- Different consumer preference models
- A minimum daily energy requirement
- A battery energy storage system

The optimisation models are implemented in Python using Gurobi.

---

# Repository Structure

```text
project/
│
├── README.md
├── requirements.txt
├── main.py
│
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
│   │
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
└── figures/
```

---

# Assignment Structure

## Question 1

### Q1 Case A

Price-elastic load model with:

- Constant marginal utility
- Cheap PV generation
- Grid import/export
- Hourly optimisation

Implemented in:

```text
src/Q1/model.py
```

Run with:

```bash
python main.py --question Q1_caseA
```

---

### Q1 Case B

Same formulation as Case A, but with expensive PV generation.

Implemented in:

```text
src/Q1/model.py
```

Run with:

```bash
python main.py --question Q1_caseB
```

---

## Question 2(b)

### Linear Disutility Model

Consumer preferences are represented through:

\[
D_t = c^L \lvert L_t - \ell_t^{ref}\rvert
\]

The model is reformulated as a linear program using an auxiliary deviation variable.

Implemented in:

```text
src/Q2_linear/model.py
```

Run the base case:

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

Reported metrics:

- Procurement cost
- Total disutility
- Objective value
- Daily energy consumed
- Absolute deviation
- Number of binding hours

---

## Question 2(c)

### Quadratic Disutility Model

Consumer preferences represented through:

\[
D_t = c^Q (L_t-\ell_t^{ref})^2
\]

The resulting optimisation problem is a convex quadratic program.

Implemented in:

```text
src/Q2_quadratic/model.py
```

Run the base case:

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

Reported metrics:

- Procurement cost
- Total disutility
- Objective value
- Daily energy consumed
- Absolute deviation
- Number of binding hours

---

## Question 3(f)

### Minimum Daily Energy Requirement

Based on the quadratic disutility model with the additional constraint:

\[
\sum_t L_t \geq E^{min}
\]

Implemented in:

```text
src/Q3_energy/model.py
```

Run the base case:

```bash
python main.py --question Q3
```

---

### Sensitivity Analysis 1: Energy Requirement

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

### Sensitivity Analysis 2: Price Spread

Price volatility is modified while keeping the daily mean constant.

Run:

```bash
python main.py --question Q3 --scenarios --analysis price_spread
```

---

## Question 3(g)

### Battery Energy Storage System

Extends Question 3 with:

- Battery charging
- Battery discharging
- State-of-charge dynamics
- Battery power limits
- Battery energy capacity
- Charging/discharging efficiencies

Implemented in:

```text
src/Q3g/model.py
```

Run the base case:

```bash
python main.py --question Q3_battery
```

---

### Sensitivity Analysis 1: Price Spread

Investigates the impact of electricity price volatility on battery value.

Run:

```bash
python main.py --question Q3_battery --scenarios --analysis price_spread
```

---

### Sensitivity Analysis 2: Battery Capacity

Battery capacities tested:

```text
2 kWh
Base case
8 kWh
```

Run:

```bash
python main.py --question Q3_battery --scenarios --analysis battery_capacity
```

---

# Outputs

For every model run, the code produces:

- Optimal primal variables
- Objective value
- Procurement cost
- Utility or disutility value
- Grid imports
- Grid exports
- Load consumption
- PV production
- Dual variables (where applicable)
- CSV results
- Summary files
- PNG figures

Results are stored in:

```text
results/<question>/
```

---

# Dependencies

Main libraries:

```text
gurobipy
numpy
pandas
matplotlib
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# Notes

- Each optimisation formulation is implemented in a separate folder.
- Every optimisation model is contained in a file named `model.py`.
- Sensitivity analyses do **not** use different optimisation formulations; they repeatedly solve the same model with modified parameter values.
- Models are loaded dynamically through `main.py`.

---

Course Assignment

Technical University of Denmark (DTU)

Active Distribution Networks and Flexible Consumption
