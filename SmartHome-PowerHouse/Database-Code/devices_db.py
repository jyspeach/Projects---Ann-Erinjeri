import os
import time
import json
import firebase_admin
from firebase_admin import credentials, firestore
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv
from hashlib import sha256

# Load environment variable from .env file
load_dotenv()

def initialize_firestore():
    # Create the Firebase configuration dictionary 
    config = {
        "type": "service_account",
        "project_id": os.getenv("FIREBASE_PROJECT_ID"),
        "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace("\\n", "\n"),
        "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
        "token_uri": "https://oauth2.googleapis.com/token"
    }
    # Initialize the Firebase Admin SDK if it is not already 
    if not firebase_admin._apps:
        cred = credentials.Certificate(config)
        firebase_admin.initialize_app(cred)
    # Return a Firestore client instance
    return firestore.client()

db = initialize_firestore()

# Define the relative path to the JSON file containing devices data
JSON_FILE_PATH = os.path.join(os.path.dirname(__file__), "../backend/devices.json")
last_json_hash = None  # Used to track changes in the file content

def hash_file_content(path):
    """Read file content and return its SHA256 hash to see if the file content has changed."""
    with open(path, "r") as f:
        content = f.read()
    return sha256(content.encode()).hexdigest()

def update_firestore():
    """Update Firestore 'Device' collection based on the JSON file changes."""
    global last_json_hash
    try:
        new_hash = hash_file_content(JSON_FILE_PATH)
    except Exception as e:
        print(f"Error reading {JSON_FILE_PATH}: {e}")
        return

    # If the file content hasn't changed, skip update
    if new_hash == last_json_hash:
        return
    last_json_hash = new_hash

    try:
        with open(JSON_FILE_PATH, "r") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading JSON data: {e}")
        return

    # Filter devices that are connected and keep only required fields
    filtered = [
        {k: d[k] for k in ["id", "name", "ip"]}
        for d in data.get("smart_home_devices", [])
        if d.get("connection_status") == "connected"
    ]

    # Get existing devices from Firestore
    existing = {doc.id: doc.to_dict() for doc in db.collection("Device").stream()}
    new_ids = {str(d["id"]) for d in filtered}
    changes = False

    # Add or update devices if changes are detected
    for d in filtered:
        did = str(d["id"])
        if did not in existing or existing[did] != d:
            db.collection("Device").document(did).set(d)
            changes = True

    # Delete devices that are no longer present in the JSON file
    for did in list(existing.keys()):
        if did not in new_ids:
            db.collection("Device").document(did).delete()
            changes = True

    if changes:
        print("Devices DB updated.")

# Custom event handler for file changes
class DevicesHandler(FileSystemEventHandler):
    def on_modified(self, event):
        # Trigger update only if the modified file is devices.json
        if event.src_path.endswith("devices.json"):
            update_firestore()

def start_watcher():
    """Start a file observer to watch for changes in the devices JSON file."""
    observer = Observer()
    observer.schedule(DevicesHandler(), path=os.path.dirname(JSON_FILE_PATH), recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    update_firestore()  # Initial update on startup (only prints if changes occur)
    start_watcher()     # Begin watching for file modifications
