from fastapi import WebSocket
from fastapi.encoders import jsonable_encoder
import json, traceback
from log_listener import LogListener
from uid import Uid

active_machines: dict[int, WebSocket] = {}
active_dashboards: list[WebSocket] = []
listeners: list[LogListener] = []

async def broadcast_to_dashboards(data):
	if not active_dashboards:
		return
	if type(data) != str:
		data = json.dumps(jsonable_encoder(data))
	for i in active_dashboards:
		try:
			await i.send_text(data)
		except:
			traceback.print_exc()


async def broadcast_machine_update(machine,event="update"):
	await broadcast_to_dashboards({"event":event,"machine":machine})

async def broadcast_order_update(order,event="update"):
	await broadcast_to_dashboards({"event":event,"order":order})

async def broadcast_log(machine:Uid, data:dict|None=None, tags:list[str]|None=None):
	for i in listeners:
		if ((not i.machine) or machine == i.machine) and ((not i.tags) or any(t in i.tags for t in tags)):
			await i.socket.send_json({
				"machine": machine,
				"tags": tags,
				"data": data,
			})