import subprocess
import time


# load_balancer_port = "8000"
# machine_management_port = "8001"
#
# load_balancer_host = "localhost"
# machine_management_host = "localhost"


class SystemObj:

    def __init__(self, p_machine_management, p_load_balancer):
        self.p_machine_management = p_machine_management
        self.p_load_balancer = p_load_balancer


def run_system(load_balancer_host="localhost", load_balancer_port="8000", machine_management_host="localhost",
               machine_management_port="8001") -> SystemObj:
    load_balancer_addr = f"http://{load_balancer_host}:{load_balancer_port}"
    machine_management_addr = f"http://{machine_management_host}:{machine_management_port}"

    # run machine management
    p_machine_management = subprocess.Popen(
        ["python3", "machine_management_app.py", "-host", machine_management_host, "-port", machine_management_port,
         "-lba", load_balancer_addr])

    # run load balancer
    p_load_balancer = subprocess.Popen(
        ["python3", "load_balancer.py", "-host", load_balancer_host, "-port", load_balancer_port,
         "-mma", machine_management_addr])

    return SystemObj(p_machine_management, p_load_balancer)


def stop_system(_system_obj: SystemObj):
    _system_obj.p_machine_management.kill()
    _system_obj.p_load_balancer.kill()


if __name__ == "__main__":
    _system_obj = run_system()
    time.sleep(5)
    stop_system(_system_obj)

