from typing import Tuple
import grpc
import linter_pb2
import linter_pb2_grpc

# This could be a function, but it is a class to simplify tests.
class LinterClient:
    @staticmethod
    def lint_code(host_port, code) -> Tuple[int, str]:
        channel = grpc.insecure_channel(host_port)
        stub = linter_pb2_grpc.LinterStub(channel)

        response = stub.LintCode(linter_pb2.LintingRequest(code=code))
        status_code = response.status
        comment = response.comment
        return status_code, comment
