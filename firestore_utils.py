import firebase_admin
from firebase_admin import credentials, firestore
import os

# Initialisation Firebase Admin
if not firebase_admin._apps:
    cred_path = "serviceAccountKey.json"  # Assurez-vous que ce fichier existe dans votre projet
    if not os.path.exists(cred_path):
        raise FileNotFoundError(f"Fichier {cred_path} non trouvé. Veuillez télécharger la clé JSON depuis Firebase Console.")

    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)

db = firestore.client()

def add_message(user, message):
    email = user.get('email') or user['user']['email']
    if not email:
        raise ValueError("Email introuvable dans l'objet utilisateur.")

    doc_ref = db.collection("messages").document()
    doc_ref.set({
        "email": email,
        "message": message
    })

def get_messages(user):
    email = user.get('email') or user['user']['email']
    if not email:
        raise ValueError("Email introuvable dans l'objet utilisateur.")

    messages_ref = db.collection("messages").where("email", "==", email)
    docs = messages_ref.stream()
    return [doc.to_dict().get("message") for doc in docs if doc.to_dict().get("message")]
