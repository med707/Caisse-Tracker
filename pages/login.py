import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

# --- Initialisation Firebase Admin (une fois) ---
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")  # Chemin vers ton fichier JSON
    firebase_admin.initialize_app(cred)

db = firestore.client()

st.title("🔐 Connexion simple + Firestore avec Firebase Admin SDK")

# Simuler un login basique par email
if 'user_email' not in st.session_state:
    email = st.text_input("Email")
    if st.button("Se connecter (simulation)"):
        if email.strip() == "":
            st.error("Veuillez entrer un email valide.")
        else:
            st.session_state['user_email'] = email.strip()
            st.experimental_rerun()
else:
    st.success(f"Connecté en tant que : {st.session_state['user_email']}")

    # Ajouter un message Firestore
    new_message = st.text_input("💬 Ajouter un message")
    if st.button("Ajouter le message"):
        if new_message.strip() == "":
            st.error("Le message ne peut pas être vide.")
        else:
            doc_ref = db.collection('messages').document()
            doc_ref.set({
                "user": st.session_state['user_email'],
                "message": new_message.strip(),
                "timestamp": firestore.SERVER_TIMESTAMP
            })
            st.success("Message ajouté !")

    # Afficher les messages
    st.subheader("📄 Messages enregistrés")
    messages = db.collection('messages').order_by('timestamp', direction=firestore.Query.DESCENDING).stream()
    for msg in messages:
        data = msg.to_dict()
        st.write(f"**{data.get('user')}** : {data.get('message')}")

    # Bouton déconnexion
    if st.button("Se déconnecter"):
        del st.session_state['user_email']
        st.experimental_rerun()
