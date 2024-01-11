FROM ubuntu:22.04
ARG LINTER_IMPL

RUN apt update
RUN apt install python3 python3-pip python-is-python3 -y

WORKDIR /linter
ADD linter_server.py .
ADD linter_base.py .
ADD linter.proto .
ADD requirements.txt .


RUN ls
RUN python -m pip install -r requirements.txt

ADD implementations/${LINTER_IMPL} linter_implementation.py
RUN ls

RUN python -m grpc_tools.protoc -I./ --python_out=./ --pyi_out=./ --grpc_python_out=./ *.proto


CMD ["python", "linter_server.py"]