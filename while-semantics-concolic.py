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
                lhs, op, rhs = self.parse_constraint(constraint)
                print(lhs, op, rhs)
                z3_constraint = self.get_z3constraint(lhs, op, rhs)
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
            print(str(model[svar].sort()))
            svar_t = str(model[svar].sort())
            if svar_t == "Int":
                var_type = "Integer"
            elif svar_t == "Real":
                var_type = svar_t
            else:
                var_type = "Bool"
            print("abcd")
            assignments += f"{svar}:{var_type} <-- {model[svar]}:{var_type} ; "
        return module.parseTerm(assignments[:-3])

    def parse_constraint(self, argument):
        # print(argument)
        # pattern = r'^\s*((?:\w+:\w+|-?\d+(?:\.\d+)?|\([^)]*\))(?:\s*[\+\-\*\/]\s*(?:\w+:\w+|-?\d+(?:\.\d+)?|\([^)]*\)))*?)\s*([<>=!]+)\s*((?:\w+:\w+|-?\d+(?:\.\d+)?|\([^)]*\))(?:\s*[\+\-\*\/]\s*(?:\w+:\w+|-?\d+(?:\.\d+)?|\([^)]*\)))*?)\s*$'
        # match = re.match(pattern, str(argument).strip())
        # if not match:
        #     print("Not match")
        #     raise ValueError("Constraint not in expected format.")
        # print(match.groups())
        # return match.groups()
        print("a")
        lhs, op, rhs = re.split(r' ([<>=!]+) ', argument)
        print(lhs, op, rhs)
        return lhs, op, rhs

    def get_z3constraint(self, lhs, op, rhs):
        lhs_list, lvar_dic = self.process_operands(lhs.split(' '))
        rhs_list, rvar_dic = self.process_operands(rhs.split(' '))
        print('aaaaaaaaaaaaaa')
        print(lhs_list, lvar_dic)
        print(rhs_list, rvar_dic)
        ops = {
            "<": lambda a, b: a < b,
            ">": lambda a, b: a > b,
            "<=": lambda a, b: a <= b,
            ">=": lambda a, b: a >= b,
            "==": lambda a, b: a == b,
            "!=": lambda a, b: a != b,
        }
        print(''.join(lhs_list))
        print(eval(''.join(lhs_list), lvar_dic))
        print(eval(''.join(rhs_list), rvar_dic))
        constraint = ops[op](eval(''.join(lhs_list), lvar_dic), eval(''.join(rhs_list), rvar_dic))
        print(constraint)
        return constraint

    def process_operands(self, l):
        var_dic = {}
        for i in range(0,len(l)):
            print(l[i])
            match_var = re.match(r'(\w+):(\w+)', l[i])
            if match_var:
                var_n, var_t = match_var.groups()
                if var_t == "Integer":
                    print("a")
                    var_dic[var_n] = Int(var_n)
                    #val = eval(re.sub(r'\)\.\w+', ')', value))
                    #print(val)
                    #val = int(value)
                elif var_t == "Real":
                    print("ab")
                    var_dic[var_n] = Real(var_n)
                    #num, det = value.split("/")
                    #val = float(value)
                    #val = Q(num, det)
                else:
                    var_dic[var_n] = Bool(var_n)
                l[i] = var_n
            else:
                print("b")
                match_int = re.search(r'.Integer', l[i])
                if match_int:
                    l[i] = re.sub(r'\)\.\w+', ')', l[i])
                # else:
                #     match_rat = re.search(r'(-?\d+)/(-?\d+)', l[i])
                #     if match_rat:
                #         print(match_rat)
                #         num, dem = match_rat.groups()
                #         print("abc")
                #         l[i] = Q(num, dem)
        print(l)
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

