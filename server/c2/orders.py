from pydantic import BaseModel
from typing import Self
from glob import glob
import pickle
import os

class Order(BaseModel):
	id: str
	name: str
	pending: list[str] = []
	done: list[str] = []
	data: dict
	creation_date: int

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

os.makedirs("data/orders", exist_ok=True)
all = {i.id: i for i in Order.load_all()}