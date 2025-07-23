import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
from io import BytesIO
from fpdf import FPDF

# --- Connexion à la base de données ---
conn = sqlite3.connect("supermarket.db", check_same_thread=False)
cursor = conn.cursor()

# --- Vérifie et crée la table si elle n'existe pas ---
cursor.execute('''
    CREATE TABLE IF NOT EXISTS caisse (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        montant REAL,
        date TEXT,
        periode TEXT
    )
''')
conn.commit()

# --- Ajoute la colonne "periode" si elle n'existe pas ---
cursor.execute("PRAGMA table_info(caisse)")
columns = [col[1] for col in cursor.fetchall()]
if "periode" not in columns:
    cursor.execute("ALTER TABLE caisse ADD COLUMN periode TEXT")
    conn.commit()

# --- Titre ---
st.title("💰 Caisse Journalière - Entrée par Plage Horaire")

# --- Définir les plages horaires ---
PERIODES = [
    "🕐 04–14",
    "🕑 14–17",
    "🌙 17–02"
]

# --- Formulaire de saisie ---
with st.form("add_entry", clear_on_submit=True):
    montant = st.number_input("Montant", min_value=0.0, format="%.2f")
    date_val = st.date_input("Date", value=datetime.now().date())
    periode = st.selectbox("Plage horaire", PERIODES)
    submit = st.form_submit_button("Enregistrer")

    if submit:
        cursor.execute(
            "INSERT INTO caisse (montant, date, periode) VALUES (?, ?, ?)",
            (montant, date_val.strftime("%Y-%m-%d"), periode)
        )
        conn.commit()
        st.success(f"✅ Montant {montant:.2f} TND enregistré pour la plage {periode}.")

# --- Lecture des données ---
df = pd.read_sql_query("SELECT * FROM caisse ORDER BY date DESC", conn)

if df.empty:
    st.info("Aucune donnée enregistrée.")
    st.stop()

# --- Résumé par date et plage ---
st.subheader("📊 Résumé par date et plage horaire")

# Choix de la date
dates = sorted(df["date"].unique(), reverse=True)
selected_date = st.selectbox("Sélectionner une date", dates)

# Filtrer les données de la date sélectionnée
df_date = df[df["date"] == selected_date]

# Créer un résumé par période
summary = df_date.groupby("periode")["montant"].sum().reindex(PERIODES).fillna(0)

# Affichage du graphique
st.bar_chart(summary)
st.write(summary.to_frame(name="Total TND"))

# Total du jour
total_day = df_date["montant"].sum()
st.success(f"🧾 Total du {selected_date} : {total_day:.2f} TND")

# Comparaison avec autres jours
st.subheader("📈 Comparaison avec d'autres jours")

selected_datetime = datetime.strptime(selected_date, "%Y-%m-%d")

# Hier
yesterday = (selected_datetime - timedelta(days=1)).strftime("%Y-%m-%d")
# Même jour de la semaine dernière
last_week_same_day = (selected_datetime - timedelta(days=7)).strftime("%Y-%m-%d")
# Même jour du mois dernier (approximatif)
try:
    last_month_same_day = selected_datetime.replace(month=selected_datetime.month - 1).strftime("%Y-%m-%d")
except ValueError:
    last_month_same_day = (selected_datetime - timedelta(days=30)).strftime("%Y-%m-%d")

comparisons = {
    "Hier": yesterday,
    "Même jour semaine dernière": last_week_same_day,
    "Même jour mois dernier": last_month_same_day
}

for label, comp_date in comparisons.items():
    comp_df = df[df["date"] == comp_date]
    comp_total = comp_df["montant"].sum()
    st.info(f"{label} ({comp_date}) : {comp_total:.2f} TND")

# --- Télécharger les données en Excel ---
st.subheader("⬇️ Télécharger les données")

def to_excel(dataframe):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        dataframe.to_excel(writer, index=False)
    return output.getvalue()

excel_file = to_excel(df)

st.download_button(
    label="📥 Télécharger toutes les données (Excel)",
    data=excel_file,
    file_name=f"caisse_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# --- Télécharger les données en PDF ---
def to_pdf(dataframe):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Résumé Caisse", ln=True, align="C")
    pdf.ln(10)

    for index, row in dataframe.iterrows():
        line = f"{row['date']} | {row['periode']} | {row['montant']:.2f} TND"
        # Encodage sûr sans erreurs Unicode
        line = line.encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(200, 8, txt=line, ln=True)

    pdf_output = pdf.output(dest='S').encode('latin-1')
    return pdf_output

pdf_file = to_pdf(df)

st.download_button(
    label="📄 Télécharger en PDF",
    data=pdf_file,
    file_name=f"caisse_{datetime.now().strftime('%Y-%m-%d')}.pdf",
    mime="application/pdf"
)

# --- Fermer la connexion ---
conn.close()

