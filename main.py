from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import chromadb

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
    name: str
    content: str

class Memory():
    def __init__(self):
        self.chroma_client = chromadb.Client()
        self.collection = self.chroma_client.create_collection(name="global")

    def add_by_id(self, id, text): 
        self.collection.add(documents=[text], ids=[id])

    def get_by_id(self, id): 
        return self.collection.get(ids=[id])
    
memory = Memory()


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/load/{name}")
def load(name: str):
    return memory.get_by_id(name)


@app.post("/save")
async def save(item: Item):
    memory.add_by_id(item.name, item.content)
    print("save", item)
    return {"status": "ok"}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
