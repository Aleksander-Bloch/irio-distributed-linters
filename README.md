# NEW

Tested with python 3.10

Run the load balancer with

`uvicorn load_balancer:app --port 8000 --reload`


Machine management runs on port 8001:

`uvicorn machine_management:app --port 8001 --reload`


To start (and stop) all linters run:
`python start_all.py`


Build & push images with build_images.sh and push_images.sh. Needs correct permissions.

To push images you either need to have an organization set up or be the owner of the repo, afaik


# OLD

Generate protobuf stubs with:
`python -m grpc_tools.protoc -I./ --python_out=./ --pyi_out=./ --grpc_python_out=./ *.proto`

Build linter servers with:
`docker build . -t no_semicolons:v0 --build-arg LINTER_IMPL=no_semicolons_linter_v0.py`

Run a single linter container with
`docker run -it --rm -p 12345:50051 no_semicolons:v0`
