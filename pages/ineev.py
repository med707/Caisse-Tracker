import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy as np
import sys
import os

# Add parent directory to Python path for lang_utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lang_utils import get_translation

# --- CONFIGURATION LANGUE ---
lang = st.sidebar.selectbox("🌍 Langue / اللغة", ["fr", "ar"], index=0)
_ = lambda key: get_translation(key, lang)

# Connexion base de données
conn = sqlite3.connect("supermarket.db", check_same_thread=False)
cursor = conn.cursor()

# Config page
st.set_page_config(
    page_title=_("comparaison_hebdomadaire"),
    layout="wide",
    page_icon="📊"
)

# Bouton retour vers page principale
if st.sidebar.button(_("Retour")):
    st.switch_page("inev")

# Titre
st.title(_("Comparaison Hebdomadaire"))

# Sélecteur jour de la semaine
jours_semaine = {
    "fr": ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"],
    "ar": ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
}
day_of_week = st.selectbox(_("Choisir le jour de la semaine"), jours_semaine[lang])

# Fonction récupération des dates pour le jour sélectionné
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
    placeholders = ','.join('?' for _ in date_strs)
    query = f"""
        SELECT date, category, subcategory, 
               SUM((sale_price - purchase_price) * quantity) as total_gain
        FROM inventory_movements
        WHERE date IN ({placeholders})
        GROUP BY date, category, subcategory
        ORDER BY date DESC
    """
    cursor.execute(query, date_strs)
    data = cursor.fetchall()

    if data:
        df = pd.DataFrame(data, columns=["Date", _("categorie"), _("sous_categorie"), "Total Gain"])

        pivot_df = df.pivot_table(
            index=[_("categorie"), _("sous_categorie")],
            columns="Date",
            values="Total Gain",
            fill_value=0
        ).reset_index()

        # Sort date columns descending
        date_columns = sorted([col for col in pivot_df.columns if col not in [_("categorie"), _("sous_categorie")]], reverse=True)
        pivot_df = pivot_df[[_("categorie"), _("sous_categorie")] + date_columns]

        if len(date_columns) >= 2:
            latest_date = date_columns[0]
            prev_date = date_columns[1]

            if latest_date in pivot_df.columns and prev_date in pivot_df.columns:
                pivot_df[_("difference_7j")] = pivot_df[latest_date] - pivot_df[prev_date]
                pivot_df[_("pourcentage_variation")] = (pivot_df[_("difference_7j")] / pivot_df[prev_date].replace(0, np.nan)) * 100
                pivot_df[_("pourcentage_variation")] = pivot_df[_("pourcentage_variation")].replace([np.inf, -np.inf], 0).fillna(0)

                pivot_df[_("difference_7j")] = pivot_df[_("difference_7j")].apply(lambda x: f"{x:+.2f}" if x != 0 else "0.00")
                pivot_df[_("pourcentage_variation")] = pivot_df[_("pourcentage_variation")].apply(lambda x: f"{x:+.1f}%" if not pd.isna(x) else "N/A")

        # Totaux par catégorie
        category_totals = df.groupby([_("categorie"), "Date"])["Total Gain"].sum().reset_index()
        category_pivot = category_totals.pivot_table(
            index=_("categorie"),
            columns="Date",
            values="Total Gain",
            fill_value=0
        ).reset_index()

        category_date_columns = sorted([col for col in category_pivot.columns if col != _("categorie")], reverse=True)
        category_pivot = category_pivot[[_("categorie")] + category_date_columns]

        if len(category_date_columns) >= 2:
            latest_date = category_date_columns[0]
            prev_date = category_date_columns[1]
            if latest_date in category_pivot.columns and prev_date in category_pivot.columns:
                category_pivot[_("difference_7j")] = category_pivot[latest_date] - category_pivot[prev_date]
                category_pivot[_("pourcentage_variation")] = (category_pivot[_("difference_7j")] / category_pivot[prev_date].replace(0, np.nan)) * 100
                category_pivot[_("pourcentage_variation")] = category_pivot[_("pourcentage_variation")].replace([np.inf, -np.inf], 0).fillna(0)

                category_pivot[_("difference_7j")] = category_pivot[_("difference_7j")].apply(lambda x: f"{x:+.2f}" if x != 0 else "0.00")
                category_pivot[_("pourcentage_variation")] = category_pivot[_("pourcentage_variation")].apply(lambda x: f"{x:+.1f}%" if not pd.isna(x) else "N/A")

        # Totaux globaux par date
        date_totals = df.groupby("Date")["Total Gain"].sum().reset_index().sort_values("Date", ascending=True)

        st.subheader(_("totaux_globaux"))
        total_cols = st.columns(len(date_strs))

        total_values = []
        for i, date in enumerate(dates):
            date_str = date.strftime("%Y-%m-%d")
            total = date_totals[date_totals["Date"] == date_str]["Total Gain"].sum()
            total_values.append(total)
            total_cols[i].metric(
                f"{_('total')} {date.strftime('%d %b')}",
                f"{total:.2f} TND"
            )

        if len(total_values) >= 2:
            diff = total_values[0] - total_values[1]
            percent_diff = (diff / total_values[1]) * 100 if total_values[1] != 0 else 0
            delta_color = "normal"
            if diff > 0:
                delta_color = "inverse"
            elif diff < 0:
                delta_color = "normal"

            total_cols[-1].metric(
                _("evolution_hebdomadaire"),
                f"{diff:+.2f} TND",
                f"{percent_diff:+.1f}%",
                delta_color=delta_color
            )

        # Affichage tableau totaux par catégorie
        st.subheader(_("totaux_par_categorie"))
        st.dataframe(category_pivot, height=400)

        # Affichage détail sous-catégorie
        st.subheader(_("detail_par_sous_categorie"))
        st.dataframe(pivot_df, height=600)

        # Graphique tendance évolution totaux globaux
        st.subheader(_("visualisation_tendances"))
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot([d.strftime("%d %b") for d in dates[::-1]], total_values[::-1],
                marker='o', linestyle='-', color='#3498db', linewidth=2)
        ax.set_title(f"{_('evolution_depenses')} {day_of_week}")
        ax.set_xlabel(_('date'))
        ax.set_ylabel(_('total_tnd'))
        ax.grid(True, linestyle='--', alpha=0.7)
        plt.xticks(rotation=45)
        st.pyplot(fig)

        # Graphique dépenses par catégorie
        if not category_totals.empty:
            st.subheader(_("depenses_par_categorie") + f" {day_of_week}")
            fig, ax = plt.subplots(figsize=(12, 7))
            stacked_df = category_totals.pivot(index=_("categorie"), columns="Date", values="Total Gain").fillna(0)
            stacked_df = stacked_df.sort_values(by=dates[0].strftime("%Y-%m-%d"), ascending=False)
            stacked_df.plot(kind='bar', stacked=False, ax=ax, width=0.8)
            ax.set_ylabel(_('total_tnd'))
            ax.set_xlabel(_("categorie"))
            plt.xticks(rotation=45, ha='right')
            ax.legend(title=_("date"), labels=[d.strftime("%d %b") for d in dates])
            ax.grid(axis='y', linestyle='--', alpha=0.7)
            st.pyplot(fig)

        # Top sous-catégories évolution
        st.subheader(_("top_evolution_sous_categories"))

        if len(date_columns) >= 2 and not pivot_df.empty:
            pivot_df["abs_change"] = pivot_df[latest_date] - pivot_df[prev_date]
            top_increases = pivot_df.nlargest(5, "abs_change")
            top_increases = top_increases[[_("categorie"), _("sous_categorie"), latest_date, prev_date, "abs_change"]]
            top_increases["evolution"] = top_increases["abs_change"].apply(lambda x: f"+{x:.2f}" if x > 0 else f"{x:.2f}")

            top_decreases = pivot_df.nsmallest(5, "abs_change")
            top_decreases = top_decreases[[_("categorie"), _("sous_categorie"), latest_date, prev_date, "abs_change"]]
            top_decreases["evolution"] = top_decreases["abs_change"].apply(lambda x: f"{x:.2f}")

            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"<h4>📈 {_('meilleures_progressions')}</h4>", unsafe_allow_html=True)
                if not top_increases.empty:
                    for _, row in top_increases.iterrows():
                        st.markdown(
                            f"<div style='background-color:#f0f9f0; padding:10px; border-radius:5px; margin-bottom:10px;'>"
                            f"<b>{row[_('sous_categorie')]}</b> ({row[_('categorie')]})<br>"
                            f"{prev_date}: <b>{row[prev_date]:.2f} TND</b> → "
                            f"{latest_date}: <b>{row[latest_date]:.2f} TND</b><br>"
                            f"<span style='color:green;'>+{row['abs_change']:.2f} TND</span>"
                            f"</div>",
                            unsafe_allow_html=True
                        )
                else:
                    st.info(_("pas_progression"))

            with col2:
                st.markdown(f"<h4>📉 {_('plus_fortes_baisses')}</h4>", unsafe_allow_html=True)
                if not top_decreases.empty:
                    for _, row in top_decreases.iterrows():
                        st.markdown(
                            f"<div style='background-color:#fef0f0; padding:10px; border-radius:5px; margin-bottom:10px;'>"
                            f"<b>{row[_('sous_categorie')]}</b> ({row[_('categorie')]})<br>"
                            f"{prev_date}: <b>{row[prev_date]:.2f} TND</b> → "
                            f"{latest_date}: <b>{row[latest_date]:.2f} TND</b><br>"
                            f"<span style='color:red;'>{row['abs_change']:.2f} TND</span>"
                            f"</div>",
                            unsafe_allow_html=True
                        )
                else:
                    st.info(_("pas_baisse"))
    else:
        st.warning(f"{_('aucune_donnee')} {day_of_week}s")

# Fermeture connexion
conn.close()
