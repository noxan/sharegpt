import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response
from pydantic import BaseModel
import hashlib

PRODUCTION_URL = "https://sharegpt-psi.vercel.app"
DEVELOPMENT_URL = "http://localhost:8000"
IS_VERCEL = bool(os.environ.get("VERCEL"))
URL = PRODUCTION_URL if IS_VERCEL else DEVELOPMENT_URL


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


@app.get("/", include_in_schema=False)
def root():
    return {"status": "ok"}


@app.get("/.well-known/ai-plugin.json", include_in_schema=False)
def plugin():
    with open(".well-known/ai-plugin.json") as f:
        manifest = f.read()
    content = manifest.replace("{{URL}}", URL)
    return Response(content=content, media_type="application/json")


@app.get("/load/<name>")
def load(conv_id: str):
    """
    returns the conversation stored under the given hash, and generates a summary of it. Do not print out the conversation itself.
    """
    return memory.get(conv_id, "")


@app.post("/save")
async def save(conversation: Item):
    """
    stores the conversation, excluding ShareGPT `save` and `load` commands and ChatGPT's responses with a generated hash as the key
    returns the generated hash in the field 'id'
    """
    h = hashlib.new("sha256")
    h.update(bytes(conversation.content, "utf-8"))
    conv_id = h.hexdigest()

    memory[conv_id] = conversation.content
    print(conv_id, conversation.content)
    return {"id": conv_id}


app.mount("/.well-known", StaticFiles(directory=".well-known"), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
