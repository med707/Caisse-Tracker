import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

st.title("✏️ Modifier un achat")

# --- Connexion à la base de données ---
conn = sqlite3.connect("supermarket.db")
cursor = conn.cursor()

# --- Récupération des données ---
query = "SELECT * FROM purchases ORDER BY date DESC"
df = pd.read_sql_query(query, conn)

# --- Filtres ---
st.sidebar.header("🔎 Filtres")

with st.sidebar:
    start_date = st.date_input("📅 Date de début", value=datetime.today().replace(day=1))
    end_date = st.date_input("📅 Date de fin", value=datetime.today())

    category_filter = st.selectbox("📂 Catégorie", ["Tous"] + sorted(df["category"].unique().tolist()))
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
    filtered_df = filtered_df[filtered_df["product"].str.contains(search_term, case=False)]

# --- Affichage du tableau ---
st.subheader("🧾 Achats filtrés")

if filtered_df.empty:
    st.info("Aucun achat trouvé.")
else:
    display_df = filtered_df[["id", "date", "product", "category", "subcategory", "supplier", "quantity", "price"]].copy()
    display_df["total"] = display_df["quantity"] * display_df["price"]
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
        new_price = st.number_input("Prix unitaire", min_value=0.0, value=float(row["price"]), format="%.2f")
        new_date = st.date_input("Date", value=pd.to_datetime(row["date"]))

        if st.button("💾 Enregistrer les modifications"):
            try:
                cursor.execute("""
                    UPDATE purchases SET
                        product = ?, category = ?, subcategory = ?, supplier = ?,
                        quantity = ?, price = ?, date = ?
                    WHERE id = ?
                """, (
                    new_product, new_category, new_subcategory, new_supplier,
                    new_quantity, new_price, new_date.strftime("%Y-%m-%d"), selected_id
                ))
                conn.commit()
                st.success("✅ Achat modifié avec succès.")
                try:
                    st.experimental_rerun()
                except AttributeError:
                    st.query_params = {"refresh": str(datetime.now())}
            except Exception as e:
                st.error(f"Erreur lors de la mise à jour : {e}")
    else:
        st.info("⛔ Saisissez un ID valide à partir du tableau.")

# --- Fermeture ---
conn.close()

