"""
Project: Paw Perfect Grooming — AI Booking Assistant

Demonstrates:
  - System prompts (grooming business persona)
  - Tool use (availability check, booking, cancellation)
  - Structured output (booking confirmations)
  - Multi-turn conversation

Usage:
  python booking_assistant.py
"""

import json
import random
import string
from datetime import datetime, timedelta
import anthropic

client = anthropic.Anthropic()

# --- In-memory "database" ---
BOOKINGS: dict[str, dict] = {}

SERVICES = {
    "bath_dry":      {"name": "Bath & Dry",               "price": 45,  "duration_mins": 60},
    "full_groom":    {"name": "Full Groom (bath+trim)",    "price": 75,  "duration_mins": 90},
    "nail_trim":     {"name": "Nail Trim",                 "price": 20,  "duration_mins": 20},
    "puppy_package": {"name": "Puppy First Groom Package", "price": 55,  "duration_mins": 75},
    "deshed":        {"name": "De-shed Treatment",         "price": 65,  "duration_mins": 90},
}

# Slots open Mon–Sat, 9 AM – 5 PM (on the hour)
OPEN_HOURS = list(range(9, 17))
OPEN_DAYS  = [0, 1, 2, 3, 4, 5]  # Mon=0 … Sat=5


# --- Tool implementations ---

def get_services() -> dict:
    return {
        "services": [
            {
                "id": sid,
                "name": svc["name"],
                "price_usd": svc["price"],
                "duration_mins": svc["duration_mins"],
            }
            for sid, svc in SERVICES.items()
        ]
    }


def check_availability(date: str, service_id: str) -> dict:
    """Return available time slots for a given date and service."""
    try:
        day = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD."}

    if day.weekday() not in OPEN_DAYS:
        return {"available": False, "reason": "We are closed on Sundays."}

    if service_id not in SERVICES:
        return {"error": f"Unknown service '{service_id}'. Call get_services for options."}

    # Slots already booked on this date
    booked_slots = {
        b["time"] for b in BOOKINGS.values()
        if b["date"] == date and b["status"] == "confirmed"
    }

    available_slots = [
        f"{hour:02d}:00"
        for hour in OPEN_HOURS
        if f"{hour:02d}:00" not in booked_slots
    ]

    return {
        "date": date,
        "service": SERVICES[service_id]["name"],
        "available_slots": available_slots,
        "available": len(available_slots) > 0,
    }


def book_appointment(
    customer_name: str,
    dog_name: str,
    dog_breed: str,
    service_id: str,
    date: str,
    time: str,
    phone: str,
) -> dict:
    """Create a confirmed booking and return a confirmation."""
    if service_id not in SERVICES:
        return {"error": f"Unknown service '{service_id}'."}

    # Check slot is still free
    conflict = any(
        b["date"] == date and b["time"] == time and b["status"] == "confirmed"
        for b in BOOKINGS.values()
    )
    if conflict:
        return {"error": f"The {time} slot on {date} was just taken. Please choose another time."}

    booking_id = "PG-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    svc = SERVICES[service_id]

    BOOKINGS[booking_id] = {
        "booking_id":    booking_id,
        "customer_name": customer_name,
        "dog_name":      dog_name,
        "dog_breed":     dog_breed,
        "service_id":    service_id,
        "service_name":  svc["name"],
        "date":          date,
        "time":          time,
        "phone":         phone,
        "price_usd":     svc["price"],
        "duration_mins": svc["duration_mins"],
        "status":        "confirmed",
    }

    return {
        "success":       True,
        "booking_id":    booking_id,
        "summary": (
            f"{dog_name} ({dog_breed}) is booked for {svc['name']} "
            f"on {date} at {time}. Total: ${svc['price']}. "
            f"Booking reference: {booking_id}."
        ),
        "booking": BOOKINGS[booking_id],
    }


def cancel_appointment(booking_id: str) -> dict:
    if booking_id not in BOOKINGS:
        return {"error": f"No booking found with ID {booking_id}."}

    b = BOOKINGS[booking_id]
    if b["status"] == "cancelled":
        return {"error": f"Booking {booking_id} is already cancelled."}

    BOOKINGS[booking_id]["status"] = "cancelled"
    return {
        "success":    True,
        "booking_id": booking_id,
        "message":    f"Booking {booking_id} for {b['dog_name']} on {b['date']} at {b['time']} has been cancelled.",
    }


# --- Tool schemas for Claude ---

TOOLS = [
    {
        "name": "get_services",
        "description": "Return the list of grooming services offered, with prices and durations.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "check_availability",
        "description": "Check which time slots are available on a given date for a service.",
        "input_schema": {
            "type": "object",
            "properties": {
                "date":       {"type": "string", "description": "Date in YYYY-MM-DD format"},
                "service_id": {"type": "string", "description": "Service ID from get_services"},
            },
            "required": ["date", "service_id"],
        },
    },
    {
        "name": "book_appointment",
        "description": "Book a grooming appointment once the customer has confirmed all details.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_name": {"type": "string"},
                "dog_name":      {"type": "string"},
                "dog_breed":     {"type": "string"},
                "service_id":    {"type": "string"},
                "date":          {"type": "string", "description": "YYYY-MM-DD"},
                "time":          {"type": "string", "description": "HH:MM (24-hour)"},
                "phone":         {"type": "string"},
            },
            "required": ["customer_name", "dog_name", "dog_breed", "service_id", "date", "time", "phone"],
        },
    },
    {
        "name": "cancel_appointment",
        "description": "Cancel an existing appointment by booking ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "booking_id": {"type": "string", "description": "The PG-XXXXXX booking reference"},
            },
            "required": ["booking_id"],
        },
    },
]

SYSTEM = """You are Bella, the friendly booking assistant for Paw Perfect Grooming.

Your job is to help customers:
1. Learn about our grooming services and prices
2. Check appointment availability
3. Book grooming appointments
4. Cancel existing appointments

Guidelines:
- Always confirm the dog's name, breed, owner name, and phone number before booking
- Suggest a service if the customer is unsure (ask about the dog's coat/size)
- Be warm and enthusiastic about dogs
- After booking, always read back the full confirmation details
- Today's date is """ + datetime.now().strftime("%Y-%m-%d (%A)") + """
- We are open Monday–Saturday, 9 AM–5 PM"""


# --- Conversation loop ---

def run_tool(name: str, inputs: dict) -> str:
    if name == "get_services":
        result = get_services()
    elif name == "check_availability":
        result = check_availability(**inputs)
    elif name == "book_appointment":
        result = book_appointment(**inputs)
    elif name == "cancel_appointment":
        result = cancel_appointment(**inputs)
    else:
        result = {"error": f"Unknown tool: {name}"}
    return json.dumps(result)


def chat(messages: list) -> tuple[str, list]:
    """Send messages to Claude, handle tool calls, return final text + updated messages."""
    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=SYSTEM,
            tools=TOOLS,
            messages=messages,
        )

        # Append assistant turn
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            # Final text reply
            text = next(b.text for b in response.content if hasattr(b, "text"))
            return text, messages

        # Handle every tool call in this turn
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            result_json = run_tool(block.name, block.input)
            tool_results.append({
                "type":        "tool_result",
                "tool_use_id": block.id,
                "content":     result_json,
            })

        messages.append({"role": "user", "content": tool_results})


def main():
    print("=" * 55)
    print("  Paw Perfect Grooming — Booking Assistant")
    print("=" * 55)
    print("Type 'quit' to exit.\n")

    messages = []
    # Kick off with a greeting
    reply, messages = chat([{"role": "user", "content": "Hello!"}])
    print(f"Bella: {reply}\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("quit", "exit", "bye"):
            print("Bella: Thanks for visiting Paw Perfect Grooming. See you and your pup soon!")
            break
        if not user_input:
            continue

        messages.append({"role": "user", "content": user_input})
        reply, messages = chat(messages)
        print(f"\nBella: {reply}\n")


if __name__ == "__main__":
    main()
