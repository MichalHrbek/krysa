from typing import Annotated

from fastapi import WebSocket, WebSocketDisconnect, WebSocketException, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

import machines
import orders
from auth import Authenticator
import con
from uid import Uid, gen_uid

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

@dash_router.put("/api/orders/create", response_model=orders.Order)
async def create_order(credentials: Annotated[HTTPBasicCredentials, Depends(dash_security)], order: orders.Order) -> orders.Order:
	auth_dashboard(credentials)
	order.id = gen_uid()
	orders.all[order.id] = order
	await con.broadcast_order_update(order)
	return order

@dash_router.patch("/api/orders/{order_id}", response_model=orders.Order)
async def update_order(credentials: Annotated[HTTPBasicCredentials, Depends(dash_security)], order_id: Uid, order: orders.Order) -> orders.Order:
	auth_dashboard(credentials)
	orders.all[order_id] = orders.all[order_id].model_copy(update=order.model_dump(exclude_unset=True))
	await con.broadcast_order_update(order)
	return orders.all[order_id]

@dash_router.delete("/api/orders/{order_id}")
async def delete_order(credentials: Annotated[HTTPBasicCredentials, Depends(dash_security)], order_id: Uid):
	auth_dashboard(credentials)
	o = orders.all[order_id]
	del orders.all[order_id]
	o.delete()
	await con.broadcast_order_update(o, event="delete")