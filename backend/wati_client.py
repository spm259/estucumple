import requests
import os

WATI_API_URL = os.getenv("WATI_API_URL")
BEARER_TOKEN = os.getenv("WATI_BEARER_TOKEN")

headers = {
    "Authorization": f"Bearer {BEARER_TOKEN}",
    "Content-Type": "application/json"
}

def send_birthday_reminder(contact_name, phone_number):
    payload = {
        "template_name": "birthday_reminder",
        "broadcast_name": "Birthday Reminder",
        "parameters": [
            {"name": "contact_name", "value": contact_name},
        ],
        "phone_number": phone_number
    }

    response = requests.post(f"{WATI_API_URL}/api/v1/sendTemplateMessage", headers=headers, json=payload)
    if response.status_code == 200:
        print("Message sent successfully")
    else:
        print(f"Failed to send message: {response.status_code} - {response.text}")
