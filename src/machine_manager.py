import logging
import threading
import time
from typing import Callable, Dict, List, Tuple

import requests
from pydantic import BaseModel

from container_manager import ContainerManager


class LoadBalancerClient:
    def __init__(self, load_balancer_url):
        self.load_balancer_url = load_balancer_url

    def rollout(self, request):
        requests.post(f"{self.load_balancer_url}/rollout/", json=request.model_dump())

    def rollback(self, linter_name):
        requests.post(f"{self.load_balancer_url}/rollback/", params={"linter_name": linter_name})


class RunningLinter(BaseModel):
    # machine means only host not port, because we connect by ssh using default ssh port
    machine: str
    container_name: str
    linter_version: str
    linter_name: str
    exposed_port: int

    def get_host_port(self):
        return f"{self.machine.split(':')[0]}:{self.exposed_port}"


# The public counterpart to RunningLinter
class LinterEndpoint(BaseModel):
    hostport: str
    name: str
    version: str


class RegisterLinterData(BaseModel):
    linter_name: str
    linter_version: str
    docker_image: str


class StartLintersRequest(BaseModel):
    linter_name: str
    linter_version: str
    n_instances: int


class RolloutRequest(BaseModel):
    linter_name: str
    old_version: str
    new_version: str
    traffic_percent_to_new_version: float


class AutoRolloutRequest(BaseModel):
    linter_name: str
    old_version: str
    new_version: str

    # time_steps[i] indicates the time we should wait before rollout stage traffic_percent_steps[i]
    # (time from previous rollout stage in seconds)
    time_steps: List[int]

    # indicates percent send to new version in nth rollout stage
    traffic_percent_steps: List[int]


class MachineManager:

    def __init__(self, container_manager_factory: Callable[[str], ContainerManager],
                 load_balancer_client: LoadBalancerClient):
        self.container_manager_factory = container_manager_factory
        self.load_balancer_client = load_balancer_client

        self.registered_machines = []

        self.container_managers: Dict[str, ContainerManager] = {}

        # for each machine gives current number of linters working there
        self.machine_to_n_linters: Dict[str, int] = {}

        self.running_linters: List[RunningLinter] = []

        # (linter_name, linter_version) -> docker image
        self.linter_images: Dict[Tuple[str, str], str] = {}

        self.linter_name_to_curr_version: Dict[str, str] = {}

        self.rollout_lock = threading.Lock()
        # tells if there is auto rollout active for current linter
        self.linter_name_to_auto_rollout: Dict[str, bool] = {}

    #############
    # MACHINES
    #############
    def add_machine(self, host: str) -> None:
        container_manager = self.container_manager_factory(host)
        self.registered_machines.append(host)
        self.container_managers[host] = container_manager
        self.machine_to_n_linters[host] = 0
        logging.info(f"Added machine {host}")

    def delete_machine(self, host: str) -> None:
        self.registered_machines.remove(host)
        self.container_managers.pop(host)
        self.machine_to_n_linters.pop(host)
        logging.info(f"Removed machine {host}")

    def list_machines(self):
        return self.registered_machines

    #############
    # LINTER VERSIONS
    #############
    def register_linter(self, linter_name, linter_version, docker_image):
        self.linter_images[linter_name, linter_version] = docker_image
        logging.info(f"Registered linter {linter_name} in version {linter_version}")

    def remove_linter(self, linter_name, linter_version):
        """Kill all linter instances and deregister"""
        logging.info(f"Removing linter named {linter_name}, version {linter_version}")

        self.linter_images.pop((linter_name, linter_version), "ignore if not exists")

        running_instances = [linter for linter in self.running_linters if
                             linter.linter_name == linter_name and linter.linter_version == linter_version]
        for linter in running_instances:
            self.stop_linter_instance(linter.machine, linter.container_name)

        # remove docker images of all versions of linter with [linter_name]
        # versions = [version for (name, version) in self.linter_images.keys() if name == linter_name]
        # for v in versions:
        #     self.linter_images.pop((linter_name, v))

    def list_registered_linters(self):
        return [RegisterLinterData(linter_name=name, linter_version=version, docker_image=image) for
                (name, version), image in self.linter_images.items()]

    #############
    # LINTER INSTANCES
    #############
    def start_linter_instance(self, linter_name, linter_version, machine) -> Tuple[str, int]:
        """Start a new instance of a given registered linter"""
        logging.info(f"Starting linter {linter_name} v {linter_version} instance on {machine}")

        # if we add the very first linter of the name [linter_name] set current version
        # for its name to its version
        if linter_name not in self.linter_name_to_curr_version:
            self.linter_name_to_curr_version[linter_name] = linter_version

        cont_manager = self.container_managers[machine]
        docker_image = self.linter_images[linter_name, linter_version]
        port, container_name = cont_manager.start_container(docker_image=docker_image)
        logging.info(
            f"Started linter {linter_name} v {linter_version} instance on {machine} port {port} as {container_name}")
        linter_instance = RunningLinter(machine=machine,
                                        container_name=container_name,
                                        linter_version=linter_version,
                                        linter_name=linter_name,
                                        exposed_port=port)

        self.running_linters.append(linter_instance)

        # If we appended a new running linter we can safely increase this dict
        self.machine_to_n_linters[machine] += 1

        return container_name, port

    def stop_linter_instance(self, machine, container_name):
        """Kill a linter instance"""
        self.container_managers[machine].stop_container(container_name)

        linter_instance = None
        for linter in self.running_linters:
            if linter.machine == machine and linter.container_name == container_name:
                linter_instance = linter
                break
        self.running_linters.remove(linter_instance)
        self.machine_to_n_linters[machine] -= 1

    def list_linters(self) -> List[LinterEndpoint]:
        # hostport: get only host from machine and add port to particular linter
        return [LinterEndpoint(hostport=linter.get_host_port(),
                               name=linter.linter_name,
                               version=linter.linter_version) for linter in self.running_linters]

    # returns list of host_ports of linter instances with linter_name and current version
    def list_linters_with_curr_version(self, linter_name: str):
        return [linter.get_host_port() for linter in self.running_linters if linter.linter_name == linter_name
                and linter.linter_version == self.linter_name_to_curr_version[linter_name]]

    def list_linters_instances(self, linter_name: str, linter_version: str):
        return [linter.get_host_port() for linter in self.running_linters if linter.linter_name == linter_name
                and linter.linter_version == linter_version]

    def get_machine_with_least_linters(self) -> str:
        return min(self.machine_to_n_linters, key=self.machine_to_n_linters.get)

    def start_linters(self, request: StartLintersRequest):
        for i in range(request.n_instances):
            machine = self.get_machine_with_least_linters()
            self.start_linter_instance(request.linter_name, request.linter_version, machine)

    # if the percent to new version == 100 we end rollout and change current version
    def rollout(self, request: RolloutRequest):
        logging.debug(f"got request: linter_name = {request.linter_name},"
                      f" old_version = {request.old_version}, new_version = {request.new_version},"
                      f" traffic_to_new = {request.traffic_percent_to_new_version}")

        if request.traffic_percent_to_new_version == 100:
            self.linter_name_to_curr_version[request.linter_name] = request.new_version
            logging.info(
                f"got 100 percent rollout changed current version of {request.linter_name} to {request.new_version}")
        self.load_balancer_client.rollout(request)

    def auto_rollout(self, request: AutoRolloutRequest):
        name = request.linter_name
        old_version = request.old_version
        new_version = request.new_version
        time_steps = request.time_steps
        traffic_steps = request.traffic_percent_steps

        self.rollout_lock.acquire()
        self.linter_name_to_auto_rollout[name] = True
        self.rollout_lock.release()

        for curr_time_step, curr_traffic_step in zip(time_steps, traffic_steps):
            time.sleep(curr_time_step)

            self.rollout_lock.acquire()

            stop_rollout = name not in self.linter_name_to_auto_rollout

            if not stop_rollout:
                self.rollout(RolloutRequest(linter_name=name, old_version=old_version, new_version=new_version,
                                            traffic_percent_to_new_version=curr_traffic_step))

            self.rollout_lock.release()

            if stop_rollout:
                return

    # rollback instantly changes current version to version given in request
    # and makes load_balancer cancel rollout
    # if the version is not specified rollback to current version
    def rollback(self, linter_name, linter_version=None):
        if linter_version is not None:
            self.linter_name_to_curr_version[linter_name] = linter_version

        self.rollout_lock.acquire()
        # does not have effect if there is no automatic rollout
        self.linter_name_to_auto_rollout.pop(linter_name, "accept absence of key")
        self.load_balancer_client.rollback(linter_name)
        self.rollout_lock.release()

    def restart_broken_linters(self, host_ports):

        to_restart = list(filter(lambda l: l.get_host_port() in host_ports, self.running_linters))

        for linter in to_restart:
            self.stop_linter_instance(linter.machine, linter.container_name)
            time.sleep(1)
            self.start_linter_instance(linter.linter_name, linter.linter_version, linter.machine)
