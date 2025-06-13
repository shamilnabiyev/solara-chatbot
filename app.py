from fastapi import FastAPI
from solara.server.fastapi import app as solara_app

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "test"}


app.mount("/solara/", app=solara_app)
