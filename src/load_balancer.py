import argparse
import sys
from typing import Tuple, Dict

import requests
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from linter_client import LinterClient


################################

# BUSINESS LOGIC

################################

# data describing the rollout phase
class RolloutData:
    old_version: str
    new_version: str
    traffic_percent_to_new_version: float

    def __init__(self, old_version, new_version, traffic_percent_to_new_version):
        self.old_version = old_version
        self.new_version = new_version
        self.traffic_percent_to_new_version = traffic_percent_to_new_version


class LoadBalancer:

    def __init__(self):
        self.machine_management_url = ""
        # maps linter name to the rollout data if there is a rollout for particular linter
        self.linter_name_to_rollout_data: Dict[str, RolloutData] = {}

    # TODO load balancing strategy
    # for now queries machine management for working linters
    def get_all_linters(self):
        url = f"{self.machine_management_url}/list_linters/"
        response = requests.get(url).json()
        return response

    def get_matching_linters(self, linter_name: str):
        all_linters = self.get_all_linters()
        print(all_linters)
        result = [linter for linter in all_linters if linter["name"] == linter_name]
        # if linter_version is not None and linter_version != "":
        #     result = [linter for linter in result if linter["version"] == linter_version]
        return result

    def get_endpoint(self, linter_name: str):
        possible_linters = self.get_matching_linters(linter_name)
        return possible_linters[0]["hostport"]  # TODO strategy goes here

    def lint_code(self, linter_name: str, code: str) -> Tuple[int, str]:
        # keep the code in memory
        # TODO retry on failure, rerouting
        hostport = self.get_endpoint(linter_name)

        # this two lines just send code to linter and get response
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
    # linter_version: Optional[str] = None
    code: str


class ResponseMessage(BaseModel):
    status_code: int
    message: str


class RolloutRequest(BaseModel):
    linter_name: str
    old_version: str
    new_version: str
    traffic_percent_to_new_version: float


# Order matters here - routes are greedily applied top-down
# FIXME get from client only linter_name and code, but not version
@app.post("/lint_code/", response_model=ResponseMessage)
async def lint_code_endpoint(request: LintingRequest):
    linter_name = request.linter_name
    # linter_version = request.linter_version
    code = request.code
    status_code, message = loadbalancer.lint_code(linter_name, code)
    return ResponseMessage(status_code=status_code, message=message)


@app.post("/rollout/")
async def rollout_endpoint(request: RolloutRequest):
    loadbalancer.linter_name_to_rollout_data[request.linter_name] = RolloutData(request.old_version,
                                                                                request.new_version,
                                                                                request.traffic_percent_to_new_version)


app.mount("/", StaticFiles(directory="./static", html=True))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-host', '--host')
    parser.add_argument('-port', '--port')
    parser.add_argument('-mma', '--load_balancer_address')
    parsed_args = parser.parse_args()
    loadbalancer.machine_management_url = parsed_args.mma

    uvicorn.run(app, port=int(parsed_args.port), host=parsed_args.host)


if __name__ == "__main__":
    main()
