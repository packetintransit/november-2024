import importlib
from nornir import InitNornir
from nornir_utils.plugins.functions import print_result
from nornir_netmiko.tasks.netmiko_send_command import netmiko_send_command
from nornir_netmiko.tasks.netmiko_send_config import netmiko_send_config
import getpass

# Initialize Nornir with credentials
nr = InitNornir(config_file="config.yaml")
username = input("Please enter domain username: ")
nr.inventory.defaults.username = username
password = getpass.getpass()
nr.inventory.defaults.password = password
hotel_code = input("Please enter hotel code: ")
nr.inventory.defaults.data = {"hotel_code": hotel_code}

def check_and_add_vlan(task, vlan_id):
    """
    Checks if the VLAN is allowed on trunk ports and adds it if missing.
    """
    # Command to get trunk port details
    trunk_command = "show interfaces trunk"
    result = task.run(task=netmiko_send_command, command_string=trunk_command, use_textfsm=True)

    # Parse the output using TextFSM (structured data)
    trunk_data = result.result
    if not trunk_data:
        print(f"No trunk ports found on {task.host.name}")
        return

    # Process trunk ports and their allowed VLANs
    config_changes = []
    for trunk in trunk_data:
        interface = trunk.get("port")
        allowed_vlans = trunk.get("vlans", "")

        # Check if the VLAN is allowed
        if vlan_id not in allowed_vlans.split(","):
            print(f"VLAN {vlan_id} is missing on {interface} of {task.host.name}")
            # Add the VLAN to the trunk port
            config_changes.append(f"interface {interface}")
            config_changes.append(f"switchport trunk allowed vlan add {vlan_id}")

    # Apply configuration changes if needed
    if config_changes:
        task.run(task=netmiko_send_config, config_commands=config_changes)
        print(f"VLAN {vlan_id} added to trunk ports on {task.host.name}")
    else:
        print(f"VLAN {vlan_id} is already allowed on all trunk ports of {task.host.name}")

def main():
    # Ask the user for the VLAN to check
    vlan_id = input("Enter the VLAN ID to check and add (if missing): ")

    # Run the check and add task on all switches
    result = nr.run(task=check_and_add_vlan, vlan_id=vlan_id)
    print_result(result)

if __name__ == "__main__":
    main()