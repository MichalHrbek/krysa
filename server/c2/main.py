import json, os, traceback
from typing import Annotated

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, WebSocketException, APIRouter, Request, HTTPException, Path, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.encoders import jsonable_encoder

from machine import Machine
from order import Order
from auth import Authenticator

# Loading
os.makedirs("data/machines", exist_ok=True)
machines = {i.id: i for i in Machine.load_all()}
orders = {i.id: i for i in Order.load_all()}


# Fastapi setup
if os.environ.get("DOCS"):
	app = FastAPI()
else:
	app = FastAPI(
		docs_url=None,
		redoc_url=None,
	)
dash_security = HTTPBasic()

if os.environ.get("CORS"):
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
		data = json.dumps(jsonable_encoder(data))
	for i in active_dashboards:
		await i.send_text(data)

async def broadcast_update(machine_id):
	await broadcast_to_dashboards({"event":"update","machine":machines[machine_id]})

def auth_dashboard(credentials: HTTPBasicCredentials):
	if not Authenticator.verify_user(credentials.username, credentials.password):
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Incorrect username or password",
			headers={"WWW-Authenticate": "Basic"},
		)

@mach_router.get("/api/{version}/register")
async def register_machine(version: int, request: Request) -> str:
	id = Machine.gen_id()
	machines[id] = Machine(id=id, version=version)
	machines[id].on_register(request.client.host)
	await broadcast_update(id)
	print("Registered: ", id)
	return id

async def send_orders():
	for i in sorted(orders.values(), lambda o: o.creation_date):
		for j in i.pending[:]:
			if j in active_machines:
				try:
					await active_machines[j].send_json({"event":"order", "orders":[i.data]})
				except:
					traceback.print_exc()
				else:
					i.pending.remove(j)
					i.done.append(j)

@mach_router.websocket("/ws/{version}/{machine_id}")
async def machine_websocket_endpoint(websocket: WebSocket, version: int, machine_id: Annotated[str, Path(min_length=32,max_length=32,pattern=r"^[0-9a-fA-F]{32}$")]):
	await websocket.accept()
	try:
		active_machines[machine_id] = websocket
		machines[machine_id].on_connect(websocket.client.host)
		await broadcast_update(machine_id)
		await send_orders(machine_id)
		while True:
			data = await websocket.receive_json()
	finally:
		machines[machine_id].on_disconnect(websocket.client.host)
		await broadcast_update(machine_id)
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
						# machines[i].orders.append(data["order"])
						# TODO: Order api
						await send_orders(i)
						await broadcast_update(i)

	except WebSocketDisconnect:
		active_dashboards.remove(websocket)

@dash_router.get("/api/machines")
def get_machines(credentials: Annotated[HTTPBasicCredentials, Depends(dash_security)]) -> dict[Annotated[str, "Machine id"],Machine]:
	auth_dashboard(credentials)
	return machines

# follow_symlink does the exact opposite of what it's supposed to and also crashes (0.45.3)???? https://github.com/encode/starlette/discussions/2850
app.mount("/dashboard/ui", StaticFiles(directory="dashui", html=True, follow_symlink=False), name="Dashboard UI")
app.include_router(dash_router, prefix="/dashboard")
app.include_router(mach_router, prefix="/machines")