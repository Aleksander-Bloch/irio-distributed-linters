import time

from run_system import *
import requests

# basic tests if request do not crush

load_balancer_port = "8000"
machine_management_port = "8001"

load_balancer_host = "localhost"
machine_management_host = "localhost"

load_balancer_addr = f"http://{load_balancer_host}:{load_balancer_port}"
machine_management_addr = f"http://{machine_management_host}:{machine_management_port}"

# hardcoded_config = [
#     {
#         "hostport": "localhost:12301",
#         "name": "no_semicolons",
#         "version": "v0",
#         "image": "ghcr.io/chedatomasz/no_semicolons:v0"
#     },
#     {
#         "hostport": "localhost:12302",
#         "name": "no_semicolons",
#         "version": "v1",
#         "image": "ghcr.io/chedatomasz/no_semicolons:v1"
#     },
#     {
#         "hostport": "localhost:12303",
#         "name": "no_semicolons",
#         "version": "v2",
#         "image": "ghcr.io/chedatomasz/no_semicolons:v2"
#     },
#     {
#         "hostport": "localhost:12304",
#         "name": "spaces_around_equals",
#         "version": "v0",
#         "image": "ghcr.io/chedatomasz/spaces_around_equals:v0"
#     },
#     {
#         "hostport": "localhost:12305",
#         "name": "spaces_around_equals",
#         "version": "v1",
#         "image": "ghcr.io/chedatomasz/spaces_around_equals:v1"
#     }
# ]


def add_machine_helper(host):
    return requests.post(f"{machine_management_addr}/add_machine/", json={"host": host})


def add_linter_helper(name, version, docker_image):
    add_linter_request = {"linter_name": name, "linter_version": version, "docker_image": docker_image}
    return requests.post(f"{machine_management_addr}/add_new_linter/", json=add_linter_request)


def start_linters_helper(name, version, n_instances=1):
    start_linters_request = {"linter_name": name, "linter_version": version, "n_instances": n_instances}
    return requests.post(f"{machine_management_addr}/start_linters/", json=start_linters_request)


def run_stop_system(func):
    def inner():
        running_system = run_system(load_balancer_host, load_balancer_port, machine_management_host,
                                    machine_management_port)
        time.sleep(5)
        try:
            func()
        finally:
            stop_system(running_system)

    return inner


# @run_stop_system
# def test_add_machine():
#     response = add_machine_helper("localhost")
#     assert response.status_code == 200
#
#
# @run_stop_system
# def test_add_linter():
#     response = add_machine_helper("localhost")
#     assert response.status_code == 200
#
#     response = add_linter_helper("aaa", "bbb", "")
#     assert response.status_code == 200


@run_stop_system
def test_start_linter_instance():
    response = add_machine_helper("localhost")
    assert response.status_code == 200

    response = add_linter_helper("no_semicolons", "v1", "ghcr.io/chedatomasz/no_semicolons:v0")
    assert response.status_code == 200

    response = start_linters_helper("no_semicolons", "v1")
    assert response.status_code == 200


if __name__ == "__main__":
    test_start_linter_instance()
