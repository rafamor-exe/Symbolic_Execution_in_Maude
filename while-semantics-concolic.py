import maude

import argparse
import z3


class SMTAssignmentHook (maude.Hook):

    def __init__(self):
        super().__init__()
        self.solver = z3.Solver()

    def run(self , term , data ):
        module = term.symbol().getModule()
        print("a")
        #for argument in term.arguments():
        #    print(argument)
        argument , = term.arguments()
        print(argument)
        self.solver.add(argument)
        print("aa")
        model = self.solver.model()
        assignments = ""
        for sv in model:
            if sv != model[-1]:
                assignments += f"{sv} <- {model[sv]} ; "
            else:
                assignments += f"{sv} <- {model[sv]}"
        return module.parseTerm(assignments)

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

