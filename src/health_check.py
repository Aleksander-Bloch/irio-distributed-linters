import logging
import time

import requests


class MachineManagerClient:
    def __init__(self, machine_management_url):
        self.machine_management_url = machine_management_url

    # returns list of dictionaries [{"name": ..., "version": ...., "hostport": ...}, ...]
    def get_all_linters(self):
        return requests.get(f"{self.machine_management_url}/list_linters/").json()

    def report_broken_linters(self, host_ports_list):
        return requests.post(f"{self.machine_management_url}/report_broken_linters/",
                             params={"host_ports": host_ports_list})


class HealthCheck:
    def __init__(self, machine_management_client, linter_client, health_check_delay):
        self.machine_management_client = machine_management_client
        self.linter_client = linter_client
        self.health_check_delay = health_check_delay

    def is_linter_responding(self, host_port):
        logging.info(host_port)
        try:
            self.linter_client.lint_code(host_port, "")
            return True
        except RuntimeError:
            return False

    def start(self):

        max_tries = 3

        while True:
            time.sleep(self.health_check_delay)
            linters = self.machine_management_client.get_all_linters()
            broken_linters_host_ports = []

            for linter in linters:
                is_responding = False
                host_port = linter["hostport"]

                for _ in range(max_tries):
                    if self.is_linter_responding(host_port):
                        is_responding = True
                        break

                if not is_responding:
                    broken_linters_host_ports.append(host_port)

            if broken_linters_host_ports:
                self.machine_management_client.report_broken_linters(broken_linters_host_ports)
