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
        for constraint in maude_constraints:
            if constraint == '(false).Boolean':
                return module.parseTerm("failed")
            elif constraint == '(true).Boolean':
                z3_constraint = True
            else:
                lhs, op, rhs = self.parse_constraint(constraint)
                z3_constraint = self.get_z3constraint(lhs, op, rhs)
            self.solver.add(z3_constraint)

        if self.solver.check() == unsat:
            return module.parseTerm("failed")

        model = self.solver.model()
        if len(model) == 0:
            return module.parseTerm("(true).Boolean")
        
        assignments = ""
        for svar in model:
            svar_t = str(model[svar].sort())
            if svar_t == "Int":
                var_type = "Integer"
            elif svar_t == "Real":
                var_type = svar_t
            else:
                var_type = "Bool"
            assignments += f"{svar}:{var_type} <-- {model[svar]}:{var_type} ; "
        return module.parseTerm(assignments[:-3])

    def parse_constraint(self, argument):
        lhs, op, rhs = re.split(r' ([<>=!]+) ', argument)
        return lhs, op, rhs

    def get_z3constraint(self, lhs, op, rhs):
        lhs_list, lvar_dic = self.process_operands(lhs.split(' '))
        rhs_list, rvar_dic = self.process_operands(rhs.split(' '))
        ops = {
            "<": lambda a, b: a < b,
            ">": lambda a, b: a > b,
            "<=": lambda a, b: a <= b,
            ">=": lambda a, b: a >= b,
            "==": lambda a, b: a == b,
            "!=": lambda a, b: a != b,
        }
        constraint = ops[op](eval(''.join(lhs_list), lvar_dic), eval(''.join(rhs_list), rvar_dic))
        return constraint

    def process_operands(self, l):
        var_dic = {}
        for i in range(0,len(l)):
            match_var = re.match(r'(\w+):(\w+)', l[i])
            if match_var:
                var_n, var_t = match_var.groups()
                if var_t == "Integer":
                    var_dic[var_n] = Int(var_n)
                elif var_t == "Real":
                    var_dic[var_n] = Real(var_n)
                else:
                    var_dic[var_n] = Bool(var_n)
                l[i] = var_n
            else:
                match_int = re.search(r'.Integer', l[i])
                if match_int:
                    l[i] = re.sub(r'\)\.\w+', ')', l[i])
        return l, var_dic

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

