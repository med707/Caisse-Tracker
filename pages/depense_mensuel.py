import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from lang_utils import get_translation

# --- LANGUE ---
lang = st.sidebar.selectbox("🌍 Langue / اللغة", ["fr", "ar"], index=0)
t = lambda key: get_translation(key, lang)

st.title(t("Dépenses mensuelles"))

# --- Connexion à la base de données ---
conn = sqlite3.connect("supermarket.db")
cursor = conn.cursor()

# --- Charger les données ---
df = pd.read_sql_query("SELECT * FROM purchases", conn)

if df.empty:
    st.info(t("aucune_donnee"))
else:
    # Vérifier colonnes
    # st.write(df.columns.tolist())  # Debug si besoin

    # Convertir la colonne date
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M")

    # Ajouter colonne total achat (pas price mais purchase_price)
    if "purchase_price" in df.columns:
        df["total"] = df["quantity"] * df["purchase_price"]
    elif "price" in df.columns:  # fallback si ancienne base
        df["total"] = df["quantity"] * df["price"]
    else:
        st.error("⚠ Impossible de calculer les dépenses : colonne prix introuvable.")
        st.stop()

    # Sélection du mois
    mois_disponibles = sorted(df["month"].unique().astype(str), reverse=True)
    mois_selectionne = st.selectbox(t("choisir_mois"), mois_disponibles)

    df_mois = df[df["month"] == mois_selectionne]

    if df_mois.empty:
        st.info(t("aucune_donnee_mois"))
    else:
        total_mensuel = df_mois["total"].sum()
        st.subheader(f"{t('depenses_totales')} {mois_selectionne} : {total_mensuel:.2f} TND")

        with st.expander(t("details")):
            st.dataframe(
                df_mois[["date", "product", "category", "subcategory", "supplier", "quantity", "purchase_price", "total"]],
                use_container_width=True
            )

        # Dépenses par catégorie
        st.subheader(t("depense_par_categorie"))
        depense_par_categorie = df_mois.groupby("category")["total"].sum().sort_values(ascending=False)
        st.bar_chart(depense_par_categorie)

        # Dépenses par fournisseur
        st.subheader(t("depense_par_fournisseur"))
        depense_par_fournisseur = df_mois.groupby("supplier")["total"].sum().sort_values(ascending=False)
        st.bar_chart(depense_par_fournisseur)

conn.close()
