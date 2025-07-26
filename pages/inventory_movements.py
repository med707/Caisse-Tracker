import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from fpdf import FPDF

# --- Connexion base de données ---
conn = sqlite3.connect("supermarket.db", check_same_thread=False)

# --- Créer table mouvements si nécessaire ---
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS inventory_movements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product TEXT,
    depot TEXT,
    movement_type TEXT,  -- 'entry' ou 'exit'
    quantity INTEGER,
    price REAL,
    date TEXT
)
""")
conn.commit()

# --- Langue (exemple simple) ---
lang = st.sidebar.selectbox("🌍 Langue / اللغة", ["fr", "ar"], index=0)
t = lambda key: key  # Ici tu peux remplacer par ta fonction de traduction

st.title(t("Mouvements d'inventaire"))

# --- Formulaire ajout mouvement ---
with st.form("movement_form", clear_on_submit=True):
    product = st.text_input(t("Nom du produit"))
    depot = st.selectbox(t("Dépôt"), ["Dépôt 1", "Dépôt 2"])
    movement_type = st.selectbox(t("Type de mouvement"), ["Entrée", "Sortie"])
    quantity = st.number_input(t("Quantité"), min_value=1, step=1)
    price = st.number_input(t("Prix unitaire (TND)"), min_value=0.01, format="%.2f")
    date = st.date_input(t("Date"), value=datetime.today())
    submitted = st.form_submit_button(t("Ajouter"))

    if submitted:
        if not product.strip():
            st.error(t("Veuillez saisir un nom de produit."))
        else:
            cursor.execute("""
            INSERT INTO inventory_movements (product, depot, movement_type, quantity, price, date)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (product.strip(), depot, movement_type.lower(), quantity, price, date.strftime("%Y-%m-%d")))
            conn.commit()
            st.success(t(f"Mouvement '{movement_type}' ajouté pour {product}."))

# --- Affichage historique ---
st.header(t("Historique des mouvements"))

query = """
SELECT rowid, product, depot, movement_type, quantity, price, date
FROM inventory_movements
ORDER BY date DESC
"""
df = pd.read_sql_query(query, conn, parse_dates=["date"])

if df.empty:
    st.info(t("Aucun mouvement enregistré."))
else:
    # Calculer jours passés en dépôt (pour simplifier on calcule durée moyenne par produit et dépôt)
    # On doit d'abord pivoter les données pour avoir entrées et sorties côte à côte

    # Exemple simple : liste des entrées
    entries = df[df["movement_type"] == "entrée"]
    exits = df[df["movement_type"] == "sortie"]

    # Merge entrées/sorties sur product + depot pour approx durée
    merged = pd.merge(entries, exits, on=["product", "depot"], suffixes=("_entry", "_exit"))

    merged["days_in_depot"] = (merged["date_exit"] - merged["date_entry"]).dt.days
    merged.loc[merged["days_in_depot"] < 0, "days_in_depot"] = None  # Pas de négatif

    st.subheader(t("Détails des mouvements avec durée en dépôt"))
    st.dataframe(merged[[
        "product", "depot", "quantity_entry", "date_entry", "quantity_exit", "date_exit", "days_in_depot"
    ]])

    # Résumé stock total par dépôt
    st.subheader(t("Résumé du stock par dépôt"))

    # Stock = total entrées - total sorties par produit et dépôt
    stock_entries = entries.groupby(["depot", "product"])["quantity"].sum().reset_index(name="qty_entry")
    stock_exits = exits.groupby(["depot", "product"])["quantity"].sum().reset_index(name="qty_exit")

    stock = pd.merge(stock_entries, stock_exits, on=["depot", "product"], how="left")
    stock["qty_exit"] = stock["qty_exit"].fillna(0)
    stock["stock"] = stock["qty_entry"] - stock["qty_exit"]

    st.dataframe(stock[["depot", "product", "stock"]])

    # Lien vers page achats (supposons page "achat_vente" dans app)
    st.markdown("### Liens vers achats")
    for prod in stock["product"].unique():
        st.markdown(f"- [{prod}](#)  <!-- Remplacer '#' par le lien réel de la page achat/vente -->")

    # --- Export Excel ---
    def to_excel(df):
        import io
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)
        return output.getvalue()

    excel_data = to_excel(df)
    st.download_button(
        label=t("Télécharger l'historique Excel"),
        data=excel_data,
        file_name=f"inventory_movements_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # --- Export PDF ---
    def to_pdf(dataframe):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, "Historique des mouvements", ln=True, align="C")
        pdf.ln(5)

        for _, row in dataframe.iterrows():
            line = (
                f"{row['date'].strftime('%Y-%m-%d')} | "
                f"{row['product']} | "
                f"{row['depot']} | "
                f"{row['movement_type']} | "
                f"Qté: {row['quantity']} | "
                f"Prix: {row['price']:.2f} TND"
            )
            pdf.cell(0, 8, line, ln=True)

        return pdf.output(dest='S').encode('latin1')

    pdf_data = to_pdf(df)
    st.download_button(
        label=t("Télécharger l'historique PDF"),
        data=pdf_data,
        file_name=f"inventory_movements_{datetime.now().strftime('%Y-%m-%d')}.pdf",
        mime="application/pdf"
    )

conn.close()

