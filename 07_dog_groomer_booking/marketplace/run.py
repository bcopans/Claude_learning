"""
KindPaw Marketplace — Entry point.

Launches either the pet owner assistant or the groomer dashboard.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from db import bootstrap, get_conn


def pick_groomer() -> int:
    with get_conn() as conn:
        groomers = conn.execute(
            "SELECT id, name, business_name FROM groomers ORDER BY id"
        ).fetchall()

    print("\nGroomers on KindPaw:")
    for g in groomers:
        print(f"  [{g['id']}] {g['name']} — {g['business_name']}")

    while True:
        try:
            gid = int(input("\nEnter your groomer ID: ").strip())
            if any(g["id"] == gid for g in groomers):
                return gid
            print("  Invalid ID — try again.")
        except ValueError:
            print("  Please enter a number.")


def main():
    print("\n╔══════════════════════════════╗")
    print("║        KindPaw               ║")
    print("║  Healthy dogs. Happy lives.  ║")
    print("╚══════════════════════════════╝")
    print("\nWho are you?")
    print("  [1] Pet owner — find & book a groomer")
    print("  [2] Groomer  — manage your schedule & clients")

    while True:
        choice = input("\nEnter 1 or 2: ").strip()
        if choice == "1":
            from owner_bot import main as owner_main
            owner_main()
            break
        elif choice == "2":
            groomer_id = pick_groomer()
            from groomer_bot import main as groomer_main
            groomer_main(groomer_id)
            break
        else:
            print("  Please enter 1 or 2.")


if __name__ == "__main__":
    bootstrap()
    main()
