from typing import Annotated

from fastapi import WebSocket, WebSocketDisconnect, WebSocketException, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

import machines
import orders
from auth import Authenticator
import con

dash_router = APIRouter()
dash_security = HTTPBasic()

def auth_dashboard(credentials: HTTPBasicCredentials):
	if not Authenticator.verify_user(credentials.username, credentials.password):
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Incorrect username or password",
			headers={"WWW-Authenticate": "Basic"},
		)

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