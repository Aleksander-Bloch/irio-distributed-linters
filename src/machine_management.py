import subprocess
import logging
import sys
from abc import ABC, abstractmethod
import uuid
from typing import List, Tuple, Callable, Dict
from fastapi import FastAPI
from pydantic import BaseModel

################################

# BUSINESS LOGIC

################################

#TODO make this threadsafe

class ContainerManager(ABC):

    @abstractmethod
    def start_container(self, docker_image: str) -> Tuple[int, str]:
        "Start an instance of the container, return the port it's running on and its name"
        raise NotImplementedError

    @abstractmethod
    def stop_container(self, container_name: str) -> None:
        "Stop the container with the given name"
        raise NotImplementedError


class SSHContainerManager:
    "Start and stop containers on a single machine. Assumes passwordless ssh is already set up."
    STARTING_PORT = 12301

    def __init__(self, machine):
        self.machine = machine
        self.occupied_ports = dict()
        self._health_check()
        #TODO add destructor which kills containers

    def _get_port(self):
        port = self.STARTING_PORT
        while port in self.occupied_ports.values():
            port+=1
        return port
    
    def _health_check(self):
        try:
            res = subprocess.run(["ssh", f"{self.machine}", "docker ps"])
            res.check_returncode()
        except subprocess.CalledProcessError as exc:
            raise ValueError("Either ssh or docker not set up properly") from exc

    
    def start_container(self, docker_image) -> Tuple[int, str]:
        "Start an instance of the container, return the port it's running on and its name"
        container_name: str = str(uuid.uuid4())

        machine_port = self._get_port()
        #TODO change to something with error checking
        #TODO this will fail if the port is used
        self.occupied_ports[container_name]=machine_port
        logging.debug("Running container manager command...")
        res = subprocess.run(["ssh", f"{self.machine}", f"docker run --rm --detach --name {container_name} -p {machine_port}:{50051} {docker_image}"])
        logging.debug("Command completed")
        res.check_returncode()
        logging.info(f"Started container {container_name} from {docker_image} on {self.machine}, visible on {machine_port}")
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


# The public counterpart to RunningLinter
class LinterEndpoint(BaseModel):
    hostport: str
    name: str
    version: str

class MachineManager:

    def __init__(self, container_manager_factory: Callable[[str], ContainerManager]):
        self.container_manager_factory = container_manager_factory
        self.registered_machines = []
        self.container_managers: Dict[str, ContainerManager] = {}

        self.running_linters: List[RunningLinter] = []
        self.linter_images: Dict[Tuple[str, str], str] = {}

    def add_machine(self, ip_port: str) -> None:
        container_manager = self.container_manager_factory(ip_port)
        self.registered_machines.append(ip_port)
        self.container_managers[ip_port] = container_manager
        logging.info(f"Added machine {ip_port}")

    def delete_machine(self, ip_port: str) -> None:
        self.registered_machines.remove(ip_port)
        self.container_managers.pop(ip_port)
        logging.info(f"Removed machine {ip_port}")

    def list_machines(self):
        return self.registered_machines
    
    def add_new_linter(self, linter_name, linter_version, docker_image):

        self.linter_images[linter_name, linter_version] = docker_image

        is_update = False
        for linter in self.running_linters:
            if linter.linter_name == linter_name:
                logging.debug(f"Detected previous version of linter {linter_name}")
                is_update = True
                break

        if is_update:
            logging.info(f"Updating linter {linter_name} to version {linter_version}")
            # Logic for staged update goes here.
            raise NotImplementedError
        else:
            logging.info(f"Creating first version of linter {linter_name}")
            #TODO have a smarter placement algorithm, maybe strategy?

            if not self.registered_machines:
                raise ValueError("No machines available to run linter")
            for machine in self.registered_machines:
                self.start_linter_instance(linter_name, linter_version, machine)

    
    def remove_linter(self, linter_name):
        "Kill all linter instances and deregister"
        logging.info(f"Removing all versions of linter {linter_name}")

        #TODO what do we do for nonexistent linters?
        running_instances = [l for l in self.running_linters if l.linter_name==linter_name]
        for l in running_instances:
            self.stop_linter_instance(l.machine, l.container_name)

        versions = [ version for (name, version) in self.linter_images.keys() if name==linter_name]
        for v in versions:
            self.linter_images.pop((linter_name, v))


    def start_linter_instance(self, linter_name, linter_version, machine) -> Tuple[str, int]:
        """Start a new instance of a given registered linter"""
        logging.info(f"Starting linter {linter_name} v {linter_version} instance on {machine}")
        cont_manager = self.container_managers[machine]
        docker_image = self.linter_images[linter_name, linter_version]
        port, container_name = cont_manager.start_container(docker_image=docker_image)
        logging.info(f"Started linter {linter_name} v {linter_version} instance on {machine} port {port} as {container_name}")
        linter_instance = RunningLinter(machine=machine,
                                            container_name = container_name,
                                            linter_version = linter_version,
                                            linter_name = linter_name,
                                            exposed_port = port)
        self.running_linters.append(linter_instance)
        return container_name


    def stop_linter_instance(self, machine, container_name):
        """Kill a linter instance""" 
        self.container_managers[machine].stop_container(container_name)

        linter_instance = None
        for linter in self.running_linters:
            if linter.machine == machine and linter.container_name==container_name:
                linter_instance = linter
                break
        self.running_linters.remove(linter_instance)
    
    def list_linters(self) -> List[LinterEndpoint]:
        return [LinterEndpoint(hostport=f"{l.machine.split(':')[0]}:{l.exposed_port}", name=l.linter_name, version=l.linter_version) for l in self.running_linters]
    

############################

# FASTAPI-SPECIFIC CODE

############################
app = FastAPI()

machine_manager = MachineManager(container_manager_factory=SSHContainerManager)

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

# Machine management
@app.post("/add_machine/")
async def add_machine(ip_port: str):
    print("got machine rquest")
    return machine_manager.add_machine(ip_port)

@app.post("delete_machine/")
async def delete_machine(ip_port: str):
    return machine_manager.delete_machine(ip_port)

@app.get("/list_machines/")
async def list_machines() -> List[str]:
    return machine_manager.list_machines()

# Linter management

@app.post("/add_new_linter/")
async def add_new_linter(linter_name: str, linter_version: str, docker_image: str):
    "Create a new linter, or update a linter to a new version."
    print("got add new linter request")
    return machine_manager.add_new_linter(linter_name, linter_version, docker_image)

@app.post("/remove_linter/")
async def remove_linter(linter_name):
    "Remove all running versions of a given linter"
    return machine_manager.remove_linter(linter_name)

@app.get("/list_linters/")
async def list_linters() -> List[LinterEndpoint]:
    return machine_manager.list_linters()


########################
# DEBUG ENDPOINTS
########################
@app.post("/unsafe_start_linter/") # debug and admin intervention, works for previously added linter
async def start_linter(linter_name: str, linter_version: str, machine: str) -> str:
    return machine_manager.start_linter_instance(linter_name, linter_version, machine)

@app.post("/unsafe_stop_linter/") # debug and admin intervention
async def stop_linter(machine: str, container_name: str):
    return machine_manager.stop_linter_instance(machine, container_name)