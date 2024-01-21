import subprocess
import time


# load_balancer_port = "8000"
# machine_management_port = "8001"
#
# load_balancer_host = "localhost"
# machine_management_host = "localhost"


class SystemObj:

    def __init__(self, p_machine_management, p_load_balancer, p_health_check):
        self.p_machine_management = p_machine_management
        self.p_load_balancer = p_load_balancer
        self.p_health_check = p_health_check


def run_system(load_balancer_host="localhost", load_balancer_port="8000", machine_management_host="localhost",
               machine_management_port="8001", health_check_host="localhost", health_check_port="8002") -> SystemObj:
    load_balancer_addr = f"http://{load_balancer_host}:{load_balancer_port}"
    machine_management_addr = f"http://{machine_management_host}:{machine_management_port}"
    health_check_addr = f"http://{health_check_host}:{health_check_port}"

    # run machine management
    p_machine_management = subprocess.Popen(
        ["python3", "machine_management_app.py", "-host", machine_management_host, "-port", machine_management_port,
         "-lba", load_balancer_addr])

    # run load balancer
    p_load_balancer = subprocess.Popen(
        ["python3", "load_balancer_app.py", "-host", load_balancer_host, "-port", load_balancer_port,
         "-mma", machine_management_addr])

    p_health_check = subprocess.Popen(
        ["python3", "health_check_app.py", "-host", health_check_host, "-port", health_check_port,
         "-mma", machine_management_addr])

    return SystemObj(p_machine_management, p_load_balancer, p_health_check)


def stop_system(_system_obj: SystemObj):
    _system_obj.p_machine_management.kill()
    _system_obj.p_load_balancer.kill()
    _system_obj.p_health_check.kill()


if __name__ == "__main__":
    _system_obj = run_system()
    time.sleep(7)
    stop_system(_system_obj)
