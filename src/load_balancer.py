import random
from abc import ABC, abstractmethod
from typing import Tuple, Dict, List

import requests

from linter_client import LinterClient


# used to make load balancer communicate with machine management service
class MachineManagementClient:
    def __init__(self, machine_management_url):
        self.machine_management_url = machine_management_url

    # returns list of host_ports of all linters instances with matching linter name
    # and which are of current version stored in machine management
    def get_linters_with_curr_version(self, linter_name) -> List[str]:
        url = f"{self.machine_management_url}/list_linters_with_curr_version/"
        return requests.get(url, params={"linter_name": linter_name}).json()

    # returns list of host_ports of all linter instances with matching name and version
    def get_linter_instances(self, name, version) -> List[str]:
        url = f"{self.machine_management_url}/list_linter_instances/"
        return requests.get(url, params={"linter_name": name, "linter_version": version}).json()


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
            return False
        return self.sent_to_new / (self.sent_to_old + self.sent_to_new) < desired_percent / 100


class RolloutManager:
    def __init__(self):
        self.linter_name_to_rollout_data: Dict[str, RolloutData] = {}
        self.linter_name_to_traffic_data: Dict[str, TrafficData] = {}

    def start_rollout(self, linter_name: str, rollout_data: RolloutData):
        self.linter_name_to_rollout_data[linter_name] = rollout_data
        self.linter_name_to_traffic_data[linter_name] = TrafficData()

    def is_rollout(self, linter_name):
        return linter_name in self.linter_name_to_rollout_data

    def choose_version(self, linter_name: str) -> str:
        rollout_data = self.linter_name_to_rollout_data[linter_name]

        desired_percent = rollout_data.traffic_percent_to_new_version

        if self.linter_name_to_traffic_data[linter_name].should_send_to_new(desired_percent):
            self.linter_name_to_traffic_data[linter_name].sent_to_new += 1
            return rollout_data.new_version
        else:
            self.linter_name_to_traffic_data[linter_name].sent_to_old += 1
            return rollout_data.old_version

    def end_rollout(self, linter_name: str):
        self.linter_name_to_rollout_data.pop(linter_name, "no rollout")
        self.linter_name_to_traffic_data.pop(linter_name, "no rollout")


class LoadBalancingStrategy(ABC):
    @abstractmethod
    def choose_linter_instance(self, host_port_list: List[str]) -> str:
        raise NotImplementedError


# on average case very good strategy
class RandomStrategy(LoadBalancingStrategy):
    def choose_linter_instance(self, host_port_list: List[str]) -> str:
        return random.choice(host_port_list)


# It's not exactly round-robin, but something that works very similar
class RoundRobinStrategy(LoadBalancingStrategy):
    def __init__(self):
        self.load_counters: dict[str, int] = {}

    # The counters will grow infinitely, but it won't be a problem
    def choose_linter_instance(self, host_port_list: List[str]) -> str:
        for host_port in host_port_list:
            if host_port not in self.load_counters:
                self.load_counters[host_port] = 0

        host_port_with_least_load = host_port_list[0]
        for host_port, load in self.load_counters.items():
            if host_port in host_port_list:
                if load < self.load_counters[host_port_with_least_load]:
                    host_port_with_least_load = host_port

        self.load_counters[host_port_with_least_load] += 1

        return host_port_with_least_load


class LoadBalancer:

    def __init__(self, strategy: LoadBalancingStrategy, machine_management_client: MachineManagementClient,
                 linter_client: LinterClient):
        self.rollout_manager = RolloutManager()
        self.machine_management_client = machine_management_client
        self.strategy = strategy
        self.linter_client = linter_client

    def choose_linter(self, linter_name):

        # first choose needed version, then apply load balancing
        if self.rollout_manager.is_rollout(linter_name):
            version = self.rollout_manager.choose_version(linter_name)
            host_port = self.strategy.choose_linter_instance(
                self.machine_management_client.get_linter_instances(linter_name, version))
        else:
            host_port = self.strategy.choose_linter_instance(
                self.machine_management_client.get_linters_with_curr_version(linter_name))

        return host_port

    def lint_code(self, linter_name: str, code: str) -> Tuple[int, str]:
        # keep the code in memory
        host_port = self.choose_linter(linter_name)

        # Real linting happens here
        try:
            status_code, message = self.linter_client.lint_code(host_port, code)
            return status_code, message
        except RuntimeError:
            status_code, message = 1, "linter error"
            return status_code, message
