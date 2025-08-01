import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from lang_utils import get_translation

# --- LANGUE ---
lang = st.sidebar.selectbox("🌍 Langue / اللغة", ["fr", "ar"], index=0)
t = lambda key: get_translation(key, lang)

# --- CONFIG PAGE ---
st.set_page_config(
    page_title=t("Statistiques"),
    layout="centered",
    page_icon="📈"
)

st.title(t("Statistiques des achats/ventes"))

# --- CONNEXION DB ---
conn = sqlite3.connect("supermarket.db", check_same_thread=False)

# --- CHARGEMENT DONNÉES ---
query = "SELECT * FROM purchases ORDER BY date DESC"
df = pd.read_sql_query(query, conn)

if df.empty:
    st.warning(t("Aucune donnée trouvée"))
    st.stop()

# --- NOMMAGE COLONNES SELON LA STRUCTURE ACTUELLE ---
df.columns = [
    "ID",            # id
    "Produit",       # product
    "Catégorie",     # category
    "Sous-catégorie",# subcategory
    "Fournisseur",   # supplier
    "Quantité",      # quantity
    "Prix d'achat",  # purchase_price
    "Prix de vente", # sale_price
    "Date"           # date
]

# Convertir Date en datetime
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

# Calculs
df["Total achat"] = df["Prix d'achat"] * df["Quantité"]
df["Total vente"] = df["Prix de vente"] * df["Quantité"]
df["Gain"] = df["Total vente"] - df["Total achat"]

# --- FILTRAGE PAR DATE ---
st.subheader(t("Filtres"))
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input(t("Date début"), value=df["Date"].min().date())
with col2:
    end_date = st.date_input(t("Date fin"), value=df["Date"].max().date())

mask = (df["Date"] >= pd.to_datetime(start_date)) & (df["Date"] <= pd.to_datetime(end_date))
filtered_df = df.loc[mask]

if filtered_df.empty:
    st.info(t("Aucun produit trouvé pour cette plage de dates"))
else:
    # --- Statistiques globales ---
    st.subheader(t("Statistiques globales"))
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(t("Valeur totale achats"), f"{filtered_df['Total achat'].sum():.2f} TND")
    col2.metric(t("Valeur totale ventes"), f"{filtered_df['Total vente'].sum():.2f} TND")
    col3.metric(t("Gain total"), f"{filtered_df['Gain'].sum():.2f} TND")
    col4.metric(t("Quantité totale"), int(filtered_df['Quantité'].sum()))

    # --- Par catégorie ---
    st.subheader(t("Dépenses par catégorie"))
    cat_totals = filtered_df.groupby("Catégorie")["Total achat"].sum().sort_values(ascending=False)
    st.bar_chart(cat_totals)

    st.subheader(t("Ventes par catégorie"))
    cat_sales = filtered_df.groupby("Catégorie")["Total vente"].sum().sort_values(ascending=False)
    st.bar_chart(cat_sales)

    st.subheader(t("Gains par catégorie"))
    cat_gains = filtered_df.groupby("Catégorie")["Gain"].sum().sort_values(ascending=False)
    st.bar_chart(cat_gains)

    # --- Par fournisseur ---
    st.subheader(t("Dépenses par fournisseur"))
    supp_totals = filtered_df.groupby("Fournisseur")["Total achat"].sum().sort_values(ascending=False)
    st.bar_chart(supp_totals)

    st.subheader(t("Ventes par fournisseur"))
    supp_sales = filtered_df.groupby("Fournisseur")["Total vente"].sum().sort_values(ascending=False)
    st.bar_chart(supp_sales)

    st.subheader(t("Gains par fournisseur"))
    supp_gains = filtered_df.groupby("Fournisseur")["Gain"].sum().sort_values(ascending=False)
    st.bar_chart(supp_gains)

# --- FERMETURE DB ---
conn.close()
