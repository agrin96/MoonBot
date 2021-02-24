from __future__ import annotations
from typing import List,Dict,Any
import numpy as np

class BaseIndicator:
	def __init__(self):
		self._indicator_buffer = None

	def next_value(self)->Any:
		print("Method not implemented in subclass.")
		return None

	def get_indicator(self)->List[Any]:
		return self._indicator_buffer.get_all()

	def make_decision(self)->str:
		print("Method not implemented in subclass.")
		return ""
	
	def __str__(self)->str:
		"""Copies the numpy array representation style of only showing the first
		and last three values."""
		if len(self._indicator_values) > 6:
			starting = F"{','.join(self._indicator_values[:3])}"
			ending = F"{self._indicator_values[-3:]}]"
			return F"[{starting} ... {ending}]"
		else:
			return str(self._indicator_values)
