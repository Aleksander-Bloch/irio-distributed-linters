# import pytest

from fastapi.testclient import TestClient

import sys
import os

# getting the name of the directory
# where the this file is present.
current = os.path.dirname(os.path.realpath(__file__))

# Getting the parent directory name
# where the current directory is present.
parent = os.path.dirname(current)

# adding the parent directory to
# the sys.path.
sys.path.append(parent)

# now we can import the module in the parent
# directory.
from virtual_machine.server import app

client = TestClient(app)


def test_add_linter_endpoint():
    with open("linters/no_semicolons_linter_v0.py", "rb") as linter_code_file:
        response = client.post("/add_linter/", files={"linter_file": linter_code_file},
                               params={"linter_name": "no_semicolons", "linter_version": 0})
        assert response.status_code == 200


def test_lint_code_file_endpoint():
    with open("linters/test_no_semicolons.txt", "rb") as code_file:
        response = client.post("/lint_code_file/", files={"code_file": code_file},
                               params={"linter_name": "no_semicolons", "linter_version": 0})
        assert response.json() == {'is_code_correct': False,
                                   'message': 'ERROR: found semicolon in line 2 at position 3'}

# test_add_linter_endpoint(test_client)
# test_lint_code_file_endpoint(test_client)
