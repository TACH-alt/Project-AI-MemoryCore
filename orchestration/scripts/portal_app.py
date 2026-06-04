import os
import json
import httpx
import subprocess
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import uuid

# CONFIGURATION
OBSIDIAN_VAULT = r"C:\Users\Legend\Desktop\Obsidian\Legendary"
STATE_FILE = r"C:\Users\Legend\Documents\Claude\Projects\MemoryCore\orchestration\state\orchestration-state.json"
ROUTER_URL = "http://10.10.10.2:20128/v1"
MEMORY_CORE_SESSION = r"C:\Users\Legend\Project-AI-MemoryCore\main\current-session.md"
AI_PROCESS_NAMES = ["gemini.exe", "notebooklm-mcp.exe", "python.exe", "node.exe", "cmd.exe", "powershell.exe"]

app = FastAPI(title="Legend Syndicate Portal")

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_active_processes():
    try:
        output = subprocess.check_output("tasklist /FI \"STATUS eq RUNNING\"", shell=True).decode()
        active = []
        for name in AI_PROCESS_NAMES:
            if name.lower() in output.lower():
                active.append(name)
        return active
    except:
        return []

def get_recent_files(limit=8):
    files = []
    for root, _, filenames in os.walk(OBSIDIAN_VAULT):
        for f in filenames:
            if f.endswith(".md") and ".obsidian" not in root:
                path = os.path.join(root, f)
                files.append({
                    "name": f,
                    "rel_path": os.path.relpath(path, OBSIDIAN_VAULT),
                    "mtime": os.path.getmtime(path)
                })
    files.sort(key=lambda x: x["mtime"], reverse=True)
    return files[:limit]

def check_9router():
    try:
        with httpx.Client(timeout=1.0) as client:
            response = client.get(f"{ROUTER_URL}/models")
            return response.status_code == 200
    except:
        return False

def read_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {"active_agent": "None", "last_model_used": "None"}

@app.get("/", response_class=HTMLResponse)
async def get_index():
    ui_path = r"C:\Users\Legend\Documents\Claude\Projects\MemoryCore\orchestration\ui\index.html"
    with open(ui_path, 'r', encoding='utf-8') as f:
        return f.read()

@app.get("/api/status")
async def get_status():
    router_online = check_9router()
    active_procs = get_active_processes()
    state = read_state()
    return {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "router_online": router_online,
        "active_processes": active_procs,
        "active_agent": state.get("active_agent", "Idle"),
        "last_model": state.get("last_model_used", "None"),
        "status_text": "ACTIVE" if active_procs else "STANDBY"
    }

@app.get("/api/recent_files")
async def recent_files():
    return get_recent_files()

@app.post("/api/execute")
async def execute_task(request: Request):
    data = await request.json()
    prompt = data.get("prompt")
    agent = data.get("agent", "Legend")
    title = data.get("title", "portal-task")
    
    # We trigger the existing .bat scripts
    script_path = r"C:\Users\Legend\Documents\Claude\Projects\MemoryCore\orchestration\scripts"
    bat_name = "ask-gemini.bat" if agent == "Legend" else "ask-chatgpt.bat"
    full_path = os.path.join(script_path, bat_name)
    
    # Run in background
    subprocess.Popen([full_path, prompt, title, "02-Gemini-Outputs"], shell=True)
    
    return {"status": "Execution started", "agent": agent}

if __name__ == "__main__":
    # Run on 0.0.0.0 to be accessible on local network
    uvicorn.run(app, host="0.0.0.0", port=30001)
