import networkx as nx
from utils import add_to_sets_dict
import itertools as itt


class GraphManager:
    """Additional structure to handle layered graphs"""
    def __init__(self):
        self.graph = nx.Graph()
        self.node_labels = []  # id to label
        self.nodes_indices = {}  # label to id with said label
        self.count = 0
        self.layers = []

    def add_nodes(self, nodes_labels):
        """Adds specified nodes into the graph and updates pointers structures"""
        nodes_labels = list(nodes_labels)
        nodes_indices = [i + self.count for i in range(len(nodes_labels))]
        self.node_labels.extend(nodes_labels)
        [add_to_sets_dict(self.nodes_indices, *lab_and_n) for lab_and_n in zip(nodes_labels, nodes_indices)]
        self.graph.add_nodes_from(nodes_indices)
        self.count += len(nodes_labels)
        return nodes_indices

    def add_layer(self, nodes_labels, connection_func=None, inter_connection_func=None, layer_params=None):
        """Adds a new layer to the graph structure, connected to the last one. If specified, connection_func is a
        2-arguments function of type (prev_layer_node_label, current_layer_node_label) -> True if they must be connected
        The inter_connection_func is a similar function for nodes inside current layer. If specified, layer_params is
        a dictionary of complementary attributes for the current layer"""
        nodes_indices, edges = self.add_nodes(nodes_labels), []
        if len(self.layers) > 0 and connection_func is not None:
            edges += [(i1, i2) for i1, i2 in itt.product(self.layers[-1]["nodes"], nodes_indices)
                      if connection_func(self.node_labels[i1], self.node_labels[i2])]
        if inter_connection_func is not None:
            edges += [(i1, i2) for i1, i2 in itt.combinations(nodes_indices, r=2)
                      if inter_connection_func(self.node_labels[i1], self.node_labels[i2])]
        self.layers.append({"nodes": nodes_indices, "nb": len(self.layers), **layer_params})
        self.graph.add_edges_from(edges)

    def get_nodes(self, ids):
        """Returns nodes labels for specified indices"""
        return [self.node_labels[i] for i in ids]

    def get_layer(self, i):
        """Returns the i-th layer"""
        return self.layers[i]
