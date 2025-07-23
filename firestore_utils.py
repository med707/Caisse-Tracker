import requests
import datetime

FIREBASE_PROJECT_ID = "gestion-supermarket"  # Mets ici ton project ID exact

def add_message(user, message):
    id_token = user['idToken']
    local_id = user['localId']

    url = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents/messages/{local_id}_{int(datetime.datetime.now().timestamp())}"
    headers = {
        "Authorization": f"Bearer {id_token}",
        "Content-Type": "application/json"
    }
    data = {
        "fields": {
            "message": {"stringValue": message},
            "timestamp": {"timestampValue": datetime.datetime.utcnow().isoformat() + "Z"},
            "user": {"stringValue": user['email']}
        }
    }

    response = requests.patch(url, headers=headers, json=data)
    response.raise_for_status()


def get_messages(user):
    id_token = user['idToken']
    url = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents/messages"
    headers = {
        "Authorization": f"Bearer {id_token}"
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return ["Erreur lors de la récupération des messages."]

    docs = response.json().get("documents", [])
    messages = []
    for doc in docs:
        fields = doc.get("fields", {})
        msg = fields.get("message", {}).get("stringValue", "")
        messages.append(msg)
    return messages
