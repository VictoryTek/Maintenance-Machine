from utils import log_action, save_last_action
import subprocess
import datetime
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
        result = subprocess.check_output(["nixos-version"], text=True).strip()
        current_version = result.split()[0]  # This returns something like "24.05pre1234"
        # Parse the base version number (like "24.05")
        base_version = current_version.split("pre")[0] if "pre" in current_version else current_version
        print(f"Current NixOS version detected: {base_version}")

        # Ask user for target version manually (since next stable version may not exist yet)
        target_version = input("Enter the NixOS version to upgrade to (e.g., 24.11): ").strip()
        if not target_version:
            print("Upgrade cancelled: No version entered.")
            return

        confirm = input(f"Upgrade NixOS {base_version} → {target_version}? [y/N]: ").strip().lower()
        if confirm != "y":
            print("Upgrade cancelled.")
            return

        # Proceed with upgrade
        subprocess.run(["sudo", "nix-channel", "--remove", "nixos"])
        subprocess.run(["sudo", "nix-channel", "--add", f"https://channels.nixos.org/nixos-{target_version}", "nixos"])
        subprocess.run(["sudo", "nix-channel", "--update"])
        subprocess.run(["sudo", "nixos-rebuild", "switch"])
        save_last_action("Version Upgrade")

    except Exception as e:
        log_action(f"NixOS upgrade failed: {e}", level="error")
        print(f"⚠️ NixOS upgrade failed: {e}")

def _debian_upgrade():
    current_codename = subprocess.check_output(["lsb_release", "-c", "-s"], text=True).strip()
    release_info = urllib.request.urlopen("https://deb.debian.org/debian/dists/stable/Release").read().decode()
    latest_codename = next((line.split(":")[1].strip() for line in release_info.splitlines() if line.startswith("Codename:")), None)
    if not latest_codename:
        raise Exception("Cannot determine latest Debian codename.")
    if current_codename == latest_codename:
        print("Already on the latest release.")
        return
    confirm = input(f"Upgrade {current_codename} → {latest_codename}? [y/N]: ").strip().lower()
    if confirm == "y":
        subprocess.run(["sudo", "cp", "/etc/apt/sources.list", f"/etc/apt/sources.list.bak"])
        subprocess.run(["sudo", "sed", "-i", f"s/{current_codename}/{latest_codename}/g", "/etc/apt/sources.list"])
        subprocess.run(["sudo", "apt", "update"])
        subprocess.run(["sudo", "apt", "full-upgrade", "-y"])
        save_last_action("Version Upgrade")
