import pddlpy
from solver import Solver
from config import cfg


domprob = pddlpy.DomainProblem(cfg["domain"], cfg["problem"])
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
