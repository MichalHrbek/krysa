from datetime import datetime
from uuid import uuid4
import pickle
from typing import Self
from glob import glob

class Machine:
	def __init__(self, uid: str, version: int, connections: dict[str, list[int]] = {}, host: str = ""):
		self.uid = uid
		self.version = version
		self.connections = connections
		self.orders: list[dict] = []
		if host: self._register_connection(host)
		self.connected = False
		self.save()
	
	def on_connect(self, host):
		self.connected = True
		self._register_connection(host)
		self.save()
	
	def _register_connection(self, host):
		time = int(datetime.now().timestamp())
		if host in self.connections:
			self.connections[host].append(time)
		else:
			self.connections[host] = [time]
	
	def on_disconnect(self, host):
		self.connected = False
	
	def gen_uid() -> str:
		return uuid4().hex

	def save(self):
		with open(f'data/machines/{self.uid}.pkl', 'wb') as f:
			pickle.dump(self, f)
	
	def load_all() -> list[Self]:
		machines = []
		for i in glob("data/machines/*.pkl"):
			with open(i, 'rb') as f:
				m = pickle.load(f)
				m.connected = False
				machines.append(m)
		return machines