# Assumes machine management is running at 8001: `uvicorn machine_management:app --port 8001 --reload`

import requests


# hardcoded_config = [
#     {
#         "hostport": "localhost:12301",
#         "name": "no_semicolons",
#         "version": "v0",
#         "image": "ghcr.io/chedatomasz/no_semicolons:v0"
#     },
#     {
#         "hostport": "localhost:12302",
#         "name": "no_semicolons",
#         "version": "v1",
#         "image": "ghcr.io/chedatomasz/no_semicolons:v1"
#     },
#     {
#         "hostport": "localhost:12303",
#         "name": "no_semicolons",
#         "version": "v2",
#         "image": "ghcr.io/chedatomasz/no_semicolons:v2"
#     },
#     {
#         "hostport": "localhost:12304",
#         "name": "spaces_around_equals",
#         "version": "v0",
#         "image": "ghcr.io/chedatomasz/spaces_around_equals:v0"
#     },
#     {
#         "hostport": "localhost:12305",
#         "name": "spaces_around_equals",
#         "version": "v1",
#         "image": "ghcr.io/chedatomasz/spaces_around_equals:v1"
#     }
# ]
def add_machine(ip_port):
    print("adding machine")
    params = {
        'ip_port': ip_port
    }
    response = requests.post(f"{management_url}/add_machine/", params=params)

    if response.status_code == 200:
        print("Machine added successfully!")
    else:
        print(f"Failed to add machine. Status code: {response.status_code}")
        print(response.text)


def add_new_linter(management_url, linter_name, linter_version, docker_image):
    print("adding linter")
    params = {
        'linter_name': linter_name,
        'linter_version': linter_version,
        'docker_image': docker_image
    }
    response = requests.post(f"{management_url}/register_linter/", params=params)

    if response.status_code == 200:
        print("Linter added successfully!")
    else:
        print(f"Failed to add linter. Status code: {response.status_code}")
        print(response.text)


def remove_linter(management_url, linter_name):
    print("removing linter")
    params = {
        'linter_name': linter_name
    }
    response = requests.post(f"{management_url}/remove_linter/", params=params)

    if response.status_code == 200:
        print("Linter removed successfully!")
    else:
        print(f"Failed to remove linter. Status code: {response.status_code}")
        print(response.text)


if __name__ == "__main__":
    management_url = "http://localhost:8001"
    add_machine("localhost")
    add_new_linter(management_url, "spaces_around_equals", "v1", "ghcr.io/chedatomasz/spaces_around_equals:v1")
    add_new_linter(management_url, "no_semicolons", "v2", "ghcr.io/chedatomasz/no_semicolons:v2")
    input()
    remove_linter(management_url, "spaces_around_equals")
    remove_linter(management_url, "no_semicolons")
