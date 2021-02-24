from __future__ import annotations
from typing import Dict,List
from .BaseNode import BaseNode

class Terminal(BaseNode):
    def __init__(self,var_name:str,is_fixed:bool=False):
        super().__init__()
        self._variable = var_name
        self._parent = None
        self._isfixed = is_fixed

    @staticmethod
    def terminal_from_dict(data:Dict)->Terminal:
        if data["type"] == "TERMINAL":
            return Terminal(
                var_name=data["variable"],
                is_fixed=data["fixed"])

    def node_as_dict(self)->Dict:
        return {
            "type":"TERMINAL",
            "variable":self._variable,
            "fixed":self._isfixed}

    def __repr__(self):
        return F"{self._variable}"

    def __str__(self):
        return self.__repr__()
