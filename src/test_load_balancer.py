import unittest
from collections import Counter
from unittest.mock import Mock, patch

import pytest
from starlette.testclient import TestClient

import load_balancer
from linter_client import LinterClient
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
    @pytest.fixture
    def fresh_app(self):
        # TODO make mock parts of the system work correctly
        machine_management_client = Mock()
        machine_management_client.rollout.return_value = None
        machine_management_client.rollback.return_value = None

        linter_client = patch.object(LinterClient, "lint_code", new=lambda x, y: y)

        return create_app(strategy=RoundRobinStrategy(),
                          machine_management_client=machine_management_client, linter_client=linter_client)

    @pytest.fixture
    def fresh_client(self, fresh_app):
        return TestClient(fresh_app)


if __name__ == '__main__':
    unittest.main()
