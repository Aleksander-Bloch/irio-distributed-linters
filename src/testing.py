import concurrent
from ast import literal_eval
from concurrent.futures import ThreadPoolExecutor

import requests

from run_system import *

# basic tests if request do not crush

load_balancer_port = "8000"
machine_management_port = "8001"

load_balancer_host = "localhost"
machine_management_host = "localhost"

load_balancer_addr = f"http://{load_balancer_host}:{load_balancer_port}"
machine_management_addr = f"http://{machine_management_host}:{machine_management_port}"


def add_machine_helper(host):
    return requests.post(f"{machine_management_addr}/add_machine/", json={"host": host})


def add_linter_helper(name, version, docker_image):
    add_linter_request = {"linter_name": name, "linter_version": version, "docker_image": docker_image}
    return requests.post(f"{machine_management_addr}/register_linter/", json=add_linter_request)


def start_linters_helper(name, version, n_instances=1):
    start_linters_request = {"linter_name": name, "linter_version": version, "n_instances": n_instances}
    return requests.post(f"{machine_management_addr}/start_linters/", json=start_linters_request)


def lint_code_helper(linter_name, code):
    lint_code_request = {"linter_name": linter_name, "code": code}
    return requests.post(f"{load_balancer_addr}/lint_code/", json=lint_code_request)


def rollout_helper(linter_name: str, old_version: str, new_version: str, traffic_percent_to_new_version: float):
    rollout_request = {"linter_name": linter_name, "old_version": old_version, "new_version": new_version,
                       "traffic_percent_to_new_version": traffic_percent_to_new_version}

    return requests.post(f"{machine_management_addr}/rollout/", json=rollout_request)


def add_machine_with_linter_helper(host, linter_name, linter_version, linter_image):
    response = add_machine_helper(host)
    assert response.status_code == 200

    response = add_linter_helper(linter_name, linter_version, linter_image)
    assert response.status_code == 200

    response = start_linters_helper(linter_name, linter_version)
    assert response.status_code == 200


def add_and_start_linter(linter_name, linter_version, linter_image):
    response = add_linter_helper(linter_name, linter_version, linter_image)
    assert response.status_code == 200

    response = start_linters_helper(linter_name, linter_version)
    assert response.status_code == 200


def run_stop_system(func):
    def inner():
        running_system = run_system(load_balancer_host, load_balancer_port, machine_management_host,
                                    machine_management_port)
        time.sleep(5)
        try:
            func()
        finally:
            stop_system(running_system)
            subprocess.run("docker stop $(docker ps -a -q)", shell=True)

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
    add_machine_with_linter_helper("localhost", "no_semicolons", "v0", "ghcr.io/chedatomasz/no_semicolons:v0")


@run_stop_system
def test_linting():
    add_machine_with_linter_helper("localhost", "no_semicolons", "v0", "ghcr.io/chedatomasz/no_semicolons:v0")

    response = lint_code_helper("no_semicolons", "dsfjsdalfdsaf;fksjfklsdaf")
    assert response.status_code == 200

    print(response.content)
    print(response.status_code)


@run_stop_system
def test_multiple_linting():
    add_machine_with_linter_helper("localhost", "no_semicolons", "v0", "ghcr.io/chedatomasz/no_semicolons:v0")

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(lint_code_helper, "no_semicolons", "dsfjsdalfdsaf;fksjfklsdaf") for _ in range(10)]
        for future in concurrent.futures.as_completed(futures):
            try:
                response = future.result()
                print(response.content)
                print(response.status_code)
                assert response.status_code == 200
            except Exception as exc:
                print(exc)


@run_stop_system
def test_rollout():
    add_machine_with_linter_helper("localhost", "no_semicolons", "v0", "ghcr.io/chedatomasz/no_semicolons:v0")

    # add and start new linter with same name, but different version
    add_and_start_linter("no_semicolons", "v1", "ghcr.io/chedatomasz/no_semicolons:v1")

    percent_to_new_version = 20

    # init rollout
    response = rollout_helper("no_semicolons", "v0", "v1", percent_to_new_version)
    assert response.status_code == 200

    code = "#saf;dsaflaksfdjaslf"

    expected_response_for_v0 = {'status_code': 1, 'message': 'ERROR: found semicolon in line 0 at position 4'}
    expected_response_for_v1 = {'status_code': 0, 'message': 'CORRECT: no redundant semicolons in code'}

    responses = []

    n_requests = 10

    for i in range(n_requests):
        response = lint_code_helper("no_semicolons", code)
        responses.append(literal_eval(response.content.decode('utf-8')))


    for r in responses:
        print(r)

    assert responses.count(expected_response_for_v1) == round(n_requests * percent_to_new_version / 100)
    assert responses.count(expected_response_for_v0) == round(n_requests * (100 - percent_to_new_version) / 100)




if __name__ == "__main__":
    test_rollout()
