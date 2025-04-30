import subprocess
import logging
import os
import re
import ast
import shutil

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
    fallback_used = False

    def disable_screen_lock():
        subprocess.run([
            "gsettings", "set",
            "org.gnome.desktop.screensaver",
            "lock-enabled", "false"
        ])
        print("🔒 Automatic screen lock disabled.")

    def enable_screen_lock():
        subprocess.run([
            "gsettings", "set",
            "org.gnome.desktop.screensaver",
            "lock-enabled", "true"
        ])
        print("🔒 Automatic screen lock re-enabled.")

    def toggle_caffeine(enable=True):
        action = "Toggle" if enable else "Toggle"  # No direct "disable", just toggle
        try:
            subprocess.run([
                "gdbus", "call", "--session",
                "--dest", "org.gnome.Shell.Extensions.Caffeine",
                "--object-path", "/org/gnome/Shell/Extensions/Caffeine",
                "--method", f"org.gnome.Shell.Extensions.Caffeine.{action}"
            ], check=True)
            print(f"☕ Caffeine {'enabled' if enable else 'disabled'}.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Failed to toggle Caffeine: {e}")
            return False

    if shutil.which("gdbus"):
        success = toggle_caffeine(True)
        if not success:
            disable_screen_lock()
            fallback_used = True
    else:
        disable_screen_lock()
        fallback_used = True

    class Inhibitor:
        def terminate(self):
            if fallback_used:
                enable_screen_lock()
            else:
                toggle_caffeine(False)

    return Inhibitor()

def detect_distro():
    try:
        with open("/etc/os-release") as f:
            os_info = f.read().lower()
            if "nobara" in os_info:
                return "nobara"
            elif "fedora" in os_info:
                return "fedora"
            elif "nixos" in os_info:
                return "nixos"
            elif "debian" in os_info:
                return "debian"
            elif "bazzite" in os_info:
                return "bazzite"
            elif "vauxite" in os_info:
                return "vauxite"
    except:
        pass
    return "unknown"

def get_distro_version(distro: str) -> str:
    if distro == "nixos":
        try:
            result = subprocess.check_output(["nixos-version"], text=True).strip()
            # This returns something like: "24.05pre5678.abcd1234"
            version = result.split()[0]  # Just take the first segment
            return version
        except Exception as e:
            print(f"⚠️ Failed to detect NixOS version: {e}")
            return "Unknown"
    elif distro == "fedora":
        return get_fedora_version()
    elif distro == "debian":
        try:
            return subprocess.check_output(["lsb_release", "-r"], text=True).strip().split(":")[1].strip()
        except Exception:
            return "Unknown"
    elif distro in ["bazzite", "vauxite", "nobara"]:
        return "Rolling"
    else:
        return "Unknown"