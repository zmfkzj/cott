from fastapi import FastAPI
from integrations.fastapi_hello import read_root

app = FastAPI()
app.get("/")(read_root)
