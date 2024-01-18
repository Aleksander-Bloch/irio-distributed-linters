from abc import ABC, abstractmethod
import logging
import subprocess
import uuid
from typing import Tuple

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