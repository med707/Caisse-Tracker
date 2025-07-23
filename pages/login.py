import sys
import os

# Ajouter le dossier parent au path pour pouvoir importer firestore_utils.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from firestore_utils import add_message, get_messages
import streamlit as st
import pyrebase

# --- Configuration Firebase (remplace par tes infos) ---
firebaseConfig = {
    'apiKey': 'TON_API_KEY',
    'authDomain': 'TON_PROJECT.firebaseapp.com',
    'projectId': 'TON_PROJECT_ID',
    'storageBucket': 'TON_PROJECT.appspot.com',
    'messagingSenderId': 'TON_SENDER_ID',
    'appId': 'TON_APP_ID',
    'databaseURL': ''
}

firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()

st.title("🔐 Connexion Firebase avec Streamlit")

if 'user' not in st.session_state:
    email = st.text_input("Email")
    password = st.text_input("Mot de passe", type="password")

    if st.button("Se connecter"):
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            st.session_state['user'] = user
            st.success(f"Connecté en tant que : {email}")
            st.experimental_rerun()
        except:
            st.error("Email ou mot de passe invalide.")
else:
    user = st.session_state['user']
    st.success(f"Connecté en tant que : {user['email']}")

    new_msg = st.text_input("💬 Ajouter un message Firestore")
    if st.button("Ajouter"):
        try:
            add_message(user, new_msg)
            st.success("Message ajouté !")
        except Exception as e:
            st.error(f"Erreur lors de l'ajout : {e}")

    st.subheader("📄 Messages enregistrés :")
    messages = get_messages(user)
    for msg in messages:
        st.write("•", msg)

    if st.button("Se déconnecter"):
        del st.session_state['user']
        st.experimental_rerun()

