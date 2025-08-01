import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from lang_utils import get_translation

# --- LANGUE ---
lang = st.sidebar.selectbox("🌍 Langue / اللغة", ["fr", "ar"], index=0)
t = lambda key: get_translation(key, lang)

# --- Titre ---
st.title(t("Dépense mensuelle"))

# --- Connexion à la base de données ---
conn = sqlite3.connect("supermarket.db")
cursor = conn.cursor()

# --- Charger les données ---
df = pd.read_sql_query("SELECT * FROM purchases", conn)

if df.empty:
    st.info(t("Aucune donnée trouvée"))
else:
    # --- Renommer les colonnes selon la structure de achat_vente.py ---
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

    # Convertir la colonne date en datetime
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Mois"] = df["Date"].dt.to_period("M")

    # Calculs
    df["Total achat"] = df["Prix d'achat"] * df["Quantité"]
    df["Total vente"] = df["Prix de vente"] * df["Quantité"]
    df["Gain"] = df["Total vente"] - df["Total achat"]

    # --- Sélection du mois ---
    mois_disponibles = sorted(df["Mois"].unique().astype(str), reverse=True)
    mois_selectionne = st.selectbox(t("Choisir un mois"), mois_disponibles)

    df_mois = df[df["Mois"] == mois_selectionne]

    if df_mois.empty:
        st.info(t("Aucune donnée pour ce mois"))
    else:
        # --- Résumé global ---
        total_achat = df_mois["Total achat"].sum()
        total_vente = df_mois["Total vente"].sum()
        gain_total = df_mois["Gain"].sum()

        st.subheader(f"{t('Dépenses totales')} {mois_selectionne}")
        col1, col2, col3 = st.columns(3)
        col1.metric(t("Total achats"), f"{total_achat:.2f} TND")
        col2.metric(t("Total ventes"), f"{total_vente:.2f} TND")
        col3.metric(t("Gain"), f"{gain_total:.2f} TND")

        # --- Détails ---
        with st.expander(t("Détails des achats et ventes")):
            st.dataframe(df_mois[[
                "Date", "Produit", "Catégorie", "Sous-catégorie", "Fournisseur",
                "Quantité", "Prix d'achat", "Prix de vente", "Total achat", "Total vente", "Gain"
            ]])

        # --- Graphique par catégorie ---
        st.subheader(t("Dépenses par catégorie"))
        depense_par_categorie = df_mois.groupby("Catégorie")["Total achat"].sum().sort_values(ascending=False)
        st.bar_chart(depense_par_categorie)

        st.subheader(t("Ventes par catégorie"))
        vente_par_categorie = df_mois.groupby("Catégorie")["Total vente"].sum().sort_values(ascending=False)
        st.bar_chart(vente_par_categorie)

        st.subheader(t("Gains par catégorie"))
        gain_par_categorie = df_mois.groupby("Catégorie")["Gain"].sum().sort_values(ascending=False)
        st.bar_chart(gain_par_categorie)

        # --- Graphique par fournisseur ---
        st.subheader(t("Dépenses par fournisseur"))
        depense_par_fournisseur = df_mois.groupby("Fournisseur")["Total achat"].sum().sort_values(ascending=False)
        st.bar_chart(depense_par_fournisseur)

        st.subheader(t("Ventes par fournisseur"))
        vente_par_fournisseur = df_mois.groupby("Fournisseur")["Total vente"].sum().sort_values(ascending=False)
        st.bar_chart(vente_par_fournisseur)

        st.subheader(t("Gains par fournisseur"))
        gain_par_fournisseur = df_mois.groupby("Fournisseur")["Gain"].sum().sort_values(ascending=False)
        st.bar_chart(gain_par_fournisseur)

# --- Fermer la connexion ---
conn.close()
