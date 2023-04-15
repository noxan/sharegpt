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


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/save")
async def save(item: Item):
    print("save", item)
    return {"status": "ok"}
