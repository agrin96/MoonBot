from __future__ import annotations
from typing import List,Union,Dict,Any
import uuid

class BaseNode:
    def __init__(self):
        self._parent = None
        self._id = str(uuid.uuid4()).replace("-","")

    def get_parent(self)->BaseNode:
        return self._parent

    def set_parent(self,node:BaseNode):
        self._parent = node
    
    def node_id(self)->str:
        return self._id

    def is_root(self)->bool:
        return self._parent == None

    def get_variable(self)->str:
        return self._variable

    def set_variable(self,new_value:Any):
        self._variable = new_value

    def is_fixed(self)->bool:
        return self._isfixed