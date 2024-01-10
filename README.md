Tested with python 3.11

Generate protobuf stubs with:
`python -m grpc_tools.protoc -I./ --python_out=./ --pyi_out=./ --grpc_python_out=./ *.proto`

Run the load balancer and machine management with:

`uvicorn load_balancer:app --reload`
