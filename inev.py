# --- inev.py ---

import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd
from lang_utils import get_translation

# --- LANGUE ---
lang = st.sidebar.selectbox("🌍 Langue / اللغة", ["fr", "ar"], index=0)
_ = lambda key: get_translation(key, lang)

# --- CATÉGORIES ---
CATEGORIES = {
    "🍼 Dépôt": {"subcategories": ["Medded", "Mlika", "Jamila"], "suppliers": []},
    "🍰 Cake": {"subcategories": ["Tom", "Moulin d'Or"], "suppliers": []},
    "🥛 Produits Laitiers": {"subcategories": ["Lait", "Yaourt"], "suppliers": ["Delice", "Vitalait", "Centrale"]},
    "🍗 Volaille": {"subcategories": ["Mazra", "Jalel"], "suppliers": ["SOTUVI", "CHA"]},
    "🍾 Farine": {"subcategories": [], "suppliers": ["Grands Moulins", "Minoterie"]},
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

st.title("👚 " + _("Supermarket Expense Tracker"))

# --- BASE DE DONNÉES ---
DB_PATH = "supermarket.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

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

# --- FORMULAIRE AJOUT ---
st.header(_("Add a product"))
category = st.selectbox(_("Category"), list(CATEGORIES.keys()))
subs = CATEGORIES[category]["subcategories"]

if isinstance(subs, dict):
    main_subcat = st.selectbox(_("Subcategory main"), list(subs.keys()))
    subcategory = st.selectbox(_("Subcategory detail"), subs[main_subcat])
else:
    if subs:
        subcategory = st.selectbox(_("Subcategory"), subs)
    else:
        subcategory = st.text_input(_("Subcategory (free text)"))

suppliers = CATEGORIES[category].get("suppliers", [])

with st.form("add_product_form", clear_on_submit=True):
    if suppliers:
        supplier = st.selectbox(_("Supplier"), suppliers)
    else:
        supplier = st.text_input(_("Supplier (free text)"))

    product = st.text_input(_("Product name"))
    quantity = st.number_input(_("Quantity"), min_value=1, step=1)
    price = st.number_input(_("Price"), min_value=0.01, format="%.2f")
    date = st.date_input(_("Date"), value=datetime.today())

    submitted = st.form_submit_button(_("Save"))
    if submitted:
        if not product.strip():
            st.error(_("Please enter a product name."))
        elif price <= 0:
            st.error(_("Price must be greater than 0."))
        else:
            cursor.execute("""
                INSERT INTO purchases (product, category, subcategory, supplier, quantity, price, date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (product.strip(), category, subcategory, supplier.strip(), quantity, price, date.strftime("%Y-%m-%d")))
            conn.commit()
            st.success(f"{_('Added')} {product} (x{quantity}) = {quantity * price:.2f} TND")

# --- HISTORIQUE DES ACHATS ---
st.subheader(f"📋 {_('Purchase History')}")
df = pd.read_sql_query("SELECT * FROM purchases ORDER BY date DESC", conn)
conn.close()

if df.empty:
    st.info(_("No purchases found."))
else:
    for i, row in df.iterrows():
        col1, col2, col3 = st.columns([6, 1, 1])
        with col1:
            st.markdown(f"""
            **🗓️ {row['date']}**  
            🛍️ **{row['product']}** | {row['category']} > {row['subcategory']}  
            🚚 {row['supplier']} | 📦 {_('Quantity')}: {row['quantity']} | 💵 {_('Price')}: {row['price']:.2f} | 💰 {_('Total')}: {row['quantity'] * row['price']:.2f}
            """)
        with col2:
            if st.button("📝", key=f"edit_{row['id']}"):
                st.session_state["edit_id"] = row['id']
                st.experimental_rerun()
        with col3:
            if st.button("🖑️", key=f"delete_{row['id']}"):
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM purchases WHERE id = ?", (row['id'],))
                conn.commit()
                conn.close()
                st.success(f"{_('Deleted')} {row['product']} {_('on')} {row['date']}")
                st.experimental_rerun()

# --- FORMULAIRE MODIFICATION ---
if "edit_id" in st.session_state:
    edit_id = st.session_state["edit_id"]
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT * FROM purchases WHERE id = ?", (edit_id,)).fetchone()
    conn.close()
    if row:
        id_, product, category, subcategory, supplier, quantity, price, date = row
        st.subheader(f"📝 {_('Modify Entry')}")
        with st.form("edit_form"):
            new_product = st.text_input(_("Product"), value=product)
            new_category = st.text_input(_("Category"), value=category)
            new_subcategory = st.text_input(_("Subcategory"), value=subcategory)
            new_supplier = st.text_input(_("Supplier"), value=supplier)
            new_quantity = st.number_input(_("Quantity"), min_value=1, value=quantity)
            new_price = st.number_input(_("Price"), min_value=0.01, value=price, step=0.01)
            new_date = st.date_input(_("Date"), value=pd.to_datetime(date))

            save = st.form_submit_button(_("Save Changes"))
            cancel = st.form_submit_button(_("Cancel"))

            if save:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE purchases
                    SET product=?, category=?, subcategory=?, supplier=?, quantity=?, price=?, date=?
                    WHERE id=?
                """, (new_product, new_category, new_subcategory, new_supplier, new_quantity, new_price, new_date.strftime("%Y-%m-%d"), edit_id))
                conn.commit()
                conn.close()
                st.success(_("Entry updated successfully!"))
                del st.session_state["edit_id"]
                st.experimental_rerun()
            if cancel:
                del st.session_state["edit_id"]
                st.experimental_rerun()

# --- PAGE LINKS ---
st.page_link("pages/ineev.py", label="🔀 " + _("Weekly Comparison"), icon="📊")
st.page_link("pages/statistics.py", label="📈 " + _("Statistics"), icon="📊")
st.page_link("pages/monthly_expense.py", label="🗓️ " + _("Monthly Expenses"), icon="📅")

