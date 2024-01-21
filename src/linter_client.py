from typing import Tuple

import grpc

import linter_pb2
import linter_pb2_grpc


class LinterClient:
    # def __init__(self):
    #     pass
    # def set_host_port(self, host_port):
    #     self.channel = grpc.insecure_channel(host_port)
    #     self.stub = linter_pb2_grpc.LinterStub(self.channel)

    # Previously we always set host_port before linting code,
    # so these lines were moved here for simplicity
    @staticmethod
    def lint_code(host_port, code) -> Tuple[int, str]:
        channel = grpc.insecure_channel(host_port)
        stub = linter_pb2_grpc.LinterStub(channel)

        response = stub.LintCode(linter_pb2.LintingRequest(code=code))
        status_code = response.status
        comment = response.comment
        return status_code, comment
