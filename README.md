# Quickstart
To start the system, navigate to the `src` folder and run `python3 run_system.py`
This will start load balancer, machine management and health check services, but won't start
any machines or linters. All service's endpoints are auto-documented on `/docs/` by Swagger.

## Setting up virtual machine and starting linter instances

Operated by Machine Management Service

- `POST /add_machine/`
  - register already working machine given its host, assumes passwordless ssh is already set up and docker daemon running

- `POST /register_linter/`
  - add link from linter name and linter version to a docker image

- `POST /start_linters/`
  - start n linter instances of given name and version

- `POST /rollout/`
  - initiates rollout of specified linter to another version, given linter name, old and new version,
    traffic percentage to new version

- `POST /auto_rollout/`
  - initiates automatic rollout that progresses to the next stage after specified time and changes 
    traffic percentage routed to the new version. We can specify multiple times and stages to change consecutively.

- `POST /rollback/`
  - rollbacks linter of particular name to specified version or to "current version" saved in machine_management if
    the version is not specified

    
## Code linting

Operated by Load Balancer Service

 - `POST /lint_code/`
    - performs code linting given linter name

## Running tests

Navigate to src directory
- Integration tests: `python3 testing.py`
- Unit tests:
  - Load balancer: `python3 test_load_balancer.py`
  - Machine management: `pytest test_machine_management.py `
  - Health check: `python3 test_health_check.py`












