from frozendict import frozendict
from utils import add_to_sets_dict, merge_sets_dicts, VariablesAssign


class OperatorCell:
    """Useful methods to handle an operator"""
    def __init__(self, op_name, dp, forward=True):
        # The forward arg states if the operation is to be performed from preconditions to effects or the other way
        # around
        self.op_name, self.dp, self.forward = op_name, dp, forward
        self.op = self._get_generic_op(self.op_name, self.dp)
        self.i_pos, self.i_neg, self.o_pos, self.o_neg = self._parse_op(self.op, self.forward)
        self.input_statements = merge_sets_dicts(self.i_pos, self.i_neg)
        self.vars = self._vars(self.input_statements)
        self.vars_assign = VariablesAssign(self.vars)

    @staticmethod
    def _build_statements_dict(statements):
        """Creates a dictionary with keys being all precondition names, and corresponding values being sets containing
        the different variable names associated to the key"""
        i_statements = {}
        for statement in statements:
            add_to_sets_dict(i_statements, statement[0], statement[1:])
        return i_statements

    @staticmethod
    def _vars(statements_dict):
        """Returns the set of all variables names involved in the operation"""
        vars_ = set()
        for _, vars_and_consts in statements_dict.items():
            [[vars_.update({lit}) for lit in vc_list] for vc_list in vars_and_consts]
        return vars_

    @staticmethod
    def _get_generic_op(op_name, dp):
        """Extracts the version of the op with most diversified set of variable names (avoid cases where different
        variables have been given, the same name) from the shitty pddlpy operators format"""
        dumb_ops_by_dumb_dev = list(dp.ground_operator(op_name))
        nb_diff_vars = [len(set(dumb_op.variable_list.values())) for dumb_op in dumb_ops_by_dumb_dev]
        return dumb_ops_by_dumb_dev[max(range(len(nb_diff_vars)), key=lambda i: nb_diff_vars[i])]

    def _parse_op(self, op, forward):
        """Uses the value of the forward arg to decide the inputs and outputs sets from preconditions and effects"""
        op_statements = map(
            self. _build_statements_dict,
            (op.precondition_pos, op.precondition_neg, op.effect_pos, op.effect_neg) if forward
            else (op.effect_pos | (op.precondition_pos - op.effect_neg), op.effect_neg,
                  op.precondition_pos & op.effect_neg, op.effect_pos)
        )
        return op_statements

    def effects_of_assignation(self, assignation, statements_dict):
        """Given an assignation in the {var_name_1: value_1, ...} format, returns all the effects of said assignation
        as a set of statements"""
        effects = set()
        for operator, vars_and_consts in statements_dict.items():
            effects |= {(operator, *(assignation[vc] if vc in self.vars else vc for vc in vc_list))
                        for vc_list in vars_and_consts}
        return frozenset(effects)

    def get_possible_assignations(self, statements):
        """From an input set of statements, determines all possible variables assignation that can lead to an action
        using the VariablesAssign structure and keeps only those which meet the feasibility criteria: all positive
        preconditions are in input statements and no negatives are"""
        vars_partial_assignations = sum([
            [frozendict({var: val for var, val in zip(var_names, s[1:])}) for var_names in self.input_statements[s[0]]]
            for s in statements
        ], [])
        vars_possible_assignations = filter(
            lambda assign: all([len(statements & self.effects_of_assignation(assign, self.i_neg)) == 0,
                                statements.issuperset(self.effects_of_assignation(assign, self.i_pos))]),
            self.vars_assign.process_assignations(list(vars_partial_assignations))
        )
        return vars_possible_assignations

    def get_possible_actions(self, statements):
        """Given a set of statements, finds all suitable variables assignations and returns the associated actions
        as frozen dictionaries summarising their behavior"""
        possible_assignations = self.get_possible_assignations(statements)
        possible_actions = [frozendict(
            {"name": self.op_name, "vars": assign,
             "precond_pos": self.effects_of_assignation(assign, self.i_pos),
             "precond_neg": self.effects_of_assignation(assign, self.i_neg),
             "effect_pos": self.effects_of_assignation(assign, self.o_pos),
             "effect_neg": self.effects_of_assignation(assign, self.o_neg)}
        )
            for assign in possible_assignations
        ]
        return possible_actions


class OperatorsManager:
    """Creates all necessary op cells and sends them statements in a smart way"""

    def __init__(self, dp):
        # Each action is created in a forward and a backward version
        self.dom_prob = dp
        self.forward_actions, self.forward_actions_mapper = self._build_actions_and_mapper(True)
        self.backward_actions, self.backward_actions_mapper = self._build_actions_and_mapper(False)

    def _build_actions_and_mapper(self, forward):
        """Creates a OpCell object for each action, and updates the mapper to send them only statements that are useful
        for their respective variables assignation"""
        ops, mapper = [], {}
        for i, op_name in enumerate(self.dom_prob.operators()):
            op_cell = OperatorCell(op_name, self.dom_prob, forward)
            [add_to_sets_dict(mapper, st_name, i) for st_name in op_cell.input_statements.keys()]
            ops.append(op_cell)
        return ops, mapper

    def get_applicable_actions(self, state, forward=True):
        """Given an input state described by a set of statements, use each OpCell's get_possible_actions method to
        build the list of all possible actions from this state"""
        actions, mapper = (self.forward_actions, self.forward_actions_mapper) if forward else \
            (self.backward_actions, self.backward_actions_mapper)
        ops_statements = [set() for _ in actions]
        for statement in state:
            [ops_statements[i].update({statement}) for i in mapper[statement[0]]]
        applicable_actions = sum([
            op_cell.get_possible_actions(op_statements) for op_cell, op_statements in zip(actions, ops_statements)
        ], [])
        return applicable_actions

    @staticmethod
    def void_action(statements):
        """Returns the action of doing nothing in the summary frozendict format"""
        void_action = frozendict(
            {"name": "void", "vars": frozendict(),
             "precond_pos": frozenset(statements),
             "precond_neg": frozenset(),
             "effect_pos": frozenset(statements),
             "effect_neg": frozenset()})
        return void_action
