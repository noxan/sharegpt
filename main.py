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

class PromptFormula(BaseModel):
    name: str
    body: str
    parameters: list

prompt_memory = dict()
conversation_memory = dict()


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
    return conversation_memory.get(conv_id, "")


@app.post("/save")
async def save(conversation: Item):
    """
    stores the conversation, excluding ShareGPT `save` and `load` commands and ChatGPT's responses with a generated hash as the key
    returns the generated hash in the field 'id'
    """
    h = hashlib.new("sha256")
    h.update(bytes(conversation.content, "utf-8"))
    conv_id = h.hexdigest()
    
    conversation_memory[conv_id] = conversation.content
    return {"id": conv_id}

@app.post('/save_prompt')
async def save_prompt_formula(prompt_formula: PromptFormula):
    """
    saves a prompt formula, which is defined with fields name, body, and parameters
    generates a hash for the formula which can be used to load it later
    """
    
    prompt_name, prompt_body, prompt_parameters = prompt_formula.name, prompt_formula.body, prompt_formula.parameters
    h = hashlib.new('sha256')
    h.update(bytes(prompt_name + str(prompt_body) + str(prompt_parameters), 'utf-8'))
    prompt_id = h.hexdigest()

    prompt_memory[prompt_id] = {
        'name': prompt_name,
        'prompt': prompt_body,
        'parameters': prompt_parameters
    }

    return {"id": prompt_id}

@app.get('/load_prompt')
async def load_prompt(prompt_id: str):
    """
    returns the prompt stored under the given hash (prompt_id)
    interpret the text that is returned and do what it says
    """
    prompt_details = prompt_memory.get(prompt_id, "")
    if prompt_details:
        prompt = f"When the user gives the command `ShareGPT run {prompt_details['name']} {prompt_details['parameters']}`, run the following prompt:\n\n{prompt_details['prompt']}\n\n \
                    but replace anything in square brackets with the users input. The user will specify parameters in the correct order."
        return prompt

app.mount("/.well-known", StaticFiles(directory=".well-known"), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
