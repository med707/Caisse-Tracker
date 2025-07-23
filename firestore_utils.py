import firebase_admin
from firebase_admin import credentials, auth, firestore
import datetime

# Initialise Firebase Admin avec ta clé JSON de service
# Remplace 'path/to/serviceAccountKey.json' par le chemin réel de ta clé
cred = credentials.Certificate('path/to/serviceAccountKey.json')
firebase_admin.initialize_app(cred)

db = firestore.client()

def verify_id_token(id_token):
    """
    Vérifie et décode un token d'identification Firebase.
    Retourne les infos utilisateur si valide, sinon None.
    """
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        print(f"Erreur de vérification du token: {e}")
        return None

def add_message(user_uid, message):
    """
    Ajoute un message dans Firestore dans la collection 'messages'.
    user_uid est l'UID Firebase de l'utilisateur.
    """
    doc_ref = db.collection('messages').document()
    doc_ref.set({
        'user_uid': user_uid,
        'message': message,
        'timestamp': datetime.datetime.utcnow()
    })

def get_messages():
    """
    Récupère tous les messages ordonnés par date décroissante.
    """
    messages_ref = db.collection('messages').order_by('timestamp', direction=firestore.Query.DESCENDING)
    docs = messages_ref.stream()

    return [
        {'user_uid': doc.to_dict().get('user_uid'), 'message': doc.to_dict().get('message'), 'timestamp': doc.to_dict().get('timestamp')}
        for doc in docs
    ]
