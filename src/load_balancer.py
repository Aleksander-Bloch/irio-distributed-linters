from typing import Tuple, Optional
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from linter_client import LinterClient
import requests

################################

# BUSINESS LOGIC

################################


def get_all_linters():
    url = "http://localhost:8001/list_linters/"
    response = requests.get(url).json()
    return response

def get_matching_linters(linter_name:str, linter_version: Optional[str]):
    all_linters = get_all_linters()
    print(all_linters)
    result = [linter for linter in all_linters if linter["name"]==linter_name]
    if linter_version is not None and linter_version !="":
        result = [linter for linter in result if linter["version"]==linter_version]
    return result

class LoadBalancer:

    def get_endpoint(self, linter_name: str, linter_version: Optional[str]):
        possible_linters = get_matching_linters(linter_name, linter_version)
        return possible_linters[0]["hostport"]#TODO strategy goes here

    def lint_code(self, linter_name: str, linter_version: Optional[str], code: str) -> Tuple[int, str]:
        # keep the code in memory
        # TODO retry on failure, rerouting
        hostport = self.get_endpoint(linter_name, linter_version)
        client = LinterClient(hostport)
        status_code, message = client.lint_code(code)
        return status_code, message

############################

# FASTAPI-SPECIFIC CODE

############################
app = FastAPI()
loadbalancer = LoadBalancer()
class LintingRequest(BaseModel):
    linter_name: str
    linter_version: Optional[str]  = None
    code: str

class ResponseMessage(BaseModel):
    status_code: int
    message: str

# Order matters here - routes are greedily applied top-down

@app.post("/lint_code/", response_model=ResponseMessage)
async def lint_code_endpoint(request: LintingRequest):
    linter_name = request.linter_name
    linter_version = request.linter_version
    code = request.code
    status_code, message = loadbalancer.lint_code(linter_name, linter_version, code)
    return ResponseMessage(status_code=status_code, message=message)

app.mount("/", StaticFiles(directory="./static", html=True))
