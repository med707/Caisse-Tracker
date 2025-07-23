import firebase_admin
from firebase_admin import credentials, firestore

# Initialiser Firebase Admin SDK
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

def add_message(user, message):
    email = user['email']
    doc_ref = db.collection("messages").document()
    doc_ref.set({
        "user": email,
        "message": message
    })

def get_messages(user):
    email = user['email']
    messages_ref = db.collection("messages").where("user", "==", email)
    docs = messages_ref.stream()
    return [doc.to_dict()["message"] for doc in docs]
