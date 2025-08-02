# finance.py - Saisie Caisse, Crédit et Dépenses (PostgreSQL / mkdb)
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="💰 Gestion Financière", layout="wide")

# --- Connexion PostgreSQL ---
try:
    DATABASE_URL = st.secrets["database"]["url"]
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        db_version = conn.execute(text("SELECT version()")).fetchone()
    st.success(f"✅ Connecté à : {db_version[0]}")
except SQLAlchemyError as e:
    st.error(f"❌ Connexion base échouée : {e}")
    st.stop()

# --- Création des tables si non existantes ---
with engine.begin() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS caisse (
            id SERIAL PRIMARY KEY,
            montant NUMERIC,
            date DATE,
            periode TEXT
        )
    """))
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS credits (
            id SERIAL PRIMARY KEY,
            montant NUMERIC,
            date DATE,
            note TEXT
        )
    """))
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS expenses (
            id SERIAL PRIMARY KEY,
            montant NUMERIC,
            date DATE,
            type TEXT
        )
    """))

# --- Sélecteur de section ---
section = st.radio("Choisir une opération :", ["💰 Caisse", "🏦 Crédit", "💸 Dépense"], horizontal=True)

# ==========================
# 💰 CAISSE
# ==========================
if section == "💰 Caisse":
    st.subheader("💰 Ajouter à la Caisse")
    with st.form("form_caisse", clear_on_submit=True):
        montant = st.number_input("Montant (TND)", min_value=0.0, format="%.2f")
        date_val = st.date_input("Date", value=datetime.now().date())
        periode = st.selectbox("Plage horaire", ["🕐 04–14", "🕑 14–17", "🌙 17–02"])
        submit_caisse = st.form_submit_button("Enregistrer")
        if submit_caisse:
            with engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO caisse (montant, date, periode)
                    VALUES (:montant, :date, :periode)
                """), {
                    "montant": montant,
                    "date": date_val,
                    "periode": periode
                })
            st.success(f"✅ {montant:.2f} TND ajouté à la caisse ({periode})")

# ==========================
# 🏦 CRÉDIT
# ==========================
elif section == "🏦 Crédit":
    st.subheader("🏦 Ajouter un Crédit")
    with st.form("form_credit", clear_on_submit=True):
        montant = st.number_input("Montant du crédit (TND)", min_value=0.0, format="%.2f")
        date_val = st.date_input("Date", value=datetime.now().date())
        note = st.text_input("Note / Source du crédit")
        submit_credit = st.form_submit_button("Enregistrer")
        if submit_credit:
            with engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO credits (montant, date, note)
                    VALUES (:montant, :date, :note)
                """), {
                    "montant": montant,
                    "date": date_val,
                    "note": note
                })
            st.success(f"✅ Crédit de {montant:.2f} TND enregistré")

# ==========================
# 💸 DÉPENSES
# ==========================
elif section == "💸 Dépense":
    st.subheader("💸 Ajouter une Dépense")
    with st.form("form_depense", clear_on_submit=True):
        montant = st.number_input("Montant dépensé (TND)", min_value=0.0, format="%.2f")
        date_val = st.date_input("Date", value=datetime.now().date())
        type_depense = st.selectbox("Type de dépense", [
            "Facture Électricité",
            "Facture Eau",
            "Loyer",
            "Consommation",
            "Autre"
        ])
        submit_depense = st.form_submit_button("Enregistrer")
        if submit_depense:
            with engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO expenses (montant, date, type)
                    VALUES (:montant, :date, :type)
                """), {
                    "montant": montant,
                    "date": date_val,
                    "type": type_depense
                })
            st.success(f"✅ Dépense de {montant:.2f} TND enregistrée ({type_depense})")

# ==========================
# 📊 Historique & Export
# ==========================
st.subheader("📜 Historique des Opérations")

tables = {
    "💰 Caisse": "caisse",
    "🏦 Crédit": "credits",
    "💸 Dépenses": "expenses"
}

selected_table = st.selectbox("Choisir la table à afficher", list(tables.keys()))
table_name = tables[selected_table]

with engine.connect() as conn:
    df_hist = pd.read_sql(f"SELECT * FROM {table_name} ORDER BY date DESC", conn)

if df_hist.empty:
    st.info("Aucune donnée enregistrée.")
else:
    st.dataframe(df_hist)

    # Export Excel
    def to_excel(dataframe):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            dataframe.to_excel(writer, index=False)
        return output.getvalue()

    st.download_button(
        label="📥 Télécharger (Excel)",
        data=to_excel(df_hist),
        file_name=f"{table_name}_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
