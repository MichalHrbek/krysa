from typing import Annotated
from fastapi import Path
from uuid import uuid4

Uid = Annotated[str, Path(min_length=32,max_length=32,pattern=r"^[0-9a-f]{32}$")]

def gen_uid() -> Uid:
	return uuid4().hex