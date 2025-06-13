from fastapi import FastAPI
import solara.server.fastapi

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "test"}


app.mount("/solara/", app=solara.server.fastapi.app)
