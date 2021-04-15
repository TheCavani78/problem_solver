from operators import OperatorsManager
from graph import GraphManager
from utils import WeightedQueue
import functools as fct


class Solver:
    """Implements the solving algorithm for the dom-prob instance"""
    def __init__(self, dp):
        self.dp = dp
        self.initial_state = frozenset({tuple(atom.predicate) for atom in self.dp.initialstate()})
        self.goal_state = frozenset({tuple(atom.predicate) for atom in self.dp.goals()})
        self.operators_manager = OperatorsManager(dp)  # Methods to apply operators
        self.rgp, self.unsolvable = self.build_relaxed_graph_plan()  # Creation of the relaxed GraphPlan
        self.depth = (len(self.rgp.layers) + 1) // 2
        self.cache = {}

    def build_relaxed_graph_plan(self):
        """Builds the relaxed graph plan from initial state"""
        rgp, total_statements, us = GraphManager(), self.initial_state, False
        rgp.add_layer(total_statements, layer_params={"type": "statements"})
        while True:
            possible_actions = self.operators_manager.get_applicable_actions(total_statements) \
                + [self.operators_manager.void_action(total_statements)]
            new_statements = fct.reduce(
                lambda s1, s2: s1 | s2, [action["effect_pos"] for action in possible_actions], set()
            )
            if total_statements.issuperset(new_statements):
                # Breaks when no additional statement is obtained
                us = True
                break
            total_statements = total_statements | new_statements

            rgp.add_layer(possible_actions,
                          connection_func=lambda statement, action: statement in action["precond_pos"],
                          layer_params={"type": "actions"})
            rgp.add_layer(total_statements,
                          connection_func=lambda action, statement: statement in action["effect_pos"],
                          layer_params={"type": "statements"})

            if total_statements.issuperset(self.goal_state):
                # Or breaks when relaxed final state is reached
                break
        return rgp, us

    def gs(self, rgp, state, goal_atom_index, table):
        """ Compute G value for given state and goal atom"""
        if rgp.node_labels[goal_atom_index] in state:
            return 0
        elif goal_atom_index in table.keys():
            return table[goal_atom_index]
        else:
            actions = rgp.graph.predecessors(goal_atom_index)
            actions_predecessors = [rgp.graph.predecessors(action) for action in actions]
            actions_predecessors_gs = [
                max([self.gs(rgp, state, i, table) for i in pred_list]) for pred_list in actions_predecessors
            ]
            gs_val = min([1 + g for g in actions_predecessors_gs]) if len(actions_predecessors_gs) > 0 else self.depth
            table[goal_atom_index] = gs_val
            return gs_val

    def compute_heuristic(self, state, mode='h_max'):
        """ Compute heuristic value for a given (state, action). """
        assert mode in ('h_plus', 'h_max')
        values_table = {}
        gs_values = [self.gs(self.rgp, state, max(self.rgp.nodes_indices[goal_atom_index]), values_table)
                     for goal_atom_index in self.goal_state]
        return sum(gs_values) if mode == 'plus' else max(gs_values)

    def solve(self, mode='h_max'):
        """Applies the A* algorithm with specified heuristic to find a plan"""
        if self.unsolvable:
            return None
        weighted_queue, final_state, processed_states = WeightedQueue(), self.goal_state, set()
        weighted_queue.insert(0, (self.initial_state, ()))
        while not weighted_queue.is_empty():
            cost, (active_state, past_actions) = weighted_queue.pop()
            if active_state.issuperset(final_state):
                return past_actions
            possible_actions = self.operators_manager.get_applicable_actions(active_state)
            for action in possible_actions:
                new_state = (active_state - action['effect_neg']) | action['effect_pos']
                new_state_hash = hash(frozenset(new_state))
                if new_state_hash not in processed_states:
                    new_cost = len(past_actions) + 1 + self.compute_heuristic(new_state, mode=mode)
                    weighted_queue.insert(new_cost, (new_state, past_actions + (action,)))
                    processed_states.update({new_state_hash})
        return None

    def display_plan(self, plan):
        """Given a plan computed by self.solve, prints the detail of its functioning"""
        if plan is None:
            print('No plan found')
        else:
            print('Plan of length ' + str(len(plan)) + ' found:')
            state = set(self.initial_state)
            for action in plan:
                print('    current state: ' + str(state))
                print(action['name'] + ': ')
                print('    needs: ' + str(set(action['precond_pos'])))
                print('    incompatible with: ' + str(set(action['precond_neg'])))
                print('    positive effects: ' + str(set(action['effect_pos'])))
                print('    negative effects: ' + str(set(action['effect_neg'])))
                state = (state - action['effect_neg']) | action['effect_pos']
            print('final state: ' + str(state))
            print('goal: ' + str(set(self.goal_state)))
            print('Objective completed !')
