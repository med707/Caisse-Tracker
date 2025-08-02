import sqlite3

conn = sqlite3.connect("supermarket.db")
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(purchases)")
columns = cursor.fetchall()  # liste des colonnes

# columns est une liste de tuples, chaque tuple = (cid, name, type, notnull, dflt_value, pk)
column_names = [col[1] for col in columns]

if "sale_price" in column_names:
    print("La colonne 'sale_price' existe déjà.")
else:
    print("La colonne 'sale_price' n'existe pas.")

conn.close()

