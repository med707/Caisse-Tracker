import os
import shutil
from datetime import datetime

# Dossier des sauvegardes
BACKUP_DIR = "backups"
DB_FILE = "supermarket.db"

# Crée une sauvegarde de la base de données
def create_backup():
    if not os.path.exists(DB_FILE):
        return False

    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"backup_{timestamp}.db"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)

    shutil.copy2(DB_FILE, backup_path)
    return True

# Restaure la dernière sauvegarde disponible
def restore_latest_backup():
    if not os.path.exists(BACKUP_DIR):
        return False

    backups = [f for f in os.listdir(BACKUP_DIR) if f.endswith(".db")]
    if not backups:
        return False

    # Trouve la sauvegarde la plus récente
    latest_backup = max(backups, key=lambda f: os.path.getctime(os.path.join(BACKUP_DIR, f)))
    latest_backup_path = os.path.join(BACKUP_DIR, latest_backup)

    shutil.copy2(latest_backup_path, DB_FILE)
    return True
