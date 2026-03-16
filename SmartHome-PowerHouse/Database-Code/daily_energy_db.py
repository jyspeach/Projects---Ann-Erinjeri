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
    # Firebase configuration setup using .env variables
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

# Path to the daily energy JSON file
JSON_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend/energy/daily_energy.json"))
last_hash = None  # Used to track file changes

def convert_ts(ts):
    """Convert an ISO timestamp string to a datetime object."""
    return datetime.fromisoformat(ts.replace("Z", ""))

def hash_file_content(path):
    """Return SHA256 hash of the file content."""
    with open(path, "r") as f:
        return sha256(f.read().encode()).hexdigest()

def update_firestore():
    """Update Firestore 'DailyEnergy' collection if file content has changed."""
    global last_hash
    if not os.path.exists(JSON_FILE_PATH):
        print(f"Error: {JSON_FILE_PATH} not found.")
        return

    new_hash = hash_file_content(JSON_FILE_PATH)
    if new_hash == last_hash:
        return  # No change detected
    last_hash = new_hash

    with open(JSON_FILE_PATH, "r") as f:
        data = json.load(f)

    batch = db.batch()
    changes = False

    # Process each entry in the JSON file and prepare updates
    for idx, entry in enumerate(data, start=1):
        doc_id = str(idx)
        new_doc = {
            "id": idx,
            "timestamp": convert_ts(entry["timestamp"]),
            "power_usage": entry["power_usage"]
        }
        ref = db.collection("DailyEnergy").document(doc_id)
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
        print("Daily Energy DB updated.")

# File event handler for daily energy JSON changes
class DailyEnergyHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith("daily_energy.json"):
            update_firestore()

def start_watcher():
    """Start the observer to monitor changes to the daily energy JSON file."""
    if not os.path.exists(JSON_FILE_PATH):
        print(f"Error: {JSON_FILE_PATH} not found.")
        return
    observer = Observer()
    observer.schedule(DailyEnergyHandler(), path=os.path.dirname(JSON_FILE_PATH), recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    update_firestore()  # Run initial sync
    start_watcher()     # Begin watching for file modifications
