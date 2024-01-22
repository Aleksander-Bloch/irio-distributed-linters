import logging
from concurrent import futures

import grpc
import linter_pb2
import linter_pb2_grpc
from linter_implementation import LinterImpl

from linter_base import LinterBase


# This file is moved to the correct path by Dockerfile, a bit hacky to avoid code duplication.

class LinterWrapper(linter_pb2_grpc.LinterServicer):
    def __init__(self):
        super().__init__()
        self.linter: LinterBase = LinterImpl()

    def LintCode(self, request: linter_pb2.LintingRequest, context) -> linter_pb2.LintingResult:
        """Missing associated documentation comment in .proto file."""
        sent_code = request.code
        status_code, response_text = self.linter.lint_code(sent_code)
        response = linter_pb2.LintingResult(status=status_code, comment=response_text)
        return response


def serve():
    port = "50051"
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    linter_pb2_grpc.add_LinterServicer_to_server(LinterWrapper(), server)
    server.add_insecure_port("[::]:" + port)
    server.start()
    print(f"Server started, listening on {port} (inside container)")
    server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig()
    serve()
