from frozendict import frozendict
import functools as fct
import numpy as np


# -------------------------------------------------------- DICTS -------------------------------------------------------
# Sets dicts are dictionaries of the {key_1: set_1, ..., key_n: set_n} type


def add_to_sets_dict(sets_dict, key, value):
    """Add the specified value in the set associated to specified key inside the specified dict, or create it if the
    key is not in the dictionary yet"""
    if key in sets_dict.keys():
        sets_dict[key].add(value)
        return True
    else:
        sets_dict[key] = {value}
        return False


def merge_sets_dicts(d1, d2):
    """Merges input sets dictionaries into a new one"""
    k1, k2 = d1.keys(), d2.keys()
    return {**{k: d1[k] | d2[k] for k in k1 & k2}, **{k: d1[k] for k in k1 - k2}, **{k: d2[k] for k in k2 - k1}}


def contains(d1, d2):
    """Returns True if d2 is a (potentially nested) sub-dict of d1"""
    if any((not hasattr(d1, 'keys'), not hasattr(d2, 'keys'))):
        return d1 == d2
    return all([contains(d1[k], d2[k]) if k in d1.keys() else False for k in d2.keys()])


def invert_dict(d):
    """Returns the inverse dict of input dict"""
    inv = {}
    for key, val in d.items():
        add_to_sets_dict(inv, val, key)
    return inv


# --------------------------------------------------- WEIGHTED QUEUE ---------------------------------------------------


class WeightedQueue:
    """Acts like a queue with weights that pops the smallest weighted elem first"""
    def __init__(self):
        self.weights = np.empty((0,))
        self.values = {}

    def insert(self, weight, value):
        already_assigned = add_to_sets_dict(self.values, weight, value)
        if not already_assigned:
            self.weights = np.sort(np.concatenate([self.weights, [weight]]))

    def pop(self):
        w = self.weights[0]
        values = list(self.values[w])
        if len(values) == 1:
            [val] = values
            del self.values[w]
            self.weights = self.weights[1:]
        else:
            val = values[int(np.random.randint(len(values)))]
            self.values[w].discard(val)
        return w, val

    def is_empty(self):
        return len(self.weights) == 0


# ----------------------------------------------- VARIABLES ASSIGNATION ------------------------------------------------


class VariablesAssign:
    """Given known var names and consecutive possible partial assignations of these variables (some can be mutually
    exclusive), returns all the possibilities to assign a value to every known variable"""

    def __init__(self, var_names):
        self.var_names = frozenset(var_names)
        self.nb_vars = len(self.var_names)
        self.tree = {}  # The tree used for this application is a nested dictionary
        
    @staticmethod
    def _compatible_trees_and_full_inclusion(tree, assignation):
        """Given a tree and a partial assignation, returns all the sub-trees which root label are compatible with said
        assignation, and returns the only one that is completely contained in assignation if it exists (which is
        specified by the full_inclusion boolean)"""
        compatible_trees, full_inclusion = set(), False
        for p_assign in tree.keys():
            matching = [assignation[var] == val for var, val in p_assign.items() if var in assignation.keys()]
            if all(matching):
                if len(matching) == len(p_assign):
                    full_inclusion = True
                    compatible_trees = [p_assign]
                    break
                compatible_trees |= {p_assign}
        return compatible_trees, full_inclusion

    def _update_tree(self, cache, tree, assignation):
        """Pushes a new variables assignation into the current tree and returns all (possibly none) total assignations
        found in the process"""
        if len(assignation) == 0:
            return {frozendict(cache)} if len(cache) == self.nb_vars else set()
        elif len(assignation) == self.nb_vars:
            return {assignation}

        compatible_trees, full_inclusion = self._compatible_trees_and_full_inclusion(tree, assignation)
        if not full_inclusion:
            tree.update({assignation: {}})
            compatible_trees |= {assignation}

        result = fct.reduce(lambda x, y: x | y, [
            self._update_tree(
                {**cache, **p_assign}, tree[p_assign],
                frozendict({var: assignation[var] for var in assignation.keys() if var not in p_assign.keys()}))
            for p_assign in compatible_trees
        ], set())
        return result

    def process_assignations(self, assignations):
        """Uses input assignations in a random order to determine all possible total variables assignation they allow"""
        full_assignations = set()
        for i in np.random.permutation(len(assignations)):
            p_assign = assignations[i]
            if all([True if var in self.var_names else p_assign[var] == var for var in p_assign.keys()]):
                full_assignations |= self._update_tree(
                    {}, self.tree, frozendict({var: p_assign[var] for var in p_assign.keys() & self.var_names})
                )
        return full_assignations

    def reset(self):
        """Resets tree"""
        self.tree = {}
