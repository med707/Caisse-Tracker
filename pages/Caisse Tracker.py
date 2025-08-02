# caisse-tracker.py (PostgreSQL / mkdb version)
import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
import pandas as pd
from io import BytesIO
from fpdf import FPDF

# --- Connect to PostgreSQL using Streamlit secrets ---
try:
    DATABASE_URL = st.secrets["database"]["url"]
    engine = create_engine(DATABASE_URL)

    # Test connection
    with engine.connect() as conn:
        db_version = conn.execute(text("SELECT version()")).fetchone()
    st.success(f"✅ Connected to: {db_version[0]}")
except SQLAlchemyError as e:
    st.error(f"❌ Database connection failed: {e}")
    st.stop()

# --- Create table if not exists ---
with engine.begin() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS caisse (
            id SERIAL PRIMARY KEY,
            montant NUMERIC,
            date DATE,
            periode TEXT
        )
    """))

# --- UI title ---
st.title("💰 Caisse Journalière - Entrée par Plage Horaire")

# --- Periods ---
PERIODES = [
    "🕐 04–14",
    "🕑 14–17",
    "🌙 17–02"
]

# --- Form to add entry ---
with st.form("add_entry", clear_on_submit=True):
    montant = st.number_input("Montant", min_value=0.0, format="%.2f")
    date_val = st.date_input("Date", value=datetime.now().date())
    periode = st.selectbox("Plage horaire", PERIODES)
    submit = st.form_submit_button("Enregistrer")

    if submit:
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO caisse (montant, date, periode)
                VALUES (:montant, :date, :periode)
            """), {
                "montant": montant,
                "date": date_val,
                "periode": periode
            })
        st.success(f"✅ Montant {montant:.2f} TND enregistré pour la plage {periode}.")

# --- Load data ---
with engine.connect() as conn:
    df = pd.read_sql("SELECT * FROM caisse ORDER BY date DESC", conn)

if df.empty:
    st.info("Aucune donnée enregistrée.")
    st.stop()

# --- Summary by date ---
st.subheader("📊 Résumé par date et plage horaire")

dates = sorted(df["date"].astype(str).unique(), reverse=True)
selected_date = st.selectbox("Sélectionner une date", dates)

df_date = df[df["date"].astype(str) == selected_date]
summary = df_date.groupby("periode")["montant"].sum().reindex(PERIODES).fillna(0)

st.bar_chart(summary)
st.write(summary.to_frame(name="Total TND"))

# Total of the day
total_day = df_date["montant"].sum()
st.success(f"🧾 Total du {selected_date} : {total_day:.2f} TND")

# --- Comparisons ---
st.subheader("📈 Comparaison avec d'autres jours")
selected_datetime = datetime.strptime(selected_date, "%Y-%m-%d")

comparisons = {
    "Hier": (selected_datetime - timedelta(days=1)).strftime("%Y-%m-%d"),
    "Même jour semaine dernière": (selected_datetime - timedelta(days=7)).strftime("%Y-%m-%d"),
    "Même jour mois dernier": (selected_datetime - timedelta(days=30)).strftime("%Y-%m-%d")
}

for label, comp_date in comparisons.items():
    comp_df = df[df["date"].astype(str) == comp_date]
    comp_total = comp_df["montant"].sum()
    st.info(f"{label} ({comp_date}) : {comp_total:.2f} TND")

# --- Export Excel ---
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

# --- Export PDF ---
def to_pdf(dataframe):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Résumé Caisse", ln=True, align="C")
    pdf.ln(10)

    for _, row in dataframe.iterrows():
        line = f"{row['date']} | {row['periode']} | {float(row['montant']):.2f} TND"
        line = line.encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(200, 8, txt=line, ln=True)

    return pdf.output(dest='S').encode('latin-1')

pdf_file = to_pdf(df)
st.download_button(
    label="📄 Télécharger en PDF",
    data=pdf_file,
    file_name=f"caisse_{datetime.now().strftime('%Y-%m-%d')}.pdf",
    mime="application/pdf"
)
