# pages/expenses.py - Gestion des Charges (PostgreSQL / mkdb)
import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from io import BytesIO

st.set_page_config(page_title="💸 Gestion des Charges", layout="wide")

# --- Connexion à la base PostgreSQL ---
try:
    DATABASE_URL = st.secrets["database"]["url"]
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        db_version = conn.execute(text("SELECT version()")).fetchone()
    st.success(f"✅ Connecté à : {db_version[0]}")
except SQLAlchemyError as e:
    st.error(f"❌ Erreur de connexion à la base : {e}")
    st.stop()

# --- Création table charges si non existante ---
with engine.begin() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS expenses (
            id SERIAL PRIMARY KEY,
            type TEXT,
            description TEXT,
            montant NUMERIC,
            date DATE
        )
    """))

st.title("💸 Gestion des Charges")

# --- Formulaire ajout charge ---
with st.form("expense_form", clear_on_submit=True):
    type_charge = st.selectbox(
        "📂 Type de charge",
        ["Loyer", "Facture Électricité", "Facture Eau", "Casse", "Consommation perso", "Autre"]
    )
    description = st.text_input("📝 Description (facultatif)")
    montant = st.number_input("💰 Montant (TND)", min_value=0.0, format="%.2f")
    date_val = st.date_input("📅 Date", value=datetime.now().date())
    submit = st.form_submit_button("Enregistrer la charge")

    if submit:
        if montant <= 0:
            st.error("Veuillez entrer un montant valide.")
        else:
            with engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO expenses (type, description, montant, date)
                    VALUES (:type, :description, :montant, :date)
                """), {
                    "type": type_charge,
                    "description": description.strip(),
                    "montant": montant,
                    "date": date_val
                })
            st.success(f"✅ Charge '{type_charge}' de {montant:.2f} TND enregistrée.")

# --- Lecture des données ---
with engine.connect() as conn:
    df = pd.read_sql("SELECT * FROM expenses ORDER BY date DESC", conn)

if df.empty:
    st.info("Aucune charge enregistrée.")
    st.stop()

# --- Affichage tableau ---
st.subheader("📜 Historique des Charges")
st.dataframe(df)

# --- Totaux par type ---
st.subheader("📊 Total par type de charge")
total_par_type = df.groupby("type")["montant"].sum().sort_values(ascending=False)
st.bar_chart(total_par_type)

# --- Export Excel ---
def to_excel(dataframe):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        dataframe.to_excel(writer, index=False)
    return output.getvalue()

st.download_button(
    label="📥 Télécharger toutes les charges (Excel)",
    data=to_excel(df),
    file_name=f"charges_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
