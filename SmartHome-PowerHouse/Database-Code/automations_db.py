import os
import json
import time
import firebase_admin
from firebase_admin import credentials, firestore
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv

# Load environment variable from .env file
load_dotenv()

def initialize_firestore():
    # Firebase configuration for automations
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

# Path to the automations JSON file
JSON_FILE_PATH = os.path.join(os.path.dirname(__file__), "../backend/automations.json")

def get_existing_automations():
    """Return a set of existing automation document IDs from Firestore."""
    return {doc.id for doc in db.collection("Automation").stream()}

def set_automations_data():
    """Sync Firestore 'Automation' collection with data from the JSON file."""
    if not os.path.exists(JSON_FILE_PATH):
        print(f"Error: {JSON_FILE_PATH} not found.")
        return
    with open(JSON_FILE_PATH, "r") as f:
        data = json.load(f)
    existing = get_existing_automations()
    enabled = {}
    # Process each automation entry
    for a in data.get("automations", []):
        if not a.get("enabled", False):
            continue  # Skip disabled automations
        aid = str(a["id"])
        d_ids = a["device_id"]
        if not isinstance(d_ids, list):
            d_ids = [d_ids]
        # Convert device IDs to Firestore document references
        refs = [db.collection("Device").document(str(d)) for d in d_ids]
        enabled[aid] = {
            "id": a["id"],
            "name": a["name"],
            "device_ids": refs,
            "triggers": a["triggers"],
            "status": a["status"]
        }
    changes = False
    # Update or add automations that are new or have changed
    for aid, adata in enabled.items():
        ref = db.collection("Automation").document(aid)
        snap = ref.get()
        if not snap.exists or snap.to_dict() != adata:
            db.collection("Automation").document(aid).set(adata)
            changes = True
    # Delete automations that are no longer enabled
    for aid in existing:
        if aid not in enabled:
            db.collection("Automation").document(aid).delete()
            changes = True
    if changes:
        print("Automations DB updated.")

# Custom event handler for automations file changes
class AutomationsHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith("automations.json"):
            set_automations_data()

def watch_automations():
    """Start observer to watch automations JSON file."""
    observer = Observer()
    observer.schedule(AutomationsHandler(), path=os.path.dirname(JSON_FILE_PATH), recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    set_automations_data()  # Initial sync
    watch_automations()     # Begin file monitoring
