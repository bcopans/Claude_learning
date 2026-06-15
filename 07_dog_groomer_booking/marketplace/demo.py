"""
KindPaw Demo — runs two scripted conversations automatically.

  Scenario A (Owner): Emma finds a groomer for Max's teddy bear cut and books
  Scenario B (Groomer): Jen views her schedule and completes Buddy's groom
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from db import bootstrap, get_conn
from owner_bot import TOOLS as OWNER_TOOLS, SYSTEM as OWNER_SYSTEM, run_tool as owner_tool, chat as owner_chat
from groomer_bot import TOOLS as GROOMER_TOOLS, build_system, run_tool as groomer_tool, chat as groomer_chat


def section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def run_owner_demo():
    section("SCENARIO A — Pet Owner: Emma books Max's next groom")

    script = [
        "Hi! I'm looking to book a groom for my Goldendoodle.",
        "My phone number is (503) 555-0101",
        "Can you show me Max's grooming history?",
        "I'd love to book the same teddy bear cut with Sarah again. What does she have available next week?",
        "Let's book the 10am slot on 2026-06-17 with the Teddy Bear Full Groom please.",
    ]

    messages = []
    # Greeting
    reply, messages = owner_chat([{"role": "user", "content": "Hello!"}])
    print(f"Sage:  {reply}\n")

    for user_msg in script:
        print(f"Emma:  {user_msg}")
        messages.append({"role": "user", "content": user_msg})
        reply, messages = owner_chat(messages)
        print(f"\nSage:  {reply}\n")
        print("-" * 50)


def run_groomer_demo():
    section("SCENARIO B — Groomer: Jen checks her schedule and completes Buddy's groom")

    groomer_id = 3
    with get_conn() as conn:
        g = conn.execute("SELECT name, business_name FROM groomers WHERE id=?", (groomer_id,)).fetchone()

    system = build_system(groomer_id, g["name"], g["business_name"])

    script = [
        "What bookings do I have coming up?",
        "Pull up the dog card for Buddy (dog 3) before his appointment.",
        "Thanks. Let's mark booking KP-A1003 as complete. Coat looked healthy, skin normal, ears clean, nails good, eyes clear. No health flags. Private note: Buddy is a big energetic boy — two people helpful for nail trim. Next groom in 10 weeks.",
    ]

    messages = []
    reply, messages = groomer_chat(
        [{"role": "user", "content": "Show me what's on my schedule today and tomorrow."}],
        system,
    )
    print(f"Assistant:  {reply}\n")
    print("-" * 50)

    for user_msg in script[1:]:
        print(f"Jen:        {user_msg}")
        messages.append({"role": "user", "content": user_msg})
        reply, messages = groomer_chat(messages, system)
        print(f"\nAssistant:  {reply}\n")
        print("-" * 50)


if __name__ == "__main__":
    bootstrap()
    run_owner_demo()
    run_groomer_demo()
    print("\nDemo complete.")
