from fastapi import WebSocket
from fastapi.encoders import jsonable_encoder
import json, traceback

active_machines: dict[int, WebSocket] = {}
active_dashboards: list[WebSocket] = []

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