import pytest

from fastapi.testclient import TestClient
from healthcheck import create_app
from unittest.mock import Mock, create_autospec

def client_with_linters(linters):
    mock_client = Mock()
    mock_client.get_all_linters.return_value = linters
    return mock_client

@pytest.fixture
def fresh_app():
    mock_client = client_with_linters([])
    return create_app(mock_client)

@pytest.fixture
def fresh_client(fresh_app):
    return TestClient(fresh_app)


def test_get_health_status_exists(fresh_client):
    response = fresh_client.get("/health_status/")
    assert response.status_code == 200

def test_get_health_status_gets_linters_and_returns_dict():
    machinemanager_client = client_with_linters([])
    app = TestClient(create_app(machinemanager_client))
    response = app.get("/health_status")
    assert response.status_code == 200
    assert response.json() == {}
    machinemanager_client.get_all_linters.assert_called_once_with()

