from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import hashlib

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
    h = hashlib.new('sha256')
    h.update(bytes(conversation.content, 'utf-8'))
    conv_id = h.hexdigest()
    
    memory[conv_id] = conversation.content
    print(conv_id, conversation.content)
    return {"id": conv_id}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", port=8000, reload=True)
