# pages/statistics.py
import streamlit as st
from sqlalchemy import create_engine, text
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date
from lang_utils import get_translation

# --- LANGUAGE ---
lang = st.sidebar.selectbox("🌍 Langue / اللغة", ["fr", "ar"], index=0)
t = lambda key: get_translation(key, lang)

st.set_page_config(page_title=t("Purchases & Statistics"), layout="wide", page_icon="📊")
st.title("📊 " + t("Purchases & Statistics"))

# --- DATABASE CONNECTION ---
DATABASE_URL = st.secrets["database"]["url"]
engine = create_engine(DATABASE_URL)

# --- LOAD PURCHASES ---
def load_purchases(start_date=None, end_date=None, search=None):
    query = """
        SELECT id, product, category, subcategory, supplier,
               quantity, purchase_price, sale_price, date
        FROM purchases
        WHERE 1=1
    """
    params = {}
    if start_date:
        query += " AND date >= :start_date"
        params["start_date"] = start_date
    if end_date:
        query += " AND date <= :end_date"
        params["end_date"] = end_date
    if search:
        query += " AND LOWER(product) LIKE :search"
        params["search"] = f"%{search.lower()}%"

    query += " ORDER BY date ASC"

    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        rows = result.fetchall()
        cols = result.keys()
        return pd.DataFrame(rows, columns=cols)

# --- FILTERS ---
col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    start_date = st.date_input(t("Start Date"), value=date(2025, 1, 1))
with col2:
    end_date = st.date_input(t("End Date"), value=date.today())
with col3:
    search = st.text_input(t("Search Product"))

# --- LOAD FILTERED DATA ---
df = load_purchases(start_date, end_date, search)

if df.empty:
    st.info(t("No purchases found for this selection."))
else:
    # --- CALCULATE TOTALS ---
    df["total_purchase"] = df["purchase_price"] * df["quantity"]
    df["total_sale"] = df["sale_price"] * df["quantity"]
    total_purchase_value = df["total_purchase"].sum()
    total_sale_value = df["total_sale"].sum()
    total_gain = total_sale_value - total_purchase_value
    margin_percent = (total_gain / total_purchase_value * 100) if total_purchase_value else 0

    # --- SUMMARY METRICS ---
    st.subheader(t("Summary"))
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(t("Total Purchase Value"), f"{total_purchase_value:.2f} TND")
    col2.metric(t("Total Sale Value"), f"{total_sale_value:.2f} TND")
    col3.metric(t("Total Gain"), f"{total_gain:.2f} TND")
    col4.metric(t("Margin %"), f"{margin_percent:.1f}%")

    # --- CHART: EVOLUTION OVER TIME ---
    daily_totals = df.groupby("date")[["total_purchase", "total_sale"]].sum().reset_index()
    st.subheader(t("Evolution Over Time"))
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(daily_totals["date"], daily_totals["total_purchase"], label=t("Purchase Value"), marker="o")
    ax.plot(daily_totals["date"], daily_totals["total_sale"], label=t("Sale Value"), marker="o")
    ax.set_xlabel(t("Date"))
    ax.set_ylabel("TND")
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.6)
    plt.xticks(rotation=45)
    st.pyplot(fig)

    # --- DETAILED TABLE ---
    st.subheader(t("Detailed Purchases"))
    st.dataframe(df, use_container_width=True)

