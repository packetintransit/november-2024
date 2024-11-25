import os
from nornir import InitNornir
from nornir_utils.plugins.functions import print_result
from nornir_netmiko.tasks import netmiko_send_command
from datetime import datetime

# Initialize Nornir
nr = InitNornir(config_file="config.yaml")
username = input("Please enter domain username: ")
nr.inventory.defaults.username = username
password = getpass.getpass()
nr.inventory.defaults.password = password
hotel_code = input("Please enter hotel code: ")
nr.inventory.defaults.data = {"hotel_code": hotel_code}

def load_hardening_requirements(file_path):
    """
    Loads the hardening requirements from a text file.
    """
    if not os.path.exists(file_path):
        print(f"Error: Hardening file '{file_path}' does not exist.")
        return []
    with open(file_path, "r") as file:
        return [line.strip() for line in file if line.strip()]

def check_hardening(task, hardening_commands):
    """
    Checks if the required hardening configurations are present on the switch.
    """
    missing_requirements = []
    # Fetch running configuration
    result = task.run(task=netmiko_send_command, command_string="show running-config", use_textfsm=False)
    running_config = result.result

    # Check each hardening command
    for command in hardening_commands:
        if command not in running_config:
            missing_requirements.append(command)

    # Store the missing requirements in the host's data
    task.host["missing_requirements"] = missing_requirements

def generate_report(nr):
    """
    Generates a report of switches missing the required hardening configurations.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"hardening_report_{timestamp}.txt"

    with open(report_file, "w") as file:
        for host in nr.inventory.hosts.values():
            missing = host.get("missing_requirements", [])
            if missing:
                file.write(f"Switch: {host.name}\n")
                file.write("Missing Configurations:\n")
                for config in missing:
                    file.write(f"  - {config}\n")
                file.write("\n")

    print(f"Report generated: {report_file}")

def main():
    # Load hardening requirements from the text file
    hardening_file = "hardening.txt"
    hardening_commands = load_hardening_requirements(hardening_file)
    if not hardening_commands:
        print("No hardening requirements loaded. Exiting.")
        return

    # Run the hardening check on all switches
    print("Checking switches for hardening compliance...")
    result = nr.run(task=check_hardening, hardening_commands=hardening_commands)
    print_result(result)

    # Generate a compliance report
    generate_report(nr)

if __name__ == "__main__":
    main()