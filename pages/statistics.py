import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from lang_utils import get_translation

# --- LANGUE ---
lang = st.sidebar.selectbox("🌍 Langue / اللغة", ["fr", "ar"], index=0)
_ = lambda key: get_translation(key, lang)

# --- CONFIG PAGE ---
st.set_page_config(
    page_title=_("Statistiques"),
    layout="centered",
    page_icon="📈"
)

st.title(_("Statistiques des achats/ventes"))

# --- CONNEXION DB ---
conn = sqlite3.connect("supermarket.db", check_same_thread=False)

# --- CHARGEMENT DONNÉES ---
df = pd.read_sql_query("SELECT * FROM purchases ORDER BY date DESC", conn)

if df.empty:
    st.warning(_("Aucune donnée trouvée"))
    st.stop()

# --- NOMMER LES COLONNES CORRECTEMENT ---
df.columns = [
    "ID",
    "Produit",
    "Catégorie",
    "Sous-catégorie",
    "Fournisseur",
    "Quantité",
    "Prix d'achat",
    "Prix de vente",
    "Date"
]

# Convertir Date en datetime
df["Date"] = pd.to_datetime(df["Date"])

# --- CALCULS ---
df["Total achat"] = df["Prix d'achat"] * df["Quantité"]
df["Total vente"] = df["Prix de vente"] * df["Quantité"]
df["Gain"] = df["Total vente"] - df["Total achat"]

# --- FILTRAGE PAR DATE ---
st.subheader(_("Filtres"))
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input(_("Date début"), value=df["Date"].min().date())
with col2:
    end_date = st.date_input(_("Date fin"), value=df["Date"].max().date())

mask = (df["Date"] >= pd.to_datetime(start_date)) & (df["Date"] <= pd.to_datetime(end_date))
filtered_df = df.loc[mask]

if filtered_df.empty:
    st.info(_("Aucun produit trouvé pour cette plage de dates"))
else:
    # --- METRICS GLOBALES ---
    st.subheader(_("Statistiques globales"))
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(_("Valeur totale achats"), f"{filtered_df['Total achat'].sum():.2f} TND")
    col2.metric(_("Valeur totale ventes"), f"{filtered_df['Total vente'].sum():.2f} TND")
    col3.metric(_("Gain total"), f"{filtered_df['Gain'].sum():.2f} TND")
    col4.metric(_("Quantité totale"), int(filtered_df['Quantité'].sum()))

    # --- PAR CATÉGORIE ---
    st.subheader(_("Dépenses par catégorie"))
    st.bar_chart(filtered_df.groupby("Catégorie")["Total achat"].sum().sort_values(ascending=False))

    st.subheader(_("Ventes par catégorie"))
    st.bar_chart(filtered_df.groupby("Catégorie")["Total vente"].sum().sort_values(ascending=False))

    st.subheader(_("Gains par catégorie"))
    st.bar_chart(filtered_df.groupby("Catégorie")["Gain"].sum().sort_values(ascending=False))

    # --- PAR FOURNISSEUR ---
    st.subheader(_("Dépenses par fournisseur"))
    st.bar_chart(filtered_df.groupby("Fournisseur")["Total achat"].sum().sort_values(ascending=False))

    st.subheader(_("Ventes par fournisseur"))
    st.bar_chart(filtered_df.groupby("Fournisseur")["Total vente"].sum().sort_values(ascending=False))

    st.subheader(_("Gains par fournisseur"))
    st.bar_chart(filtered_df.groupby("Fournisseur")["Gain"].sum().sort_values(ascending=False))

# --- FERMETURE ---
conn.close()
