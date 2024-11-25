from nornir import InitNornir
from nornir_netmiko.tasks import netmiko_send_command
from nornir_utils.plugins.functions import print_result
import re
from datetime import datetime, timedelta
import getpass

# Initialize Nornir
nr = InitNornir(config_file="config.yaml")
username = input("Please enter domain username: ")
nr.inventory.defaults.username = username
password = getpass.getpass()
nr.inventory.defaults.password = password
hotel_code = input("Please enter hotel code: ")
nr.inventory.defaults.data = {"hotel_code": hotel_code}

# Define the time range for analysis (last 24 hours)
now = datetime.now()
time_window_start = now - timedelta(days=1)

def parse_logs(task):
    """
    Parses logs from the switch to find interfaces that flapped more than 10 times in the last 24 hours.
    """
    # Fetch logs from the switch
    result = task.run(task=netmiko_send_command, command_string="show logging", use_textfsm=False)
    logs = result.result

    # Regular expression to match log entries for interface flapping
    flap_regex = re.compile(r"(?P<timestamp>\w+\s+\d+\s\d+:\d+:\d+).*Interface (?P<interface>\S+) .*changed state to (up|down)")

    flap_counts = {}
    for line in logs.splitlines():
        match = flap_regex.search(line)
        if match:
            timestamp_str = match.group("timestamp")
            interface = match.group("interface")

            # Parse timestamp
            try:
                timestamp = datetime.strptime(timestamp_str, "%b %d %H:%M:%S")
                # Adjust year for proper comparison (assuming logs are for the current year)
                timestamp = timestamp.replace(year=now.year)
            except ValueError:
                continue

            # Check if the log entry is within the last 24 hours
            if time_window_start <= timestamp <= now:
                if interface not in flap_counts:
                    flap_counts[interface] = 0
                flap_counts[interface] += 1

    # Filter interfaces that flapped more than 10 times
    flapped_interfaces = {k: v for k, v in flap_counts.items() if v > 10}

    # Save results in host data
    task.host["flapped_interfaces"] = flapped_interfaces

def generate_report(nr):
    """
    Generates a report of switches and interfaces that flapped more than 10 times.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"flap_report_{timestamp}.txt"

    with open(report_file, "w") as file:
        for host in nr.inventory.hosts.values():
            flapped_interfaces = host.get("flapped_interfaces", {})
            if flapped_interfaces:
                file.write(f"Switch: {host.name}\n")
                file.write("Flapped Interfaces:\n")
                for interface, count in flapped_interfaces.items():
                    file.write(f"  - {interface}: {count} flaps\n")
                file.write("\n")

    print(f"Report generated: {report_file}")

def main():
    print("Analyzing logs for interface flapping...")
    result = nr.run(task=parse_logs)
    print_result(result)

    # Generate and save the report
    generate_report(nr)

if __name__ == "__main__":
    main()