import streamlit as st
import sqlite3
from datetime import datetime, time
import pandas as pd
import matplotlib.pyplot as plt
from lang_utils import get_translation

# --- Language selection ---
lang = st.sidebar.selectbox("🌍 Langue / اللغة", ["fr", "ar"], index=0)
_ = lambda key: get_translation(key, lang)

st.title("💰 Caisse Journalière")

# --- Connect to database ---
conn = sqlite3.connect("supermarket.db")
cursor = conn.cursor()

# --- Create table if not exists ---
cursor.execute('''
    CREATE TABLE IF NOT EXISTS caisse (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        montant REAL,
        date_heure TEXT
    )
''')
conn.commit()

# --- Ajouter un enregistrement de caisse ---
st.subheader("➕ Ajouter un montant")
with st.form("add_cash", clear_on_submit=True):
    montant = st.number_input("Montant", min_value=0.0, format="%.2f")
    date_val = st.date_input("Date", value=datetime.now().date())
    time_val = st.time_input("Heure", value=datetime.now().time())

    submit = st.form_submit_button("💾 Enregistrer")

    if submit:
        date_heure = datetime.combine(date_val, time_val)
        cursor.execute(
            "INSERT INTO caisse (montant, date_heure) VALUES (?, ?)", 
            (montant, date_heure.strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        st.success(f"Montant de {montant:.2f} TND enregistré.")

# --- Charger les données ---
df = pd.read_sql_query("SELECT * FROM caisse", conn, parse_dates=['date_heure'])

if df.empty:
    st.warning("Aucune donnée de caisse disponible.")
    st.stop()

# --- Section analyse ---
st.subheader("📊 Analyse par jour")

# Sélection de la date pour analyse
unique_dates = sorted(df['date_heure'].dt.date.unique(), reverse=True)
selected_date = st.selectbox("Sélectionner une date", unique_dates)

# Filtrage des données pour la date choisie
selected_df = df[df['date_heure'].dt.date == selected_date].copy()
selected_df['heure'] = selected_df['date_heure'].dt.time

# --- Définir les plages horaires ---
def classify_period(t):
    if time(5, 0) <= t < time(14, 0):
        return "🕔 05h–14h"
    elif time(14, 0) <= t < time(17, 0):
        return "🕑 14h–17h"
    else:
        return "🕔 17h–01h"

selected_df['période'] = selected_df['heure'].apply(classify_period)

# --- Résumé par période ---
summary = selected_df.groupby('période')['montant'].sum().reindex(["🕔 05h–14h", "🕑 14h–17h", "🕔 17h–01h"]).fillna(0)

st.write(f"### Résumé du {selected_date}")
st.bar_chart(summary)
st.write(summary.to_frame(name="Total TND"))

# --- Alertes si montant bas ---
low_thresholds = {
    "🕔 05h–14h": 350.0,
    "🕑 14h–17h": 80.0,
    "🕔 17h–01h": 350.0
}

for period, total in summary.items():
    if total < low_thresholds[period]:
        st.error(f"🚨 Attention: le total pour la période '{period}' est bas ({total:.2f} TND < {low_thresholds[period]} TND)")

# --- Total de la journée ---
total_day = selected_df['montant'].sum()
st.success(f"💵 Total de la journée: {total_day:.2f} TND")

if total_day < 1000:
    st.error(f"🚨 Alerte: Total journalier faible ({total_day:.2f} TND < 1000 TND)")

# --- Comparaison avec une autre journée ---
st.subheader("📅 Comparaison avec un autre jour")
other_dates = [d for d in unique_dates if d != selected_date]
if other_dates:
    compare_date = st.selectbox("Comparer avec", other_dates)
    compare_df = df[df['date_heure'].dt.date == compare_date].copy()
    compare_df['heure'] = compare_df['date_heure'].dt.time
    compare_df['période'] = compare_df['heure'].apply(classify_period)
    compare_summary = compare_df.groupby('période')['montant'].sum().reindex(["🕔 05h–14h", "🕑 14h–17h", "🕔 17h–01h"]).fillna(0)

    # Afficher les deux comparés
    st.write(f"### Comparaison: {selected_date} vs {compare_date}")
    comparison_df = pd.DataFrame({
        str(selected_date): summary,
        str(compare_date): compare_summary
    })
    st.bar_chart(comparison_df)
    st.write(comparison_df)
else:
    st.info("Aucune autre journée disponible pour comparaison.")

conn.close()

