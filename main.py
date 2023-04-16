import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response
from pydantic import BaseModel
import hashlib
from typing import Dict
from pymongo import MongoClient

MONGO_URI = "mongodb+srv://cerebral_valley:cerebral_valley_041523@cluster0.byzwutn.mongodb.net/?retryWrites=true&w=majority"

client = MongoClient(MONGO_URI)
db = client["sharegpt"]
memory = db["memory"]

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

@app.get("/", include_in_schema=False)
def root():
    return {"status": "ok"}

@app.get("/.well-known/ai-plugin.json", include_in_schema=False)
def plugin():
    with open(".well-known/ai-plugin.json") as f:
        manifest = f.read()
    return Response(content=manifest, media_type="application/json")

@app.get("/load/id/{conv_id}")
def load(conv_id: str):
    item = memory.find_one({"_id": conv_id})
    return item.get("payload", "") if item else ""

@app.get("/load/name/{name}")
def load(name: str):
    item = memory.find_one({"payload.name": name})
    return item.get("payload", "") if item else ""

@app.post("/save")
async def save(json_payload: Dict):
    json_str = str(json_payload)
    h = hashlib.new("sha256")
    h.update(bytes(json_str, "utf-8"))
    payload_id = h.hexdigest()

    memory.insert_one({"_id": payload_id, "payload": json_payload})
    return {"id": payload_id}

@app.post("/save_prompt")
async def save_prompt_formula(prompt_formula: PromptFormula):
    prompt_name, prompt_body, prompt_parameters = prompt_formula.name, prompt_formula.body, prompt_formula.parameters
    h = hashlib.new("sha256")
    h.update(bytes(prompt_name + str(prompt_body) + str(prompt_parameters), "utf-8"))
    prompt_id = h.hexdigest()

    memory.insert_one(
        {
            "_id": prompt_id,
            "payload": {
                "name": prompt_name,
                "prompt": prompt_body,
                "parameters": prompt_parameters,
            }
        }
    )

    return {"id": prompt_id}

@app.get("/load_prompt/{prompt_id}")
async def load_prompt(prompt_id: str):
    prompt_details = memory.find_one({"_id": prompt_id})
    if prompt_details:
        payload = prompt_details["payload"]
        prompt = f"When the user gives the command `ShareGPT run {payload['name']} {payload['parameters']}`, run the following prompt:\n\n{payload['prompt']}\n\n \
                    but replace anything in square brackets with the users input. The user will specify parameters in the correct order."
        return prompt


app.mount("/.well-known", StaticFiles(directory=".well-known"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
