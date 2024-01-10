from concurrent import futures
import logging

import grpc
import linter_pb2, linter_pb2_grpc


class ExampleLinter(linter_pb2_grpc.LinterServicer):
    def LintCode(self, request: linter_pb2.LintingRequest, context) -> linter_pb2.LintingResult:
        """Missing associated documentation comment in .proto file."""
        sent_code = request.code
        response = linter_pb2.LintingResult(status=404, comment=f"hello world, you sent me: {sent_code}")
        return response


def serve():
    port = "50051"
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    linter_pb2_grpc.add_LinterServicer_to_server(ExampleLinter(), server)
    server.add_insecure_port("[::]:" + port)
    server.start()
    print("Server started, listening on " + port)
    server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig()
    serve()