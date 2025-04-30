from core import update_system, version_upgrade, reboot_system
from utils import detect_distro, load_last_action, inhibit_sleep
import os

def main_menu():
    inhibitor = inhibit_sleep()
    try:
        while True:
            os.system("clear")
            distro = detect_distro()
            last_action = load_last_action()
            print(f"🔍 Distribution: {distro.capitalize()}")
            if last_action:
                print(f"✅ Last action: {last_action}")
            print("\n==== Maintenance Menu ====")
            print("1. Update System")
            print("2. Version Upgrade")
            print("3. Reboot")
            print("4. Exit")
            choice = input("\nChoose [1-4]: ").strip()
            
            if choice == "1":
                update_system(distro)
            elif choice == "2":
                version_upgrade(distro)
            elif choice == "3":
                reboot_system()
            elif choice == "4":
                print("Exiting...")
                break
            else:
                print("Invalid choice.")
            
            input("\nPress Enter to continue...")
    finally:
        inhibitor.terminate()

if __name__ == "__main__":
    main_menu()
