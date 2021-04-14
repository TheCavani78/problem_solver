import pddlpy
import os
from solver import Solver


print(os.path.abspath(os.path.curdir))
domprob = pddlpy.DomainProblem("./pddl-lib/examples-pddl/domain-03.pddl", "./pddl-lib/examples-pddl/problem-03.pddl")
g = Solver(domprob).relaxed_graph_plan
print(g.layers)
print(g.node_labels)
print(g.nodes_indices)
print(g.graph.edges)
print('----------')
for l in g.layers:
    print(l)

for st in g.get_layer(2)["nodes"]:
    print(g.get_nodes([st]))
