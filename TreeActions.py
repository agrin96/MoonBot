from __future__ import annotations
from typing import List,Dict
from DataStructures.Node import Node
from DataStructures.Terminal import Terminal

def stringify_tree(node:Node,previous:str="",_depth:int=0)->str:
    """Prints a tree like structure to the terminal when passed a node in a 
    tree.
    Parameters:
        previous (str): Can be used to prefix the printed tree with some text.
    Returns the tree structure string representation of the node.
    """
    output = ""
    if node.is_root() or _depth == 0:
        output += F"\n[{node}]"
        if isinstance(node,Terminal):
            return output
    
    children,last = node.children()[:-1],node.children()[-1]
    for child in children:
        if isinstance(child,Terminal):
            output += F"\n{previous}├───{child}"
        else:
            output += F"\n{previous}├───[{child}]"
            output += stringify_tree(node=child,
                                     previous=previous+"│   ",
                                     _depth=_depth+1)

    if isinstance(last,Terminal):
        output += F"\n{previous}└───{last}"
    else:
        output += F"\n{previous}└───[{last}]"
        output += stringify_tree(last,previous=previous+"    ",_depth=_depth+1)
    
    return output


def pprint_tree(node:Node):
    """Convenience method for using stringify to print trees for debugging."""
    print(stringify_tree(node))


def evaluate_next_value(node:Node,candles:List[Dict]):
    """Descend through the tree and update the indicators in each node."""
    if isinstance(node,Terminal):
        return
    
    node.evaluate(candles)
    for child in node.children():
        evaluate_next_value(child,candles)


def make_tree_decision(node:Node)->str:
    """Returns the string decision result of traversing the decision tree."""
    if isinstance(node,Terminal):
        return str(node)

    next_node = node.get_decision()
    return make_tree_decision(next_node)