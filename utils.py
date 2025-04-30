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
    caffeine_enabled = False

    try:
        # Check if caffeine extension is installed
        extensions = subprocess.check_output(["gsettings", "get", "org.gnome.shell", "enabled-extensions"], text=True)
        if "'caffeine@patapon.info'" in extensions:
            # Enable caffeine extension
            subprocess.run(["gdbus", "call", "--session", "--dest", "org.gnome.Shell",
                            "--object-path", "/org/gnome/Shell/Extensions/Caffeine",
                            "--method", "org.gnome.Shell.Extensions.Caffeine.SetActive", "true"])
            caffeine_enabled = True
            print("☕ Caffeine enabled to prevent sleep.")
        else:
            # Backup original value and disable screen lock
            original_lock = subprocess.check_output([
                "gsettings", "get", "org.gnome.desktop.screensaver", "lock-enabled"
            ], text=True).strip()
            os.environ["GNOME_SCREEN_LOCK_BACKUP"] = original_lock
            subprocess.run([
                "gsettings", "set", "org.gnome.desktop.screensaver", "lock-enabled", "false"
            ])
            print("🔒 Screen lock disabled temporarily.")
    except Exception as e:
        print(f"⚠️ Failed to inhibit sleep: {e}")

    class Inhibitor:
        def terminate(self):
            if caffeine_enabled:
                subprocess.run(["gdbus", "call", "--session", "--dest", "org.gnome.Shell",
                                "--object-path", "/org/gnome/Shell/Extensions/Caffeine",
                                "--method", "org.gnome.Shell.Extensions.Caffeine.SetActive", "false"])
                print("☕ Caffeine disabled.")
            else:
                # Restore previous screen lock setting
                original = os.environ.get("GNOME_SCREEN_LOCK_BACKUP", "true")
                subprocess.run([
                    "gsettings", "set", "org.gnome.desktop.screensaver", "lock-enabled", original
                ])
                print("🔒 Screen lock restored.")

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

def get_distro_version(distro):
    try:
        if distro == "fedora":
            import re
            with open("/etc/os-release") as f:
                match = re.search(r'VERSION_ID="?(\d+)"?', f.read())
                return match.group(1) if match else "Unknown"
        elif distro == "nixos":
            with open("/etc/os-release") as f:
                for line in f:
                    if line.startswith("VERSION="):
                        return line.split("=")[1].strip().strip('"')
        elif distro == "debian":
            return subprocess.check_output(["lsb_release", "-r", "-s"], text=True).strip()
        elif distro == "nobara":
            with open("/etc/nobara-release") as f:
                return f.read().strip()
        elif distro in ["bazzite", "vauxite"]:
            return "rolling"
        else:
            return "Unknown"
    except Exception:
        return "Unknown"
