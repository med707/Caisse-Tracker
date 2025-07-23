import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="📈 Calculateur de Gain", layout="wide")

# Connexion à la base
conn = sqlite3.connect("supermarket.db", check_same_thread=False)

# Vérifie que la table "purchases" existe
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product TEXT,
        category TEXT,
        subcategory TEXT,
        supplier TEXT,
        quantity INTEGER,
        purchase_price REAL,
        sale_price REAL,
        date TEXT
    )
""")
conn.commit()

st.title("📊 Calculateur de Gain sur les Ventes")

# Lecture des données
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
df = pd.read_sql_query(query, conn, parse_dates=['date'])

if df.empty:
    st.warning("Aucune donnée disponible pour le calcul de gain.")
    st.stop()

# Filtrage par date
df["date"] = pd.to_datetime(df["date"]).dt.date
dates = sorted(df["date"].unique(), reverse=True)
selected_date = st.selectbox("📅 Sélectionner une date", dates)

filtered_df = df[df["date"] == selected_date]

# Affichage du tableau
st.subheader(f"🛒 Détail des Achats/Ventes pour le {selected_date}")
st.dataframe(filtered_df)

# Résumé
total_gain = filtered_df["gain"].sum()
total_vente = (filtered_df["sale_price"] * filtered_df["quantity"]).sum()
total_achat = (filtered_df["purchase_price"] * filtered_df["quantity"]).sum()

col1, col2, col3 = st.columns(3)
col1.metric("🛒 Total Achat", f"{total_achat:.2f} TND")
col2.metric("💰 Total Vente", f"{total_vente:.2f} TND")
col3.metric("📈 Gain Net", f"{total_gain:.2f} TND", delta=f"{(total_gain/total_achat*100):.2f}%" if total_achat else "0%")

# Graphique par produit
st.subheader("📦 Gain par produit")
gain_par_produit = filtered_df.groupby("product")["gain"].sum().sort_values(ascending=False)
st.bar_chart(gain_par_produit)

# Téléchargement Excel
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

conn.close()

