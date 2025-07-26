import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy as np
import sys
import os

# Add parent directory to path for lang_utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lang_utils import get_translation

# --- LANGUE ---
lang = st.sidebar.selectbox("🌍 Langue / اللغة", ["fr", "ar"], index=0)
_ = lambda key: get_translation(key, lang)

# --- DB CONNECTION ---
conn = sqlite3.connect("supermarket.db", check_same_thread=False)
cursor = conn.cursor()

# --- PAGE CONFIG ---
st.set_page_config(
    page_title=_("comparaison_hebdomadaire"),
    layout="wide",
    page_icon="📊"
)

# --- RETURN BUTTON ---
if st.sidebar.button(_("Retour")):
    st.switch_page("inev")

# --- TITLE ---
st.title(_("Comparaison Hebdomadaire"))

# --- WEEKDAY SELECTION ---
jours_semaine = {
    "fr": ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"],
    "ar": ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
}
day_of_week = st.selectbox(_("Choisir le jour de la semaine"), jours_semaine[lang])

# --- FUNCTION TO GET DATES FOR SELECTED WEEKDAY ---
def get_dates_for_day(day_name, weeks=4):
    DAY_MAPPING_FR = {"Lundi": 0, "Mardi": 1, "Mercredi": 2, "Jeudi": 3, "Vendredi": 4, "Samedi": 5, "Dimanche": 6}
    DAY_MAPPING_AR = {"الاثنين": 0, "الثلاثاء": 1, "الأربعاء": 2, "الخميس": 3, "الجمعة": 4, "السبت": 5, "الأحد": 6}

    day_num = DAY_MAPPING_FR[day_name] if lang == "fr" else DAY_MAPPING_AR[day_name]

    today = datetime.today()
    dates = []
    days_since = (today.weekday() - day_num) % 7
    current_day = today if days_since == 0 else today - timedelta(days=days_since)

    for i in range(weeks):
        date = current_day - timedelta(weeks=i)
        dates.append(date.date())
    return dates

dates = get_dates_for_day(day_of_week, weeks=4)
date_strs = [d.strftime("%Y-%m-%d") for d in dates]

if len(date_strs) == 0:
    st.warning(_("Aucune date sélectionnée."))
else:
    placeholders = ",".join("?" for _ in date_strs)
    query = f"""
        SELECT date, product, depot, movement_type, 
               SUM(quantity * price) as total_value
        FROM inventory_movements
        WHERE date IN ({placeholders})
        GROUP BY date, product, depot, movement_type
        ORDER BY date DESC
    """
    cursor.execute(query, date_strs)
    data = cursor.fetchall()

    if data:
        df = pd.DataFrame(data, columns=["Date", _("Produit"), _("Dépôt"), _("Type Mouvement"), _("Valeur Totale")])

        # Pivot table: Show total value by product and depot per date
        pivot_df = df.pivot_table(
            index=[_("Produit"), _("Dépôt"), _("Type Mouvement")],
            columns="Date",
            values=_("Valeur Totale"),
            fill_value=0
        ).reset_index()

        # Sort dates descending for display
        date_columns = sorted([col for col in pivot_df.columns if col not in [_("Produit"), _("Dépôt"), _("Type Mouvement")]], reverse=True)
        pivot_df = pivot_df[[_("Produit"), _("Dépôt"), _("Type Mouvement")] + date_columns]

        # Calculate week-over-week difference & percent variation if at least two weeks available
        if len(date_columns) >= 2:
            latest_date = date_columns[0]
            prev_date = date_columns[1]

            pivot_df[_("Différence 7j")] = pivot_df[latest_date] - pivot_df[prev_date]
            pivot_df[_("Variation %")] = (pivot_df[_("Différence 7j")] / pivot_df[prev_date].replace(0, np.nan)) * 100
            pivot_df[_("Variation %")] = pivot_df[_("Variation %")].replace([np.inf, -np.inf], 0).fillna(0)

            # Format columns
            pivot_df[_("Différence 7j")] = pivot_df[_("Différence 7j")].apply(lambda x: f"{x:+.2f}" if x != 0 else "0.00")
            pivot_df[_("Variation %")] = pivot_df[_("Variation %")].apply(lambda x: f"{x:+.1f}%" if not pd.isna(x) else "N/A")

        # Show dataframe
        st.subheader(_("Détail des valeurs par produit, dépôt et type de mouvement"))
        st.dataframe(pivot_df, height=600)

        # Totaux par date (tous produits, dépôts, types confondus)
        totals_per_date = df.groupby("Date")[_("Valeur Totale")].sum().reset_index().sort_values("Date", ascending=True)

        st.subheader(_("Totaux globaux par date"))
        total_cols = st.columns(len(date_strs))
        total_values = []
        for i, date in enumerate(dates):
            date_str = date.strftime("%Y-%m-%d")
            total = totals_per_date[totals_per_date["Date"] == date_str][_('Valeur Totale')].sum()
            total_values.append(total)
            total_cols[i].metric(
                f"{_('total')} {date.strftime('%d %b')}",
                f"{total:.2f} TND"
            )

        # Show evolution for last 2 weeks
        if len(total_values) >= 2:
            diff = total_values[0] - total_values[1]
            percent_diff = (diff / total_values[1]) * 100 if total_values[1] != 0 else 0
            delta_color = "normal"
            if diff > 0:
                delta_color = "inverse"
            elif diff < 0:
                delta_color = "normal"

            total_cols[-1].metric(
                _("Évolution Hebdomadaire"),
                f"{diff:+.2f} TND",
                f"{percent_diff:+.1f}%",
                delta_color=delta_color
            )

        # Plot global totals trend
        st.subheader(_("Visualisation des tendances"))
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot([d.strftime("%d %b") for d in dates[::-1]], total_values[::-1],
                marker='o', linestyle='-', color='#3498db', linewidth=2)
        ax.set_title(f"{_('Évolution des valeurs totales')} - {day_of_week}")
        ax.set_xlabel(_('Date'))
        ax.set_ylabel(_('Valeur Totale (TND)'))
        ax.grid(True, linestyle='--', alpha=0.7)
        plt.xticks(rotation=45)
        st.pyplot(fig)

    else:
        st.warning(f"{_('Aucune donnée disponible pour')} {day_of_week}s.")

# --- CLOSE DB ---
conn.close()
