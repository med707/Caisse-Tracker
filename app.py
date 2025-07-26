import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

# Initialisation Firebase (une seule fois)
@st.cache_resource
def init_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = init_firebase()

st.title("Exemple Streamlit + Firebase Firestore")

# Exemple : ajouter un document
if st.button("Ajouter un document test"):
    doc_ref = db.collection("tests").document()
    doc_ref.set({"message": "Bonjour depuis Streamlit!"})
    st.success("Document ajouté !")

# Exemple : lire des documents
docs = db.collection("tests").stream()
st.write("Documents dans la collection 'tests':")
for doc in docs:
    st.write(f"- {doc.id}: {doc.to_dict()}")

