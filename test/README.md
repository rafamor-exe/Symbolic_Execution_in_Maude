# Test

---

## Concrete

Using the While language in While language are specified in `language-semantics/while-semantics-concrete.maude`, we can define a program $P$:

```
if iv('k) >= val(0) then { iv('res) := iv('k); }
else { iv('res) := - iv('k); }
```

To execute the program concretely for `'k := 0`, load the semantics in Maude:
```
maude <repo>/language-semantics/while-semantics-concrete.maude
```
and execute
```
search < if iv('k) >= val(0) then{iv('res) := iv('k) ;} else {iv('res) := - iv('k) ;} | 'k |->I 0 | RSTR:RStore | BSTR:BStore > =>! S:State .
```

---

## Symbolic execution

We can symbolically execute $P$ as shown in the main [Usage Section](../README.md#usage). Moreover, we can check that the absolute value is always positive by searching for a state where the value of `'res` violates the search condition (is strictly less than $0$), and checking that there is no solution. We can execute the command
```
python3 semantics-analysis-ext.py 
  --program "start(if (iv('k) >= val(0)) then { iv('res) := iv('k) ; } else {iv('res) := - iv('k) ;})" 
  --pattern "'<_|_>['P:Program, '_|_|_['_\`,_['_|->Is_[''res.Sort, 'RES:Integer], 'IS:IStoreS], 'RS:RStoreS, 'BS:BStoreS]]" 
  --file "language-semantics/while-semantics-concrete.maude" 
  --analysis "maude-se" 
  --sType "'*"
  --mod "upModule('WHILE-MAUDE, true)" 
  --stSort "'State" 
  --svars "(k, Integer)" 
  --sCond "'_<_['RES:Integer, '0.Integer] = 'true.Bool" 
  --solN 0
```

A more complex example could be a program $P_1$ with loops:

```
rv('y) := val(20); 
rv('i) := val(5); 
while rv('k) < rv('y) do {
  if rv('k) > val(10) then { 
    rv('z) := rv('y) / rv('i); 
  }
  rv('k) := rv('k) + val(1); 
  rv('i) := rv('i) - val(1); 
}
```
where `'k` is a symbolic variable. We want to find a buggy state where we have a division by $0$. So we search in the state space for a state where `'i == 0` to catch the bug. We can execute the following:

```
python3 semantics-analysis-ext.py 
    --program "start(rv('y) := val(20) ; rv('i) := val(5) ; while rv('k) < rv('y) do {if rv('k) > val(10) then {rv('z) := rv('y) / rv('i) ; } rv('k) := rv('k) + val(1) ; rv('i) := rv('i) - val(1) ;})" 
    --pattern "'<_|_>['__['_:=_;['RV1:RVar, '_/_['RExp1:RExp, 'rv[''i.Sort]]], 'Prest:Program], '_|_|_['ISTRSf:IStoreS, '_\`,_['_|->Rs_[''i.Sort, '0/1.Real], 'RSTRSf:RStoreS], 'BSTRSf:BStoreS]]" 
    --file "language-semantics/while-semantics-concrete.maude" 
    --analysis "maude-se" 
    --mod "upModule('WHILE-MAUDE, true)" 
    --stSort "'State" 
    --svars "(k, Real)"
    --sType "'*" --solN 0
```
The semantics are transformed, and the symbolic search uses the `metaSmtSearch` function from MaudeSE. The result is a state where the bug occurs.

---

## Concolic testing

We can execute $P$ with concolic testing as shown in the main [Usage Section](../README.md#usage).

Similarly to the previous example, we can use concolic testing to find bugs in complex programs. Consider a program $P_2$ that, at some point in execution, may end encounter a division by $0$. $P_2$ is presented as

```
iv('i) := val(5); 
while iv('k) < iv('y) do {
    if iv('k) > val(10) then {
        iv('x) := iv('k) * iv('y);
        iv('a) := iv('x) - iv('i);
        iv('z) := iv('y) / iv('a);
    }
    iv('k) := iv('k) + val(1); 
    iv('i) := iv('i) * val(2);
}
```
where variables `'k` and `'y` are symbolic. We can execute the program with

```
python3 semantics-analysis-ext.py 
  --program "start(iv('i) := val(5); while iv('k) < iv('y) do { if iv('k) > val(10) then {iv('x) := iv('k) * iv('y) ; iv('a) := iv('x) - iv('i); iv('z) := iv('y) / iv('a) ;} iv('k) := iv('k) + val(1) ; iv('i) := iv('i) * val(2) ;})" 
  --pattern "concolicState('State, '<_|_>['__['_:=_;['IV1:IVar, '_/_['IExp1:IExp, 'iv['IV:Qid]]], 'Prest:Program], '_|_|_['_\`,_['_|->I_['IV:Qid, '0.Zero], 'ISTRf:IStore], 'RSTRf:RStore, 'BSTRf:BStore]])" 
  --file "language-semantics/while-semantics-concrete.maude" 
  --analysis "concolic" 
  --mod "upModule('WHILE-MAUDE, true)" 
  --stSort "'State" 
  --svars "(k, Integer) ; (y, Integer)" 
  --sType "'*" --solN 0
```
The function `concolicState` is provided by the framework and generates a concolic state from the concrete state sort and the target pattern as a Maude term. This execution finds the bug with the initial assignment $\texttt{'k} \mapsto 9, \texttt{'y} \mapsto 20$ and after $7$ iterations of the loop.


We can use [maude_shell](https://github.com/ningit/maude-shell) to execute the same command over the transformed concolic module. First, we must select the transformed module with

```
select VERIFICATION-COMMANDS .
select transformModSymb(upModule('WHILE-MAUDE, true), 'State, conc) .
```

Then, we can use the ordinary Maude `search` command

```
search [1] startC(start(iv('i) := val(5); while iv('k) < iv('y) do { if iv('k) > val(10) then {iv('x) := iv('k) * iv('y) ; iv('a) := iv('x) - iv('i); iv('z) := iv('y) / iv('a) ;} iv('k) := iv('k) + val(1) ; iv('i) := iv('i) * val(2) ;}), ('k, k:Integer) ('y, y:Integer)) =>* [< IV1:IVar := IExp1:IExp / iv(IV:Qid) ; Pf:Program | (ISTRf:IStore, IV:Qid |->I 0) | RSTRf:RStore | BSTRf:BStore >][SMS:State {CST:Boolean}][SMSInit:State] .
```

## Symbolic execution via narrowing

Examples of symbolic execution with narrowing can be found in the [ad-hoc transformation file](../adhoc-analysis/narrowing-symexe.maude)
