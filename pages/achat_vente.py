import streamlit as st
import sqlite3
import pandas as pd
import os
from datetime import datetime
from lang_utils import get_translation
from backup_utils import create_backup, restore_latest_backup

# --- CONFIGURATION LANGUE ---
lang = st.sidebar.selectbox("🌍 Langue / اللغة", ["fr", "ar"], index=0)
t = lambda key: get_translation(key, lang)

st.title("🧾 " + t("Quick Entry for Purchase"))

# --- Restauration auto si base absente ---
if not os.path.exists("supermarket.db"):
    restored = restore_latest_backup()
    if not restored:
        st.error(t("❌ La base de données est introuvable et aucune sauvegarde n'a été trouvée."))

# --- Connexion DB ---
conn = sqlite3.connect("supermarket.db", check_same_thread=False)
cursor = conn.cursor()

# --- Création table si inexistante ---
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

# --- CATEGORIES ---
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

# --- Interface ---
category = st.selectbox("📂 " + t("Category"), list(CATEGORIES.keys()))

# Gestion des sous-catégories (y compris imbriquées)
sub = CATEGORIES[category].get("subcategories", [])
subcategory = ""
if isinstance(sub, dict):
    main_sub = st.selectbox("📁 " + t("Subcategory group"), list(sub.keys()))
    subcategory = st.selectbox("📁 " + t("Subcategory"), sub[main_sub])
elif isinstance(sub, list) and sub:
    subcategory = st.selectbox("📁 " + t("Subcategory"), sub)
else:
    subcategory = st.text_input("📁 " + t("Subcategory"))

# Fournisseurs
suppliers = CATEGORIES[category].get("suppliers", [])
supplier = st.selectbox("🏢 " + t("Supplier"), suppliers) if suppliers else st.text_input("🏢 " + t("Supplier"))

product = st.text_input("📦 " + t("Product name"))
quantity = st.number_input("🔢 " + t("Quantity"), min_value=1, step=1)
purchase_price = st.number_input("💰 " + t("Purchase price"), min_value=0.0, step=0.1)
sale_price = st.number_input("🏷️ " + t("Sale price"), min_value=0.0, step=0.1)
date = st.date_input("📅 " + t("Date"), value=datetime.today()).strftime("%Y-%m-%d")

# --- Sauvegarde en base ---
if st.button("✅ " + t("Add Purchase")):
    if product:
        cursor.execute("""
            INSERT INTO purchases (product, category, subcategory, supplier, quantity, purchase_price, sale_price, date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (product, category, subcategory, supplier, quantity, purchase_price, sale_price, date))
        conn.commit()
        create_backup()  # 💾 Sauvegarde auto
        st.success(t("Purchase added successfully!"))
    else:
        st.warning(t("Please fill in the product name."))
