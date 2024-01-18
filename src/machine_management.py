import argparse
import subprocess
import logging
import sys
from abc import ABC, abstractmethod
import uuid
from typing import List, Tuple, Callable, Dict

import requests
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel


################################

# BUSINESS LOGIC

################################

# TODO make this threadsafe

class ContainerManager(ABC):

    @abstractmethod
    def start_container(self, docker_image: str) -> Tuple[int, str]:
        """Start an instance of the container, return the port it's running on and its name"""
        raise NotImplementedError

    @abstractmethod
    def stop_container(self, container_name: str) -> None:
        """Stop the container with the given name"""
        raise NotImplementedError


class SSHContainerManager(ContainerManager):
    """Start and stop containers on a single machine. Assumes passwordless ssh is already set up."""
    STARTING_PORT = 12301

    def __init__(self, machine):
        self.machine = machine
        # only occupied by our linter services
        # maps container name to port
        # container name is random and unique
        self.occupied_ports = dict()
        self._health_check()
        # TODO add destructor which kills containers

    # returns new port which is not occupied by our system
    # TODO we don't check if it is occupied by some other service
    def _get_port(self):
        port = self.STARTING_PORT
        while port in self.occupied_ports.values():
            port += 1
        return port

    def _health_check(self):
        try:
            # TODO: go through working docker containers and check if all expected to work really work
            res = subprocess.run(["ssh", f"{self.machine}", "docker ps"])
            res.check_returncode()
        except subprocess.CalledProcessError as exc:
            raise ValueError("Either ssh or docker not set up properly") from exc

    def start_container(self, docker_image) -> Tuple[int, str]:
        """Start an instance of the container, return the port it's running on and its name"""
        container_name: str = str(uuid.uuid4())

        machine_port = self._get_port()
        # we don't know what ports are currently used by our operating system
        # TODO change to something with error checking
        # TODO this will fail if the port is used
        self.occupied_ports[container_name] = machine_port
        logging.debug("Running container manager command...")

        # add docker which will listen on its port 50051
        # request to [machine_port] of the machine will be forwarded to this docker
        docker_command = f"docker run --rm --detach --name {container_name} -p {machine_port}:{50051} {docker_image}"
        res = subprocess.run(["ssh", f"{self.machine}", docker_command])

        logging.debug("Command completed")
        res.check_returncode()
        logging.info(
            f"Started container {container_name} from {docker_image} on {self.machine}, visible on {machine_port}")
        return machine_port, container_name

    def stop_container(self, container_name):
        res = subprocess.run(["ssh", f"{self.machine}", f"docker stop {container_name}"])
        res.check_returncode()
        self.occupied_ports.pop(container_name)
        logging.info(f"Stopped container {container_name} on {self.machine}")


class RunningLinter(BaseModel):
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


class MachineManager:

    def __init__(self, container_manager_factory: Callable[[str], ContainerManager],
                 load_balancer_url):
        self.container_manager_factory = container_manager_factory
        self.registered_machines = []

        self.container_managers: Dict[str, ContainerManager] = {}

        # for each machine gives current number of linters working there
        self.machine_to_n_linters: Dict[str, int] = {}

        self.running_linters: List[RunningLinter] = []

        # (linter_name, linter_version) -> docker image
        self.linter_images: Dict[Tuple[str, str], str] = {}

        self.load_balancer_url = load_balancer_url

        self.linter_name_to_curr_version: Dict[str, str] = {}

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
        logging.info("Registered linter {linter_name} in version {linter_version}")

    def remove_linter(self, linter_name, linter_version):
        """Kill all linter instances and deregister"""
        logging.info(f"Removing linter named {linter_name}, version {linter_version}")

        # TODO may be we should do something about not existing linter
        self.linter_images.pop((linter_name, linter_version), "ignore if not exists")

        running_instances = [linter for linter in self.running_linters if
                             linter.linter_name == linter_name and linter.linter_version == linter_version]
        for linter in running_instances:
            self.machine_to_n_linters[linter.machine] -= 1
            self.stop_linter_instance(linter.machine, linter.container_name)

        # remove docker images of all versions of linter with [linter_name]
        # versions = [version for (name, version) in self.linter_images.keys() if name == linter_name]
        # for v in versions:
        #     self.linter_images.pop((linter_name, v))

    def list_registered_linters(self):
        return[RegisterLinterData(linter_name=name, linter_version = version, docker_image=image) for (name,version), image in self.linter_images.items()]

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
        # TODO start_container may fail and throw
        port, container_name = cont_manager.start_container(docker_image=docker_image)
        logging.info(
            f"Started linter {linter_name} v {linter_version} instance on {machine} port {port} as {container_name}")
        linter_instance = RunningLinter(machine=machine,
                                        container_name=container_name,
                                        linter_version=linter_version,
                                        linter_name=linter_name,
                                        exposed_port=port)
        self.running_linters.append(linter_instance)
        return container_name, port

    def stop_linter_instance(self, machine, container_name):
        """Kill a linter instance"""
        # TODO stop_container may fail and throw
        self.container_managers[machine].stop_container(container_name)

        linter_instance = None
        for linter in self.running_linters:
            if linter.machine == machine and linter.container_name == container_name:
                linter_instance = linter
                break
        self.running_linters.remove(linter_instance)

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


############################

# FASTAPI-SPECIFIC CODE

############################
class RolloutRequest(BaseModel):
    linter_name: str
    old_version: str
    new_version: str
    traffic_percent_to_new_version: float

class RegisterLinterData(BaseModel):
    linter_name: str
    linter_version: str
    docker_image: str


class StartLintersRequest(BaseModel):
    linter_name: str
    linter_version: str
    n_instances: int

def create_app(load_balancer_url: str):
    app = FastAPI()

    machine_manager = MachineManager(container_manager_factory=SSHContainerManager,
                                     load_balancer_url=load_balancer_url)

    # Machine management

    # Assumes admin will add machine with passwordless ssh set up

    class AddMachine(BaseModel):
        host: str


    @app.post("/add_machine/")
    async def add_machine(request: AddMachine):
        print("got machine request")
        return machine_manager.add_machine(request.host)


    @app.post("delete_machine/")
    async def delete_machine(host: str):
        return machine_manager.delete_machine(host)


    @app.get("/list_machines/")
    async def list_machines() -> List[str]:
        return machine_manager.list_machines()


    # Linter management

    @app.post("/register_linter/")
    async def register_linter(request: RegisterLinterData):
        """Register a new linter or a new version, but without starting any instances."""
        machine_manager.register_linter(request.linter_name, request.linter_version, request.docker_image)


    @app.post("/remove_linter/")
    async def remove_linter(linter_name: str, linter_version: str):
        """Deregister a given linter version, killing all its running instances."""
        return machine_manager.remove_linter(linter_name, linter_version)

    @app.get("/list_registered_linters/")
    async def list_registered_linters() -> List[RegisterLinterData]:
        """List all registered linters and versions"""
        return machine_manager.list_registered_linters()

    @app.get("/list_linters/")
    async def list_linters() -> List[LinterEndpoint]:
        return machine_manager.list_linters()


    @app.get("/list_linters_with_curr_version/")
    async def list_linters_with_curr_version(linter_name: str) -> List[str]:
        return machine_manager.list_linters_with_curr_version(linter_name)


    @app.get("/list_linter_instances/")
    async def list_linter_instances(linter_name: str, linter_version: str) -> List[str]:
        return machine_manager.list_linters_instances(linter_name, linter_version)

    @app.post("/start_linters/")
    async def start_linters(request: StartLintersRequest):
        for i in range(request.n_instances):
            machine = machine_manager.get_machine_with_least_linters()
            machine_manager.start_linter_instance(request.linter_name, request.linter_version, machine)
            machine_manager.machine_to_n_linters[machine] += 1


    # if the percent to new version == 100 we end rollout and change current version
    @app.post("/rollout/")
    async def rollout(request: RolloutRequest):
        if request.traffic_percent_to_new_version == 100:
            machine_manager.linter_name_to_curr_version[request.linter_name] = request.new_version
        requests.post(f"{machine_manager.load_balancer_url}/rollout/", data=request)


    # rollback instantly changes current version to version given in request
    # and makes load_balancer cancel rollout
    @app.post("/rollback/")
    async def rollback(linter_name: str, linter_version: str):
        machine_manager.linter_name_to_curr_version[linter_name] = linter_version
        requests.post(f"{machine_manager.load_balancer_url}/rollback/", params={"linter_name": linter_name})


    ########################
    # DEBUG ENDPOINTS
    ########################
    @app.post("/unsafe_start_linter/")  # debug and admin intervention, works for previously added linter
    async def start_linter(linter_name: str, linter_version: str, host: str) -> Tuple[str, int]:
        return machine_manager.start_linter_instance(linter_name, linter_version, host)


    @app.post("/unsafe_stop_linter/")  # debug and admin intervention
    async def stop_linter(machine: str, container_name: str):
        return machine_manager.stop_linter_instance(machine, container_name)

    return app


def main():
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument('-host', '--host')
    parser.add_argument('-port', '--port')
    parser.add_argument('-lba', '--load_balancer_address')
    parsed_args = parser.parse_args()
    app = create_app(load_balancer_url=parsed_args.load_balancer_address)

    uvicorn.run(app, port=int(parsed_args.port), host=parsed_args.host)


if __name__ == "__main__":
    main()
