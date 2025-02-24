from fastapi import FastAPI, WebSocket, WebSocketDisconnect, APIRouter, Request, HTTPException, Path
import json
from machine import Machine
import os
from fastapi.middleware.cors import CORSMiddleware
from typing import Annotated

# Loading
os.makedirs("machines", exist_ok=True)
machines = {i.uid: i for i in Machine.load_all()}


# Fastapi setup
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

dash_router = APIRouter()
mach_router = APIRouter()


# Runtime
active_machines: dict[int, WebSocket] = {}
active_dashboards: list[WebSocket] = []

async def broadcast_to_dashboards(data):
	if not active_dashboards:
		return
	if type(data) != str:
		data = json.dumps(data)
	for i in active_dashboards:
		await i.send_text(data)

@mach_router.get("/api/{version}/register")
def register_machine(version: int, request: Request):
	uid = Machine.gen_uid()
	m = Machine(uid, version, request.client.host)
	machines[uid] = m
	print("Registered: ", uid)
	return uid

@mach_router.websocket("/ws/{version}/{machine_id}")
async def machine_websocket_endpoint(websocket: WebSocket, version: int, machine_id: Annotated[str, Path(min_length=32,max_length=32,pattern=r"^[0-9a-fA-F]{32}$")]):
	await websocket.accept()
	active_machines[machine_id] = websocket
	machines[machine_id].on_connect(websocket.client.host)
	await broadcast_to_dashboards({"event":"connected", "machine": machines[machine_id].__dict__})
	try:
		while True:
			data = await websocket.receive_json()
			# await manager.send_personal_message(f"You wrote: {data}", websocket)
	except WebSocketDisconnect:
		machines[machine_id].on_disconnect(websocket.client.host)
		await broadcast_to_dashboards({"event":"disconnected", "machine": machines[machine_id].__dict__})
		del active_machines[machine_id]

@dash_router.websocket("/ws")
async def dashboard_websocket_endpoint(websocket: WebSocket):
	await websocket.accept()
	active_dashboards.append(websocket)
	try:
		while True:
			data = await websocket.receive_json()
			match data["event"]:
				case "order":
					for i in data["ids"]:
						active_machines[i].send(data["order"])
	except WebSocketDisconnect:
		active_dashboards.remove(websocket)

@dash_router.get("/api/machines")
def get_machines():
	return machines

app.include_router(dash_router, prefix="/dashboard")
app.include_router(mach_router, prefix="/machines")