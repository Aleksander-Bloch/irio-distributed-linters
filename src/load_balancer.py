import argparse
import random
import sys
from abc import ABC, abstractmethod
from typing import Tuple, Dict, List

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


class TrafficData:
    def __init__(self, sent_to_old=0, sent_to_new=0):
        self.sent_to_old = sent_to_old
        self.sent_to_new = sent_to_new

    # also updates send_to_new or sent_to_old
    def should_send_to_new(self, desired_percent: float) -> bool:
        if self.sent_to_old + self.sent_to_new == 0:
            return True
        is_sent_to_new: bool = self.sent_to_new / (self.sent_to_old + self.sent_to_new) < desired_percent / 100
        if is_sent_to_new:
            self.sent_to_new += 1
        else:
            self.sent_to_old += 1
        return is_sent_to_new


class RolloutManager:
    def __init__(self):
        self.linter_name_to_rollout_data: Dict[str, RolloutData] = {}
        self.linter_name_to_traffic_data: Dict[str, TrafficData] = {}

    def start_rollout(self, linter_name: str, rollout_data: RolloutData):
        self.linter_name_to_rollout_data[linter_name] = rollout_data
        self.linter_name_to_traffic_data[linter_name] = TrafficData()

    def is_rollout(self, linter_name):
        return linter_name in self.linter_name_to_rollout_data

    def which_version_should_be_used(self, linter_name: str) -> str:
        rollout_data = self.linter_name_to_rollout_data[linter_name]

        desired_percent = rollout_data.traffic_percent_to_new_version

        if self.linter_name_to_traffic_data[linter_name].should_send_to_new(desired_percent):
            return rollout_data.new_version
        else:
            return rollout_data.old_version


class LoadBalancingStrategy(ABC):
    @abstractmethod
    def choose_linter_instance(self, host_port_list: List[str]) -> str:
        raise NotImplementedError


# on average case very good strategy
class RandomStrategy(LoadBalancingStrategy):
    def choose_linter_instance(self, host_port_list: List[str]) -> str:
        return random.choice(host_port_list)


class RoundRobinStrategy(LoadBalancingStrategy):

    def choose_linter_instance(self, host_port_list: List[str]) -> str:
        raise NotImplementedError


class LoadBalancer:

    def __init__(self, strategy: LoadBalancingStrategy):
        self.machine_management_url = ""

        self.rollout_manager = RolloutManager()

        self.strategy = strategy

    # TODO load balancing strategy
    # for now queries machine management for working linters
    def get_all_linters(self):
        url = f"{self.machine_management_url}/list_linters/"
        return requests.get(url).json()

    # returns list of host_ports of all linters instances with matching linter name
    # and which are of current version stored in machine management
    def get_linters_with_curr_version(self, linter_name) -> List[str]:
        url = f"{self.machine_management_url}/list_linters_with_curr_version/"
        return requests.get(url, params={"linter_name": linter_name}).json()

    # returns list of host_ports of all linter instances with matching name and version
    def get_linter_instances(self, name, version) -> List[str]:
        url = f"{self.machine_management_url}/list_linter_instances/"
        return requests.get(url, params={"linter_name": name, "linter_version": version}).json()

    def get_matching_linters(self, linter_name: str):
        all_linters = self.get_all_linters()
        print(all_linters)
        result = [linter for linter in all_linters if linter["name"] == linter_name]
        # if linter_version is not None and linter_version != "":
        #     result = [linter for linter in result if linter["version"] == linter_version]
        return result

    def get_endpoint(self, linter_name: str, linter_version: str):
        possible_linters = self.get_matching_linters(linter_name)
        return possible_linters[0]["hostport"]  # TODO strategy goes here

    def lint_code(self, linter_name: str, code: str) -> Tuple[int, str]:
        # keep the code in memory

        # TODO retry on failure, rerouting
        # manage rollout
        if self.rollout_manager.is_rollout(linter_name):

            version = self.rollout_manager.which_version_should_be_used(linter_name)
            host_port = self.strategy.choose_linter_instance(self.get_linter_instances(linter_name, version))
        else:
            host_port = self.strategy.choose_linter_instance(self.get_linters_with_curr_version(linter_name))

        # this two lines just send code to linter and get response
        client = LinterClient(host_port)
        status_code, message = client.lint_code(code)

        return status_code, message


############################

# FASTAPI-SPECIFIC CODE

############################

app = FastAPI()
loadbalancer = LoadBalancer(RandomStrategy())


class LintingRequest(BaseModel):
    linter_name: str
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
@app.post("/lint_code/", response_model=ResponseMessage)
async def lint_code_endpoint(request: LintingRequest):
    linter_name = request.linter_name
    code = request.code
    status_code, message = loadbalancer.lint_code(linter_name, code)
    return ResponseMessage(status_code=status_code, message=message)


@app.post("/rollout/")
async def rollout_endpoint(request: RolloutRequest):
    loadbalancer.rollout_manager.start_rollout(request.linter_name, RolloutData(request.old_version,
                                                                                request.new_version,
                                                                                request.traffic_percent_to_new_version))


app.mount("/", StaticFiles(directory="./static", html=True))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-host', '--host')
    parser.add_argument('-port', '--port')
    parser.add_argument('-mma', '--machine_management_address')
    parsed_args = parser.parse_args()
    loadbalancer.machine_management_url = parsed_args.machine_management_address

    uvicorn.run(app, port=int(parsed_args.port), host=parsed_args.host)


if __name__ == "__main__":
    main()
