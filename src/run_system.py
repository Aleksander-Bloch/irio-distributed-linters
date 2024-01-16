import subprocess

load_balancer_port = "8000"
machine_management_port = "8001"

load_balancer_host = "localhost"
machine_management_host = "localhost"

load_balancer_addr = f"http://{load_balancer_host}:{load_balancer_port}"
machine_management_addr = f"http://{machine_management_host}:{machine_management_port}"

# run machine management
subprocess.Popen(
    ["python3", "machine_management.py", "-host", machine_management_host, "-port", machine_management_port,
     "-lba", load_balancer_addr])

# run load balancer
subprocess.Popen(["python3", "load_balancer.py", "-host", load_balancer_host, "-port", load_balancer_port,
                  "-mma", machine_management_addr])
