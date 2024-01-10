from typing import List
from fastapi import FastAPI

app = FastAPI()


class MachineManager:

    def __init__(self):
        self.registered_machines = []

    def add_machine(self, ip_port):
        """
        Add a given machine to a pool of available linter executors.
        
        Assumes passwordless ssh is already set up.
        """
        self.registered_machines.append(ip_port)

    def delete_machine(self, ip_port):
        self.registered_machines.remove(ip_port)

    def list_machines(self):
        return self.registered_machines
    

    def start_linter(self, linter_name, linter_version, docker_image):
        """Start a new linter type - only if it doesn't already exist"""
        raise NotImplementedError

    def stop_linter(self, linter_name, linter_version):
        """Kill the given version, no staged rollout"""
        raise NotImplementedError
    
    def list_linters(self):
        raise NotImplementedError
    
    def update_linter(self, linter_name, linter_version, docker_image):
        """This is the function for staged rollout """
        raise NotImplementedError
    

machine_manager = MachineManager()

@app.post("add_machine")
async def add_machine(ip_port: str):
    raise NotImplementedError

@app.get("/list_machines")
async def list_machines() -> List[str]:
    return machine_manager.list_machines()
