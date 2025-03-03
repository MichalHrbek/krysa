import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from dashboard_routes import dash_router
from rat_routes import rat_router


# Fastapi setup
if os.environ.get("DOCS"):
	app = FastAPI()
else:
	app = FastAPI(
		docs_url=None,
		redoc_url=None,
	)

if os.environ.get("CORS"):
	app.add_middleware(
		CORSMiddleware,
		allow_origins=["*"],
		allow_credentials=True,
		allow_methods=["*"],
		allow_headers=["*"],
	)

# follow_symlink does the exact opposite of what it's supposed to and also crashes (0.45.3)???? https://github.com/encode/starlette/discussions/2850
app.mount("/dashboard/ui", StaticFiles(directory="dashui", html=True, follow_symlink=False), name="Dashboard UI")
app.include_router(dash_router, prefix="/dashboard")
app.include_router(rat_router, prefix="/machines")