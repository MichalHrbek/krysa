from fastapi import WebSocket
from fastapi.encoders import jsonable_encoder
import json

active_machines: dict[int, WebSocket] = {}
active_dashboards: list[WebSocket] = []

async def broadcast_to_dashboards(data):
	if not active_dashboards:
		return
	if type(data) != str:
		data = json.dumps(jsonable_encoder(data))
	for i in active_dashboards:
		await i.send_text(data)

async def broadcast_update(machine):
	await broadcast_to_dashboards({"event":"update","machine":machine})