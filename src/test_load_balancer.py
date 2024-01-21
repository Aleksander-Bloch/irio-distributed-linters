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


class TestLinting(unittest.TestCase):
    code_1 = "code_1"
    expected_result_1 = (0, "result_1")
    expected_result_1_dict = {"status_code": expected_result_1[0], "message": expected_result_1[1]}

    expected_host_port_1 = "host_port_1"

    @staticmethod
    def get_name(n):
        return f"name_{n}"

    @staticmethod
    def get_host_ports(n):
        return [f"host_port_{i}_{n}" for i in range(10)]

    #linter_name_to_host_port = {get_name(n): get_host_ports(n) for n in range(10)}

    def fresh_app(self):
        # TODO make mock parts of the system work correctly
        machine_management_client = Mock()
        machine_management_client.get_linters_with_curr_version.side_effect = [
            self.expected_host_port_1]  # self.linter_name_to_host_port.get
        machine_management_client.get_linter_instances.return_value = [self.expected_host_port_1]

        def fake_lint_code(host_port, code):
            if host_port != self.expected_host_port_1 or code != self.code_1:
                return 1, "bad result"

            return self.expected_result_1

        linter_client = Mock()
        linter_client.lint_code.side_effect = fake_lint_code

        return create_app(strategy=RoundRobinStrategy(),
                          machine_management_client=machine_management_client, linter_client=linter_client)

    @staticmethod
    def fresh_client(fresh_app):
        return TestClient(fresh_app)

    def setUp(self):
        self.client = TestLinting.fresh_client(self.fresh_app())

    def test_basic_linting(self):
        response = self.client.post("/lint_code/", json={"linter_name": "linter_1", "code": self.code_1})
        self.assertEqual(json.loads(response.content.decode('utf-8')), self.expected_result_1_dict)


if __name__ == '__main__':
    unittest.main()
