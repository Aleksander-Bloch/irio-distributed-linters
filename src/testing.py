import math
from ast import literal_eval
from concurrent.futures import ThreadPoolExecutor

from run_system import *
from testing_utils import *

# basic tests if request do not crush

load_balancer_port = "8000"
machine_management_port = "8001"

load_balancer_host = "localhost"
machine_management_host = "localhost"

load_balancer_addr = f"http://{load_balancer_host}:{load_balancer_port}"
machine_management_addr = f"http://{machine_management_host}:{machine_management_port}"


def add_machine_with_linter(host, linter_name, linter_version, linter_image):
    response = TestingUtils.add_machine(host)
    assert response.status_code == 200

    response = TestingUtils.add_linter(linter_name, linter_version, linter_image)
    assert response.status_code == 200

    response = TestingUtils.start_linters(linter_name, linter_version)
    assert response.status_code == 200


def add_and_start_linter(linter_name, linter_version, linter_image):
    response = TestingUtils.add_linter(linter_name, linter_version, linter_image)
    assert response.status_code == 200

    response = TestingUtils.start_linters(linter_name, linter_version)
    assert response.status_code == 200


def check_traffic_percentage(code: str, expected_result_old: dict, expected_result_new: dict, linter_name: str,
                             expected_traffic: int):
    divisor = math.gcd(expected_traffic, 100)
    n_requests = 100 // divisor
    n_expected_to_new = expected_traffic // divisor
    n_expected_to_old = n_requests - n_expected_to_new
    responses = TestingUtils.collect_concurrent_linting_responses(linter_name, code, n_requests)

    for r in responses:
        assert r.status_code == 200

    parsed_responses = [literal_eval(r.content.decode('utf-8')) for r in responses]

    assert parsed_responses.count(
        expected_result_new) == n_expected_to_new, f"{parsed_responses.count(expected_result_new)} != {n_expected_to_new}"

    assert parsed_responses.count(
        expected_result_old) == n_expected_to_old, f"{parsed_responses.count(expected_result_old)} != {n_expected_to_old}"


def run_stop_system(func):
    def inner():
        running_system = run_system(load_balancer_host, load_balancer_port, machine_management_host,
                                    machine_management_port)
        # wait for system to start
        time.sleep(5)
        try:
            func()
        finally:
            stop_system(running_system)
            subprocess.run("docker stop $(docker ps -a -q)", shell=True)

    return inner


@run_stop_system
def test_start_linter_instance():
    add_machine_with_linter("localhost", "no_semicolons", "v0", "ghcr.io/chedatomasz/no_semicolons:v0")


@run_stop_system
def test_single_linting():
    add_machine_with_linter("localhost", "no_semicolons", "v0", "ghcr.io/chedatomasz/no_semicolons:v0")

    response = TestingUtils.lint_code("no_semicolons", "dsfjsdalfdsaf;fksjfklsdaf")
    assert response.status_code == 200

    print(response.content)
    print(response.status_code)


@run_stop_system
def test_multiple_linting():
    add_machine_with_linter("localhost", "no_semicolons", "v0", "ghcr.io/chedatomasz/no_semicolons:v0")

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(TestingUtils.lint_code, "no_semicolons", "dsfjsdalfdsaf;fksjfklsdaf") for _ in
                   range(10)]
        for future in concurrent.futures.as_completed(futures):
            try:
                response = future.result()
                print(response.content)
                print(response.status_code)
                assert response.status_code == 200
            except Exception as exc:
                print(exc)


@run_stop_system
def test_rollout_sequential():
    add_machine_with_linter("localhost", "no_semicolons", "v0", "ghcr.io/chedatomasz/no_semicolons:v0")

    # add and start new linter with same name, but different version
    add_and_start_linter("no_semicolons", "v1", "ghcr.io/chedatomasz/no_semicolons:v1")

    percent_to_new_version = 20

    # init rollout
    response = TestingUtils.rollout("no_semicolons", "v0", "v1", percent_to_new_version)
    assert response.status_code == 200

    code = "#saf;dsaflaksfdjaslf"

    expected_response_for_v0 = {'status_code': 1, 'message': 'ERROR: found semicolon in line 0 at position 4'}
    expected_response_for_v1 = {'status_code': 0, 'message': 'CORRECT: no redundant semicolons in code'}

    responses = []

    n_requests = 10

    for i in range(n_requests):
        response = TestingUtils.lint_code("no_semicolons", code)
        responses.append(literal_eval(response.content.decode('utf-8')))

    for r in responses:
        print(r)

    assert responses.count(expected_response_for_v1) == round(n_requests * percent_to_new_version / 100)
    assert responses.count(expected_response_for_v0) == round(n_requests * (100 - percent_to_new_version) / 100)


@run_stop_system
def test_rollout_concurrent():
    add_machine_with_linter("localhost", "no_semicolons", "v0", "ghcr.io/chedatomasz/no_semicolons:v0")

    # add and start new linter with same name, but different version
    add_and_start_linter("no_semicolons", "v1", "ghcr.io/chedatomasz/no_semicolons:v1")

    percent_to_new_version = 20

    # init rollout
    response = TestingUtils.rollout("no_semicolons", "v0", "v1", percent_to_new_version)
    assert response.status_code == 200

    code = "#saf;dsaflaksfdjaslf"

    expected_response_for_v0 = {'status_code': 1, 'message': 'ERROR: found semicolon in line 0 at position 4'}
    expected_response_for_v1 = {'status_code': 0, 'message': 'CORRECT: no redundant semicolons in code'}

    n_requests = 10

    responses = TestingUtils.collect_concurrent_linting_responses("no_semicolons", code, n_requests)

    parsed_responses = [literal_eval(r.content.decode('utf-8')) for r in responses]

    for r in parsed_responses:
        print(r)

    assert parsed_responses.count(expected_response_for_v1) == round(n_requests * percent_to_new_version / 100)
    assert parsed_responses.count(expected_response_for_v0) == round(n_requests * (100 - percent_to_new_version) / 100)


@run_stop_system
def test_rollback():
    linter_name = "no_semicolons"

    add_machine_with_linter("localhost", linter_name, "v0", "ghcr.io/chedatomasz/no_semicolons:v0")

    # add and start new linter with same name, but different version
    add_and_start_linter(linter_name, "v1", "ghcr.io/chedatomasz/no_semicolons:v1")

    percent_to_new_version = 20

    # init rollout
    response = TestingUtils.rollout(linter_name, "v0", "v1", percent_to_new_version)
    assert response.status_code == 200

    code = "#saf;dsaflaksfdjaslf"

    expected_response_for_v0 = {'status_code': 1, 'message': 'ERROR: found semicolon in line 0 at position 4'}
    expected_response_for_v1 = {'status_code': 0, 'message': 'CORRECT: no redundant semicolons in code'}

    n_requests = 10

    responses = TestingUtils.collect_concurrent_linting_responses(linter_name, code, n_requests)

    parsed_responses = [literal_eval(r.content.decode('utf-8')) for r in responses]

    for r in parsed_responses:
        print(r)

    assert parsed_responses.count(expected_response_for_v1) == round(n_requests * percent_to_new_version / 100)
    assert parsed_responses.count(expected_response_for_v0) == round(n_requests * (100 - percent_to_new_version) / 100)

    response = TestingUtils.rollback(linter_name)
    responses = TestingUtils.collect_concurrent_linting_responses(linter_name, code, n_requests)

    parsed_responses = [literal_eval(r.content.decode('utf-8')) for r in responses]

    for r in parsed_responses:
        print(r)

    # after rollback all request should come from version v0
    assert parsed_responses.count(expected_response_for_v0) == n_requests


@run_stop_system
def test_auto_rollout():
    linter_name = "no_semicolons"
    old_version = "v0"
    new_version = "v1"
    code = "#saf;dsaflaksfdjaslf"
    add_machine_with_linter("localhost", linter_name, "v0", "ghcr.io/chedatomasz/no_semicolons:v0")
    add_and_start_linter(linter_name, "v1", "ghcr.io/chedatomasz/no_semicolons:v1")

    expected_response_for_v0 = {'status_code': 1, 'message': 'ERROR: found semicolon in line 0 at position 4'}
    expected_response_for_v1 = {'status_code': 0, 'message': 'CORRECT: no redundant semicolons in code'}

    auto_rollout_request = {"linter_name": linter_name, "old_version": old_version, "new_version": new_version,
                            "time_steps": [5, 10, 6], "traffic_percent_steps": [10, 50, 100]}

    assert200(TestingUtils.auto_rollout(auto_rollout_request))

    check_traffic_percentage(code, expected_response_for_v0, expected_response_for_v1, linter_name, 0)
    time.sleep(6)
    check_traffic_percentage(code, expected_response_for_v0, expected_response_for_v1, linter_name, 10)
    time.sleep(10)
    check_traffic_percentage(code, expected_response_for_v0, expected_response_for_v1, linter_name, 50)
    time.sleep(6)
    check_traffic_percentage(code, expected_response_for_v0, expected_response_for_v1, linter_name, 100)


@run_stop_system
def test_rollback_during_auto_rollout():
    linter_name = "no_semicolons"
    old_version = "v0"
    new_version = "v1"
    code = "#saf;dsaflaksfdjaslf"
    add_machine_with_linter("localhost", linter_name, "v0", "ghcr.io/chedatomasz/no_semicolons:v0")
    add_and_start_linter(linter_name, "v1", "ghcr.io/chedatomasz/no_semicolons:v1")

    expected_response_for_v0 = {'status_code': 1, 'message': 'ERROR: found semicolon in line 0 at position 4'}
    expected_response_for_v1 = {'status_code': 0, 'message': 'CORRECT: no redundant semicolons in code'}

    auto_rollout_request = {"linter_name": linter_name, "old_version": old_version, "new_version": new_version,
                            "time_steps": [5, 5], "traffic_percent_steps": [50, 100]}

    assert200(TestingUtils.auto_rollout(auto_rollout_request))

    check_traffic_percentage(code, expected_response_for_v0, expected_response_for_v1, linter_name, 0)
    time.sleep(6)
    check_traffic_percentage(code, expected_response_for_v0, expected_response_for_v1, linter_name, 50)
    TestingUtils.rollback(linter_name)
    check_traffic_percentage(code, expected_response_for_v0, expected_response_for_v1, linter_name, 0)
    time.sleep(5)
    check_traffic_percentage(code, expected_response_for_v0, expected_response_for_v1, linter_name, 0)


if __name__ == "__main__":
    test_rollback_during_auto_rollout()
