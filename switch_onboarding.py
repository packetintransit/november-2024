import csv
import serial
import time
import os
import subprocess

# Function: Configure switch via console
def configure_switch_console(console_port, baudrate, static_ip, gateway):
    commands = [
        "enable",
        "configure terminal",
        "vlan 10",
        "exit",
        "interface vlan 10",
        f"ip address {static_ip} 255.255.255.128",
        "no shutdown",
        "exit",
        f"ip default-gateway {gateway}",
        "crypto key generate rsa",
        "2048",
        "ip ssh version 2",
        "username admin privilege 15 secret Password123",
        "line vty 0 4",
        "login local",
        "transport input ssh",
        "line vty 5 15",
        "login local",
        "transport input ssh",
        "exit",
        "write memory",
    ]

    try:
        ser = serial.Serial(console_port, baudrate, timeout=1)
        for cmd in commands:
            ser.write(cmd.encode() + b'\n')
            time.sleep(1)
        ser.close()
        print(f"Initial configuration applied to {static_ip}")
    except Exception as e:
        print(f"Error: {e}")

# Function: Verify SSH connectivity
def verify_ssh(static_ip):
    try:
        result = subprocess.run(
            ["ping", "-c", "3", static_ip], capture_output=True, text=True
        )
        if result.returncode == 0:
            print(f"SSH reachable at {static_ip}")
            return True
        else:
            print(f"SSH unreachable at {static_ip}")
            return False
    except Exception as e:
        print(f"Error during SSH verification: {e}")
        return False

# Function: Run Ansible playbook
def run_ansible_playbook(inventory_file, playbook_file):
    try:
        result = subprocess.run(
            ["ansible-playbook", "-i", inventory_file, playbook_file],
            capture_output=True,
            text=True,
        )
        print(result.stdout)
        if result.returncode == 0:
            print("Ansible playbook executed successfully")
        else:
            print("Ansible playbook failed")
    except Exception as e:
        print(f"Error running Ansible playbook: {e}")

# Main Workflow
def main():
    # Read MAC-to-IP mapping
    with open("switch_mgmt_ips.csv", "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            mac_address = row["MAC_ADDRESS"]
            static_ip = row["STATIC_IP"]
            gateway = "10.127.28.126"  # Static gateway for VLAN 10

            print(f"Processing switch with MAC: {mac_address}, IP: {static_ip}")

            # Step 1: Console configuration
            console_port = "COM3"  # Replace with actual console port
            baudrate = 9600
            configure_switch_console(console_port, baudrate, static_ip, gateway)

            # Step 2: Verify SSH connectivity
            if verify_ssh(static_ip):
                # Step 3: Run Ansible playbook
                inventory_file = "inventory.yml"
                playbook_file = "deploy_switch_config.yml"

                # Add switch to inventory
                with open(inventory_file, "a") as inv_file:
                    inv_file.write(
                        f"switch_{mac_address} ansible_host={static_ip} ansible_user=admin ansible_password=Password123 ansible_connection=network_cli ansible_network_os=ios\n"
                    )

                # Run Ansible playbook
                run_ansible_playbook(inventory_file, playbook_file)
            else:
                print(f"SSH unreachable for switch {mac_address}. Skipping Ansible.")

if __name__ == "__main__":
    main()