import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd
import sys
import os

# Ajouter le dossier courant au path pour trouver lang_utils.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from lang_utils import get_translation
from fpdf import FPDF

# --- LANGUE ---
lang = st.sidebar.selectbox("🌍 Langue / اللغة", ["fr", "ar"], index=0)
t = lambda key: get_translation(key, lang)

# --- CATÉGORIES ---
CATEGORIES = {
    "🍼 Dépôt": {"subcategories": ["Medded", "Mlika", "Jamila"], "suppliers": []},
    "🍰 Cake": {"subcategories": ["Tom", "Moulin d'Or"], "suppliers": []},
    "🥛 Produits Laitiers": {"subcategories": ["Lait", "Yaourt"], "suppliers": ["Delice", "Vitalait", "Centrale"]},
    "🍗 Volaille": {"subcategories": ["Mazra", "Jalel"], "suppliers": ["SOTUVI", "CHA"]},
    "🌾 Farine": {"subcategories": [], "suppliers": ["Grands Moulins", "Minoterie"]},
    "🥤 Liquides": {"subcategories": ["Eau", "Boissons Gazeuses", "Jus"], "suppliers": ["Cristal", "Coca-Cola", "Pepsi"]},
    "🧴 Hygiène & Beauté": {
        "subcategories": {
            "🧼 Hygiène": ["Judy", "Lilas", "Nawar", "Syso", "Sunsilk", "Autre"],
            "💄 Beauté": ["Yassine", "L'Oréal", "Autre"]
        },
        "suppliers": []
    },
    "🧀 Fromage": {"subcategories": ["Majesté", "Landor", "Traditionnel"], "suppliers": []},
    "🥩 Twebel": {"subcategories": ["Twebel", "Elmalah"], "suppliers": []},
    "🍦 Glace": {"subcategories": [], "suppliers": ["Frigo", "Polar"]},
    "🥖 Daily": {"subcategories": ["Gâteaux", "Pain"], "suppliers": ["Boulangerie du Coin", "Fournée Dorée"]},
    "🐶 Animaux": {"subcategories": ["Pet's"], "suppliers": ["Royal Canin", "Pedigree"]},
    "🏠 Maison": {"subcategories": [], "suppliers": []},
    "📦 Divers": {"subcategories": [], "suppliers": []},
    "🎉 Autres": {"subcategories": [], "suppliers": []}
}

st.title("➕ " + t("Add a product"))

# --- Connexion à la base ---
conn = sqlite3.connect("supermarket.db", check_same_thread=False)
cursor = conn.cursor()

# --- Création table ---
cursor.execute("""
CREATE TABLE IF NOT EXISTS purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product TEXT,
    category TEXT,
    subcategory TEXT,
    supplier TEXT,
    quantity INTEGER,
    purchase_price REAL,
    sale_price REAL,
    date TEXT
)
""")
conn.commit()

# --- Formulaire d’ajout ---
category = st.selectbox(t("Category"), list(CATEGORIES.keys()))
subs = CATEGORIES[category]["subcategories"]
if isinstance(subs, dict):
    main_subcat = st.selectbox(t("Subcategory main"), list(subs.keys()))
    subcategory = st.selectbox(t("Subcategory detail"), subs[main_subcat])
else:
    subcategory = st.selectbox(t("Subcategory"), subs) if subs else st.text_input(t("Subcategory (free text)"))

suppliers = CATEGORIES[category].get("suppliers", [])
supplier = st.selectbox(t("Supplier"), suppliers) if suppliers else st.text_input(t("Supplier (free text)"))

with st.form("add_form", clear_on_submit=True):
    product = st.text_input(t("Product name"))
    quantity = st.number_input(t("Quantity"), min_value=1, step=1)
    purchase_price = st.number_input(t("Purchase price per unit (TND)"), min_value=0.01, format="%.2f")
    sale_price = st.number_input(t("Sale price per unit (TND)"), min_value=0.01, format="%.2f")
    date = st.date_input(t("Date"), value=datetime.today())
    submitted = st.form_submit_button(t("Save"))

    if submitted:
        if not product.strip():
            st.error(t("Please enter a product name."))
        elif sale_price < purchase_price:
            st.warning(t("Price must be greater than 0."))
        else:
            cursor.execute("""
                INSERT INTO purchases (product, category, subcategory, supplier, quantity, purchase_price, sale_price, date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                product.strip(), category, subcategory, supplier.strip(), quantity, purchase_price, sale_price, date.strftime("%Y-%m-%d")
            ))
            conn.commit()
            gain = (sale_price - purchase_price) * quantity
            st.success(f"✅ {product} {t('Added')}. {t('Gain')}: {gain:.2f} TND")
            st.experimental_rerun()

# --- Affichage historique avec gains ---
st.header(t("Purchase History"))

query = """
SELECT
    id,
    product,
    category,
    subcategory,
    supplier,
    quantity,
    purchase_price,
    sale_price,
    date,
    (sale_price - purchase_price) * quantity AS gain
FROM purchases
ORDER BY date DESC
"""

df = pd.read_sql_query(query, conn, parse_dates=["date"])

if df.empty:
    st.info(t("No purchases found."))
else:
    # Formatage monétaire
    for col in ["purchase_price", "sale_price", "gain"]:
        df[col] = df[col].fillna(0).map(lambda x: f"{x:.2f} TND")

    st.dataframe(df[["date", "product", "category", "subcategory", "supplier", "quantity", "purchase_price", "sale_price", "gain"]])

# --- Export Excel ---
def to_excel(dataframe):
    import io
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        dataframe.to_excel(writer, index=False)
    return output.getvalue()

excel_data = to_excel(df)

st.download_button(
    label=t("Download purchase history (Excel)"),
    data=excel_data,
    file_name=f"purchase_history_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# --- Export PDF ---
def to_pdf(dataframe):
    def clean_text(text):
        return ''.join(c for c in str(text) if ord(c) < 128)  # Supprime caractères non-ASCII

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, "Purchase History", ln=True, align="C")
    pdf.ln(5)

    for _, row in dataframe.iterrows():
        line = (
            f"{clean_text(row['date'].strftime('%Y-%m-%d'))} | "
            f"{clean_text(row['product'])} | "
            f"{clean_text(row['category'])} > {clean_text(row['subcategory'])} | "
            f"{clean_text(row['supplier'])} | Qty: {row['quantity']} | "
            f"Purchase: {row['purchase_price']} | Sale: {row['sale_price']} | Gain: {row['gain']}"
        )
        pdf.cell(0, 8, line, ln=True)

    return pdf.output(dest='S').encode('latin1')

pdf_data = to_pdf(df)

st.download_button(
    label=t("Download purchase history (PDF)"),
    data=pdf_data,
    file_name=f"purchase_history_{datetime.now().strftime('%Y-%m-%d')}.pdf",
    mime="application/pdf"
)

conn.close()

