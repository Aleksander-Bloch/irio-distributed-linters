from typing import Tuple

import grpc

import linter_pb2
import linter_pb2_grpc


class LinterClient:
    def __init__(self, hostport):
        self.channel = grpc.insecure_channel(hostport)
        self.stub = linter_pb2_grpc.LinterStub(self.channel)

    def lint_code(self, code) -> Tuple[int, str]:
        response = self.stub.LintCode(linter_pb2.LintingRequest(code=code))
        status_code = response.status
        comment = response.comment
        return status_code, comment
