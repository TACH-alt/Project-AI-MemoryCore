import os
import time
import subprocess
import glob
from datetime import datetime

# CONFIGURATION
OBSIDIAN_SESSIONS = r"C:\Users\Legend\Desktop\Obsidian\Legendary\01-Sessions"
WORKER_SCRIPT = r"C:\Users\Legend\Documents\Claude\Projects\MemoryCore\orchestration\scripts\ask-worker.py"
PROCESSED_LOG = r"C:\Users\Legend\Documents\Claude\Projects\MemoryCore\orchestration\state\processed_handoffs.log"

def get_unprocessed_handoffs():
    # Find all files starting with HANDOFF-
    handoffs = glob.glob(os.path.join(OBSIDIAN_SESSIONS, "HANDOFF-*.md"))
    
    # Check against log
    processed = []
    if os.path.exists(PROCESSED_LOG):
        with open(PROCESSED_LOG, 'r') as f:
            processed = f.read().splitlines()
    
    unprocessed = [f for f in handoffs if f not in processed]
    return unprocessed

def mark_as_processed(filepath):
    with open(PROCESSED_LOG, 'a') as f:
        f.write(filepath + "\n")

def process_handoff(filepath):
    print(f"\n[🚀 AUTOMATION] New Handoff Detected: {os.path.basename(filepath)}")
    
    # Read the file to get the prompt/task
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Basic logic: Use the whole content as the prompt for the worker
        # We target "Legend" as the default high-context worker for handoffs
        title = os.path.basename(filepath).replace(".md", "")
        
        print(f"[🤖] Delegating to Legend via 9Router...")
        
        # Call the worker script
        cmd = [
            "python", 
            WORKER_SCRIPT, 
            "--prompt", content, 
            "--agent", "Legend", 
            "--title", f"Result-{title}", 
            "--folder", "02-Gemini-Outputs"
        ]
        
        subprocess.run(cmd)
        
        # Mark as processed so we don't run it again
        mark_as_processed(filepath)
        print(f"[✅] Handoff Complete. Result saved to Obsidian.")
        
    except Exception as e:
        print(f"[❌] Error processing handoff: {e}")

if __name__ == "__main__":
    print("==========================================")
    print("   LEGEND'S AUTO-HANDOFF WATCHER v1.0")
    print("   Monitoring Obsidian for Claude signals...")
    print("==========================================")
    
    # Ensure log exists
    if not os.path.exists(os.path.dirname(PROCESSED_LOG)):
        os.makedirs(os.path.dirname(PROCESSED_LOG))
        
    while True:
        try:
            new_tasks = get_unprocessed_handoffs()
            for task in new_tasks:
                process_handoff(task)
            
            time.sleep(5) # Check every 5 seconds
        except KeyboardInterrupt:
            print("\nStopping Watcher...")
            break
        except Exception as e:
            print(f"Watcher Error: {e}")
            time.sleep(10)
