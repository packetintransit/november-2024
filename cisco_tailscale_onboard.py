import paramiko
import requests

class CiscoTailscaleOnboard:
    def __init__(self, tailscale_api_key, ssh_user, ssh_password):
        """
        Initialize the library.
        :param tailscale_api_key: API key for Tailscale management.
        :param ssh_user: SSH username for the Cisco switches.
        :param ssh_password: SSH password for the Cisco switches.
        """
        self.tailscale_api_key = tailscale_api_key
        self.ssh_user = ssh_user
        self.ssh_password = ssh_password
        self.tailscale_api_url = "https://api.tailscale.com/api/v2"

    def onboard_switch(self, switch_ip, hostname):
        """
        Onboard a Cisco switch to Tailscale.
        :param switch_ip: IP address of the Cisco switch.
        :param hostname: Desired hostname for the Tailscale device.
        """
        try:
            # Step 1: Configure Tailscale on the switch
            self._configure_tailscale_on_switch(switch_ip)

            # Step 2: Add switch to Tailscale
            self._add_device_to_tailscale(hostname)
            
            print(f"Successfully onboarded {hostname} ({switch_ip}) to Tailscale.")
        except Exception as e:
            print(f"Error onboarding switch: {e}")

    def _configure_tailscale_on_switch(self, switch_ip):
        """
        Configure Tailscale on the Cisco switch using SSH.
        :param switch_ip: IP address of the Cisco switch.
        """
        try:
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(switch_ip, username=self.ssh_user, password=self.ssh_password)

            # Install Tailscale or configure routing
            commands = [
                "configure terminal",
                "interface vlan1",  # Example interface for Tailscale
                "ip address dhcp",
                "exit",
                "ip http server",
                "exit"
            ]

            for command in commands:
                stdin, stdout, stderr = ssh_client.exec_command(command)
                print(stdout.read().decode())

            ssh_client.close()
        except Exception as e:
            raise Exception(f"SSH configuration failed for {switch_ip}: {e}")

    def _add_device_to_tailscale(self, hostname):
        """
        Add the device to the Tailscale network.
        :param hostname: Desired hostname for the device in Tailscale.
        """
        try:
            headers = {"Authorization": f"Bearer {self.tailscale_api_key}"}
            data = {
                "hostname": hostname,
                "tags": ["tag:cisco-switch"],  # Example tags
            }
            response = requests.post(f"{self.tailscale_api_url}/devices", headers=headers, json=data)

            if response.status_code != 200:
                raise Exception(f"Tailscale API error: {response.text}")
        except Exception as e:
            raise Exception(f"Tailscale device addition failed: {e}")