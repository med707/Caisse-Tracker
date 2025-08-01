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
query = "SELECT * FROM purchases ORDER BY date DESC"
df = pd.read_sql_query(query, conn)

if df.empty:
    st.warning(_("Aucune donnée trouvée"))
    st.stop()

# --- SÉCURISER LES NOMS DE COLONNES ---
# Vérifier ce que la BDD renvoie réellement
st.write("📌 Colonnes trouvées :", df.columns.tolist())

# On suppose qu'on a bien ces colonnes :
# id, product, category, subcategory, supplier, quantity, purchase_price, sale_price, date

# --- TRAITEMENT ---
df["date"] = pd.to_datetime(df["date"])
df["total_achat"] = df["purchase_price"] * df["quantity"]
df["total_vente"] = df["sale_price"] * df["quantity"]
df["gain"] = df["total_vente"] - df["total_achat"]

# --- FILTRAGE PAR DATE ---
st.subheader(_("Filtres"))
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input(_("Date début"), value=df["date"].min().date())
with col2:
    end_date = st.date_input(_("Date fin"), value=df["date"].max().date())

mask = (df["date"] >= pd.to_datetime(start_date)) & (df["date"] <= pd.to_datetime(end_date))
filtered_df = df.loc[mask]

if filtered_df.empty:
    st.info(_("Aucun produit trouvé pour cette plage de dates"))
else:
    st.subheader(_("Statistiques globales"))
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(_("Valeur totale achats"), f"{filtered_df['total_achat'].sum():.2f} TND")
    col2.metric(_("Valeur totale ventes"), f"{filtered_df['total_vente'].sum():.2f} TND")
    col3.metric(_("Gain total"), f"{filtered_df['gain'].sum():.2f} TND")
    col4.metric(_("Quantité totale"), int(filtered_df['quantity'].sum()))

    # --- PAR CATÉGORIE ---
    st.subheader(_("Dépenses par catégorie"))
    cat_totals = filtered_df.groupby("category")["total_achat"].sum().sort_values(ascending=False)
    st.bar_chart(cat_totals)

    st.subheader(_("Ventes par catégorie"))
    cat_sales = filtered_df.groupby("category")["total_vente"].sum().sort_values(ascending=False)
    st.bar_chart(cat_sales)

    st.subheader(_("Gains par catégorie"))
    cat_gains = filtered_df.groupby("category")["gain"].sum().sort_values(ascending=False)
    st.bar_chart(cat_gains)

    # --- PAR FOURNISSEUR ---
    st.subheader(_("Dépenses par fournisseur"))
    supp_totals = filtered_df.groupby("supplier")["total_achat"].sum().sort_values(ascending=False)
    st.bar_chart(supp_totals)

    st.subheader(_("Ventes par fournisseur"))
    supp_sales = filtered_df.groupby("supplier")["total_vente"].sum().sort_values(ascending=False)
    st.bar_chart(supp_sales)

    st.subheader(_("Gains par fournisseur"))
    supp_gains = filtered_df.groupby("supplier")["gain"].sum().sort_values(ascending=False)
    st.bar_chart(supp_gains)

# --- FERMETURE DB ---
conn.close()
