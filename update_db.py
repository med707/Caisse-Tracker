import sqlite3

# Connexion à la base
conn = sqlite3.connect("supermarket.db")
cursor = conn.cursor()

# Colonnes à vérifier
required_columns = {
    "purchase_price": "REAL",
    "sale_price": "REAL"
}

# Récupérer les colonnes existantes
cursor.execute("PRAGMA table_info(purchases)")
existing_columns = [col[1] for col in cursor.fetchall()]

# Ajouter les colonnes manquantes
for col, col_type in required_columns.items():
    if col not in existing_columns:
        cursor.execute(f"ALTER TABLE purchases ADD COLUMN {col} {col_type}")
        print(f"✅ Colonne '{col}' ajoutée.")

conn.commit()
conn.close()
print("✅ Mise à jour terminée.")
