import pddlpy
from solver import Solver
from config import cfg


if __name__ == '__main__':
    domprob = pddlpy.DomainProblem(cfg["domain"], cfg["problem"])
    s = Solver(domprob)
    s.display_plan(s.solve(mode=cfg['heuristic']))

