import pytest

from fastapi.testclient import TestClient
from machine_management import create_app

@pytest.fixture
def fresh_app():
    return create_app("no_load_balancer") #This breaks dependencies on load balancer


@pytest.fixture
def fresh_client(fresh_app):
    return TestClient(fresh_app)

def test_list_registered_linters(fresh_client):
    response = fresh_client.get("/list_registered_linters/")
    assert response.status_code == 200
    assert response.json() == []

def test_register_linter(fresh_client):
    client = fresh_client
    register_linter_request = {"linter_name": "python_foo",
                          "linter_version": "v0.0.1",
                          "docker_image": "foo.bar:baz"}
    registration_response = client.post("/register_linter/", json=register_linter_request)
    assert registration_response.status_code == 200

    listing_response = client.get("/list_registered_linters/")
    assert listing_response.status_code == 200
    assert listing_response.json() == [register_linter_request]

def test_tests_independent(fresh_client):
    response = fresh_client.get("/list_registered_linters/")
    assert response.status_code == 200
    assert response.json() == [] # make sure the linter we registered in a different test does not persist here

