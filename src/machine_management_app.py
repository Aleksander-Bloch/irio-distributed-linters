import argparse
import logging
import sys
import threading
from typing import List, Tuple

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from container_manager import SSHContainerManager
from machine_manager import LoadBalancerClient, LinterEndpoint, MachineManager, RegisterLinterData, RolloutRequest, \
    StartLintersRequest, AutoRolloutRequest


def create_app(load_balancer_client):
    app = FastAPI()
    machine_manager = MachineManager(load_balancer_client=load_balancer_client,
                                     container_manager_factory=SSHContainerManager)

    class AddMachine(BaseModel):
        host: str

    @app.post("/add_machine/")
    async def add_machine(request: AddMachine):
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
        return machine_manager.start_linters(request)

    @app.post("/rollout/")
    async def rollout(request: RolloutRequest):
        return machine_manager.rollout(request)

    @app.post("/auto_rollout/")
    async def auto_rollout(request: AutoRolloutRequest):
        auto_rollout_thread = threading.Thread(target=machine_manager.auto_rollout, args=(request,))
        auto_rollout_thread.start()
        # return with status 200 after auto rollout is initialized
        return

    @app.post("/rollback/")
    async def rollback(linter_name: str, linter_version: str | None = None):
        logging.info("machine_management got rollback request")
        return machine_manager.rollback(linter_name, linter_version)

    # receive report from health check and restart broken linters
    @app.post("/report_broken_linters/")
    async def report_broken_linters(host_ports: List[str]):
        logging.info("machine_management got broken linters report")
        return machine_manager.restart_broken_linters(host_ports)

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
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument('-host', '--host')
    parser.add_argument('-port', '--port')
    parser.add_argument('-lba', '--load_balancer_address')
    parsed_args = parser.parse_args()

    load_balancer_client = LoadBalancerClient(load_balancer_url=parsed_args.load_balancer_address)

    app = create_app(load_balancer_client=load_balancer_client)

    uvicorn.run(app, port=int(parsed_args.port), host=parsed_args.host)


if __name__ == "__main__":
    main()
