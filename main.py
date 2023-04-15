from typing import Annotated, List
from fastapi import Body, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

app = FastAPI()
app.mount("/.well-known", StaticFiles(directory=".well-known"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://chat.openai.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Item(BaseModel):
    content: str

memory = dict()

@app.get("/load/<name>")
def load(name: str):
    return memory.get(name, "")


@app.post("/save")
async def save(name: str, item: Item):
    memory[name] = item.content
    print("save", item)
    return {"status": "ok"}
