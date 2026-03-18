import argparse
import sys
import re
import time

ADHOC_CONCOLIC_IMPL = 'adhoc-analysis/while-semantics-concolic.maude'

SEMANTICS_TRANSFORMER_MAUDE = 'semantics-analysis-tr.maude'

def get_args():
    parser = argparse.ArgumentParser(description="Argument Parser for Maude While Language Concolic Engine", 
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--program", action="store", help="Concrete initial state of the search", default='')
    parser.add_argument("--pattern", action="store", help="Pattern to match", default='')
    parser.add_argument("--op", action="store", help="Maude operation", default="search")
    parser.add_argument("--file", action="store", help="File containing the semantics", default=ADHOC_CONCOLIC_IMPL)
    parser.add_argument("--mod", action="store", help="Semantics module", default="upTerm('WHILE-MAUDE, true)")
    parser.add_argument("--path", action="store", help="Show execution path", default=False)

    parser.add_argument("--analysis", action="store", help="Type of analysis to perform (e.g.: maude-se, concolic)", default="")
    parser.add_argument("--stSort", action="store", help="State sort", default="'State")
    parser.add_argument("--valOp", action="store", help="Internal value operator in semantics (different from syntax 'val)", default="'placeholderVal")
    parser.add_argument("--sCond", action="store", help="Search conditions", default="nil")
    parser.add_argument("--sType", action="store", help="Search type", default="'!")
    parser.add_argument("--bound", action="store", help="Search bound", default="unbounded")
    parser.add_argument("--solN", action="store", help="Solution number", default=0)

    parser.add_argument("--svars", action="store", help="List of symbolic variables pairs of the form (name, type) ; (name2, type2) ; ... ; (nameN, typeN)", default=[])
    parser.add_argument("--symbCond", action="store", help="Initial symbolic conditions", default="true")

    parser.add_argument("--logic", action="store", help="Logic to use in MaudeSE analysis", default="'QF_LRA")
    parser.add_argument("--fold", action="store", help="Allow folding in MaudeSE analysis", default="false")

    parser.add_argument("--metrics", action="store_true", help="Enable rewrite metrics without module transformation")
    return parser.parse_args()

def getSymbVarCond(args) :
    # Parse symbolic var-val pairs
    svPairs = ""
    svDict = {}
    i = 0
    for sv in args.svars.split(";"):
        sv = re.sub(r"[\( \)]", "", sv).split(",")
        svN = sv[0]
        svT = sv[1]
        svDict[svN] = f"{svN}{str(i)}:{svT}"
        svPairs += f"(\'{svN},{svDict[svN]}) "
        i += 1
    symbCond = args.symbCond.split(" and ")
    reSymbCond = ['(true).Boolean']
    for cnd in symbCond:
        for var, val in svDict.items():
            if var in cnd:
                cndMod = cnd.replace(var, val)
                reSymbCond.append(cndMod)
    symbCond = ' and '.join(reSymbCond)
    return svPairs, symbCond

if __name__ == '__main__':
    args = get_args()

    # Select analysis
    if args.analysis == "maude-se":
        import maudeSE

        maudeSE.maude.init(advise=True)
        maudeSE.maude.load("smt.maude")
        maudeSE.maude.load("smt-check")
        maudeSE.load(args.file)
        maudeSE.maude.load(SEMANTICS_TRANSFORMER_MAUDE)
        mod = maudeSE.maude.getModule('MAUDE-SE-EXT')
        #maudeSE.maude.input("set trace on .")
        # MaudeSE main still needs to be invoked to be able to reduce
        # It is invoked with the language semantics instead of the transformer because of collision ("multiple parses" Maude warning)  
        sys.argv = ["maude-se", args.file, "-no-meta"]
        maudeSE.main()

        svPairs, symbCond = getSymbVarCond(args)
        if not args.metrics :
            t = f"""searchMaudeSE(
                        {args.mod},
                        {args.stSort},
                        {args.valOp},
                        "{args.program}",
                        {args.pattern},
                        upTerm({symbCond}) = 'true.Boolean /\\ {args.sCond},
                        {args.sType},
                        {args.bound},
                        {args.solN},
                        {args.logic},
                        {args.fold},
                        {svPairs})"""
            t = mod.parseTerm(t)
            n_rew = t.reduce()
            print(t)
            print(f"Rewrites: {n_rew}")
            print("---------")
            print("With path:")
            path = f"""searchPathMaudeSE(" \
                                    {args.mod},
                                    {args.stSort},
                                    {args.valOp},
                                    "{args.program}",
                                    {args.pattern},
                                    upTerm({symbCond}) = 'true.Boolean /\\ {args.sCond},
                                    {args.sType},
                                    {args.bound},
                                    {args.solN},
                                    {args.logic},
                                    {args.fold},
                                    {svPairs})"""
            path = mod.parseTerm(path)
            path.reduce()
            print(path)
        else:
            print("---------")
            print("Only measure search rewrites")
            start = time.time()
            t_mod = f"transformModSymb({args.mod}, {args.stSort}, {args.valOp}, maudeSE)"
            t_mod = mod.parseTerm(t_mod)
            t_mod.reduce()
            mod_time = time.time()
            t_0 = f"""getTerm(metaParse({t_mod},
                                        tokenize("{args.program}"),
                                        {args.stSort}))"""
            t_0 = mod.parseTerm(t_0)
            t_0.reduce()
            term_time = time.time()
            #print(t_0)
            t_search = f"""metaSmtSearch({t_mod},
                                        'startSE[{t_0}, searchSubVarConst(upTerm({svPairs}), maudeSE),'_|_|_['empty.IStoreS, 'empty.RStoreS, 'empty.BStoreS]],
                                        {args.pattern},
                                        modCond(upTerm({symbCond}) = 'true.Boolean /\\ {args.sCond}, {args.valOp}, maudeSE),
                                        {args.sType},
                                        {args.bound},
                                        {args.solN},
                                        {args.logic},
                                        {args.fold})"""
            t_search = mod.parseTerm(t_search)
            n_rew = t_search.reduce()
            end = time.time()
            print(t_search)
            print(f"Rewrites: {n_rew}")
            print(f"Module transformation time (s): {mod_time - start}")
            print(f"Term reduction time (s): {term_time - mod_time}")
            print(f"Search time (s): {end - term_time}")
            print(f"Total time elapsed (s): {end - start}")
    elif args.analysis == "concolic":
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
            maude.load(args.file)
            maude.load(SEMANTICS_TRANSFORMER_MAUDE)
            mod = maude.getModule('VERIFICATION-COMMANDS')
            svPairs, symbCond = getSymbVarCond(args)
            if not args.metrics:
                t = f"""searchConcolic(
                                   {args.mod},
                                   {args.stSort},
                                   {args.valOp},
                                   "{args.program}",
                                   {args.pattern},
                                   {args.sCond},
                                   {args.sType},
                                   {args.bound},
                                   {args.solN},
                                   {svPairs},
                                   {symbCond})"""
                t = mod.parseTerm(t)
                t.reduce()                
                print(t)
                if args.path:
                    print("---------")
                    print("With path:")
                    path = f"""searchPathConcolic(
                                           {args.mod},
                                           {args.stSort},
                                           {args.valOp},
                                           "{args.program}",
                                           {args.pattern},
                                           {args.sCond},
                                           {args.sType},
                                           {args.bound},
                                           {args.solN},
                                           {svPairs},
                                           {symbCond})"""
                    path = mod.parseTerm(path)
                    path.reduce()
                    print(path)
            else:
                print("---------")
                print("Only measure search rewrites")
                start = time.time()
                t_mod = f"transformModSymb({args.mod}, {args.stSort}, {args.valOp}, conc)"
                t_mod = mod.parseTerm(t_mod)
                t_mod.reduce()
                mod_time = time.time()
                t_0 = f"""getTerm(metaParse({args.mod},
                                            tokenize("{args.program}"),
                                            {args.stSort}))"""
                t_0 = mod.parseTerm(t_0)
                t_0.reduce()
                term_time = time.time()
                #print(t_0)
                t_search = f"""metaSearch({t_mod},
                                            'startC['_where_[{t_0}, searchSubVarConst(upTerm({symbCond}), conc)],
                                                    searchSubVarConst(upTerm({svPairs}), conc)],
                                            {args.pattern},
                                            {args.sCond},
                                            {args.sType},
                                            {args.bound},
                                            {args.solN})"""
                t_search = mod.parseTerm(t_search)
                n_rew = t_search.reduce()
                end = time.time()
                print(t_search)
                print(f"Rewrites: {n_rew}")
                print(f"Module transformation time (s): {mod_time - start}")
                print(f"Term reduction time (s): {term_time - mod_time}")
                print(f"Search time (s): {end - term_time}")
                print(f"Total time elapsed (s): {end - start}")
    elif args.analysis == "symb":
        import maude
        from maudeSMTHook import SMTAssignmentHook
        maude.init(advise=True)
        maude.load(args.file)
        maude.load(SEMANTICS_TRANSFORMER_MAUDE)
        mod = maude.getModule('VERIFICATION-COMMANDS')
        svPairs, symbCond = getSymbVarCond(args)
        print("---------")
        print("Only measure search rewrites")
        start = time.time()
        t_mod = f"transformModSymb({args.mod}, {args.stSort}, {args.valOp}, symb)"
        t_mod = mod.parseTerm(t_mod)
        t_mod.reduce()
        mod_time = time.time()
        t_0 = f"""getTerm(metaParse({t_mod},
                                    tokenize("{args.program}"),
                                    {args.stSort}))"""
        t_0 = mod.parseTerm(t_0)
        t_0.reduce()
        term_time = time.time()
        #print(t_0)
        t_search = f"""metaSearch({t_mod},
                                    '_`{{_`}}[{t_0}, 'true.Boolean],
                                    {args.pattern},
                                    {args.sCond},
                                    {args.sType},
                                    {args.bound},
                                    {args.solN})"""
        t_search = mod.parseTerm(t_search)
        n_rew = t_search.reduce()
        end = time.time()
        print(t_search)
        print(f"Rewrites: {n_rew}")
        print(f"Module transformation time (s): {mod_time - start}")
        print(f"Term reduction time (s): {term_time - mod_time}")
        print(f"Search time (s): {end - term_time}")
        print(f"Total time elapsed (s): {end - start}")



    
