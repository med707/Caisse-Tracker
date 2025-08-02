# gain.py - PostgreSQL / mkdb version avec calcul mensuel complet
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from io import BytesIO

# --- Config page ---
st.set_page_config(page_title="📈 Calculateur de Gain", layout="wide")

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

# --- Création des tables si elles n'existent pas ---
with engine.begin() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS purchases (
            id SERIAL PRIMARY KEY,
            product TEXT,
            category TEXT,
            subcategory TEXT,
            supplier TEXT,
            quantity INTEGER,
            purchase_price NUMERIC,
            sale_price NUMERIC,
            date DATE
        )
    """))
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

st.title("📊 Calculateur de Gain sur les Ventes")

# --- Lecture des données Achats/Ventes ---
query = """
SELECT 
    id, 
    product, 
    category, 
    subcategory, 
    supplier, 
    quantity, 
    purchase_price, 
    sale_price, 
    date,
    (sale_price - purchase_price) * quantity AS gain
FROM purchases
WHERE purchase_price IS NOT NULL AND sale_price IS NOT NULL
ORDER BY date DESC
"""

with engine.connect() as conn:
    df = pd.read_sql(query, conn)

if df.empty:
    st.warning("Aucune donnée disponible pour le calcul de gain.")
    st.stop()

df["date"] = pd.to_datetime(df["date"]).dt.date
dates = sorted(df["date"].unique(), reverse=True)
selected_date = st.selectbox("📅 Sélectionner une date", dates)

filtered_df = df[df["date"] == selected_date]

# --- Tableau détaillé ---
st.subheader(f"🛒 Détail des Achats/Ventes pour le {selected_date}")
st.dataframe(filtered_df)

# --- Résumé du jour ---
total_gain = filtered_df["gain"].sum()
total_vente = (filtered_df["sale_price"] * filtered_df["quantity"]).sum()
total_achat = (filtered_df["purchase_price"] * filtered_df["quantity"]).sum()

col1, col2, col3 = st.columns(3)
col1.metric("🛒 Total Achat", f"{total_achat:.2f} TND")
col2.metric("💰 Total Vente", f"{total_vente:.2f} TND")
col3.metric("📈 Gain Net", f"{total_gain:.2f} TND", delta=f"{(total_gain/total_achat*100):.2f}%" if total_achat else "0%")

# --- Graphique gain par produit ---
st.subheader("📦 Gain par produit")
gain_par_produit = filtered_df.groupby("product")["gain"].sum().sort_values(ascending=False)
st.bar_chart(gain_par_produit)

# --- Export Excel ---
def to_excel(dataframe):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        dataframe.to_excel(writer, index=False)
    return output.getvalue()

st.download_button(
    label="📥 Télécharger (Excel)",
    data=to_excel(filtered_df),
    file_name=f"gain_{selected_date}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# =========================
# 📆 Vue mensuelle avancée
# =========================
st.header("📆 Vue mensuelle")

mode_vue = st.radio("Mode d'affichage :", ["📅 Jour", "🗓 Mois"], horizontal=True)

if mode_vue == "📅 Jour":
    st.write("📊 Analyse journalière déjà affichée ci-dessus.")
else:
    query_all = """
    SELECT 
        p.date,
        (p.sale_price - p.purchase_price) * p.quantity AS gain_vente,
        p.sale_price * p.quantity AS total_vente,
        p.purchase_price * p.quantity AS total_achat,
        COALESCE(ca.montant, 0) AS caisse,
        COALESCE(cr.montant, 0) AS credit,
        COALESCE(ch.montant, 0) AS depense
    FROM purchases p
    LEFT JOIN (
        SELECT date, SUM(montant) AS montant FROM caisse GROUP BY date
    ) ca ON ca.date = p.date
    LEFT JOIN (
        SELECT date, SUM(montant) AS montant FROM credits GROUP BY date
    ) cr ON cr.date = p.date
    LEFT JOIN (
        SELECT date, SUM(montant) AS montant FROM expenses GROUP BY date
    ) ch ON ch.date = p.date
    """

    try:
        with engine.connect() as conn:
            df_all = pd.read_sql(query_all, conn)
    except SQLAlchemyError as e:
        st.error(f"Erreur récupération données : {e}")
        st.stop()

    if df_all.empty:
        st.warning("Aucune donnée disponible pour la vue mensuelle.")
    else:
        df_all["date"] = pd.to_datetime(df_all["date"])
        df_all["mois"] = df_all["date"].dt.to_period("M").astype(str)

        df_month = df_all.groupby("mois").agg({
            "gain_vente": "sum",
            "total_vente": "sum",
            "total_achat": "sum",
            "caisse": "sum",
            "credit": "sum",
            "depense": "sum"
        }).reset_index()

        df_month["gain_brut"] = df_month["gain_vente"]
        df_month["gain_net"] = (df_month["caisse"] + df_month["credit"]) - df_month["depense"]

        df_month["evol_brut_%"] = df_month["gain_brut"].pct_change() * 100
        df_month["evol_net_%"] = df_month["gain_net"].pct_change() * 100

        df_month["evol_brut_%"] = df_month["evol_brut_%"].fillna(0).apply(lambda x: f"{x:+.1f}%")
        df_month["evol_net_%"] = df_month["evol_net_%"].fillna(0).apply(lambda x: f"{x:+.1f}%")

        st.subheader("📊 Résumé mensuel")
        st.dataframe(df_month.style.format({
            "gain_brut": "{:.2f} TND",
            "gain_net": "{:.2f} TND",
            "total_vente": "{:.2f} TND",
            "total_achat": "{:.2f} TND",
            "caisse": "{:.2f} TND",
            "credit": "{:.2f} TND",
            "depense": "{:.2f} TND"
        }))

        st.subheader("📈 Évolution mensuelle du gain net")
        st.line_chart(df_month.set_index("mois")[["gain_net", "gain_brut"]])
