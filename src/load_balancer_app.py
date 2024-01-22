import argparse
import logging
import sys

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from linter_client import LinterClient
from load_balancer import LoadBalancer, MachineManagementClient, RolloutData, RoundRobinStrategy


# app takes linter_client only for testing simplicity
def create_app(strategy, machine_management_client, linter_client):
    app = FastAPI()
    load_balancer = LoadBalancer(strategy, machine_management_client, linter_client)

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
        status_code, message = load_balancer.lint_code(linter_name, code)
        return ResponseMessage(status_code=status_code, message=message)

    @app.post("/rollout/")
    async def rollout_endpoint(request: RolloutRequest):
        logging.info(
            f"ROLLOUT linter_name: {request.linter_name}, old_version: {request.old_version}, new_version: {request.new_version}, traffic_percent_to_new_version: {request.traffic_percent_to_new_version}")
        if request.traffic_percent_to_new_version == 100:
            logging.info("Got 100 percent rollout request")
            load_balancer.rollout_manager.end_rollout(request.linter_name)
        else:
            old = request.old_version
            new = request.new_version
            traffic = request.traffic_percent_to_new_version
            load_balancer.rollout_manager.start_rollout(request.linter_name, RolloutData(old, new, traffic))

    @app.post("/rollback/")
    async def rollback_endpoint(linter_name: str):
        load_balancer.rollout_manager.end_rollout(linter_name)

    app.mount("/", StaticFiles(directory="./static", html=True))

    return app


def main():
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument('-host', '--host')
    parser.add_argument('-port', '--port')
    parser.add_argument('-mma', '--machine_management_address')
    parsed_args = parser.parse_args()

    machine_management_client = MachineManagementClient(machine_management_url=parsed_args.machine_management_address)
    app = create_app(strategy=RoundRobinStrategy(), machine_management_client=machine_management_client,
                     linter_client=LinterClient())

    uvicorn.run(app, port=int(parsed_args.port), host=parsed_args.host)


if __name__ == "__main__":
    main()
