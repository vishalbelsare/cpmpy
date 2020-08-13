# Tias Guns, 2019

from .variables import *
from .expressions import *
from .globalconstraints import *

### variable creation, objects in .variables

# N-dimensional array of Boolean Decision Variables
def BoolVar(shape=None):
    if shape is None or shape == 1:
        return BoolVarImpl()
    length = np.prod(shape)
    
    # create base data
    data = np.array([BoolVarImpl() for _ in range(length)]) # repeat new instances
    # insert into custom ndarray
    return NDVarArray(shape, dtype=object, buffer=data)

# Relation between 'rows' and 'cols', Boolean Variables in a pandas dataframe
class Relation(object):
    # rows, cols: list of names
    def __init__(self, rows, cols):
        rel = BoolVar((len(rows),len(cols)))
        self.df = pd.DataFrame(index=rows, columns=cols)
        for i,r in enumerate(rows):
            for j,c in enumerate(cols):
                self.df.loc[r,c] = rel[i,j]
    # use as: rel['a','b']
    def __getitem__(self, key):
        try:
            return self.df.loc[key]
        except KeyError:
            return False

# N-dimensional array of Integer Decision Variables with lower-bound and upper-bound
def IntVar(lb, ub, shape=None):
    if shape is None or shape == 1:
        return IntVarImpl(lb,ub)
    length = np.prod(shape)
    
    # create base data
    data = np.array([IntVarImpl(lb,ub) for _ in range(length)]) # repeat new instances
    # insert into custom ndarray
    return NDVarArray(shape, dtype=object, buffer=data)

# N-dimensional wrapper, wrap a standard array (e.g. [1,2,3,4] whatever)
# so that we can do [1,2,3,4][var1] == var2, e.g. element([1,2,3,4],var1,var2)
# needed because standard arrays can not be indexed by non-constants
def cparray(arr):
    if not isinstance(arr, np.ndarray):
        arr = np.array(arr)
    return NDVarArray(shape=arr.shape, dtype=type(arr.flat[0]), buffer=arr)


# implication constraint: a -> b
# Python does not offer relevant syntax...
# I am considering overloading bitshift >>
# for double implication, use equivalence a == b
def implies(a, b):
    # both constant
    if type(a) == bool and type(b) == bool:
        return (~a | b)
    # one constant
    if a is True:
        return b
    if a is False:
        return True
    if b is True:
        return True
    if b is False:
        return ~a

    return Operator('->', [a.boolexpr(), b.boolexpr()])


# all: listwise 'and'
def all(iterable):
    collect = [] # logical expressions
    for elem in iterable:
        if elem is False:
            return False # no need to create constraint
        elif elem is True:
            pass
        elif isinstance(elem, Expression):
            collect.append( elem.boolexpr() )
        else:
            raise "unknown argument to 'all'"
    if len(collect) == 1:
        return collect[0]
    if len(collect) >= 2:
        return Operator("and", collect)
    return True
        
# any: listwise 'or'
def any(iterable):
    print("Doing the 'any'")
    collect = [] # logical expressions
    for elem in iterable:
        if elem is True:
            return True # no need to create constraint
        elif elem is False:
            pass
        elif isinstance(elem, Expression):
            collect.append( elem.boolexpr() )
        else:
            raise "unknown argument to 'any'"
    if len(collect) == 1:
        return collect[0]
    if len(collect) >= 2:
        return Operator("or", collect)
    return False

# min: listwise 'min'
def min(iterable):
    # constants only?
    if not any(isinstance(elem, Expression) for elem in iterable):
        return np.min(iterable)
    return GlobalConstraint("min", list(iterable))
def max(iterable):
    # constants only?
    if not any(isinstance(elem, Expression) for elem in iterable):
        return np.max(iterable)
    return GlobalConstraint("max", list(iterable))

from .model import *
