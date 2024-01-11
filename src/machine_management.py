from typing import List
from fastapi import FastAPI
from pydantic import BaseModel

################################

# BUSINESS LOGIC

################################

hardcoded_config = [
    {
        "hostport": "localhost:12301",
        "name": "no_semicolons",
        "version": "v0",
        "image": "ghcr.io/chedatomasz/no_semicolons:v0"
    },
    {
        "hostport": "localhost:12302",
        "name": "no_semicolons",
        "version": "v1",
        "image": "ghcr.io/chedatomasz/no_semicolons:v1"
    },
    {
        "hostport": "localhost:12303",
        "name": "no_semicolons",
        "version": "v2",
        "image": "ghcr.io/chedatomasz/no_semicolons:v2"
    },
    {
        "hostport": "localhost:12304",
        "name": "spaces_around_equals",
        "version": "v0",
        "image": "ghcr.io/chedatomasz/spaces_around_equals:v0"
    },
    {
        "hostport": "localhost:12305",
        "name": "spaces_around_equals",
        "version": "v1",
        "image": "ghcr.io/chedatomasz/spaces_around_equals:v1"
    }
]




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
        return hardcoded_config
    
    def update_linter(self, linter_name, linter_version, docker_image):
        """This is the function for staged rollout """
        raise NotImplementedError
    

############################

# FASTAPI-SPECIFIC CODE

############################
app = FastAPI()

machine_manager = MachineManager()

@app.post("/add_machine/")
async def add_machine(ip_port: str):
    raise NotImplementedError

@app.get("/list_machines/")
async def list_machines() -> List[str]:
    return machine_manager.list_machines()


class Endpoint(BaseModel):
    hostport: str
    name: str
    version: str
    image: str

@app.get("/list_linters/")
async def list_linters() -> List[Endpoint]:
    linters = machine_manager.list_linters()
    return [Endpoint(**d) for d in linters]