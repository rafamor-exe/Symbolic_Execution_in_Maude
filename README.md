# Symbolic_Execution_in_Maude

> Framework for symbolic analysis and concolic testing of programs based on the semantics with Maude.

---

## Table of Contents
- [About](#about)
- [Structure](#structure)
- [Installation](#installation)
- [Usage](#usage)

---

## About

This project provides a framework for symbolic analysis and concolic testing based on program semantics specified in [Maude](https://github.com/maude-lang/Maude). The framework transforms concrete program semantics into semantics ready for such analyses. After the transformation:

- Symbolic execution is performed with [MaudeSE](https://github.com/postechsv/maude-se).
- Concolic testing is performed with the transformed rules and a custom Python hook that connects with an SMT solver.

In both cases, the execution is performed by the subsequent application of semantic rules, represented by rewrite rules.

The framework provides the arithmetic for Boolean, integer, and real-valued expressions including literals and variables. In addition, it includes evaluation functions (`eval`) that transform those expressions in ordinary Maude types `Bool`, `Int`, and `Rat` to symbolic types `Boolean`, `Integer`, and `Real` from the Maude SMT library.

---

## Structure

```text
Symbolic_Execution_in_Maude/
├── semantics-basics/           # Framework basics
├── language-semantics/         # Semantics examples
├── test/                       # Tests and commands
├── adhoc-analysis/             # Ad-hoc implementations (e.g. narrowing)
├── README.md
├── maudeSMTHook.py             # Custom Python SMT Maude hook for concolic
├── semantics-analysis-ext.py   # High-level execution script
└── semantics-analysis-tr.maude # Semantics metalevel transformer
```

---

## Installation

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

## Usage

Import module `CONCRETE-FW` from `semantics-basics/semantics-basics-maudeTypes.maude` in the target semantics system module. Construct the concrete semantics with the expressions provided (`BExp`, `IExp`, and `RExp`), and use `eval` functions to evaluate them. `eval` functions can be used as rule conditions to explore symbolic paths during execution. There are semantics examples that already implement this in the `language-semantics/` directory.

The script `semantics-analysis-ext.py` is provided as a high-level interface for both analyses. It has several parameters that can be adjusted. The following command lists all parameters

```
python3 semantics-analysis-ext.py --help
```

As an example, the semantics of a simple While language are specified in `language-semantics/while-semantics-concrete.maude`. Consider a program $P$ that calculates the absolute value:
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