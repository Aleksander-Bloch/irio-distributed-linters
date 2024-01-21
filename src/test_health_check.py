import threading
import time
import unittest
from unittest.mock import Mock

import uvicorn

from health_check_app import create_app


class TestHealthCheck(unittest.TestCase):
    linters_list = [{"name": "aaa", "version": "v1", "hostport": "hp1"},
                    {"name": "bbb", "version": "v1", "hostport": "hp2"},
                    {"name": "ccc", "version": "v1", "hostport": "hp3"},
                    {"name": "ddd", "version": "v1", "hostport": "hp4"}]

    # 0: success, 1: failure (for linter client)
    success_fail_list = [0, 0, 1, 1, 1, 0]

    health_check_delay = 3

    # n good and 1 bad, n good 1 bad, ...
    # n_reliable = 3

    def unreliable(self):
        if self.success_fail_list[self.curr_success_fail_idx] == 0:
            self.curr_success_fail_idx = (self.curr_success_fail_idx + 1) % len(self.success_fail_list)
        else:
            self.curr_success_fail_idx = (self.curr_success_fail_idx + 1) % len(self.success_fail_list)
            raise RuntimeError()

    def fresh_client(self):
        self.machine_management_client = Mock()
        self.machine_management_client.get_all_linters.return_value = self.linters_list
        self.machine_management_client.report_broken_linters.return_value = None

        linter_client = Mock()
        linter_client.lint_code.side_effect = lambda x, y: self.unreliable()

        app = create_app(machine_management_client=self.machine_management_client, linter_client=linter_client,
                         health_check_delay=self.health_check_delay)

        # we need start real app in test, because TestClient did not work
        thread = threading.Thread(target=uvicorn.run, kwargs={"app": app, "port": 8002, "host": "localhost"},
                                  daemon=True)
        thread.start()

    def setUp(self):
        self.curr_success_fail_idx = 0
        self.fresh_client()

    def test_health_check(self):

        time.sleep(self.health_check_delay + 1)

        self.machine_management_client.get_all_linters.assert_called_with()
        self.machine_management_client.report_broken_linters.assert_called_with(["hp3"])


if __name__ == '__main__':
    unittest.main()
