from cpmpy import Model, SolverLookup
from cpmpy.expressions.globalconstraints import *

import pytest

SOLVERNAME = None

# Exclude some global constraints for solvers
# Can be used when .value() method is not implemented/contains bugs
EXCLUDE_GLOBAL = {"ortools": {"circuit"},
                  "gurobi": {"circuit"},
                  "minizinc": {"circuit"},
                  "pysat": {"circuit", "element","min","max","allequal","alldifferent"}}

# Exclude certain operators for solvers.
# Not all solvers support all operators in CPMpy
EXCLUDE_OPERATORS = {"gurobi": {"mod"},
                     "pysat": {"sum", "wsum", "sub", "mod", "div", "pow", "abs", "mul","-"}}

# Some solvers only support a subset of operators in imply-constraints
# This subset can differ between left and right hand side of the implication
EXCLUDE_IMPL = {"ortools": {"xor", "element"},
                "z3": {"min", "max", "abs"}} # TODO this will become emtpy after resolving issue #105

# Variables to use in the rest of the test script
NUM_ARGS = [intvar(-3, 5, name=n) for n in "xyz"]   # Numerical variables
NN_VAR = intvar(0, 10, name="n_neg")                # Non-negative variable, needed in power functions
POS_VAR = intvar(1,10, name="s_pos")                # A strictly positive variable
NUM_VAR = intvar(0, 10, name="l")                   # A numerical variable

BOOL_ARGS = [boolvar(name=n) for n in "abc"]        # Boolean variables
BOOL_VAR = boolvar(name="p")                        # A boolean variable


def numexprs():
    """
    Generate all numerical expressions
    Numexpr:
        - Operator (non-Boolean) with all args Var/constant (examples: +,*,/,mod,wsum)
                                                           (CPMpy class 'Operator', not is_bool())
        - Global constraint (non-Boolean) (examples: Max,Min,Element)
                                                           (CPMpy class 'GlobalConstraint', not is_bool()))
    """
    if SOLVERNAME is None:
        return

    names = [(name, arity) for name, (arity, is_bool) in Operator.allowed.items() if not is_bool]
    if SOLVERNAME in EXCLUDE_OPERATORS:
        names = [(name, arity) for name, arity in names if name not in EXCLUDE_OPERATORS[SOLVERNAME]]
    for name, arity in names:
        if name == "wsum":
            operator_args = [list(range(len(NUM_ARGS))), NUM_ARGS]
        elif name == "div" or name == "pow":
            operator_args = [NN_VAR,2]
        elif name == "mod":
            operator_args = [NUM_ARGS[0],POS_VAR]
        elif arity != 0:
            operator_args = NUM_ARGS[:arity]
        else:
            operator_args = NUM_ARGS

        yield Operator(name, operator_args)


# Generate all possible comparison constraints
def comp_constraints():
    """
        Generate all comparison constraints
        - Numeric equality:  Numexpr == Var                (CPMpy class 'Comparison')
                         Numexpr == Constant               (CPMpy class 'Comparison')
        - Numeric disequality: Numexpr != Var              (CPMpy class 'Comparison')
                           Numexpr != Constant             (CPMpy class 'Comparison')
        - Numeric inequality (>=,>,<,<=): Numexpr >=< Var  (CPMpy class 'Comparison')
    """
    for comp_name in Comparison.allowed:
        for numexpr in numexprs():
            for rhs in [NUM_VAR, 1]:
                yield Comparison(comp_name, numexpr, rhs)

    for comp_name in Comparison.allowed:
        for glob_expr in global_constraints():
            if not glob_expr.is_bool():
                for rhs in [NUM_VAR, 1]:
                    yield Comparison(comp_name, glob_expr, rhs)


# Generate all possible boolean expressions
def bool_exprs():
    """
        Generate all boolean expressions:
        - Boolean operators: and([Var]), or([Var]), xor([Var]) (CPMpy class 'Operator', is_bool())
        - Boolean equality: Var == Var                          (CPMpy class 'Comparison')
    """
    if SOLVERNAME is None:
        return

    names = [(name, arity) for name, (arity, is_bool) in Operator.allowed.items() if is_bool]
    if SOLVERNAME in EXCLUDE_OPERATORS:
        names = [(name, arity) for name, arity in names if name not in EXCLUDE_OPERATORS[SOLVERNAME]]

    for name, arity in names:
        if arity != 0:
            operator_args = BOOL_ARGS[:arity]
        else:
            operator_args = BOOL_ARGS

        yield Operator(name, operator_args)
        # Negated boolean values
        yield Operator(name, [~ arg for arg in operator_args])

    for eq_name in ["==", "!="]:
        yield Comparison(eq_name, *BOOL_ARGS[:2])

    for cpm_cons in global_constraints():
        if cpm_cons.is_bool():
            yield cpm_cons

def global_constraints():
    """
        Generate all global constraints
        -  AllDifferent, AllEqual, Circuit,  Minimum, Maximum, Element
    """
    if SOLVERNAME is None:
        return

    global_cons = [AllDifferent, AllEqual, Minimum, Maximum]
    # TODO: add Circuit
    for global_type in global_cons:
        cons = global_type(NUM_ARGS)
        if SOLVERNAME not in EXCLUDE_GLOBAL or \
                cons.name not in EXCLUDE_GLOBAL[SOLVERNAME]:
            yield cons

    if SOLVERNAME not in EXCLUDE_GLOBAL or \
            "element" not in EXCLUDE_GLOBAL[SOLVERNAME]:
        yield cpm_array(NUM_ARGS)[NUM_VAR]

    if SOLVERNAME not in EXCLUDE_GLOBAL or \
            "xor" not in EXCLUDE_GLOBAL[SOLVERNAME]:
        yield Xor(BOOL_ARGS)

    if SOLVERNAME not in EXCLUDE_GLOBAL or \
            "cumulative" not in EXCLUDE_GLOBAL[SOLVERNAME]:
        s = intvar(0,10,shape=3,name="start")
        e = intvar(0,10,shape=3,name="end")
        dur = [1,4,3]
        demand = [4,5,7]
        cap = 10
        yield Cumulative(s, dur, e, demand, cap)


def reify_imply_exprs():
    """
    - Reification (double implication): Boolexpr == Var    (CPMpy class 'Comparison')
    - Implication: Boolexpr -> Var                         (CPMpy class 'Operator', is_bool())
                   Var -> Boolexpr                         (CPMpy class 'Operator', is_bool())
    """
    if SOLVERNAME is None:
        return

    for bool_expr in bool_exprs():
        if SOLVERNAME not in EXCLUDE_IMPL or  \
                bool_expr.name not in EXCLUDE_IMPL[SOLVERNAME]:
            yield bool_expr.implies(BOOL_VAR)
            yield BOOL_VAR.implies(bool_expr)
            yield bool_expr == BOOL_VAR

    for comp_expr in comp_constraints():
        lhs, rhs = comp_expr.args
        if SOLVERNAME not in EXCLUDE_IMPL or \
                (not isinstance(lhs, Expression) or lhs.name not in EXCLUDE_IMPL[SOLVERNAME]) and \
                (not isinstance(rhs, Expression) or rhs.name not in EXCLUDE_IMPL[SOLVERNAME]):
            yield comp_expr.implies(BOOL_VAR)
            yield BOOL_VAR.implies(comp_expr)
            yield comp_expr == BOOL_VAR


@pytest.mark.parametrize("constraint", bool_exprs(), ids=lambda c: str(c))
def test_bool_constaints(constraint):
    """
        Tests boolean constraint by posting it to the solver and checking the value after solve.
    """
    if SOLVERNAME is None:
        return
    assert SolverLookup.get(SOLVERNAME, Model(constraint)).solve()
    assert constraint.value()


@pytest.mark.parametrize("constraint", comp_constraints(), ids=lambda c: str(c))
def test_comparison_constraints(constraint):
    """
        Tests comparison constraint by posting it to the solver and checking the value after solve.
    """
    if SOLVERNAME is None:
        return
    assert SolverLookup.get(SOLVERNAME,Model(constraint)).solve()
    assert constraint.value()


@pytest.mark.parametrize("constraint", reify_imply_exprs(), ids=lambda c: str(c))
def test_reify_imply_constraints(constraint):
    """
        Tests boolean expression by posting it to solver and checking the value after solve.
    """
    if SOLVERNAME is None:
        return
    assert SolverLookup.get(SOLVERNAME, Model(constraint)).solve()
    assert constraint.value()
