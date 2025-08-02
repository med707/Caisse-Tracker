# pages/depense_mensuel.py
import streamlit as st
from sqlalchemy import create_engine, text
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import calendar
from lang_utils import get_translation

# --- LANGUAGE ---
lang = st.sidebar.selectbox("🌍 Langue / اللغة", ["fr", "ar"], index=0)
t = lambda key: get_translation(key, lang)

st.set_page_config(page_title=t("Monthly Expenses"), layout="wide", page_icon="📅")
st.title("📅 " + t("Monthly Expenses"))

# --- DATABASE CONNECTION ---
DATABASE_URL = st.secrets["database"]["url"]
engine = create_engine(DATABASE_URL)

# --- SELECT YEAR & MONTH ---
today = datetime.today()
years = list(range(today.year - 5, today.year + 1))
year = st.selectbox(t("Year"), years, index=years.index(today.year))
month_names = list(calendar.month_name)[1:]  # Jan -> Dec
month_name = st.selectbox(t("Month"), month_names, index=today.month - 1)

# Convert month name to month number
month_num = month_names.index(month_name) + 1

# --- CALCULATE START & END DATE ---
start_date = datetime(year, month_num, 1)
_, last_day = calendar.monthrange(year, month_num)
end_date = datetime(year, month_num, last_day)

# --- FETCH DATA FROM DATABASE ---
query = """
    SELECT date, SUM(purchase_price * quantity) AS total
    FROM purchases
    WHERE date BETWEEN :start AND :end
    GROUP BY date
    ORDER BY date ASC
"""
with engine.connect() as conn:
    result = conn.execute(text(query), {"start": start_date, "end": end_date}).fetchall()

if not result:
    st.info(t("No data for this month."))
else:
    # --- CONVERT TO DATAFRAME ---
    df = pd.DataFrame(result, columns=["Date", "Total"])
    df["Date"] = pd.to_datetime(df["Date"])

    # Ensure all days are present in DataFrame
    all_days = pd.date_range(start=start_date, end=end_date)
    df = df.set_index("Date").reindex(all_days, fill_value=0).rename_axis("Date").reset_index()

    # --- DISPLAY TABLE ---
    st.subheader(t("Daily Expenses"))
    st.dataframe(df.style.format({"Total": "{:.2f} TND"}), height=400, use_container_width=True)

    # --- PLOT GRAPH ---
    st.subheader(t("Daily Expenses Chart"))
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(df["Date"], df["Total"], marker="o", linestyle="-", color="#3498db")
    ax.set_title(f"{t('Daily expenses for')} {month_name} {year}")
    ax.set_xlabel(t("Date"))
    ax.set_ylabel("TND")
    ax.grid(True, linestyle="--", alpha=0.7)
    plt.xticks(rotation=45)
    st.pyplot(fig)

    # --- SHOW TOTAL ---
    total_expense = df["Total"].sum()
    st.metric(t("Total Monthly Expenses"), f"{total_expense:.2f} TND")
