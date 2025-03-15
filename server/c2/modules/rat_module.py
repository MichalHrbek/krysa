from pydantic import BaseModel
from typing import ClassVar
from uid import Uid

class RatModule(BaseModel):
	name: ClassVar[str] = "module_example"
	machine_id: Uid

	async def handle_dashboard_message(self, data: dict):
		pass
	
	async def handle_rat_message(self, data: dict):
		pass
	
	def get_client_code() -> str:
		return """
def hello():
	print('Hello from the example module')

modules["examplemodule"] = {}
modules["examplemodule"]["onload"] = hello
modules["examplemodule"]["onconnect"] = hello
modules["examplemodule"]["install"] = hello
modules["examplemodule"]["uninstall"] = hello
modules["examplemodule"]["postinstall"] = hello
"""