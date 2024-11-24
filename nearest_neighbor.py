import importlib
from nornir import InitNornir
from nornir_utils.plugins.functions import print_result
from nornir_netmiko.tasks.netmiko_send_command import netmiko_send_command
from datetime import date
import pathlib
import getpass
import networkx as nx

# Initialize Nornir with config
nr = InitNornir(config_file="config.yaml")

# Gather credentials and hotel-specific filter
username = input("Please enter domain username: ")
nr.inventory.defaults.username = username
password = getpass.getpass()
nr.inventory.defaults.password = password
hotel_code = input("Please enter hotel code: ")
nr.inventory.defaults.data = {"hotel_code": hotel_code}

# Function to gather spanning tree data
def gather_topology(task):
    """
    Collects spanning tree and neighbor information from switches.
    """
    # Run commands to get STP and CDP neighbor data
    stp_result = task.run(
        task=netmiko_send_command, 
        command_string="show spanning-tree", 
        use_textfsm=True
    )
    cdp_result = task.run(
        task=netmiko_send_command, 
        command_string="show cdp neighbors detail", 
        use_textfsm=True
    )

    # Parse spanning tree cost data
    stp_data = stp_result.result
    cdp_data = cdp_result.result
    
    # Extract relevant information
    task.host["stp_costs"] = parse_stp_data(stp_data)
    task.host["neighbors"] = parse_cdp_data(cdp_data)


# Helper function to parse STP data
def parse_stp_data(stp_output):
    """
    Parses spanning tree data to extract STP costs for each port.
    """
    parsed_data = {}
    for line in stp_output:
        port = line.get("port", "")
        cost = line.get("cost", 0)
        if port:
            parsed_data[port] = int(cost)
    return parsed_data


# Helper function to parse CDP neighbor data
def parse_cdp_data(cdp_output):
    """
    Parses CDP neighbor data to extract switch-to-switch links.
    """
    neighbors = []
    for neighbor in cdp_output:
        local_port = neighbor.get("local_interface", "")
        remote_device = neighbor.get("destination_host", "")
        remote_port = neighbor.get("port_id", "")
        if local_port and remote_device:
            neighbors.append((local_port, remote_device, remote_port))
    return neighbors


# Create the topology graph
def create_topology_graph(task):
    """
    Creates a network graph based on STP costs and CDP neighbors.
    """
    topology = nx.Graph()

    # Add edges to the graph
    for local_port, remote_device, remote_port in task.host["neighbors"]:
        stp_cost = task.host["stp_costs"].get(local_port, 1)  # Default cost if not found
        topology.add_edge(task.host.name, remote_device, weight=stp_cost)

    return topology


# Find the nearest neighbor
def find_nearest_neighbor(graph, start_node):
    """
    Finds the nearest neighbor from a given node using the shortest STP cost.
    """
    distances = nx.single_source_dijkstra_path_length(graph, start_node, weight="weight")
    sorted_neighbors = sorted(distances.items(), key=lambda x: x[1])
    if len(sorted_neighbors) > 1:
        return sorted_neighbors[1]  # Skip the start node itself
    return None


# Main function
def main():
    # Step 1: Gather network topology data
    print("Gathering topology data...")
    result = nr.run(task=gather_topology)
    print_result(result)

    # Step 2: Build the network graph
    print("Creating network graph...")
    network_graph = nx.Graph()
    for host in nr.inventory.hosts.values():
        task = host.data.get("gather_topology_task")
        graph = create_topology_graph(task)
        network_graph = nx.compose(network_graph, graph)

    # Step 3: Find the nearest neighbor for a selected switch
    start_node = input("Enter the switch name to find the nearest neighbor: ")
    if start_node not in network_graph:
        print(f"Switch {start_node} not found in the network topology.")
        return

    nearest = find_nearest_neighbor(network_graph, start_node)
    if nearest:
        print(f"The nearest neighbor to {start_node} is {nearest[0]} with a cost of {nearest[1]}.")
    else:
        print(f"No neighbors found for {start_node}.")


if __name__ == "__main__":
    main()
