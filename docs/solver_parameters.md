# Setting solver parameters and hyperparameter search

## Calling a solver by name

You can see the list of available solvers (and subsolvers) as follows:

```python
from cpmpy import *

print(SolverLookup.solvernames())
```

On my system, with pysat and minizinc installed, this gives `['ortools', 'minizinc', 'minizinc:chuffed', 'minizinc:coin-bc', ..., 'pysat:minicard', 'pysat:minisat22', 'pysat:minisat-gh']

You can use any of these solvers by passing its name to the `Model.solve()` parameter 'solver' as such:

```python
a,b = boolvar(2)
Model(a|b).solve(solver='minizinc:chuffed')
```

## Setting solver parameters
OR-tools has many solver parameters, [documented here](https://github.com/google/or-tools/blob/stable/ortools/sat/sat_parameters.proto).

CPMpy's interface to ortools accepts keyword arguments to `solve()`, and will set the corresponding or-tools parameters if the name matches. We documented some of the frequent once in our [CPM_ortools API](cpmpy/solvers/ortools.py).

For example, with `model` a CPMpy Model(), you can do the following to make or-tools use 8 parallel cores and print search progress:

```python
from cpmpy import *
from cpmpy.solvers import CPM_ortools

s = CPM_ortools(model)
s.solve(num_search_workers=8, log_search_progress=True)
```


## Hyperparameter search across different parameters
Because CPMpy offers programmatic access to the solver API, hyperparameter search can be straightforwardly done with little overhead between the calls.

The tools directory contains a utility to efficiently search through the hyperparameter space defined by the solvers `tunable_params`.
This utlity is based on the SMBO framework and speeds up the search by implementing adaptive capping.

The parameter tuner is based on the following publication: 
>Ignace Bleukx, Senne Berden, Lize Coenen, Nicholas Decleyre, Tias Guns (2022). Model-Based Algorithm
>Configuration with Adaptive Capping and Prior Distributions. In: Schaus, P. (eds) Integration of Constraint
>Programming, Artificial Intelligence, and Operations Research. CPAIOR 2022. Lecture Notes in Computer Science,
>vol 13292. Springer, Cham. https://doi.org/10.1007/978-3-031-08011-1_6

Solver interfaces not providing the set of tunable parameters can still be tuned by using this utility and providing the parameter (values) yourself.

```python
from cpmpy import *
from cpmpy.tools import ParameterTuner

model = Model(...)

tunables = {
    "search_branching":[0,1,2],
    "linearization_level":[0,1],
    'symmetry_level': [0,1,2]}
defaults = {
    "search_branching": 0,
    "linearization_level": 1,
    'symmetry_level': 2
}

tuner = ParameterTuner("ortools", model, tunables, defaults)
best_params = tuner.tune(max_tries=100)
best_runtime = tuner.best_runtime
```