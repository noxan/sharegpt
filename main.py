import os
from typing import List
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


class Formula(BaseModel):
    name: str
    description: str
    parameters: List[str]


def build_prompt_formula_prompt(formula_name, formula_description, formula_parameters):
    formula = f"{formula_name} is a formula. A formula specifies how the Assistant should complete a task, given parameters. A formula is not code. \n\n Parameters of the formula: \n{formula_parameters} \n\n Description of the formula: \n{formula_description}"
    return formula


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
    """
    stores the conversation, excluding any prompt/response pairs that resulted in a call to this API.
    returns the generated hash in the field 'id'
    """
    json_str = str(json_payload)
    h = hashlib.new("sha256")
    h.update(bytes(json_str, "utf-8"))
    payload_id = h.hexdigest()
    memory.insert_one({"_id": payload_id, "payload": json_payload})
    return {"id": payload_id}


@app.post("/save_formula")
async def save_formula(formula: Formula):
    """
    saves a formula, which is defined with fields name, description, and parameters
    A formula specifies how the Assistant should complete a task, given parameters.
    A formula is not code. The prompt name should contain no spaces.
    The returned id can be used to access the formula
    """
    formula_name, fromula_description, formula_params = (
        formula.name,
        formula.description,
        formula.parameters,
    )
    h = hashlib.new("sha256")
    h.update(
        bytes(formula_name + str(fromula_description) + str(formula_params), "utf-8")
    )
    prompt_id = h.hexdigest()

    formula_prompt = build_prompt_formula_prompt(
        formula_name, fromula_description, formula_params
    )
    memory.insert_one({"_id": prompt_id, "payload": formula_prompt})

    return {"id": prompt_id, "formula_prompt": formula_prompt}


@app.get("/load_formula")
async def load_formula(formula_id: str):
    """
    returns the formula corresponding to the given hash (formula_id) from ShareGPT
    """
    formula_prompt = memory.find_one({"_id": formula_id})
    return formula_prompt


app.mount("/.well-known", StaticFiles(directory=".well-known"), name="static")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
