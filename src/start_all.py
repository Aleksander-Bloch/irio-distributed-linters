from machine_management import hardcoded_config
import docker

def start_linter(client, port, image, container_name):
    try:
        container = client.containers.run(
            image,
            name=container_name,
            ports={50051:port},
            detach=True,
            remove=True,
        )
        print(f"Container from {image} started successfully.")
    except docker.errors.APIError as e:
        print(f"Error starting container from {image}: {e}")



if __name__ == "__main__":
    client = docker.from_env()
    for endpoint in hardcoded_config:
        hostport = endpoint["hostport"]
        name = endpoint["name"]
        version = endpoint["version"]
        container_name = f"{name}_{version}"
        image = endpoint["image"]
        port = hostport.split(":")[-1]
        start_linter(client, port, image, container_name)

    input()
    print("Starting shutdown...")
    try:
        containers = client.containers.list()
        for container in containers:
            container.stop()
            print(f"Container {container.name} stopped successfully.")
    except docker.errors.APIError as e:
        print(f"Error stopping containers: {e}")

