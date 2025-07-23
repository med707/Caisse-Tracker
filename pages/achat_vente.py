import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd
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

st.title("➕ " + t("Ajouter un achat/vente"))

# --- Connexion à la base ---
conn = sqlite3.connect("supermarket.db", check_same_thread=False)
cursor = conn.cursor()

# --- Création table avec colonnes achat/vente ---
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
category = st.selectbox(t("Catégorie"), list(CATEGORIES.keys()))
subs = CATEGORIES[category]["subcategories"]
if isinstance(subs, dict):
    main_subcat = st.selectbox(t("Sous-catégorie principale"), list(subs.keys()))
    subcategory = st.selectbox(t("Sous-catégorie détaillée"), subs[main_subcat])
else:
    subcategory = st.selectbox(t("Sous-catégorie"), subs) if subs else st.text_input(t("Sous-catégorie (libre)"))

suppliers = CATEGORIES[category].get("suppliers", [])
supplier = st.selectbox(t("Fournisseur"), suppliers) if suppliers else st.text_input(t("Fournisseur (libre)"))

with st.form("add_form", clear_on_submit=True):
    product = st.text_input(t("Nom du produit"))
    quantity = st.number_input(t("Quantité"), min_value=1, step=1)
    purchase_price = st.number_input(t("Prix d'achat unitaire (TND)"), min_value=0.01, format="%.2f")
    sale_price = st.number_input(t("Prix de vente unitaire (TND)"), min_value=0.01, format="%.2f")
    date = st.date_input(t("Date"), value=datetime.today())
    submitted = st.form_submit_button(t("💾 Enregistrer"))

if submitted:
    if not product.strip():
        st.error(t("⚠️ Veuillez saisir un nom de produit."))
    elif sale_price < purchase_price:
        st.warning(t("⚠️ Le prix de vente doit être supérieur ou égal au prix d'achat."))
    else:
        cursor.execute("""
            INSERT INTO purchases (product, category, subcategory, supplier, quantity, purchase_price, sale_price, date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            product.strip(), category, subcategory, supplier.strip(), quantity, purchase_price, sale_price, date.strftime("%Y-%m-%d")
        ))
        conn.commit()
        gain = (sale_price - purchase_price) * quantity
        st.success(f"✅ {product} ajouté. Gain estimé : {gain:.2f} TND")

# BOUTON DE RAFRAÎCHISSEMENT EN DEHORS DU FORMULAIRE
if st.button(t("🔄 Rafraîchir la page")):
    st.experimental_rerun()

# --- Affichage tableau avec gains ---
st.header(t("Historique Achat/Vente"))

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
    st.info(t("Aucun achat/vente enregistré."))
else:
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
    label=t("Télécharger l'historique en Excel"),
    data=excel_data,
    file_name=f"historique_achat_vente_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# --- Export PDF ---
def to_pdf(dataframe):
    def clean_text(text):
        return ''.join(c for c in str(text) if ord(c) < 128)  # Supprime emojis, caractères spéciaux

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, "Historique Achat/Vente", ln=True, align="C")
    pdf.ln(5)

    for _, row in dataframe.iterrows():
        line = (
            f"{clean_text(row['date'].strftime('%Y-%m-%d'))} | "
            f"{clean_text(row['product'])} | "
            f"{clean_text(row['category'])} > {clean_text(row['subcategory'])} | "
            f"{clean_text(row['supplier'])} | Qté: {row['quantity']} | "
            f"Achat: {row['purchase_price']} | Vente: {row['sale_price']} | Gain: {row['gain']}"
        )
        pdf.cell(0, 8, line, ln=True)

    pdf_bytes = pdf.output(dest='S').encode('latin1')
    return pdf_bytes

pdf_data = to_pdf(df)

st.download_button(
    label=t("Télécharger l'historique en PDF"),
    data=pdf_data,
    file_name=f"historique_achat_vente_{datetime.now().strftime('%Y-%m-%d')}.pdf",
    mime="application/pdf"
)

conn.close()

