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
machines = {i.id: i for i in Machine.load_all()}


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

async def broadcast_update(machine_id):
	await broadcast_to_dashboards({"event":"update","machines":[machines[machine_id]]})

@mach_router.get("/api/{version}/register")
def register_machine(version: int, request: Request) -> str:
	id = Machine.gen_id()
	machines[id] = Machine(id=id, version=version)
	machines[id].on_register(request.client.host)
	print("Registered: ", id)
	return id

async def send_orders(machine_id: str):
	if machine_id not in active_machines:
		return
	if machines[machine_id].orders:
		await active_machines[machine_id].send_json({"event":"order", "orders":machines[machine_id].orders})
	machines[machine_id].orders = []

@mach_router.websocket("/ws/{version}/{machine_id}")
async def machine_websocket_endpoint(websocket: WebSocket, version: int, machine_id: Annotated[str, Path(min_length=32,max_length=32,pattern=r"^[0-9a-fA-F]{32}$")]):
	await websocket.accept()
	active_machines[machine_id] = websocket
	try:
		machines[machine_id].on_connect(websocket.client.host)
		await broadcast_to_dashboards({"event":"connected", "machine": machines[machine_id].__dict__})
		await send_orders(machine_id)
		while True:
			data = await websocket.receive_json()
	except:# WebSocketDisconnect:
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
					for i in data["machine_ids"]:
						machines[i].orders.append(data["order"])
						await send_orders(i)

	except WebSocketDisconnect:
		active_dashboards.remove(websocket)

@dash_router.get("/api/machines")
def get_machines(credentials: Annotated[HTTPBasicCredentials, Depends(dash_security)]) -> dict[Annotated[str, "Machine id"],Machine]:
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