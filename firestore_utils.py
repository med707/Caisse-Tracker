import requests
import datetime

FIREBASE_PROJECT_ID = "TON_PROJECT_ID"  # Remplace par ton projectId Firebase

def add_message(user, message):
    id_token = user['idToken']
    local_id = user['localId']

    doc_id = f"{local_id}_{int(datetime.datetime.now().timestamp())}"
    url = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents/messages/{doc_id}"
    
    headers = {"Authorization": f"Bearer {id_token}"}
    data = {
        "fields": {
            "message": {"stringValue": message},
            "timestamp": {"timestampValue": datetime.datetime.utcnow().isoformat() + "Z"},
            "user": {"stringValue": user['email']}
        }
    }

    response = requests.put(url, headers=headers, json=data)
    response.raise_for_status()


def get_messages(user):
    id_token = user['idToken']
    url = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents/messages"
    headers = {"Authorization": f"Bearer {id_token}"}

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return ["Erreur de récupération."]
    
    docs = response.json().get("documents", [])
    user_msgs = [
        doc["fields"]["message"]["stringValue"]
        for doc in docs
        if doc["fields"].get("user", {}).get("stringValue", "") == user['email']
    ]
    return user_msgs

