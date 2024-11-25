import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time

# Controller credentials and settings
CONTROLLER_IPS = ["192.168.1.2", "192.168.1.3"]  # Replace with your controllers' IPs
USERNAME = "admin"  # Replace with your username
PASSWORD = "password"  # Replace with your password
POLL_INTERVAL = 300  # Time in seconds between polls

# Email settings
SMTP_SERVER = "smtp.example.com"  # Replace with your SMTP server
SMTP_PORT = 587  # Replace with your SMTP server's port
EMAIL_USERNAME = "your_email@example.com"  # Replace with your email
EMAIL_PASSWORD = "your_email_password"  # Replace with your email password
NOTIFICATION_EMAIL = "recipient@example.com"  # Replace with the recipient's email

# API Endpoints
API_BASE = "/v9_1/aps"  # Adjust based on API version of your SZ controllers


def get_access_points(controller_ip):
    """
    Fetches the list of access points and their status from the controller.
    """
    url = f"https://{controller_ip}{API_BASE}"
    try:
        response = requests.get(url, auth=(USERNAME, PASSWORD), verify=False)
        response.raise_for_status()
        return response.json().get("list", [])
    except requests.RequestException as e:
        print(f"Error connecting to controller {controller_ip}: {e}")
        return []


def send_notification(subject, message):
    """
    Sends an email notification.
    """
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_USERNAME
        msg["To"] = NOTIFICATION_EMAIL
        msg["Subject"] = subject

        msg.attach(MIMEText(message, "plain"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
            server.send_message(msg)

        print("Notification sent successfully.")
    except Exception as e:
        print(f"Failed to send notification: {e}")


def monitor_access_points():
    """
    Monitors access points and sends notifications when any go offline.
    """
    previous_status = {}

    while True:
        current_status = {}
        for controller_ip in CONTROLLER_IPS:
            aps = get_access_points(controller_ip)
            for ap in aps:
                ap_name = ap.get("name")
                ap_mac = ap.get("mac")
                ap_status = ap.get("status")  # e.g., "Online" or "Offline"

                current_status[ap_mac] = {
                    "name": ap_name,
                    "status": ap_status,
                    "controller": controller_ip,
                }

        # Check for changes in status
        offline_aps = []
        for mac, details in current_status.items():
            if details["status"].lower() != "online":
                offline_aps.append(details)

            if mac in previous_status:
                if details["status"] != previous_status[mac]["status"]:
                    print(f"Status changed for {details['name']}: {details['status']}")

        # Send notification for offline APs
        if offline_aps:
            subject = "Alert: Access Points Offline"
            message = "The following access points are offline:\n\n"
            for ap in offline_aps:
                message += f"- {ap['name']} (MAC: {ap['mac']}, Controller: {ap['controller']})\n"

            send_notification(subject, message)

        # Update the previous status
        previous_status = current_status

        # Wait before polling again
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    monitor_access_points()