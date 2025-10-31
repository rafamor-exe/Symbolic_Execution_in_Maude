import maude

import argparse
from z3 import *
import re


class SMTAssignmentHook (maude.Hook):

    def __init__(self):
        super().__init__()
        self.solver = None

    def run(self , term , data):
        self.solver = Solver()
        #print(term)
        module = term.symbol().getModule()
        argument , = term.arguments()
        maude_constraints = re.sub(r"(val)?[\(\)]", '', str(argument)).split(' and ')
        #print(maude_constraints)
        for constraint in maude_constraints:
            if constraint == '(false).Boolean':
                return module.parseTerm("failed")
            elif constraint == '(true).Boolean':
                z3_constraint = True
            else:
                lhs, op, rhs = self.parse_constraint(constraint)
                #print(lhs, op, rhs)
                z3_constraint = self.get_z3constraint(lhs, op, rhs)
            #print(z3_constraint)
            self.solver.add(z3_constraint)
            #print("added")

        if self.solver.check() == unsat:
            return module.parseTerm("failed")

        model = self.solver.model()
        if len(model) == 0:
            return module.parseTerm("(true).Boolean")
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
                var_type = "Bool"
                #val_ext = ":" + var_type
            assignments += f"{svar}:{var_type} <-- {model[svar]}{val_ext} ; "
            #print(assignments)
        return module.parseTerm(assignments[:-3])

    def parse_constraint(self, argument):
        return re.split(r' ([<>=!]+) ', argument)

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
        #print(lhs_list)
        #print(rhs_list)
        if lhs_list[0] != 'not':
            constraint = ops[op](eval(''.join(lhs_list), lvar_dic), eval(''.join(rhs_list), rvar_dic))
        else:
            constraint = Not(ops[op](eval(''.join(lhs_list[1:]), lvar_dic), eval(''.join(rhs_list), rvar_dic)))
        #print(constraint)
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
                    #print("int matched")
                    l[i] = re.sub(r'\.Integer', '', l[i])
                    #print(l[i])
        return l, var_dic

def get_args():
    parser = argparse.ArgumentParser(description="Argument Parser for Maude While Language Concolic Engine", 
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--program", action="store", help="Program to load", default='')
    parser.add_argument("--pattern", action="store", help="Pattern to match", default='')
    parser.add_argument("--svars", action="store", help="Symbolic variables", default=[])
    parser.add_argument("--op", action="store", help="Maude operation", default="search")
    return parser.parse_args()


if __name__ == '__main__':
    maude.init(advise=False)
    SMThook = SMTAssignmentHook()
    maude.connectEqHook('get-SMTassignment', SMThook)
    maude.load('while-semantics-concolic.maude')
    args = get_args()
    wmod = maude.getModule('WHILE-MAUDE')
    t = wmod.parseTerm(args.program)
    if args.op == "search":
        pattern = wmod.parseTerm(args.pattern)
        #print(t)
        i = 0
        for solution, substitution, path, num in t.search(maude.NORMAL_FORM, pattern):
            print("\n--------------\n", f"[{i}]", solution, 'with SUBS: \n\n', substitution, "\nand PATH:\n\n")
            #for step in path():
            #    print(step)
            print("\n--------------\n")
            i += 1
    else:
        t.rewrite()
        print(t)
