import unittest
import load_balancer
from collections import Counter


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


if __name__ == '__main__':
    unittest.main()
