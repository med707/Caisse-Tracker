import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from lang_utils import get_translation

# --- LANGUE ---
lang = st.sidebar.selectbox("🌍 Langue / اللغة", ["fr", "ar"], index=0)
t = lambda key: get_translation(key, lang)

st.title("🧾 " + t("Quick Entry for Purchase"))

# --- Get database URL from Streamlit secrets ---
DATABASE_URL = st.secrets["database"]["url"]

# --- Create SQLAlchemy engine ---
engine = create_engine(DATABASE_URL)

# --- Initialize database table if not exists ---
def init_db():
    with engine.connect() as conn:
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS purchases (
            id SERIAL PRIMARY KEY,
            product TEXT NOT NULL,
            category TEXT,
            subcategory TEXT,
            supplier TEXT,
            quantity INTEGER,
            purchase_price NUMERIC,
            sale_price NUMERIC,
            date DATE
        )
        """))
        conn.commit()

init_db()

# --- Category setup (your original CATEGORIES dict) ---
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

# --- Streamlit UI ---
category = st.selectbox("📂 " + t("Category"), list(CATEGORIES.keys()))

# Handle subcategories (including nested)
sub = CATEGORIES[category].get("subcategories", [])
subcategory = ""
if isinstance(sub, dict):
    main_sub = st.selectbox("📁 " + t("Subcategory group"), list(sub.keys()))
    subcategory = st.selectbox("📁 " + t("Subcategory"), sub[main_sub])
elif isinstance(sub, list) and sub:
    subcategory = st.selectbox("📁 " + t("Subcategory"), sub)
else:
    subcategory = st.text_input("📁 " + t("Subcategory"))

# Suppliers
suppliers = CATEGORIES[category].get("suppliers", [])
supplier = st.selectbox("🏢 " + t("Supplier"), suppliers) if suppliers else st.text_input("🏢 " + t("Supplier"))

product = st.text_input("📦 " + t("Product name"))
quantity = st.number_input("🔢 " + t("Quantity"), min_value=1, step=1)
purchase_price = st.number_input("💰 " + t("Purchase price"), min_value=0.0, step=0.1)
sale_price = st.number_input("🏷️ " + t("Sale price"), min_value=0.0, step=0.1)
date = st.date_input("📅 " + t("Date"), value=datetime.today())

if st.button("✅ " + t("Add Purchase")):
    if not product.strip():
        st.warning(t("Please fill in the product name."))
    else:
        # Insert into DB
        try:
            with engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO purchases (product, category, subcategory, supplier, quantity, purchase_price, sale_price, date)
                    VALUES (:product, :category, :subcategory, :supplier, :quantity, :purchase_price, :sale_price, :date)
                """), {
                    "product": product,
                    "category": category,
                    "subcategory": subcategory,
                    "supplier": supplier,
                    "quantity": quantity,
                    "purchase_price": purchase_price,
                    "sale_price": sale_price,
                    "date": date
                })
            st.success(t("Purchase added successfully!"))
        except SQLAlchemyError as e:
            st.error(f"{t('Database error')}: {str(e)}")
