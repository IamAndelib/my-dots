#!/usr/bin/env python3
import subprocess
import json
import os
import time
from collections import defaultdict

def get_current_workspace():
    result = subprocess.run(["hyprctl", "activeworkspace", "-j"], capture_output=True, text=True)
    data = json.loads(result.stdout)
    return str(data["id"])

def get_clients():
    result = subprocess.run(["hyprctl", "clients", "-j"], capture_output=True, text=True)
    return json.loads(result.stdout)

def close_window(address):
    subprocess.run(["hyprctl", "dispatch", "closewindow", f"address:{address}"])
    time.sleep(0.2)

def force_kill(pid):
    try:
        os.kill(pid, 0)
        os.kill(pid, 9)
    except Exception:
        pass

def is_magic_workspace(ws_id):
    """Check if workspace ID represents a magic workspace (negative ID)"""
    try:
        return int(ws_id) < 0
    except (ValueError, TypeError):
        return False

def main():
    current_ws = get_current_workspace()
    print(f"Current workspace: {current_ws}")
    
    preserve_pids = defaultdict(int)
    preserve_classes = defaultdict(int)
    
    print("Identifying processes to preserve on current workspace and magic workspaces...")
    clients = get_clients()
    
    for client in clients:
        ws_id = str(client.get("workspace", {}).get("id"))
        pid = client.get("pid")
        cls = client.get("class")
        
        if not ws_id or ws_id == "null":
            continue
            
        # Preserve processes on current workspace OR magic workspaces
        if ws_id == current_ws or is_magic_workspace(ws_id):
            preserve_pids[pid] = 1
            preserve_classes[cls] = 1
            if is_magic_workspace(ws_id):
                print(f"Preserving {cls} (PID: {pid}) on magic workspace {ws_id}")
    
    print("Processing windows for closure...")
    for client in clients:
        address = client.get("address")
        ws_id = str(client.get("workspace", {}).get("id"))
        pid = client.get("pid")
        cls = client.get("class")
        
        print(f"Checking window {cls} (PID: {pid}) on workspace {ws_id}")
        
        if not ws_id or ws_id == "null":
            print("Skipping window with null/empty workspace")
            continue
            
        # Skip magic workspaces entirely
        if is_magic_workspace(ws_id):
            print(f"Skipping magic workspace {ws_id}")
            continue
            
        # Skip current workspace
        if ws_id == current_ws:
            continue
            
        # Close windows on other regular workspaces
        print(f"Closing {cls} (PID: {pid}) on workspace {ws_id}")
        close_window(address)
        
        should_kill = True
        
        # Don't kill if PID is also used on current workspace or magic workspaces
        if preserve_pids.get(pid):
            print(f"Not killing PID {pid} - also used on current workspace or magic workspace")
            should_kill = False
        
        # Handle shared applications (browsers, etc.)
        shared_apps = {
            "chrome": ["chrome", "Chrome", "chromium", "Chromium"],
            "firefox": ["firefox", "Firefox"],
            "edge": ["edge", "Edge"]
        }
        
        for variants in shared_apps.values():
            if any(v in cls for v in variants):
                if any(preserve_classes.get(v) for v in variants):
                    print(f"Not killing {cls} process - instance exists on current workspace or magic workspace")
                    should_kill = False
                break
        
        if should_kill:
            print(f"Process {pid} still running, force killing...")
            force_kill(pid)
    
    print("Finished processing windows on other workspaces")

if __name__ == "__main__":
    main()
