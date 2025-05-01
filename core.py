# Core - Maintenance Machine

from utils import log_action, save_last_action
import subprocess
import re
import urllib.request

def update_system(distro):
    log_action(f"Starting system update for {distro}")
    reboot_after = input("\nReboot after update? [y/N]: ").strip().lower() == "y"
    try:
        if distro == "fedora":
            subprocess.run(["sudo", "dnf", "upgrade", "--refresh", "-y"])
        elif distro == "nixos":
            subprocess.run(["sudo", "nix-channel", "--update"])
            subprocess.run(["sudo", "nixos-rebuild", "switch"])
        elif distro == "debian":
            subprocess.run(["sudo", "apt", "update"])
            subprocess.run(["sudo", "apt", "upgrade", "-y"])
        elif distro == "nobara":
            subprocess.run(["nobara-sync", "cli"])
        elif distro in ["bazzite", "vauxite"]:
            subprocess.run(["topgrade", "--yes"])
        else:
            raise Exception(f"Unsupported distribution: {distro}")

        log_action("System update completed")
        save_last_action("Update System")
        if reboot_after:
            subprocess.run(["sudo", "reboot"])
    except Exception as e:
        log_action(f"Update failed: {e}", level="error")
        print(f"⚠️ Update failed: {e}")

def version_upgrade(distro):
    log_action(f"Starting version upgrade for {distro}")
    try:
        if distro == "fedora":
            _fedora_upgrade()
        elif distro == "nixos":
            _nixos_upgrade()
        elif distro == "debian":
            _debian_upgrade()
        elif distro == "nobara":
            subprocess.run(["nobara-sync", "cli"])
            save_last_action("Version Upgrade")
        elif distro in ["bazzite", "vauxite"]:
            print(f"{distro.capitalize()} upgrades managed automatically.")
            log_action(f"{distro.capitalize()} upgrade skipped (automatic)")
        else:
            raise Exception(f"Unsupported distribution: {distro}")
    except Exception as e:
        log_action(f"Version upgrade failed: {e}", level="error")
        print(f"⚠️ Version upgrade failed: {e}")

def reboot_system():
    subprocess.run(["sudo", "reboot"])

def _fedora_upgrade():
    from utils import get_fedora_version
    current_version = get_fedora_version()
    next_version = current_version + 1
    confirm = input(f"Upgrade Fedora {current_version} → {next_version}? [y/N]: ").strip().lower()
    if confirm == "y":
        subprocess.run(["sudo", "dnf", "system-upgrade", "download", f"--releasever={next_version}", "-y"])
        subprocess.run(["sudo", "dnf", "system-upgrade", "reboot"])
        save_last_action("Version Upgrade")

def _nixos_upgrade():
    try:
        # Fetch the latest stable NixOS version from the official channels
        url = "https://channels.nixos.org/"
        with urllib.request.urlopen(url) as response:
            html = response.read().decode("utf-8")

        # Extract all 'nixos-YY.MM' entries
        matches = re.findall(r'nixos-(\d{2}\.\d{2})', html)
        if not matches:
            raise Exception("No stable NixOS versions found.")

        # Sort versions and get the latest
        latest_version = sorted(matches, key=lambda x: list(map(int, x.split('.'))))[-1]
        print(f"Latest stable NixOS version detected: {latest_version}")

        # Get current version
        current_version_output = subprocess.check_output(["nixos-version"], text=True).strip()
        current_version = current_version_output.split()[0]
        base_version = current_version.split("pre")[0] if "pre" in current_version else current_version
        print(f"Current NixOS version detected: {base_version}")

        if base_version == latest_version:
            print("Already on the latest stable release.")
            return

        confirm = input(f"Upgrade NixOS {base_version} → {latest_version}? [y/N]: ").strip().lower()
        if confirm != "y":
            print("Upgrade cancelled.")
            return

        # Proceed with upgrade
        subprocess.run(["sudo", "nix-channel", "--remove", "nixos"])
        subprocess.run(["sudo", "nix-channel", "--add", f"https://channels.nixos.org/nixos-{latest_version}", "nixos"])
        subprocess.run(["sudo", "nix-channel", "--update"])
        subprocess.run(["sudo", "nixos-rebuild", "switch"])
        save_last_action("Version Upgrade")

    except Exception as e:
        log_action(f"NixOS upgrade failed: {e}", level="error")
        print(f"⚠️ NixOS upgrade failed: {e}")

def _debian_upgrade():
    try:
        current_codename = subprocess.check_output(["lsb_release", "-c", "-s"], text=True).strip()
        with urllib.request.urlopen("https://deb.debian.org/debian/dists/stable/Release") as response:
            release_info = response.read().decode()

        latest_codename = next(
            (line.split(":")[1].strip() for line in release_info.splitlines() if line.startswith("Codename:")),
            None
        )

        if not latest_codename:
            raise Exception("Cannot determine latest Debian codename.")

        if current_codename == latest_codename:
            print("Already on the latest release.")
            return

        confirm = input(f"Upgrade {current_codename} → {latest_codename}? [y/N]: ").strip().lower()
        if confirm == "y":
            subprocess.run(["sudo", "cp", "/etc/apt/sources.list", "/etc/apt/sources.list.bak"])
            subprocess.run(["sudo", "sed", "-i", f"s/{current_codename}/{latest_codename}/g", "/etc/apt/sources.list"])
            subprocess.run(["sudo", "apt", "update"])
            subprocess.run(["sudo", "apt", "full-upgrade", "-y"])
            save_last_action("Version Upgrade")
    except Exception as e:
        log_action(f"Debian upgrade failed: {e}", level="error")
        print(f"⚠️ Debian upgrade failed: {e}")
