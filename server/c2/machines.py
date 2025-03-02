from datetime import datetime
from uuid import uuid4
import pickle
from typing import Self
from glob import glob
from pydantic import BaseModel
import os
import orders
import con

class Machine(BaseModel):
	id: str
	version: int
	connections: dict[str, list[int]] = {}
	connected: bool = False

	async def on_register(self, host):
		self._register_connection(host)
		self.save()
		await con.broadcast_update(all[id])
	
	async def on_connect(self, host):
		self.connected = True
		self._register_connection(host)
		self.save()
		await self.send_pending_orders()
		await con.broadcast_update(self)
	
	def _register_connection(self, host):
		time = int(datetime.now().timestamp())
		if host in self.connections:
			self.connections[host].append(time)
		else:
			self.connections[host] = [time]
	
	async def on_disconnect(self, host):
		self.connected = False
		try:
			await con.broadcast_update(self)
		except:
			pass
		finally:
			del con.active_machines[self.id]
	
	def gen_id() -> str:
		return uuid4().hex

	def save(self):
		with open(f'data/machines/{self.id}.pkl', 'wb') as f:
			pickle.dump(self, f)
	
	def load_all() -> list[Self]:
		machines = []
		for i in glob("data/machines/*.pkl"):
			with open(i, 'rb') as f:
				m = pickle.load(f)
				m.connected = False
				machines.append(m)
		return machines
	
	def get_pending_orders(self) -> list[orders.Order]:
		return [i for i in orders.all.values() if self.id in i.pending]
	
	async def send_pending_orders(self):
		if self.id not in con.active_machines:
			return
		pending = self.get_pending_orders()
		try:
			await con.active_machines[id].send_json({"event":"order", "orders":[i.data for i in pending]})
		except:
			print(f"Could't send orders to {self.id}")
		else:
			for i in pending:
				i.pending.remove(self.id)
				i.done.append(self.id)


os.makedirs("data/machines", exist_ok=True)
all = {i.id: i for i in Machine.load_all()}