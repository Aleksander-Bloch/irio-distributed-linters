from fastapi import FastAPI
import requests
import uvicorn
import logging
import argparse
import sys

class MachineManagerClient:
    def __init__(self, address):
        self.address = address

    def get_all_linters(self):
        url = f"{self.address}/list_linters/"
        return requests.get(url).json()

def create_app(machine_manager_client):
    app = FastAPI()

    health_status = {}

    @app.get("/health_status/")
    async def get_health_status():
        all_linters = machine_manager_client.get_all_linters()
        hostports = [l["hostport"] for l in all_linters]
        return {hostport: {"last_queried": None, "last_success": None, "last_failure": None} for hostport in hostports}


    return app



def main():
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument('-host', '--host')
    parser.add_argument('-port', '--port')
    parser.add_argument('-mma', '--machine_management_address')
    parsed_args = parser.parse_args()
    app = create_app(load_balancer_url=parsed_args.load_balancer_address)

    uvicorn.run(app, port=int(parsed_args.port), host=parsed_args.host)


if __name__ == "__main__":
    main()
