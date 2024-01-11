FROM ubuntu:22.04
ARG LINTER_IMPL="linter_server.py"

RUN apt update
RUN apt install python3 python3-pip python-is-python3 -y

WORKDIR /linter
ADD . .
ADD . ../linter.proto

RUN ls

RUN python -m pip install -r requirements.txt

RUN python -m grpc_tools.protoc -I./ --python_out=./ --pyi_out=./ --grpc_python_out=./ *.proto


CMD ["python", "linter_server.py"]