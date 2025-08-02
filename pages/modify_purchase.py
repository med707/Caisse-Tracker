import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

st.title("✏️ Modifier un achat")

# --- Récupérer l'URL de la base de données depuis Streamlit secrets ---
DATABASE_URL = st.secrets["database"]["url"]

# --- Créer le moteur SQLAlchemy ---
engine = create_engine(DATABASE_URL)

# --- Vérification connexion ---
try:
    with engine.connect() as conn:
        db_version = conn.execute(text("SELECT version()")).fetchone()
    st.success(f"✅ Connecté à la base: {db_version[0]}")
except SQLAlchemyError as e:
    st.error(f"❌ Erreur de connexion à la base: {e}")
    st.stop()

# --- Charger les données ---
try:
    with engine.connect() as conn:
        df = pd.read_sql("SELECT * FROM purchases ORDER BY date DESC", conn)
except Exception as e:
    st.error(f"Erreur lors du chargement des données: {e}")
    st.stop()

# --- Sidebar filtres ---
st.sidebar.header("🔎 Filtres")

with st.sidebar:
    start_date = st.date_input("📅 Date de début", value=datetime.today().replace(day=1))
    end_date = st.date_input("📅 Date de fin", value=datetime.today())
    categories = ["Tous"] + sorted(df["category"].dropna().unique().tolist()) if not df.empty else ["Tous"]
    category_filter = st.selectbox("📂 Catégorie", categories)
    search_term = st.text_input("🔍 Rechercher un produit")

# --- Application des filtres ---
filtered_df = df.copy()

if category_filter != "Tous":
    filtered_df = filtered_df[filtered_df["category"] == category_filter]

filtered_df["date"] = pd.to_datetime(filtered_df["date"])
filtered_df = filtered_df[
    (filtered_df["date"] >= pd.to_datetime(start_date)) &
    (filtered_df["date"] <= pd.to_datetime(end_date))
]

if search_term:
    filtered_df = filtered_df[filtered_df["product"].str.contains(search_term, case=False, na=False)]

# --- Affichage du tableau ---
st.subheader("🧾 Achats filtrés")

if filtered_df.empty:
    st.info("Aucun achat trouvé.")
else:
    display_df = filtered_df[[
        "id", "date", "product", "category", "subcategory", "supplier",
        "quantity", "purchase_price", "sale_price"
    ]].copy()

    display_df["total_purchase"] = display_df["quantity"] * display_df["purchase_price"]
    display_df["total_sale"] = display_df["quantity"] * display_df["sale_price"]
    display_df.set_index("id", inplace=True)

    st.dataframe(display_df)

    selected_id = st.number_input("🆔 Saisir l’ID à modifier", min_value=1, step=1)

    if selected_id in display_df.index:
        row = display_df.loc[selected_id]

        st.subheader(f"✏️ Modifier l'achat ID {selected_id}")
        new_product = st.text_input("Produit", value=row["product"])
        new_category = st.text_input("Catégorie", value=row["category"])
        new_subcategory = st.text_input("Sous-catégorie", value=row["subcategory"])
        new_supplier = st.text_input("Fournisseur", value=row["supplier"])
        new_quantity = st.number_input("Quantité", min_value=0, value=int(row["quantity"]))
        new_purchase_price = st.number_input("Prix d'achat unitaire", min_value=0.0, value=float(row["purchase_price"]), format="%.2f")
        new_sale_price = st.number_input("Prix de vente unitaire", min_value=0.0, value=float(row["sale_price"]), format="%.2f")
        new_date = st.date_input("Date", value=pd.to_datetime(row["date"]))

        if st.button("💾 Enregistrer les modifications"):
            try:
                with engine.begin() as conn:
                    conn.execute(text("""
                        UPDATE purchases SET
                            product = :product, category = :category, subcategory = :subcategory, supplier = :supplier,
                            quantity = :quantity, purchase_price = :purchase_price, sale_price = :sale_price, date = :date
                        WHERE id = :id
                    """), {
                        "product": new_product,
                        "category": new_category,
                        "subcategory": new_subcategory,
                        "supplier": new_supplier,
                        "quantity": new_quantity,
                        "purchase_price": new_purchase_price,
                        "sale_price": new_sale_price,
                        "date": new_date.strftime("%Y-%m-%d"),
                        "id": selected_id
                    })
                st.success("✅ Achat modifié avec succès.")
            except SQLAlchemyError as e:
                st.error(f"Erreur lors de la mise à jour : {e}")
    else:
        st.info("⛔ Saisissez un ID valide à partir du tableau.")
