from pydantic import BaseModel
from uid import Uid
from typing import Optional
from fastapi import WebSocket
from starlette.websockets import WebSocketState
import con

class Tunnel:
	id: Uid
	machine_socket: Optional[WebSocket]
	dashboard_socket: Optional[WebSocket]

	async def close(self):
		if self.machine_socket and self.machine_socket.client_state == WebSocketState.CONNECTED:
			await self.machine_socket.close()
		if self.dashboard_socket and self.dashboard_socket.client_state == WebSocketState.CONNECTED:
			await self.dashboard_socket.close()
	
	def __init__(self, id: Uid, machine_socket: Optional[WebSocket], dashboard_socket: Optional[WebSocket]):
		self.id = id
		self.machine_socket = machine_socket
		self.dashboard_socket = dashboard_socket