import requests
import os

def send_pushover_message(title, message):
    print("Sending pushover message:", message)

    url = "https://api.pushover.net/1/messages.json"

    data = {
        "token": os.getenv("PUSHOVER_APP_TOKEN"),
        "user": os.getenv("PUSHOVER_USER"),
        "device": os.getenv("PUSHOVER_DEVICE"),
        "title": title,
        "message": message,
    }

    response = requests.post(url, data=data)
    print(response.text)
