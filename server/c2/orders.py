from pydantic import BaseModel
from typing import Self
from glob import glob
import pickle, os, traceback
import con
from uid import Uid

class Order(BaseModel):
	id: str = None
	name: str = ""
	pending: list[str] = []
	done: list[str] = []
	data: dict = {}
	creation_date: int = 0

	def save(self):
		with open(f'data/orders/{self.id}.pkl', 'wb') as f:
			pickle.dump(self, f)
	
	def delete(self):
		if os.path.exists(f'data/orders/{self.id}.pkl'):
			os.remove(f'data/orders/{self.id}.pkl')
	
	def __setattr__(self, key, value):
		super().__setattr__(key, value)
		self.save()

	def load_all() -> list[Self]:
		orders = []
		for i in glob("data/orders/*.pkl"):
			with open(i, 'rb') as f:
				o = pickle.load(f)
				orders.append(o)
		return orders
	
	async def send_to_pending(self):
		for i in self.pending:
			if i in con.active_machines:
				try:
					await con.active_machines[i].send_json({"event":"order", "orders":[self.data]})
				except:
					traceback.print_exc()
				else:
					self.pending.remove(i)
					self.done.append(i)
					await con.broadcast_order_update(self)
		self.save()

os.makedirs("data/orders", exist_ok=True)
all: dict[Uid, Order] = {i.id: i for i in Order.load_all()}