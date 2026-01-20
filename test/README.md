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

We can symbolically execute $P$ as shown in the main [Usage Section](../README.md#usage).

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
We want to find a buggy state where we have a division by $0$. So we search in the state space for a state where `'i == 0` to catch the bug. We can execute the following:

```
python3 semantics-analysis-ext.py 
    --program "start(rv('y) := val(20) ; rv('i) := val(5) ; while rv('k) < rv('y) do {if rv('k) > val(10) then {rv('z) := rv('y) / rv('i) ; } rv('k) := rv('k) + val(1) ; rv('i) := rv('i) - val(1) ;})" 
    --pattern "'<_|_>['__['_:=_;['RV1:RVar, '_/_['RExp1:RExp, 'rv[''i.Sort]]], 'Prest:Program], '_|_|_['ISTRSf:IStoreS, '_\`,_['_|->Rs_[''i.Sort, '0/1.Real], 'RSTRSf:RStoreS], 'BSTRSf:BStoreS]]" 
    --file "language-semantics/while-semantics-concrete.maude" 
    --analysis "maude-se" 
    --modL "upModule('WHILE-MAUDE, true)" 
    --stSort "'State" 
    --svars "(k, Real)"
    --sType "'*" --solN 0
```
The semantics are transformed, and the symbolic search uses the `metaSmtSearch` function from MaudeSE. The result is a state where the bug occurs.

---

## Concolic testing
