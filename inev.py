import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt

# --- Your categories and subcategories dict ---
CATEGORIES = {
    "🍼 Dépôt": {
        "subcategories": ["Medded", "Mlika", "Jamila"],
        "suppliers": []
    },
    "🍰 Cake": {
        "subcategories": ["Tom", "Moulin d'Or"],
        "suppliers": []
    },
    "🥛 Produits Laitiers": {
        "subcategories": ["Lait", "Yaourt"],
        "suppliers": ["Delice", "Vitalait", "Centrale"]
    },
    "🍗 Volaille": {
        "subcategories": ["Mazra", "Jalel"],
        "suppliers": ["SOTUVI", "CHA"]
    },
    "🌾 Farine": {
        "subcategories": [],
        "suppliers": ["Grands Moulins", "Minoterie"]
    },
    "🥤 Liquides": {
        "subcategories": ["Eau", "Boissons Gazeuses", "Jus"],
        "suppliers": ["Cristal", "Coca-Cola", "Pepsi"]
    },
    "🧴 Hygiène & Beauté": {
        "subcategories": {
            "🧼 Hygiène": ["Judy", "Lilas", "Nawar", "Syso", "Sunsilk", "Autre"],
            "💄 Beauté": ["Yassine", "L'Oréal", "Autre"]
        },
        "suppliers": []
    },
    "🧀 Fromage": {
        "subcategories": ["Majesté", "Landor", "Traditionnel"],
        "suppliers": []
    },
    "🥩 Twebel": {
        "subcategories": ["Twebel", "Elmalah"],
        "suppliers": []
    },
    "🍦 Glace": {
        "subcategories": [],
        "suppliers": ["Frigo", "Polar"]
    },
    "🥖 Daily": {
        "subcategories": ["Gâteaux", "Pain"],
        "suppliers": ["Boulangerie du Coin", "Fournée Dorée"]
    },
    "🐶 Animaux": {
        "subcategories": ["Pet's"],
        "suppliers": ["Royal Canin", "Pedigree"]
    },
    "🏠 Maison": {
        "subcategories": [],
        "suppliers": []
    },
    "📦 Divers": {
        "subcategories": [],
        "suppliers": []
    },
    "🎉 Autres": {
        "subcategories": [],
        "suppliers": []
    }
}

st.title("🛒 Supermarket Expense Tracker")

# Connect to SQLite
db_path = "supermarket.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create table if not exists
cursor.execute("""
CREATE TABLE IF NOT EXISTS purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product TEXT,
    category TEXT,
    subcategory TEXT,
    supplier TEXT,
    quantity INTEGER,
    price REAL,
    date TEXT
)
""")
conn.commit()

# --- Select category (outside form) ---
st.header("Add a product")
category = st.selectbox("Category", list(CATEGORIES.keys()))

# --- Handle subcategories ---
subs = CATEGORIES[category]["subcategories"]
if isinstance(subs, dict):
    main_subcat = st.selectbox("Subcategory main", list(subs.keys()))
    subcategory = st.selectbox("Subcategory detail", subs[main_subcat])
else:
    if subs:
        subcategory = st.selectbox("Subcategory", subs)
    else:
        subcategory = st.text_input("Subcategory (free text)")

# --- Get supplier list ---
suppliers_list = CATEGORIES[category].get("suppliers", [])

# --- Form for product details ---
with st.form("add_product_form", clear_on_submit=True):
    if suppliers_list:
        supplier = st.selectbox("Supplier", suppliers_list)
    else:
        supplier = st.text_input("Supplier (free text)")

    product = st.text_input("Product name")
    quantity = st.number_input("Quantity", min_value=1, step=1)
    price = st.number_input("Price per unit", min_value=0.01, format="%.2f")
    date = st.date_input("Date", value=datetime.today())

    submitted = st.form_submit_button("Save")

    if submitted:
        if not product.strip():
            st.error("Please enter a product name.")
        elif price <= 0:
            st.error("Price must be greater than 0.")
        else:
            cursor.execute(
                "INSERT INTO purchases (product, category, subcategory, supplier, quantity, price, date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (product.strip(), category, subcategory, supplier.strip(), quantity, price, date.strftime("%Y-%m-%d"))
            )
            conn.commit()
            total = quantity * price
            st.success(f"Added {product} (x{quantity}) at {price:.2f} = {total:.2f} TND")

# --- Show purchases summary ---
st.header("Purchase history")
df = pd.read_sql_query("SELECT * FROM purchases ORDER BY date DESC", conn)

if df.empty:
    st.info("No purchases found.")
else:
    df["Total"] = df["quantity"] * df["price"]
    st.dataframe(df[["date", "product", "category", "subcategory", "supplier", "quantity", "price", "Total"]])

conn.close()

# --- Page Links ---
st.page_link("pages/ineev.py", label="🔁 Comparaison Hebdomadaire", icon="📊")
st.page_link("pages/statistics.py", label="📈 Statistiques", icon="📊")
st.page_link("pages/monthly_expense.py", label="🗓️ Dépenses Mensuelles", icon="📅")


