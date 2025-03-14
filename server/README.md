# Dashboard
### Setup
`npm install`
### Run
Dev: `npm run dev`  
Build: `npm run build`  

# C2 server
### Setup
`pip install -r requirements.txt`
### Run
Dev: `CORS=1 DOCS=1 fastapi dev main.py`  
Prod: `fastapi run main.py`
### Auth
Create a username and password with `python3 auth.py`

# Deployment
`./build.sh`  
`docker run -p 8000:8000 krysa`