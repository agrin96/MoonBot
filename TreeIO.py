import json
from DataStructures.Node import Node
from DataStructures.Terminal import Terminal

def deserialize_tree(json_data:str,_depth:int=0)->Node:
    """Read in a serialized tree and convert it into a node tree. Returns the
    root node.
    Parameters:
        json_data (str): json serialized tree representation. 
        depth (int): Default to 0, shouldn't be modified since its used for
            recursion."""
    tree = json_data
    if _depth == 0:
        tree = json.loads(json_data)

    if "parent" not in tree:
        return Terminal.terminal_from_dict(tree)
    node = Node.node_from_dict(tree["parent"])
    
    for child in tree["children"]:
        node.add_child(deserialize_tree(child,_depth=_depth+1))

    if node.is_root():
        return node