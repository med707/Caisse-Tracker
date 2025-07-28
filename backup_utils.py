import os
import shutil
from datetime import datetime

BACKUP_FOLDER = "backups"

def ensure_backup_folder():
    """Créer le dossier backups s'il n'existe pas."""
    os.makedirs(BACKUP_FOLDER, exist_ok=True)

def create_backup(db_file="supermarket.db"):
    """
    Crée une copie de sauvegarde horodatée de la base de données.
    """
    ensure_backup_folder()
    if os.path.exists(db_file):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(BACKUP_FOLDER, f"backup_supermarket_{timestamp}.db")
        shutil.copy(db_file, backup_file)
        print(f"✅ Backup created: {backup_file}")
        return backup_file
    else:
        print("⚠️ Database file not found, backup not created.")
        return None

def list_backups():
    """
    Liste les fichiers de sauvegarde existants, triés du plus récent au plus ancien.
    """
    ensure_backup_folder()
    backups = [f for f in os.listdir(BACKUP_FOLDER) if f.startswith("backup_supermarket_") and f.endswith(".db")]
    backups.sort(reverse=True)
    return backups

def restore_backup(filename, db_file="supermarket.db"):
    """
    Restaure la base de données depuis un fichier de sauvegarde précis.
    """
    backup_path = os.path.join(BACKUP_FOLDER, filename)
    if not os.path.exists(backup_path):
        print(f"❌ Backup file {filename} not found.")
        return False
    try:
        shutil.copy(backup_path, db_file)
        print(f"✅ Restored database from backup: {filename}")
        return True
    except Exception as e:
        print(f"❌ Error restoring backup: {e}")
        return False

def restore_latest_backup(db_file="supermarket.db"):
    """
    Restaure la base de données depuis la dernière sauvegarde disponible.
    """
    backups = list_backups()
    if not backups:
        print("⚠️ No backups found.")
        return False
    latest_backup = backups[0]
    return restore_backup(latest_backup, db_file=db_file)

