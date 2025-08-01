import streamlit as st
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import OperationalError
from datetime import datetime
from lang_utils import get_translation

# --- LANGUE ---
lang = st.sidebar.selectbox("🌍 Langue / اللغة", ["fr", "ar"], index=0)
t = lambda key: get_translation(key, lang)

st.title("🧾 " + t("Quick Entry for Purchase"))

# --- Get Postgres URL from secrets ---
DATABASE_URL = st.secrets["database"]["url"]

# --- Create engine ---
engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 5})

# --- Check if table exists, create if not ---
inspector = inspect(engine)
if "purchases" not in inspector.get_table_names():
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE purchases (
                id SERIAL PRIMARY KEY,
                product TEXT,
                category TEXT,
                subcategory TEXT,
                supplier TEXT,
                quantity INTEGER,
                purchase_price REAL,
                sale_price REAL,
                date DATE
            )
        """))
        conn.commit()

# --- Categories data ---
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

# --- UI Inputs ---
category = st.selectbox("📂 " + t("Category"), list(CATEGORIES.keys()))

sub = CATEGORIES[category].get("subcategories", [])
subcategory = ""
if isinstance(sub, dict):
    main_sub = st.selectbox("📁 " + t("Subcategory group"), list(sub.keys()))
    subcategory = st.selectbox("📁 " + t("Subcategory"), sub[main_sub])
elif isinstance(sub, list) and sub:
    subcategory = st.selectbox("📁 " + t("Subcategory"), sub)
else:
    subcategory = st.text_input("📁 " + t("Subcategory"))

suppliers = CATEGORIES[category].get("suppliers", [])
supplier = st.selectbox("🏢 " + t("Supplier"), suppliers) if suppliers else st.text_input("🏢 " + t("Supplier"))

product = st.text_input("📦 " + t("Product name"))
quantity = st.number_input("🔢 " + t("Quantity"), min_value=1, step=1)
purchase_price = st.number_input("💰 " + t("Purchase price"), min_value=0.0, step=0.1)
sale_price = st.number_input("🏷️ " + t("Sale price"), min_value=0.0, step=0.1)
date = st.date_input("📅 " + t("Date"), value=datetime.today())

# --- Insert into DB ---
if st.button("✅ " + t("Add Purchase")):
    if not product:
        st.warning(t("Please fill in the product name."))
    else:
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
