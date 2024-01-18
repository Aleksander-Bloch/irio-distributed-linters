import pytest

from fastapi.testclient import TestClient
from machine_management_app import create_app

@pytest.fixture
def fresh_app():
    def load_balancer_rollback_callback(*args):
        raise NotImplementedError()
    
    def load_balancer_rollout_callback(*args):
        raise NotImplementedError()
    return create_app(load_balancer_rollout_callback=load_balancer_rollout_callback,
                      load_balancer_rollback_callback=load_balancer_rollback_callback) #This breaks dependencies on load balancer

@pytest.fixture
def fresh_client(fresh_app):
    return TestClient(fresh_app)

@pytest.fixture
def example_linter_registration():
    return {"linter_name": "python_foo",
                          "linter_version": "v0.0.1",
                          "docker_image": "foo.bar:baz"}


# Linter registration and deregistration

def test_list_registered_linters(fresh_client):
    response = fresh_client.get("/list_registered_linters/")
    assert response.status_code == 200
    assert response.json() == []

def test_register_linter(fresh_client, example_linter_registration):
    client = fresh_client
    register_linter_request = example_linter_registration
    registration_response = client.post("/register_linter/", json=register_linter_request)
    assert registration_response.status_code == 200

    listing_response = client.get("/list_registered_linters/")
    assert listing_response.status_code == 200
    assert listing_response.json() == [register_linter_request]

def test_tests_independent(fresh_client):
    response = fresh_client.get("/list_registered_linters/")
    assert response.status_code == 200
    assert response.json() == [] # make sure the linter we registered in a different test does not persist here

def test_deregister_linter(fresh_client, example_linter_registration):
    client = fresh_client
    registration_request = example_linter_registration
    client.post("/register_linter/", json=registration_request)
    remove_params = {"linter_name": registration_request["linter_name"], "linter_version": registration_request["linter_version"]}
    remove_response = client.post("/remove_linter/", params=remove_params)
    assert remove_response.status_code == 200

    requery_response = client.get("/list_registered_linters/")
    assert requery_response.status_code == 200
    assert requery_response.json() == []

@pytest.mark.skip
def test_linter_deregistration_removes_instances():
    raise NotImplementedError #TODO implement
