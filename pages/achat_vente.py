import streamlit as st
import sqlite3
import pandas as pd
import os
import shutil
from datetime import datetime
from lang_utils import get_translation

# --- CONFIGURATION LANGUE ---
lang = st.sidebar.selectbox("🌍 Langue / اللغة", ["fr", "ar"], index=0)
t = lambda key: get_translation(key, lang)

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

# --- SAUVEGARDE & RESTAURATION ---

def create_backup(db_file="supermarket.db", backup_prefix="backup_supermarket_"):
    if os.path.exists(db_file):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{backup_prefix}{timestamp}.db"
        shutil.copy(db_file, backup_file)
        print(f"✅ Sauvegarde créée : {backup_file}")

def restore_latest_backup(db_file="supermarket.db", backup_prefix="backup_supermarket_"):
    backups = sorted(
        [f for f in os.listdir() if f.startswith(backup_prefix) and f.endswith(".db")],
        reverse=True
    )
    if not backups:
        print("⚠️ Aucune sauvegarde trouvée.")
        return False
    latest_backup = backups[0]
    try:
        shutil.copy(latest_backup, db_file)
        print(f"✅ Base restaurée depuis : {latest_backup}")
        return True
    except Exception as e:
        print(f"❌ Erreur restauration : {e}")
        return False

# --- RESTAURATION SI DB MANQUANTE ---
if not os.path.exists("supermarket.db"):
    restored = restore_latest_backup()
    if not restored:
        st.error(t("❌ La base de données est introuvable et aucune sauvegarde n'a été trouvée."))

# --- CONNEXION BASE ---
conn = sqlite3.connect("supermarket.db", check_same_thread=False)
cursor = conn.cursor()

# --- CREATION TABLE SI NON EXISTANTE ---
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

st.title("🧾 " + t("Quick Entry for Purchase"))

# --- FORMULAIRE AJOUT PRODUIT ---

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
            st.warning(t("Sale price should be equal or greater than purchase price."))
        else:
            cursor.execute("""
                INSERT INTO purchases (product, category, subcategory, supplier, quantity, purchase_price, sale_price, date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                product.strip(), category, subcategory, supplier.strip(), quantity, purchase_price, sale_price, date.strftime("%Y-%m-%d")
            ))
            conn.commit()

            create_backup()

            gain = (sale_price - purchase_price) * quantity
            st.success(f"✅ {product} {t('Added')}. {t('Gain')}: {gain:.2f} TND")
            st.experimental_rerun()

# --- AFFICHAGE HISTORIQUE AVEC GAINS ---

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

# --- EXPORT EXCEL ---

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

conn.close()
