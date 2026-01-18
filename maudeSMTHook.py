
import maude
from z3 import *
import re

class SMTAssignmentHook (maude.Hook):

    def __init__(self):
        super().__init__()
        self.solver = None
        self.module = None
        self.trueT = None
        self.falseT = None
        self.op_conv = {
                        "not_": lambda a: Not(self.toZ3(a)),
                        "_<_": lambda a, b: self.toZ3(a) < self.toZ3(b),
                        "_>_": lambda a, b: self.toZ3(a) > self.toZ3(b),
                        "_<=_": lambda a, b: self.toZ3(a) <= self.toZ3(b),
                        "_>=_": lambda a, b: self.toZ3(a) >= self.toZ3(b),
                        "_==_": lambda a, b: self.toZ3(a) == self.toZ3(b),
                        "_===_": lambda a, b: self.toZ3(a) == self.toZ3(b),
                        "_!=_": lambda a, b: self.toZ3(a) != self.toZ3(b),
                        "_+_": lambda a, b: self.toZ3(a) + self.toZ3(b),
                        "_-_": lambda a, b: self.toZ3(a) - self.toZ3(b),
                        "_*_": lambda a, b: self.toZ3(a) * self.toZ3(b),
                        "_/_": lambda a, b: self.toZ3(a) / self.toZ3(b),
                        "_div_": lambda a, b: self.toZ3(a) / self.toZ3(b),
                        "toReal": lambda a: self.toZ3(a),
                        "toInteger": lambda a: self.toZ3(a),
                        "toBoolean": lambda a: self.toZ3(a),
                        }

    def toZ3(self, t):
        op = t.symbol()
        args = list(t.arguments())
        #print(op)
        #print(args)
        if not args:
            # If no arguments, then t it is either a constant or a variable
            if t.equal(self.falseT):
                return False
            elif t.equal(self.trueT):
                return True
            elif t.isVariable():
                var_n = t.getVarName()
                var_t = t.getSort()
                #print(var_n, var_t)
                if str(var_t) == "Boolean":
                    return Bool(var_n)
                elif str(var_t) == "Integer":
                    return Int(var_n)
                elif str(var_t) == "Real":
                    return Real(var_n)
            else: 
                # Integer and Real constants
                cons_t = t.getSort()
                if str(cons_t) == "Integer":
                    return t.toInt()
                elif str(cons_t) == "Real":
                    return t.toFloat()
        else:
            #print(*args)
            #print(str(self.op_conv[str(op)](*args)))
            # If term has args, construct operation with dictorionary of operators
            return self.op_conv[str(op)](*args)

    def separate_constraints(self, t):
        consL = []
        #print(t.symbol())
        # Recursively convert individual constraints to Z3 constraints 
        if not (str(t.symbol()) == '_and_'):
            consL.append(self.toZ3(t))
        else:
            args = list(t.arguments())
            #print(args)
            consL.extend(self.separate_constraints(args[0]))
            consL.extend(self.separate_constraints(args[1]))
        # Return list of Z3 cosntraints
        return consL

    def run(self , term , data):
        #print(term)
        # Hook attributes definition
        self.solver = Solver()
        self.module = term.symbol().getModule()
        self.trueT = self.module.parseTerm('(true).Boolean')
        self.falseT = self.module.parseTerm('(false).Boolean')
        
        argument , = term.arguments()
        #print(argument)

        # Separate constraint by conjunction operator
        consL = self.separate_constraints(argument)
        #print(consL)
        
        for cst in consL:
            self.solver.add(cst)

        if self.solver.check() == unsat:
            return self.module.parseTerm("failed")

        model = self.solver.model()
        if len(model) == 0:
            return self.module.parseTerm("(true).Boolean <-- (true).Boolean")
        #print(model)
        assignments = ""
        for svar in model:
            #print(svar)
            svar_t = str(model[svar].sort())
            val_ext = ""
            if svar_t == "Int":
                var_type = "Integer"
                #val_ext = ":" + var_type
            elif svar_t == "Real":
                var_type = svar_t
                if not re.search(r'/', str(model[svar])):
                    val_ext = "/1"
            else:
                var_type = "Boolean"
                #val_ext = "." + var_type
            assignments += f"{svar}:{var_type} <-- {str(model[svar]).lower()}{val_ext} , "
            #print(assignments)
        return self.module.parseTerm(assignments[:-3])

hook = SMTAssignmentHook()
maude.connectEqHook('get-SMTassignment', hook)