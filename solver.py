from operators import OperatorsManager
from graph import GraphManager
import functools as fct


class Solver:
    """Implements the solving algorithm for the dom-prob instance"""
    def __init__(self, dp):
        self.dp = dp
        self.operators_manager = OperatorsManager(dp)  # Methods to apply operators
        self.relaxed_graph_plan = self.build_relaxed_graph_plan()  # Creation of the relaxed GraphPlan

    def build_relaxed_graph_plan(self):
        """Builds the relaxed graph plan from initial state"""
        rgp, statements_layer = GraphManager(), {tuple(atom.predicate) for atom in self.dp.initialstate()}
        rgp.add_layer(statements_layer, layer_params={"type": "statements"})
        while True:
            possible_actions = self.operators_manager.get_applicable_actions(statements_layer) \
                + [self.operators_manager.void_action(statements_layer)]
            new_statements = fct.reduce(
                lambda s1, s2: s1 | s2, [action["effect_pos"] for action in possible_actions], set()
            )
            if statements_layer.issuperset(new_statements):
                # Breaks when no additional statement is obtained
                break
            statements_layer = statements_layer | new_statements

            rgp.add_layer(possible_actions,
                          connection_func=lambda statement, action: statement in action["precond_pos"],
                          layer_params={"type": "actions"})
            rgp.add_layer(statements_layer,
                          connection_func=lambda action, statement: statement in action["effect_pos"],
                          layer_params={"type": "statements"})
        return rgp
