import streamlit as st
import pyrebase
from firestore_utils import add_message, get_messages

# --- Config Firebase ---
firebaseConfig = {
    'apiKey': 'AIzaSyBI29zVQRZhOdigOBEt7gA8YYaEeoEU8Pk',
    'authDomain': 'gestion-supermarket.firebaseapp.com',
    'projectId': 'gestion-supermarket',
    'storageBucket': 'gestion-supermarket.appspot.com',
    'messagingSenderId': '553981389663',
    'appId': '1:553981389663:web:c8db775b8cf47e2ae5e4ea',
    'databaseURL': ''  # Non requis ici
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
