from __future__ import annotations
from typing import List,Union,Dict
import numpy as np
import sys
from copy import deepcopy

sys.path.append("../Indicators")
from Indicators.IndicatorVariables import indicator_variables
from .BaseNode import BaseNode
from .Terminal import Terminal

class Node(BaseNode):
    def __init__(self,name:str,indicator:Any):
        super().__init__()
        self._indicator = indicator
        self._name = name
        self._children = []


    @staticmethod
    def node_from_dict(data:Dict)->Node:
        if data["type"] == "NODE":
            variable = [I for I in indicator_variables 
                        if I['name'] == data["variable"]["name"]][0]

            raw_vars = data["variable"]["variables"]
            kwargs = {k:v["value"] for k,v in raw_vars.items()}
            
            indicator = variable["generator"]
            indicator = indicator(**kwargs)

            return Node(name=variable["name"],indicator=indicator)


    def evaluate(self,candles:List[Dict]):
        """Generate the next value of the indicator."""
        self._indicator.next_value(candles)
    

    def get_decision(self)->Node:
        """Return an array mask of which decisions to make."""
        decision = self._indicator.make_decision()
        if decision == "BUY":
            return self._children[0]
        elif decision == "HOLD":
            return self._children[1]
        elif decision == "SELL":
            return self._children[2]


    def add_child(self,node:Union[Node,Terminal],index:int=-1):
        if index == -1:
            self._children.append(node)
        else:
            self._children.insert(index,node)
        node.set_parent(self)


    def children(self)->List:
        return self._children


    def __repr__(self):
        return str(self._indicator)


    def __str__(self):
        return self.__repr__()