docker build . -t ghcr.io/chedatomasz/no_semicolons:v0 --build-arg LINTER_IMPL=no_semicolons_linter_v0.py
docker build . -t ghcr.io/chedatomasz/no_semicolons:v1 --build-arg LINTER_IMPL=no_semicolons_linter_v1.py
docker build . -t ghcr.io/chedatomasz/no_semicolons:v2 --build-arg LINTER_IMPL=no_semicolons_linter_v2.py

docker build . -t ghcr.io/chedatomasz/spaces_around_equals:v0 --build-arg LINTER_IMPL=spaces_around_assignment_linter_v0.py
docker build . -t ghcr.io/chedatomasz/spaces_around_equals:v1 --build-arg LINTER_IMPL=spaces_around_assignment_linter_v1.py