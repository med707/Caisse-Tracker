import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import sys
import os

# Import des traductions
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lang_utils import get_translation

# --- LANGUE ---
lang = st.sidebar.selectbox("🌍 Langue / اللغة", ["fr", "ar"], index=0)
_ = lambda key: get_translation(key, lang)

# --- CONFIG PAGE ---
st.set_page_config(
    page_title=_("comparaison_hebdomadaire"),
    layout="wide",
    page_icon="📊"
)

# --- Connexion mkdb PostgreSQL ---
try:
    DATABASE_URL = st.secrets["database"]["url"]
    engine = create_engine(DATABASE_URL)
except SQLAlchemyError as e:
    st.error(f"❌ Erreur de connexion à la base : {e}")
    st.stop()

# --- TITRE ---
st.title(_("Comparaison Hebdomadaire des Achats"))

# --- JOURS DE LA SEMAINE ---
jours_semaine = {
    "fr": ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"],
    "ar": ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
}
day_of_week = st.selectbox(_("Choisir le jour de la semaine"), jours_semaine[lang])

# --- OBTENIR DATES ---
def get_dates_for_day(day_name, weeks=4):
    day_mapping_fr = {"Lundi": 0, "Mardi": 1, "Mercredi": 2, "Jeudi": 3, "Vendredi": 4, "Samedi": 5, "Dimanche": 6}
    day_mapping_ar = {"الاثنين": 0, "الثلاثاء": 1, "الأربعاء": 2, "الخميس": 3, "الجمعة": 4, "السبت": 5, "الأحد": 6}
    day_num = day_mapping_fr[day_name] if lang == "fr" else day_mapping_ar[day_name]

    today = datetime.today()
    days_since = (today.weekday() - day_num) % 7
    current_day = today if days_since == 0 else today - timedelta(days=days_since)

    return [(current_day - timedelta(weeks=i)).date() for i in range(weeks)]

dates = get_dates_for_day(day_of_week, weeks=4)
date_strs = [d.strftime("%Y-%m-%d") for d in dates]

if date_strs:
    placeholders = ", ".join([f":date{i}" for i in range(len(date_strs))])
    params = {f"date{i}": date_strs[i] for i in range(len(date_strs))}

    query = f"""
        SELECT date, product, category, supplier,
               SUM(quantity * purchase_price) AS total_achat,
               SUM(quantity * sale_price) AS total_vente
        FROM purchases
        WHERE date IN ({placeholders})
        GROUP BY date, product, category, supplier
        ORDER BY date DESC
    """

    try:
        with engine.connect() as conn:
            data = conn.execute(text(query), params).fetchall()
    except SQLAlchemyError as e:
        st.error(f"Erreur lors de la récupération des données: {e}")
        st.stop()

    if data:
        df = pd.DataFrame(data, columns=["Date", _("Produit"), _("Catégorie"), _("Fournisseur"), _("Total Achat"), _("Total Vente")])

        # Pivot table
        pivot_df = df.pivot_table(
            index=[_("Produit"), _("Catégorie"), _("Fournisseur")],
            columns="Date",
            values=_("Total Achat"),
            fill_value=0
        ).reset_index()

        # Sort date columns descending
        date_columns = sorted([c for c in pivot_df.columns if c not in [_("Produit"), _("Catégorie"), _("Fournisseur")]], reverse=True)
        pivot_df = pivot_df[[_("Produit"), _("Catégorie"), _("Fournisseur")] + date_columns]

        # Calculate difference and percentage variation
        if len(date_columns) >= 2:
            latest_date, prev_date = date_columns[0], date_columns[1]
            pivot_df[_("Différence 7j")] = pivot_df[latest_date] - pivot_df[prev_date]
            pivot_df[_("Variation %")] = (pivot_df[_("Différence 7j")] / pivot_df[prev_date].replace(0, np.nan)) * 100
            pivot_df[_("Variation %")] = pivot_df[_("Variation %")].replace([np.inf, -np.inf], 0).fillna(0)

            pivot_df[_("Différence 7j")] = pivot_df[_("Différence 7j")].apply(lambda x: f"{x:+.2f}" if x != 0 else "0.00")
            pivot_df[_("Variation %")] = pivot_df[_("Variation %")].apply(lambda x: f"{x:+.1f}%" if not pd.isna(x) else "N/A")

        st.subheader(_("Détail par produit, catégorie et fournisseur"))
        st.dataframe(pivot_df, height=600)

        # Totaux par date
        totals_per_date = df.groupby("Date")[_("Total Achat")].sum().reset_index().sort_values("Date", ascending=True)
        total_values = totals_per_date[_("Total Achat")].tolist()

        st.subheader(_("Totaux globaux par date"))
        cols = st.columns(len(dates))
        for i, date in enumerate(dates):
            cols[i].metric(f"{date.strftime('%d %b')}", f"{total_values[i]:.2f} TND")

        # Graphique
        st.subheader(_("Évolution des dépenses"))
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot([d.strftime("%d %b") for d in dates[::-1]], total_values[::-1],
                marker='o', linestyle='-', color='#3498db', linewidth=2)
        ax.set_title(f"{_('Évolution des dépenses')} - {day_of_week}")
        ax.set_xlabel(_('Date'))
        ax.set_ylabel(_('Total (TND)'))
        ax.grid(True, linestyle='--', alpha=0.7)
        plt.xticks(rotation=45)
        st.pyplot(fig)

    else:
        st.warning(f"{_('Aucune donnée disponible pour')} {day_of_week}.")
else:
    st.warning(_("Aucune date sélectionnée."))
