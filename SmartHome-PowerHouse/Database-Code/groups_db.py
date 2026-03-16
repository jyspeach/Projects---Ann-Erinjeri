import os
import json
import time
import firebase_admin
from firebase_admin import credentials, firestore
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv

# Load environment variable
load_dotenv()

def initialize_firestore():
    # Firebase configuration for groups
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

# Path to the users JSON file, which contains group information
JSON_FILE_PATH = os.path.join(os.path.dirname(__file__), "users_db.json")

def add_device_groups():
    """Create or update device group documents in Firestore using a unique doc ID format."""
    if not os.path.exists(JSON_FILE_PATH):
        print(f"Error: {JSON_FILE_PATH} not found.")
        return
    with open(JSON_FILE_PATH, "r") as f:
        data = json.load(f)
    changes = False
    # Iterate through each user and process their device groups
    for user in data.get("users", []):
        uid = str(user["user_id"])
        user_ref = db.collection("Profile").document(uid)
        # Skip users without device groups
        if "device_groups" not in user:
            continue
        for group in user["device_groups"]:
            # Create a unique document ID by combining user ID and group ID (e.g., "1-2")
            doc_id = f"{uid}-{group['id']}"
            # Convert device IDs to Firestore document references
            refs = [db.collection("Device").document(str(d)) for d in group["devices"]]
            group_data = {
                "user-group_id": doc_id,  # Store the unique ID in this field
                "name": group["name"],
                "status": group["status"],
                "devices": refs,
                "user": user_ref
            }
            db.collection("DeviceGroup").document(doc_id).set(group_data)
            changes = True
    if changes:
        print("Groups DB updated.")

# Event handler for changes in the users JSON file
class GroupsHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith("users_db.json"):
            add_device_groups()

def watch_groups():
    """Start observer to monitor the users JSON file for group changes."""
    observer = Observer()
    observer.schedule(GroupsHandler(), path=os.path.dirname(JSON_FILE_PATH), recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    add_device_groups()  # Initial sync of groups
    watch_groups()       # Start file monitoring
