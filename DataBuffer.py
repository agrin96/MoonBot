from __future__ import annotations
from typing import List,Any,Dict
import os

class DataBuffer:
	def __init__(self,max_size:int,filename:str=None,header:List[str]=None):
		"""Creates a databuffer. Optionally if filename and header are specified
		then every time a value is pushed to the buffer it will be appended to
		a file with the name specified in the buffers/ folder."""
		self._buffer_size = max_size
		self._buffer = []
		
		self._filepath = None
		if filename and header:
			if not os.path.exists(os.path.join(os.getcwd(),'buffers/')):
				os.mkdir(os.path.join(os.getcwd(),'buffers/'))

			self._filepath = os.path.join(os.getcwd(),'buffers/',filename)

			if os.path.exists(self._filepath):
				os.remove(self._filepath)
				
			with open(self._filepath,"w+") as file:
				file.write(','.join(header) + '\n')


	def get(self,index:int)->Any:
		"""Returns the value at the specified index without deleting. """
		return self._buffer[index]


	def get_all(self)->List[Any]:
		"""Returns the full buffer without flushing it."""
		return self._buffer
	

	def push(self,value:Any):
		"""Add a value to the buffer. Works in a FIFO basis, but deletes
		elements exceeding buffer size."""
		while len(self._buffer) >= self._buffer_size:
			self._buffer.pop(0)
		
		self._buffer.append(value)
		
		if self._filepath:
			with open(self._filepath,"a") as file:
				if isinstance(value,List):
					file.write(','.join([str(v) for v in value]) + '\n')
				elif isinstance(value,Dict):
					file.write(','.join([str(v) for k,v in value.items()])+'\n')
				else:
					file.write(str(value) + '\n')
				


	def pop(self)->Any:
		"""Returns the top value in the buffer and deletes it."""
		return self._buffer.pop(-1)


	def flush(self)->List[Any]:
		"""Return the whole buffer and clear it."""
		temp = self._buffer.copy()
		self._buffer = []
		return temp


	def is_full(self)->bool:
		return len(self._buffer) == self._buffer_size
	
	
	def current_size(self)->int:
		return len(self._buffer)


	def __str__(self)->str:
		"""Copies the numpy array representation style of only showing the first
		and last three values."""
		if len(self._buffer) > 6:
			return F"[{''.join(self._buffer[:3])} ... {','.join(self._buffer[-3:])}]"
		else:
			return str(self._buffer)