import os
import subprocess

def main():
    
    scripts = [
        "daily_energy_db.py",
        "automations_db.py",
        "devices_db.py",
        "energy_goal_db.py",
        "groups_db.py",
        "monthly_energy_db.py",
        "users_db.py"
    ]
    
    current_dir = os.path.dirname(__file__)
    processes = []

    
    for script in scripts:
        script_path = os.path.join(current_dir, script)
        
        if os.path.isfile(script_path):
            print(f"Running {script} in parallel...")
            # Launching in parallel (non-blocking)
            process = subprocess.Popen(["python", script_path])
            processes.append(process)
        else:
            print(f"Script not found: {script_path}")

    # Waiting for all processes to finish
    for process in processes:
        process.wait()

    print("All scripts have finished execution.")

if __name__ == "__main__":
    main()

    
    
 