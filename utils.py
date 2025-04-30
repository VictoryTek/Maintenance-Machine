import subprocess
import logging
import os
import re

LAST_ACTION_FILE = os.path.expanduser("~/.maintenance_tool_last_action")
LOG_PATH = os.path.expanduser("~/maintenance_tool.log")

logging.basicConfig(filename=LOG_PATH, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def log_action(action, level="info"):
    getattr(logging, level)(action)

def save_last_action(action):
    with open(LAST_ACTION_FILE, "w") as f:
        f.write(action)

def load_last_action():
    if os.path.exists(LAST_ACTION_FILE):
        with open(LAST_ACTION_FILE, "r") as f:
            return f.read().strip()
    return None

def inhibit_sleep():
    return subprocess.Popen(["systemd-inhibit", "--what=idle:sleep:shutdown", "--why=Maintenance in progress", "sleep", "infinity"])

def detect_distro():
    try:
        with open("/etc/os-release") as f:
            data = f.read().lower()
            if "vauxite" in data:
                return "vauxite"
            if "bazzite" in data:
                return "bazzite"
            if "fedora" in data:
                return "fedora"
            if "debian" in data:
                return "debian"
            if "nixos" in data:
                return "nixos"
    except FileNotFoundError:
        pass
    return "unknown"

def get_fedora_version():
    try:
        with open("/etc/fedora-release") as f:
            return int(re.search(r"(\d+)", f.read()).group(1))
    except Exception:
        return 0
