import json, os, traceback
from typing import Annotated

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, WebSocketException, APIRouter, Request, HTTPException, Path, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.encoders import jsonable_encoder

import machines
import orders
from auth import Authenticator
import con

ID_TYPE = Annotated[str, Path(min_length=32,max_length=32,pattern=r"^[0-9a-fA-F]{32}$")]


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

def auth_dashboard(credentials: HTTPBasicCredentials):
	if not Authenticator.verify_user(credentials.username, credentials.password):
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Incorrect username or password",
			headers={"WWW-Authenticate": "Basic"},
		)

@mach_router.get("/api/{version}/register")
async def register_machine(version: int, request: Request) -> str:
	id = machines.Machine.gen_id()
	machines.all[id] = machines.Machine(id=id, version=version)
	await machines.all[id].on_register(request.client.host)
	print("Registered: ", id)
	return id

@mach_router.websocket("/ws/{version}/{machine_id}")
async def machine_websocket_endpoint(websocket: WebSocket, version: int, machine_id: ID_TYPE):
	await websocket.accept()
	try:
		con.active_machines[machine_id] = websocket
		await machines.all[machine_id].on_connect(websocket.client.host)
		while True:
			data = await websocket.receive_json()
	finally:
		await machines.all[machine_id].on_disconnect(websocket.client.host)

@dash_router.websocket("/ws")
async def dashboard_websocket_endpoint(websocket: WebSocket):
	await websocket.accept()
	data = await websocket.receive_json()
	
	authed = Authenticator.verify_user(data["username"], data["password"])
	if not authed:
		raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

	con.active_dashboards.append(websocket)
	try:
		while True:
			data = await websocket.receive_json()
	except WebSocketDisconnect:
		print("Dashboard disconnected")
	finally:
		con.active_dashboards.remove(websocket)

@dash_router.get("/api/machines")
def get_machines(credentials: Annotated[HTTPBasicCredentials, Depends(dash_security)]) -> dict[str,machines.Machine]:
	auth_dashboard(credentials)
	return machines.all

@dash_router.get("/api/orders")
def get_orders(credentials: Annotated[HTTPBasicCredentials, Depends(dash_security)]) -> dict[str,orders.Order]:
	auth_dashboard(credentials)
	return orders.all

# follow_symlink does the exact opposite of what it's supposed to and also crashes (0.45.3)???? https://github.com/encode/starlette/discussions/2850
app.mount("/dashboard/ui", StaticFiles(directory="dashui", html=True, follow_symlink=False), name="Dashboard UI")
app.include_router(dash_router, prefix="/dashboard")
app.include_router(mach_router, prefix="/machines")