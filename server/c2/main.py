import json, os
from typing import Annotated

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, WebSocketException, APIRouter, Request, HTTPException, Path, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles

from machine import Machine
from auth import Authenticator

# Loading
os.makedirs("data/machines", exist_ok=True)
machines = {i.uid: i for i in Machine.load_all()}


# Fastapi setup
app = FastAPI()
dash_security = HTTPBasic()

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
	data = await websocket.receive_json()
	
	authed = Authenticator.verify_user(data["username"], data["password"])
	if not authed:
		raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

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
def get_machines(credentials: Annotated[HTTPBasicCredentials, Depends(dash_security)]):
	if not Authenticator.verify_user(credentials.username, credentials.password):
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Incorrect username or password",
			headers={"WWW-Authenticate": "Basic"},
		)
	return machines

# follow_symlink does the exact opposite of what it's supposed to and also crashes (0.45.3)???? https://github.com/encode/starlette/discussions/2850
app.mount("/dashboard/ui", StaticFiles(directory="dashui", html=True, follow_symlink=False), name="Dashboard UI")
app.include_router(dash_router, prefix="/dashboard")
app.include_router(mach_router, prefix="/machines")