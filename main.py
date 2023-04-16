import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response
from pydantic import BaseModel

URL = os.environ.get("VERCEL_URL", "http://localhost:8000")


app = FastAPI()

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


@app.get("/.well-known/ai-plugin.json", include_in_schema=False)
def plugin():
    with open(".well-known/ai-plugin.json") as f:
        manifest = f.read()
    content = manifest.replace("{{URL}}", URL)
    return Response(content=content, media_type="application/json")


@app.get("/load/<name>")
def load(name: str):
    return memory.get(name, "")


@app.post("/save")
async def save(name: str, item: Item):
    memory[name] = item.content
    print("save", item)
    return {"status": "ok"}


app.mount("/.well-known", StaticFiles(directory=".well-known"), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
