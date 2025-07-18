import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from lang_utils import get_translation

# --- Langue ---
lang = st.sidebar.selectbox("🌍 Langue / اللغة", ["fr", "ar"], index=0)
t = lambda key: get_translation(key, lang)  # safer than using _

# --- Titre ---
st.title(t("depense_mensuel"))

# --- Connexion à la base de données ---
conn = sqlite3.connect("supermarket.db")
cursor = conn.cursor()

# --- Charger les données ---
df = pd.read_sql_query("SELECT * FROM purchases", conn)

if df.empty:
    st.info(t("aucune_donnee"))
else:
    # Convertir la colonne date en datetime
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M")

    mois_disponibles = sorted(df["month"].unique().astype(str), reverse=True)
    mois_selectionne = st.selectbox(t("choisir_mois"), mois_disponibles)

    df_mois = df[df["month"] == mois_selectionne]

    if df_mois.empty:
        st.info(t("aucune_donnee_mois"))
    else:
        df_mois["total"] = df_mois["quantity"] * df_mois["price"]
        total_mensuel = df_mois["total"].sum()

        st.subheader(f"{t('depenses_totales')} {mois_selectionne} : {total_mensuel:.2f} TND")

        with st.expander(t("details")):
            st.dataframe(df_mois[["date", "product", "category", "subcategory", "supplier", "quantity", "price", "total"]])

        # Graphique par catégorie
        st.subheader(t("depense_par_categorie"))
        depense_par_categorie = df_mois.groupby("category")["total"].sum().sort_values(ascending=False)

        st.bar_chart(depense_par_categorie)

        # Graphique par fournisseur
        st.subheader(t("depense_par_fournisseur"))
        depense_par_fournisseur = df_mois.groupby("supplier")["total"].sum().sort_values(ascending=False)
        st.bar_chart(depense_par_fournisseur)

conn.close()
