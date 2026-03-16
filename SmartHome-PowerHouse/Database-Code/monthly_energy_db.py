import os
import time
import json
import firebase_admin
from firebase_admin import credentials, firestore
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv
from datetime import datetime
from hashlib import sha256

# Load environment variable
load_dotenv()

def initialize_firestore():
    # Firebase configuration for monthly energy data
    config = {
        "type": "service_account",
        "project_id": os.getenv("FIREBASE_PROJECT_ID"),
        "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace("\\n", "\n"),
        "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
        "token_uri": "https://oauth2.googleapis.com/token"
    }
    if not firebase_admin._apps:
        cred = credentials.Certificate(config)
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = initialize_firestore()

# Define path to monthly energy JSON file
JSON_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend/energy/monthly_energy.json"))
last_hash = None  # To track changes via hash

def convert_ts(ts):
    """Convert ISO timestamp string to datetime object."""
    return datetime.fromisoformat(ts.replace("Z", ""))

def hash_file_content(path):
    """Return SHA256 hash for the file's content."""
    with open(path, "r") as f:
        return sha256(f.read().encode()).hexdigest()

def update_firestore():
    """Update Firestore 'MonthlyEnergy' collection when JSON file changes."""
    global last_hash
    if not os.path.exists(JSON_FILE_PATH):
        print(f"Error: {JSON_FILE_PATH} not found.")
        return
    new_hash = hash_file_content(JSON_FILE_PATH)
    if new_hash == last_hash:
        return
    last_hash = new_hash

    with open(JSON_FILE_PATH, "r") as f:
        data = json.load(f)

    batch = db.batch()
    changes = False

    # Process each entry and update Firestore accordingly
    for idx, entry in enumerate(data, start=1):
        doc_id = str(idx)
        new_doc = {
            "id": idx,
            "timestamp": convert_ts(entry["timestamp"]),
            "power_usage": entry["power_usage"]
        }
        ref = db.collection("MonthlyEnergy").document(doc_id)
        snap = ref.get()
        if not snap.exists:
            batch.set(ref, new_doc)
            changes = True
        else:
            if snap.to_dict().get("power_usage") != new_doc["power_usage"]:
                batch.update(ref, {"power_usage": new_doc["power_usage"]})
                changes = True

    if changes:
        batch.commit()
        print("Monthly Energy DB updated.")

# Event handler for monthly energy JSON file modifications
class MonthlyEnergyHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith("monthly_energy.json"):
            update_firestore()

def start_watcher():
    """Start the observer to watch monthly energy JSON file."""
    if not os.path.exists(JSON_FILE_PATH):
        print(f"Error: {JSON_FILE_PATH} not found.")
        return
    observer = Observer()
    observer.schedule(MonthlyEnergyHandler(), path=os.path.dirname(JSON_FILE_PATH), recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    update_firestore()  # Initial update
    start_watcher()     # Begin file monitoring
