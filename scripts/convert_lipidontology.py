import os
import shutil
import numpy as np
import pandas as pd

import rpy2.robjects as robjects
from rpy2.robjects.packages import importr
from rpy2.robjects.vectors import DataFrame, FloatVector, IntVector, StrVector, ListVector, Matrix


# https://stackoverflow.com/a/24799752 (CC BY-SA 4.0) with modifications
def recurse_r_object(data):
    """
    step through an R object recursively and convert the types to python types as appropriate. 
    Leaves will be converted to e.g. numpy arrays or lists as appropriate and the whole graph to a dictionary.
    """
    r_dict_types = [DataFrame, ListVector]
    r_array_types = [FloatVector, IntVector, Matrix]
    r_list_types = [StrVector]
    if type(data) in r_dict_types:
        return dict(zip(data.names, [recurse_r_object(elt) for elt in data]))
    elif type(data) in r_list_types:
        return [recurse_r_object(elt) for elt in data]
    elif type(data) in r_array_types:
        return np.array(data)
    else:
        if hasattr(data, "rclass"):  # An unsupported r class
            raise KeyError('Could not proceed, type {} is not defined'
                        'to add support for this type, just add it to the imports '
                        'and to the appropriate type list above'.format(type(data)))
        else:
            return data  # We reached the end of recursion

def recursive_graph(parent, subgraph, list):
    if isinstance(subgraph, dict):
        for key in subgraph.keys():
            list.append((parent, key))
            recursive_graph(key, subgraph[key], list)
    else:
        for val in subgraph:
            list.append((parent, val))

# initialize R base and utils
importr('base')
importr('utils')

# Create data/lipidontology directory, if it doesnt exist
os.makedirs('data/lipidontology', exist_ok=True)

# read and convert the LION tree structure
with open('external/lipidontology/OntologyApp/data/20191010 LION_tree_structure.R', 'r') as f:
    lipidontology_structure_file = f.read()

lion_graph_R = robjects.r(lipidontology_structure_file)
lion_graph_dict = recurse_r_object(lion_graph_R)
lion_edgelist = []
recursive_graph('root', lion_graph_dict, lion_edgelist)

with open('data/lipidontology/lion_graph.tsv', 'w') as f:
    for (n1, n2) in lion_edgelist:
        f.write(str(n1) + '\t' + str(n2) + '\n')

# copy the LION association table
shutil.copy('external/lipidontology/OntologyApp/data/20190704 LION_association.txt', 'data/lipidontology/lion_association.tsv')
