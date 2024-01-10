import grpc
import logging
import linter_pb2, linter_pb2_grpc

def run():
    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.
    print("Will try to send code ...")
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = linter_pb2_grpc.LinterStub(channel)
        response = stub.LintCode(linter_pb2.LintingRequest(code="print(helloworld)"))
    print("Greeter client received: " + str(response))


if __name__ == "__main__":
    logging.basicConfig()
    run()