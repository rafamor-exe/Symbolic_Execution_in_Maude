import argparse
import sys

ADHOC_CONCOLIC_IMPL = 'adhoc-analysis/while-semantics-concolic.maude'

SEMANTICS_TRANSFORMER_MAUDE = 'semantics-analysis-module-transformer.maude'

def get_args():
    parser = argparse.ArgumentParser(description="Argument Parser for Maude While Language Concolic Engine", 
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--program", action="store", help="Program to load", default='')
    parser.add_argument("--pattern", action="store", help="Pattern to match", default='')
    parser.add_argument("--svars", action="store", help="Symbolic variables", default=[])
    parser.add_argument("--op", action="store", help="Maude operation", default="search")
    parser.add_argument("--file", action="store", help="File containing the semantics", default=ADHOC_CONCOLIC_IMPL)
    parser.add_argument("--mod", action="store", help="Semantics module", default="WHILE-MAUDE")

    parser.add_argument("--analysis", action="store", help="Type of analysis to perform (e.g.: maude-se, concolic)", default="")
    parser.add_argument("--modL", action="store", help="List of Maude modules to transform to SMT", default="")
    parser.add_argument("--stSort", action="store", help="State sort", default="")
    parser.add_argument("--valOp", action="store", help="Value operator", default="")
    parser.add_argument("--sCond", action="store", help="Search conditions", default="nil")
    parser.add_argument("--sType", action="store", help="Search type", default="'!")
    parser.add_argument("--bound", action="store", help="Search bound", default="unbounded")
    parser.add_argument("--solN", action="store", help="Solution number", default=0)

    parser.add_argument("--logic", action="store", help="Logic to use in MaudeSE analysis", default="'QF_LRA")
    parser.add_argument("--fold", action="store", help="Allow folding in MaudeSE analysis", default="false")
    return parser.parse_args()


if __name__ == '__main__':
    args = get_args()
    if args.analysis == "maude-se":
        import maudeSE

        maudeSE.maude.init(advise=True)
        maudeSE.maude.load("smt.maude")
        maudeSE.maude.load("smt-check")
        maudeSE.maude.load(SEMANTICS_TRANSFORMER_MAUDE)
        maudeSE.maude.load(args.file)
        mod = maudeSE.maude.getModule('MAUDE-SE-EXT')

        # MaudeSE main still needs to be invoked to be able to reduce
        # It is invoked with the language semantics instead of the transformer because of collision ("multiple parses" Maude warning)  
        sys.argv = ["maude-se", args.file, "-no-meta"]
        maudeSE.main()

        t = "searchMaudeSE(" \
                        +args.modL+"," \
                        +args.stSort+"," \
                        +'\"'+args.program+'\"'+"," \
                        +args.pattern+"," \
                        +args.sCond+"," \
                        +str(args.sType)+"," \
                        +str(args.bound)+"," \
                        +str(args.solN)+"," \
                        +str(args.logic)+"," \
                        +str(args.fold)+")"
        t = mod.parseTerm(t)
        t.reduce()
        print(t)
        print("---------")
        print("With path:")
        path = "searchPathMaudeSE(" \
                                  +args.modL+"," \
                                  +args.stSort+"," \
                                  +'\"'+args.program+'\"'+"," \
                                  +args.pattern+"," \
                                  +args.sCond+"," \
                                  +str(args.sType)+"," \
                                  +str(args.bound)+"," \
                                  +str(args.solN)+"," \
                                  +str(args.logic)+"," \
                                  +str(args.fold)+")"
        path = mod.parseTerm(path)
        path.reduce()
        print(path)
    else:
        import maude
        from maudeSMTHook import SMTAssignmentHook
        maude.init(advise=True)
        SMThook = SMTAssignmentHook()
        maude.connectEqHook('get-SMTassignment', SMThook)
        if args.file == ADHOC_CONCOLIC_IMPL:
            maude.load(args.file)
            mod = maude.getModule(args.mod)
            t = mod.parseTerm(args.program)
            if args.op == "search":
                pattern = mod.parseTerm(args.pattern)
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
        else:
            if args.analysis == "concolic":
                maude.load(SEMANTICS_TRANSFORMER_MAUDE)
                maude.load(args.file)
                mod = maude.getModule('VERIFICATION-COMMANDS')
                t = "searchConcolic(" \
                                    +args.modL+"," \
                                    +args.stSort+"," \
                                    +args.valOp+"," \
                                    +'\"'+args.program+'\"'+"," \
                                    +args.pattern+"," \
                                    +args.sCond+"," \
                                    +str(args.sType)+"," \
                                    +str(args.bound)+"," \
                                    +str(args.solN)+")"
                t = mod.parseTerm(t)
                t.reduce()                
        print(t)


    
