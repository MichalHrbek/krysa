from typing import Annotated
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect, WebSocketException, APIRouter, HTTPException, Depends, status, Query
from fastapi.security import HTTPBasic, HTTPBasicCredentials

import machines
import orders
from tunnels import Tunnel
from auth import Authenticator
import con
from uid import Uid, gen_uid
from log_listener import LogListener

dash_router = APIRouter()
dash_security = HTTPBasic()
DashboardCredentials = Annotated[HTTPBasicCredentials, Depends(dash_security)]

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

@dash_router.websocket("/logs/ws")
async def logs_websocket_endpoint(websocket: WebSocket, machine: Annotated[Uid | None, Query()] = None, tags:Annotated[list[str] | None, Query()] = None):
	await websocket.accept()
	data = await websocket.receive_json()
	
	authed = Authenticator.verify_user(data["username"], data["password"])
	if not authed:
		raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
	
	l = LogListener(websocket, machine, tags)
	con.listeners.append(l)
	# con.active_dashboards.append(websocket)
	try:
		while True:
			data = await websocket.receive_json()
	except WebSocketDisconnect:
		print("Dashboard disconnected")
	finally:
		con.listeners.remove(l)
		# con.active_dashboards.remove(websocket)

@dash_router.get("/machines")
def get_machines(credentials: DashboardCredentials) -> dict[str,machines.Machine]:
	auth_dashboard(credentials)
	return machines.all

@dash_router.get("/orders")
def get_orders(credentials: DashboardCredentials) -> dict[str,orders.Order]:
	auth_dashboard(credentials)
	return orders.all

@dash_router.put("/orders/create", response_model=orders.Order)
async def create_order(credentials: DashboardCredentials, order: orders.Order) -> orders.Order:
	auth_dashboard(credentials)
	order.id = gen_uid()
	orders.all[order.id] = order
	orders.all[order.id].creation_date = int(datetime.now().timestamp())
	orders.all[order.id].save()
	await orders.all[order.id].send_to_pending()
	return order

@dash_router.patch("/orders/{order_id}", response_model=orders.Order)
async def update_order(credentials: DashboardCredentials, order_id: Uid, order: orders.Order) -> orders.Order:
	auth_dashboard(credentials)
	orders.all[order_id] = orders.all[order_id].model_copy(update=order.model_dump(exclude_unset=True))
	orders.all[order_id].save()
	await orders.all[order_id].send_to_pending()
	return orders.all[order_id]

@dash_router.delete("/orders/{order_id}")
async def delete_order(credentials: DashboardCredentials, order_id: Uid):
	auth_dashboard(credentials)
	o = orders.all[order_id]
	del orders.all[order_id]
	o.delete()
	await con.broadcast_order_update(o, event="delete")

@dash_router.websocket("/shell/{machine_id}")
async def shell_websocket_endpoint(websocket: WebSocket, machine_id: Uid):
	await websocket.accept()
	data = await websocket.receive_json()
	
	authed = Authenticator.verify_user(data["username"], data["password"])
	if not authed:
		raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
	
	if machine_id not in con.active_machines:
		return
	
	tunnel = Tunnel(gen_uid(), None, websocket)
	con.tunnels[tunnel.id] = tunnel

	await con.active_machines[machine_id].send_json({"event":"shell", "tunnel_id":tunnel.id})

	try:
		while True:
			data = await websocket.receive_text()
			if tunnel.machine_socket:
				await tunnel.machine_socket.send_text(data)
	except WebSocketDisconnect:
		pass
	finally:
		await tunnel.close()
		del con.tunnels[tunnel.id]