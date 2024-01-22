import argparse
import logging
import sys
import threading
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from health_check import HealthCheck
from health_check import MachineManagerClient
from linter_client import LinterClient


def create_app(machine_management_client, linter_client, health_check_delay=5):
    def health_check():
        logging.info("started health check service")
        health_check_obj = HealthCheck(machine_management_client, linter_client, health_check_delay)
        health_check_obj.start()

    @asynccontextmanager
    async def health_check_starter(app_arg):
        thread = threading.Thread(target=health_check, daemon=True)
        thread.start()

        yield

    app = FastAPI(lifespan=health_check_starter)

    return app


def main():
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument('-host', '--host')
    parser.add_argument('-port', '--port')
    parser.add_argument('-mma', '--machine_management_address')
    parsed_args = parser.parse_args()

    app = create_app(machine_management_client=MachineManagerClient(parsed_args.machine_management_address),
                     linter_client=LinterClient())

    uvicorn.run(app, port=int(parsed_args.port), host=parsed_args.host)


if __name__ == "__main__":
    main()
