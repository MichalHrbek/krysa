from pydantic import BaseModel
from typing import Self
from glob import glob
import pickle
import os

class Order(BaseModel):
	id: str
	pending: list[str] = []
	done: list[str] = []
	data: dict
	creation_date: int

	def load_all() -> list[Self]:
		orders = []
		for i in glob("data/orders/*.pkl"):
			with open(i, 'rb') as f:
				o = pickle.load(f)
				orders.append(o)
		return orders

os.makedirs("data/orders", exist_ok=True)
all = {i.id: i for i in Order.load_all()}