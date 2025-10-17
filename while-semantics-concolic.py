import maude

import argparse
from z3 import *
import re


class SMTAssignmentHook (maude.Hook):

    def __init__(self):
        super().__init__()
        self.solver = Solver()

    def run(self , term , data):
        module = term.symbol().getModule()
        argument , = term.arguments()
        maude_constraints = str(argument).split(' and ')
        print(maude_constraints)
        for constraint in maude_constraints:
            if constraint == '(false).Boolean':
                return module.parseTerm("failed")
            elif constraint == '(true).Boolean':
                z3_constraint = True
            else:
                var_name, var_type, operator, value = self.parse_constraint(constraint)
                print(var_name, var_type, operator, value)
                if '/' not in value:
                    z3_constraint = self.get_z3constraint(var_name, var_type, operator, value)
                else:
                    z3_constraint = self.get_z3constraint(var_name, var_type, operator, value)
            print(z3_constraint)
            self.solver.add(z3_constraint)

        if self.solver.check() == unsat:
            return module.parseTerm("failed")

        model = self.solver.model()
        print(model)
        if len(model) == 0:
            return module.parseTerm("(true).Boolean")
        
        assignments = ""
        for svar in model:
            assignments += f"{svar}:{var_type} <-- {model[svar]}:{var_type} ; "
        return module.parseTerm(assignments[:-3])

    def parse_constraint(self, argument):
        print(argument)
        pattern = r'(\w+):(\w+)\s*([<>=!]+)\s*((?:(?:\([^)]*\)\.\w+|-?\d+(?:\.\d+)?)(?:\s*[\+\-\*\/]\s*(?:\([^)]*\)\.\w+|-?\d+(?:\.\d+)?))*))'
        match = re.match(pattern, str(argument).strip())
        if not match:
            print("Not match")
            raise ValueError("Constraint not in expected format.")
        print(match.groups())
        return match.groups()

    def get_z3constraint(self, var_name, var_type, operator, value):
        if var_type == "Integer":
            print("a")
            var = Int(var_name)
            val = eval(re.sub(r'\)\.\w+', ')', value))
            print(val)
            #val = int(value)
        elif var_type == "Real":
            var = Real(var_name)
            num, det = value.split("/")
            #val = float(value)
            val = Q(num, det)
        else:
            var = Bool(var_name)

        ops = {
            "<": lambda a, b: a < b,
            ">": lambda a, b: a > b,
            "<=": lambda a, b: a <= b,
            ">=": lambda a, b: a >= b,
            "==": lambda a, b: a == b,
            "!=": lambda a, b: a != b,
        }

        if operator not in ops:
            raise ValueError(f"Unsupported operator: {operator}")

        constraint = ops[operator](var, val)
        return constraint

def get_args():
    parser = argparse.ArgumentParser(description="Argument Parser for Maude While Language Concolic Engine", 
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--program", action="store", help="Program to load", default='')
    parser.add_argument("--svars", action="store", help="Symbolic variables", default=[])
    return parser.parse_args()


if __name__ == '__main__':
    maude.init()
    SMThook = SMTAssignmentHook()
    maude.connectEqHook('get-SMTassignment', SMThook)
    maude.load('while-semantics-concolic.maude')
    args = get_args()
    wmod = maude.getModule('WHILE-MAUDE')
    t = wmod.parseTerm(args.program)
    t.reduce()
    print(t)

