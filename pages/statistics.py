import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import sys
import os

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # for main dir

from lang_utils import get_translation

# --- LANGUAGE CONFIG ---
lang = st.sidebar.selectbox("🌍 Langue / اللغة", ["fr", "ar"], index=0)
_ = lambda key: get_translation(key, lang)

# --- PAGE CONFIG ---
st.set_page_config(
    page_title=_("statistics_page_title"),
    layout="centered",
    page_icon="📈"
)

st.title(_("statistics_page_title"))

# --- DATABASE CONNECTION ---
conn = sqlite3.connect("supermarket.db", check_same_thread=False)

# --- LOAD DATA ---
query = "SELECT * FROM purchases ORDER BY date DESC"
df = pd.read_sql_query(query, conn)

if df.empty:
    st.warning(_("no_data_found"))
    st.stop()

# --- DATA CLEANUP ---
df.columns = ["ID", "Produit", "Prix", "Quantité", "Date", "Catégorie", "Sous-catégorie", "Fournisseur"]
df["Total"] = df["Prix"] * df["Quantité"]
df["Date"] = pd.to_datetime(df["Date"])

# --- FILTERS ---
st.subheader(_("filters_title"))
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input(_("start_date_label"), value=datetime.today().replace(day=1))
with col2:
    end_date = st.date_input(_("end_date_label"), value=datetime.today())

mask = (df["Date"] >= pd.to_datetime(start_date)) & (df["Date"] <= pd.to_datetime(end_date))
filtered_df = df.loc[mask]

if filtered_df.empty:
    st.info(_("no_products_found"))
else:
    st.subheader(_("global_statistics"))
    col1, col2, col3 = st.columns(3)
    col1.metric(_("total_value"), f"{filtered_df['Total'].sum():.2f} TND")
    col2.metric(_("average_price"), f"{filtered_df['Prix'].mean():.2f} TND")
    col3.metric(_("total_quantity"), int(filtered_df['Quantité'].sum()))

    # --- BY CATEGORY ---
    st.subheader(_("category_expenses"))
    cat_totals = filtered_df.groupby("Catégorie")["Total"].sum().sort_values(ascending=False)
    st.bar_chart(cat_totals)

    # --- BY SUPPLIER ---
    st.subheader(_("supplier_expenses"))
    if "Fournisseur" in filtered_df.columns:
        supp_totals = filtered_df.groupby("Fournisseur")["Total"].sum().sort_values(ascending=False)
        st.bar_chart(supp_totals)

# --- CLOSE DB ---
conn.close()

