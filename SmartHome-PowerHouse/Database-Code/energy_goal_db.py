import os
import time
import json
import firebase_admin
from firebase_admin import credentials, firestore
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv
from hashlib import sha256

# Load environment variable
load_dotenv()

def initialize_firestore():
    # Firebase configuration for Energy Goal
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

# Path to the energy goal JSON file
JSON_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend/energy/energy_goal.json"))
last_hash = None  # Track changes with hash

def hash_file_content(path):
    """Return SHA256 hash of file content."""
    with open(path, "r") as f:
        return sha256(f.read().encode()).hexdigest()

def update_firestore():
    """Update Firestore 'EnergyGoal' document if file changes."""
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

    doc_id = "1"  # Only one document is used for energy goal
    new_doc = {"goal_value": data["goal_value"]}
    ref = db.collection("EnergyGoal").document(doc_id)
    snap = ref.get()
    changes = False
    if not snap.exists:
        ref.set(new_doc)
        changes = True
    else:
        if snap.to_dict().get("goal_value") != new_doc["goal_value"]:
            ref.update(new_doc)
            changes = True

    if changes:
        print("Energy Goal DB updated.")

# Event handler for changes in energy_goal.json
class EnergyGoalHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith("energy_goal.json"):
            update_firestore()

def start_watcher():
    """Start watching the energy goal JSON file for changes."""
    if not os.path.exists(JSON_FILE_PATH):
        print(f"Error: {JSON_FILE_PATH} not found.")
        return
    observer = Observer()
    observer.schedule(EnergyGoalHandler(), path=os.path.dirname(JSON_FILE_PATH), recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    update_firestore()  # Initial sync
    start_watcher()     # Start monitoring file changes
