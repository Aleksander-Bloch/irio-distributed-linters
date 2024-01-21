import json
import unittest
from collections import Counter
from unittest.mock import Mock

from starlette.testclient import TestClient

import load_balancer
from load_balancer import RoundRobinStrategy
from load_balancer_app import create_app


class RoundRobinStrategyTester(unittest.TestCase):
    def test_equal_distribution(self):
        round_robin_strategy = load_balancer.RoundRobinStrategy()
        round_robin_strategy.load_counters = {"aa": 3, "bb": 3, "cc": 2}
        linters_host_ports = ["aa", "bb", "cc"]
        self.assertEqual(round_robin_strategy.choose_linter_instance(linters_host_ports), "cc")  # add assertion here

    def test_equal_distribution2(self):
        round_robin_strategy = load_balancer.RoundRobinStrategy()
        linters_host_ports = ["aa", "bb", "cc"]

        for i in range(10):
            round_robin_strategy.choose_linter_instance(linters_host_ports)

        # Use Counter to check if two lists has the same element
        self.assertEqual(Counter(list(round_robin_strategy.load_counters.values())), Counter([4, 3, 3]))


# used just for testing
class Linter:
    def __init__(self, name, version, host_port, linting_function):
        self.name = name
        self.version = version
        self.host_port = host_port
        self.linting_function = linting_function

    @staticmethod
    def lint_func1(code):
        return 0, str(hash(code))

    @staticmethod
    def lint_func2(code):
        return 1, str(hash(code))


class TestLinting(unittest.TestCase):
    linter_list = [Linter("name1", "v1", "hp1", Linter.lint_func1),
                   Linter("name2", "v1", "hp2", Linter.lint_func2)]

    @staticmethod
    def lint_result_to_dict(lint_result):
        return {"status_code": lint_result[0], "message": lint_result[1]}

    def get_linters_with_curr_version(self, name):
        return [linter.host_port for linter in self.linter_list if linter.name == name]

    def fresh_client(self):
        machine_management_client = Mock()
        machine_management_client.get_linters_with_curr_version.side_effect = lambda \
            name: self.get_linters_with_curr_version(name)

        def fake_lint_code(host_port, code):
            linter = list(filter(lambda x: x.host_port == host_port, self.linter_list))[0]
            return linter.linting_function(code)

        linter_client = Mock()
        linter_client.lint_code.side_effect = fake_lint_code

        app = create_app(strategy=RoundRobinStrategy(),
                         machine_management_client=machine_management_client, linter_client=linter_client)

        return TestClient(app)

    def setUp(self):
        self.client = self.fresh_client()

    def test_basic_linting(self):
        linter = self.linter_list[0]
        code = "abcd"

        response = self.client.post("/lint_code/", json={"linter_name": linter.name, "code": code})
        self.assertEqual(json.loads(response.content.decode('utf-8')),
                         TestLinting.lint_result_to_dict(linter.linting_function(code)))


if __name__ == '__main__':
    unittest.main()
