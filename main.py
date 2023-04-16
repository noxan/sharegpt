from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

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

@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/load/<name>")
def load(name: str):
    return memory.get(name, "")


@app.post("/save")
async def save(name: str, item: Item):
    memory[name] = item.content
    print("save", item)
    return {"status": "ok"}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
