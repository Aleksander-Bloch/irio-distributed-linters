from fastapi import FastAPI
from pydantic import BaseModel
import os

app = FastAPI()


def get_endpoint(linter_name, linter_version):
    raise NotImplementedError()

def get_result_from_endpoint(endpoint, code):
    raise NotImplementedError()

def lint_code(linter_name: str, linter_version: str, code: str):
    # keep the code in memory
    # TODO retry on failure, rerouting
    endpoint = get_endpoint(linter_name, linter_version)
    linting_result = get_result_from_endpoint(endpoint, code)
    return {"linting result": linting_result}




class LintingRequest(BaseModel):
    linter_name: str
    linter_version: str | None = None
    code: str

@app.post("lint_code")
async def lint_code_endpoint(request: LintingRequest):
    linter_name = request.linter_name
    linter_version = request.linter_version
    code = request.code
    return lint_code(linter_name, linter_version, code)