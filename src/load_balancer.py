from typing import Tuple
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from linter_client import LinterClient

################################

# BUSINESS LOGIC

################################

class LoadBalancer:

    def get_endpoint(self, linter_name, linter_version):
        return "localhost:12345"
        raise NotImplementedError()

    def lint_code(self, linter_name: str, linter_version: str, code: str) -> Tuple[int, str]:
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
    linter_version: str | None = None
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
