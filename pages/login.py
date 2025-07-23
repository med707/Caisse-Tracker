import pyrebase
import streamlit as st

# --- Firebase config ---
firebaseConfig = {
    'apiKey': 'your_api_key',
    'authDomain': 'your_project.firebaseapp.com',
    'projectId': 'your_project_id',
    'storageBucket': 'your_project.appspot.com',
    'messagingSenderId': 'your_sender_id',
    'appId': 'your_app_id',
    'databaseURL': ''
}

firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()

# --- Streamlit login form ---
st.title("Login")

email = st.text_input("Email")
password = st.text_input("Password", type="password")

if st.button("Login"):
    try:
        user = auth.sign_in_with_email_and_password(email, password)
        st.success(f"Logged in as {email}")
        # Use session_state to track login
        st.session_state['user'] = email
    except:
        st.error("Invalid credentials")

