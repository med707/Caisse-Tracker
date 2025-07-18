import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import calendar
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lang_utils import get_translation

# --- CONFIGURATION LANGUE ---
lang = st.sidebar.selectbox("🌍 Langue / اللغة", ["fr", "ar"], index=0)
_ = lambda key: get_translation(key, lang)

st.set_page_config(
    page_title=_("depense_mensuel"),
    layout="wide",
    page_icon="📅"
)

# Connect DB
conn = sqlite3.connect("supermarket.db", check_same_thread=False)
cursor = conn.cursor()

# Sidebar return button
if st.sidebar.button(_("Retour")):
    st.switch_page("inev")

st.title(_("Dépenses tout le long du mois"))

# Select year and month
today = datetime.today()
years = list(range(today.year - 5, today.year + 1))
year = st.selectbox(_("Année"), years, index=years.index(today.year))
month = st.selectbox(_("Mois"), list(calendar.month_name)[1:], index=today.month - 1)

# Compute start and end dates
start_date = datetime(year, month.index(month) + 1 if isinstance(month, str) else month, 1)
_, last_day = calendar.monthrange(year, month.index(month) + 1 if isinstance(month, str) else month)
end_date = datetime(year, month.index(month) + 1 if isinstance(month, str) else month, last_day)

start_str = start_date.strftime("%Y-%m-%d")
end_str = end_date.strftime("%Y-%m-%d")

query = """
    SELECT date, SUM(price * quantity) as total
    FROM purchases
    WHERE date BETWEEN ? AND ?
    GROUP BY date
    ORDER BY date
"""
cursor.execute(query, (start_str, end_str))
data = cursor.fetchall()

if data:
    df = pd.DataFrame(data, columns=["Date", "Total"])
    df["Date"] = pd.to_datetime(df["Date"])
    
    # Ensure all days present
    all_days = pd.date_range(start=start_date, end=end_date)
    df = df.set_index("Date").reindex(all_days, fill_value=0).rename_axis("Date").reset_index()

    # Show table
    st.subheader(_("Dépenses journalières"))
    st.dataframe(df.style.format({"Total": "{:.2f} TND"}), height=400)

    # Plot
    st.subheader(_("Graphique des dépenses journalières"))
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(df["Date"], df["Total"], marker='o', linestyle='-')
    ax.set_title(f"{_('Dépenses journalières pour')} {month} {year}")
    ax.set_xlabel(_("Date"))
    ax.set_ylabel(_("Total (TND)"))
    ax.grid(True, linestyle='--', alpha=0.7)
    plt.xticks(rotation=45)
    st.pyplot(fig)
else:
    st.info(_("aucune_donnee_mois"))

conn.close()

