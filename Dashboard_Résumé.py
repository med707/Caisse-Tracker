import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from lang_utils import get_translation

# --- LANGUE ---
lang = st.sidebar.selectbox("\U0001F30D Langue / اللغة", ["fr", "ar"], index=0)
_ = lambda key: get_translation(key, lang)

st.set_page_config(page_title="\U0001F4CA Tableau de Bord", layout="wide")
st.title("\U0001F4CA " + _("Tableau de Bord Global"))

# --- Connexion DB ---
conn = sqlite3.connect("supermarket.db")
df = pd.read_sql_query("SELECT * FROM purchases", conn)
conn.close()

if df.empty:
    st.warning(_("Aucune donnée à afficher."))
    st.stop()

# --- Préparation ---
df["Total"] = df["quantity"] * df["price"]
df["date"] = pd.to_datetime(df["date"])

# --- KPIs ---
st.subheader(_("Dépenses Globales"))
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(_("Nombre total d'articles"), len(df))
with col2:
    st.metric(_("Montant total dépensé"), f"{df['Total'].sum():.2f} TND")
with col3:
    st.metric(_("Nombre de fournisseurs"), df["supplier"].nunique())

# --- Dépenses par Catégorie ---
st.subheader(_("\U0001F4C8 Dépenses par Catégorie"))
cat_data = df.groupby("category")["Total"].sum().reset_index().sort_values(by="Total", ascending=False)
fig1 = px.pie(cat_data, names="category", values="Total", title=_("Répartition par catégorie"))
st.plotly_chart(fig1, use_container_width=True)

# --- Dépenses par Fournisseur ---
st.subheader(_("\U0001F4CB Top Fournisseurs"))
sup_data = df.groupby("supplier")["Total"].sum().reset_index().sort_values(by="Total", ascending=False).head(10)
fig2 = px.bar(sup_data, x="supplier", y="Total", title=_("Top 10 Fournisseurs"), text_auto=True)
st.plotly_chart(fig2, use_container_width=True)

# --- Dépenses par Mois ---
st.subheader(_("\U0001F4C5 Évolution Mensuelle"))
df["Mois"] = df["date"].dt.to_period("M").astype(str)
monthly_data = df.groupby("Mois")["Total"].sum().reset_index()
fig3 = px.line(monthly_data, x="Mois", y="Total", markers=True, title=_("Dépenses par mois"))
st.plotly_chart(fig3, use_container_width=True)

# --- Navigation ---
st.page_link("inev.py", label=_("⬅️ Retour à l'accueil"))

