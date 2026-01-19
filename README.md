# Symbolic_Execution_in_Maude

> Framework for symbolic analysis and concolic testing of programs based on the semantics with Maude.

---

## 📌 Table of Contents
- [About](#about)
- [Installation](#installation)
- [Usage](#usage)

---

## 📖 About

This project provides a framework for symbolic analysis and concolic testing based on program semantics specified in [Maude](https://github.com/maude-lang/Maude). The framework transforms concrete program semantics into semantics ready for such analyses. After the transformation:

- Symbolic execution is performed with [MaudeSE](https://github.com/postechsv/maude-se).
- Concolic testing is performed with the transformed rules and a custom Python hook that connects with an SMT solver.

---

## 📦 Installation

Requires:
- Python >= 3.10
- [Maude Python library](https://github.com/fadoss/maude-bindings)
- MaudeSE (for symbolic execution)
- Z3 Python library

Download the framework with
```
git clone https://github.com/rafamor-exe/Symbolic_Execution_in_Maude
cd Symbolic_Execution_in_Maude
```

---

## ⚙️ Usage

The script `semantics-analysis-ext.py` is provided as a high-level interface for both analyses. It has several parameters that can be adjusted. The following command lists all parameters

```
python3 semantics-analysis-ext.py --help
```

Consider a program $P$ that calculates the absolute value:
```
if iv('k) >= val(0) then { iv('res) := iv('k); }
else { iv('res) := - iv('k); }
```
One can use the script to symbolically execute $P$ as
```
python3 semantics-analysis-ext.py 
    --program "start(if (iv('k) >= val(0)) then { iv('res) := iv('k) ; } 
                     else {iv('res) := - iv('k) ;})" 
    --pattern "'<_|_>['nil.Program, 'STR:Stores]" 
    --file "language-semantics/while-semantics-concrete.maude" 
    --analysis "maude-se" 
    --sType "'*" 
    --modL "upModule('WHILE-MAUDE, true)" --stSort "'State" 
    --svars "(k, Integer)" --solN 0
```
To perform concolic testing, simply change the `analysis` flag to `"concolic"` and the pattern to a concolic state. A concolic state constructor is provided given the state sort and a concrete state as a term, for example: `concolicState('State, '<_|_>['nil.Program, 'STR:Stores])`
```
python3 semantics-analysis-ext.py 
    --program "start(if (iv('k) >= val(0)) then { iv('res) := iv('k) ; } 
                     else {iv('res) := - iv('k) ;})" 
    --pattern "concolicState('State, '<_|_>['nil.Program, 'STR:Stores])" 
    --file "language-semantics/while-semantics-concrete.maude" 
    --analysis "concolic" 
    --sType "'*" 
    --modL "upModule('WHILE-MAUDE, true)" --stSort "'State" 
    --svars "(k, Integer)" --solN 0
```