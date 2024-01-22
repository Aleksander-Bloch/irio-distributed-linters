import concurrent
from concurrent.futures import ThreadPoolExecutor

import requests


def assert200(response):
    assert response.status_code == 200


class TestingUtils:
    load_balancer_port = "8000"
    machine_management_port = "8001"

    load_balancer_host = "localhost"
    machine_management_host = "localhost"

    load_balancer_addr = f"http://{load_balancer_host}:{load_balancer_port}"
    machine_management_addr = f"http://{machine_management_host}:{machine_management_port}"

    @classmethod
    def add_machine(cls, host):
        return requests.post(f"{cls.machine_management_addr}/add_machine/", json={"host": host})

    @classmethod
    def add_linter(cls, name, version, docker_image):
        add_linter_request = {"linter_name": name, "linter_version": version, "docker_image": docker_image}
        return requests.post(f"{cls.machine_management_addr}/register_linter/", json=add_linter_request)

    @classmethod
    def start_linters(cls, name, version, n_instances=1):
        start_linters_request = {"linter_name": name, "linter_version": version, "n_instances": n_instances}
        return requests.post(f"{cls.machine_management_addr}/start_linters/", json=start_linters_request)

    @classmethod
    def lint_code(cls, linter_name, code):
        lint_code_request = {"linter_name": linter_name, "code": code}
        return requests.post(f"{cls.load_balancer_addr}/lint_code/", json=lint_code_request)

    @classmethod
    def rollout(cls, linter_name: str, old_version: str, new_version: str, traffic_percent_to_new_version: float):
        rollout_request = {"linter_name": linter_name, "old_version": old_version, "new_version": new_version,
                           "traffic_percent_to_new_version": traffic_percent_to_new_version}

        return requests.post(f"{cls.machine_management_addr}/rollout/", json=rollout_request)

    @classmethod
    def auto_rollout(cls, auto_rollout_request: dict):
        return requests.post(f"{cls.machine_management_addr}/auto_rollout/", json=auto_rollout_request)

    @classmethod
    def rollback(cls, linter_name: str, linter_version=None):
        rollback_request = {"linter_name": linter_name, "linter_version": linter_version}
        return requests.post(f"{cls.machine_management_addr}/rollback/", params=rollback_request)

    @staticmethod
    def collect_concurrent_linting_responses(linter_name: str, code: str, n_requests: int):
        responses = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=n_requests) as executor:
            futures = [executor.submit(TestingUtils.lint_code, linter_name, code) for _ in range(n_requests)]
            for future in concurrent.futures.as_completed(futures):
                response = future.result()
                responses.append(response)

        return responses
