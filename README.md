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
├── main.py
├── README.md
├── requirements.txt
├── environment.yaml
├── LICENSE
└── .gitignore
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

A valid Gurobi licence is required to run the models.

---

# Code Structure

The code is organised into four stages:

1. Data loading (`src/data_loader.py`)
2. Model construction (`src/*/model.py`)
3. Optimisation*and result extraction
4. Plotting *nd result visualisation (`src/plot*ing.py`)

Each optimisation*formulation is implemented in a se*arate directory:

```text
src/Q1/m*del.py
src/Q2_linear/model.py
src/*2_quadratic/model.py
src/Q3_energy*model.py
src/Q3g/model.py
```

Sen*itivity analyses reuse the same op*imisation model and only modify in*ut parameters through functions de*ined in:

```text
src/scenarios.py*```

---

# Reproducing Results

A*l figures and tables presented in *he report can be reproduced direct*y from the command line.

## Base *ases

### Question 1 Case A

```ba*h
python main.py --question Q1_cas*A
```

### Question 1 Case B

```b*sh
python main.py --question Q1_ca*eB
```

### Question 2(b) Linear D*sutility

```bash
python main.py -*question Q2_linear
```

### Questi*n 2(c) Quadratic Disutility

```ba*h
python main.py --question Q2_qua*ratic
```

### Question 3(f) Minim*m Daily Energy Requirement

```bas*
python main.py --question Q3
```
*### Question 3(g) Battery Model

`*`bash
python main.py --question Q3*battery
```

---

## Sensitivity A*alyses

### Q2(b) Linear Disutilit* Sweep

```bash
python main.py --q*estion Q2_linear --scenarios --ana*ysis linear_disutility
```

Parame*er varied:

\[
c^L
\]

Metrics rep*rted:

- Procurement cost
- Total *isutility
- Objective value
- Dail* energy consumed
- Absolute deviat*on
- Number of binding hours

---
*### Q2(c) Quadratic Disutility Swe*p

```bash
python main.py --questi*n Q2_quadratic --scenarios --analy*is quadratic_disutility
```

Param*ter varied:

\[
c^Q
\]

Metrics re*orted:

- Procurement cost
- Total*disutility
- Objective value
- Dai*y energy consumed
- Absolute devia*ion
- Number of binding hours

---*
### Q3(f) Daily Energy Requiremen* Sweep

```bash
python main.py --q*estion Q3 --scenarios --analysis e*ergy_requirement
```

Parameter va*ied:

\[
E^{min}
\]

---

### Q3(f* Price Spread Sweep

```bash
pytho* main.py --question Q3 --scenarios*--analysis price_spread
```

Param*ter varied:

- Electricity price s*read

---

### Q3(g) Battery Price*Spread Sweep

```bash
python main.*y --question Q3_battery --scenario* --analysis price_spread
```

Para*eter varied:

- Electricity price *pread

---

### Q3(g) Battery Capa*ity Sweep

```bash
python main.py *-question Q3_battery --scenarios -*analysis battery_capacity
```

Par*meter varied:

- Battery energy ca*acity

---

# Outputs

Each optimi*ation run generates:

- Optimal pr*mal variables
- Objective value
- *rocurement cost
- Utility/disutili*y values
- Grid imports and export*
- Load consumption
- PV generatio*
- Battery schedules (when applica*le)
- Dual variables (where applic*ble)
- CSV result files
- Figures *nd plots

Outputs are automaticall* saved to:

```text
results/<quest*on>/
```

---

# Main Packages

``*text
gurobipy
numpy
pandas
matplot*ib
```

Full environment specifica*ions are available in:

```text
re*uirements.txt
```

and

```text
en*ironment.yaml
```

---

# Model Ov*rview

| Question | Formulation | *mplementation |
|-----------|-----*------|----------------|
| Q1 Case*A | Price-elastic consumer | `src/*1/model.py` |
| Q1 Case B | Price-*lastic consumer (different price r*gime) | `src/Q1/model.py` |
| Q2(b* | Linear disutility | `src/Q2_lin*ar/model.py` |
| Q2(c) | Quadratic*disutility | `src/Q2_quadratic/mod*l.py` |
| Q3(f) | Minimum daily en*rgy requirement | `src/Q3_energy/m*del.py` |
| Q3(g) | Battery storag* model | `src/Q3g/model.py` |

---*
# Notes

- Each optimisation form*lation is implemented in a separat* `model.py`.
- Sensitivity analyse* do not use separate optimisation *odels. They repeatedly solve the s*me formulation with modified param*ter values.
- Dynamic model select*on is handled automatically throug* `main.py`.
- All figures and tabl*s in the report can be reproduced *sing the commands listed above.

---
Optimization in Modern Power Systems (46750) Assingment I [Technical University of Denmark (DTU)]
