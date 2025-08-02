import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import os, sys

# --- Import traductions ---
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lang_utils import get_translation

# --- Connexion DB ---
try:
    DATABASE_URL = st.secrets["database"]["url"]
    engine = create_engine(DATABASE_URL)
except SQLAlchemyError as e:
    st.error(f"❌ {get_translation('Erreur de connexion à la base', 'fr')}: {e}")
    st.stop()

# --- Créer table si besoin ---
def init_db():
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS inventory_movements (
                id SERIAL PRIMARY KEY,
                product TEXT,
                depot TEXT,
                movement_type TEXT,  -- 'entry' ou 'exit'
                quantity INTEGER,
                price NUMERIC,
                date DATE
            )
        """))

init_db()

# --- Langue ---
lang = st.sidebar.selectbox("🌍 Langue / اللغة", ["fr", "ar"], index=0)
_ = lambda key: get_translation(key, lang)

st.set_page_config(page_title=_("Mouvements d'inventaire"), layout="wide")
st.title(_("Mouvements d'inventaire"))

# --- Formulaire ajout mouvement ---
with st.form("movement_form", clear_on_submit=True):
    product = st.text_input(_("Nom du produit"))
    depot = st.selectbox(_("Dépôt"), ["Dépôt 1", "Dépôt 2"])
    movement_display = st.selectbox(_("Type de mouvement"), [_("Entrée"), _("Sortie")])
    # Normalisation pour stockage en base
    movement_type_db = "entry" if movement_display == _("Entrée") else "exit"
    quantity = st.number_input(_("Quantité"), min_value=1, step=1)
    price = st.number_input(_("Prix unitaire (TND)"), min_value=0.01, format="%.2f")
    date = st.date_input(_("Date"), value=datetime.today())
    submitted = st.form_submit_button(_("Ajouter"))

    if submitted:
        if not product.strip():
            st.error(_("Veuillez saisir un nom de produit."))
        else:
            try:
                with engine.begin() as conn:
                    conn.execute(text("""
                        INSERT INTO inventory_movements 
                        (product, depot, movement_type, quantity, price, date)
                        VALUES (:product, :depot, :movement_type, :quantity, :price, :date)
                    """), {
                        "product": product.strip(),
                        "depot": depot,
                        "movement_type": movement_type_db,
                        "quantity": quantity,
                        "price": price,
                        "date": date
                    })
                st.success(_("Mouvement ajouté avec succès."))
            except SQLAlchemyError as e:
                st.error(f"{_('Erreur base de données')}: {str(e)}")

# --- Affichage historique ---
st.header(_("Historique des mouvements"))

try:
    with engine.connect() as conn:
        df = pd.read_sql("SELECT * FROM inventory_movements ORDER BY date DESC", conn)
except SQLAlchemyError as e:
    st.error(f"{_('Erreur lors de la récupération des données')}: {e}")
    st.stop()

if df.empty:
    st.info(_("Aucun mouvement enregistré."))
else:
    df["date"] = pd.to_datetime(df["date"])

    # --- Séparer entrées et sorties ---
    entries = df[df["movement_type"] == "entry"].copy()
    exits = df[df["movement_type"] == "exit"].copy()

    # Renommer pour fusion
    entries = entries.rename(columns={
        "quantity": "quantity_entry",
        "date": "date_entry"
    })
    exits = exits.rename(columns={
        "quantity": "quantity_exit",
        "date": "date_exit"
    })

    # Fusion pour calcul durée
    merged = pd.merge(
        entries, exits,
        on=["product", "depot"],
        suffixes=("_entry", "_exit"),
        how="outer"
    )

    merged["days_in_depot"] = (merged["date_exit"] - merged["date_entry"]).dt.days
    merged.loc[merged["days_in_depot"] < 0, "days_in_depot"] = None

    st.subheader(_("Détails des mouvements avec durée en dépôt"))
    st.dataframe(merged[[
        "product", "depot", "quantity_entry", "date_entry",
        "quantity_exit", "date_exit", "days_in_depot"
    ]])

    # --- Résumé stock par dépôt ---
    st.subheader(_("Résumé du stock par dépôt"))
    stock_entries = entries.groupby(["depot", "product"])["quantity_entry"].sum().reset_index()
    stock_exits = exits.groupby(["depot", "product"])["quantity_exit"].sum().reset_index()

    stock = pd.merge(stock_entries, stock_exits, on=["depot", "product"], how="left")
    stock["quantity_exit"] = stock["quantity_exit"].fillna(0)
    stock["stock"] = stock["quantity_entry"] - stock["quantity_exit"]

    st.dataframe(stock[["depot", "product", "stock"]])

    # --- Liens vers achats ---
    st.markdown("### " + _("Liens vers achats"))
    for prod in stock["product"].unique():
        st.markdown(f"- [{prod}](#)")

    # --- Export Excel ---
    def to_excel(dataframe):
        import io
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            dataframe.to_excel(writer, index=False)
        return output.getvalue()

    excel_data = to_excel(df)
    st.download_button(
        label=_("Télécharger l'historique Excel"),
        data=excel_data,
        file_name=f"inventory_movements_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # --- Export PDF ---
    def to_pdf(dataframe):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, _("Historique des mouvements"), ln=True, align="C")
        pdf.ln(5)
        for _, row in dataframe.iterrows():
            line = (
                f"{row['date'].strftime('%Y-%m-%d')} | "
                f"{row['product']} | {row['depot']} | "
                f"{row['movement_type']} | "
                f"Qté: {row['quantity']} | "
                f"Prix: {row['price']:.2f} TND"
            )
            pdf.cell(0, 8, line, ln=True)
        return pdf.output(dest='S').encode('latin1')

    pdf_data = to_pdf(df)
    st.download_button(
        label=_("Télécharger l'historique PDF"),
        data=pdf_data,
        file_name=f"inventory_movements_{datetime.now().strftime('%Y-%m-%d')}.pdf",
        mime="application/pdf"
    )
