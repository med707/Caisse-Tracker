import os
import shutil
from datetime import datetime

BACKUP_DIR = "backups"
DB_FILE = "supermarket.db"

def create_backup():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"{BACKUP_DIR}/supermarket_backup_{timestamp}.db"
    shutil.copy2(DB_FILE, backup_filename)
    return backup_filename

def restore_latest_backup():
    if not os.path.exists(BACKUP_DIR):
        return False
    backups = sorted([f for f in os.listdir(BACKUP_DIR) if f.endswith(".db")], reverse=True)
    if backups:
        latest_backup = backups[0]
        shutil.copy2(os.path.join(BACKUP_DIR, latest_backup), DB_FILE)
        return True
    return False

