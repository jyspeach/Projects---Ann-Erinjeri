import os
import json
import time
import bcrypt
import firebase_admin
from firebase_admin import credentials, firestore
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv

# Load environment variablesfrom .env file
load_dotenv()

def initialize_firestore():
    # Set up Firebase configuration using environment variables
    config = {
        "type": "service_account",
        "project_id": os.getenv("FIREBASE_PROJECT_ID"),
        "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace("\\n", "\n"),
        "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
        "token_uri": "https://oauth2.googleapis.com/token"
    }
    # Initialize Firebase Admin SDK if not already done
    if not firebase_admin._apps:
        cred = credentials.Certificate(config)
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = initialize_firestore()

# Define the path to the users JSON file
JSON_FILE_PATH = os.path.join(os.path.dirname(__file__), "../database/users_db.json")

def hash_password(pw):
    """Hash a plain text password using bcrypt."""
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

def get_existing_users():
    """Return a dictionary of existing users from Firestore."""
    return {doc.id: doc.to_dict() for doc in db.collection("Profile").stream()}

def set_users_data():
    """Sync Firestore 'Profile' collection with users data from JSON file."""
    if not os.path.exists(JSON_FILE_PATH):
        print(f"Error: {JSON_FILE_PATH} not found.")
        return

    with open(JSON_FILE_PATH, "r") as f:
        data = json.load(f)

    existing = get_existing_users()
    users = {}
    # Process each user from the JSON data
    for u in data.get("users", []):
        uid = str(u["user_id"])
        new_pw = u["user_password"]
        # Preserve existing password hash if the password hasn't changed
        if uid in existing and bcrypt.checkpw(new_pw.encode(), existing[uid]["user_password"].encode()):
            hpw = existing[uid]["user_password"]
        else:
            hpw = hash_password(new_pw)
        # Convert allocated device IDs to Firestore document references
        devices = [db.collection("Device").document(str(d)) for d in u.get("allocated_devices", [])]
        users[uid] = {
            "user_id": u["user_id"],
            "user_name": u["user_name"],
            "user_password": hpw,
            "allocated_devices": devices,
            "user_role": u["user_role"]
        }

    changes = False
    # Add or update users in Firestore if there are any differences
    for uid, udata in users.items():
        if uid not in existing or existing[uid] != udata:
            db.collection("Profile").document(uid).set(udata)
            changes = True

    # Delete users that no longer exist in the JSON
    for uid in list(existing.keys()):
        if uid not in users:
            db.collection("Profile").document(uid).delete()
            changes = True

    if changes:
        print("Users DB updated.")

# Custom file event handler for the users JSON file
class UsersHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith("users_db.json"):
            set_users_data()

def watch_users():
    """Start the observer to watch the users JSON file for changes."""
    observer = Observer()
    observer.schedule(UsersHandler(), path=os.path.dirname(JSON_FILE_PATH), recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    set_users_data()  # Initial sync
    watch_users()     # Start watching for file modifications
