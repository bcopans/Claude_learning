"""
KindPaw — Groomer Dashboard AI Assistant

Helps groomers manage their schedule, pull dog cards before appointments,
record health observations, and grow their reputation.
"""

import json
from datetime import datetime

import anthropic

from db import bootstrap, get_conn

client = anthropic.Anthropic()

# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def view_my_schedule(groomer_id: int, date: str = None) -> dict:
    with get_conn() as conn:
        if date:
            dates_clause = "AND b.date = ?"
            params = (groomer_id, date)
        else:
            today = datetime.now().strftime("%Y-%m-%d")
            dates_clause = "AND b.date >= ?"
            params = (groomer_id, today)

        bookings = conn.execute(f"""
            SELECT b.id, b.date, b.time, b.status, b.cut_style,
                   b.special_requests, b.total_price,
                   d.id AS dog_id, d.name AS dog_name, d.breed, d.temperament_tags,
                   o.name AS owner_name, o.phone AS owner_phone,
                   s.name AS service_name, s.duration_mins
            FROM bookings b
            JOIN dogs d ON b.dog_id = d.id
            JOIN owners o ON b.owner_id = o.id
            JOIN services s ON b.service_id = s.id
            WHERE b.groomer_id=? {dates_clause} AND b.status='confirmed'
            ORDER BY b.date, b.time
        """, params).fetchall()

        results = []
        for b in bookings:
            results.append({
                **dict(b),
                "temperament": json.loads(b["temperament_tags"]),
            })

        return {"upcoming_bookings": results, "count": len(results)}


def get_dog_card(dog_id: int) -> dict:
    with get_conn() as conn:
        dog = conn.execute("SELECT * FROM dogs WHERE id=?", (dog_id,)).fetchone()
        if not dog:
            return {"error": f"Dog {dog_id} not found."}

        owner = conn.execute("SELECT name, phone FROM owners WHERE id=?", (dog["owner_id"],)).fetchone()

        history = conn.execute("""
            SELECT b.date, b.cut_style, b.special_requests,
                   g.name AS groomer_name,
                   s.name AS service_name,
                   gr.coat_condition, gr.skin_condition, gr.ear_condition,
                   gr.nail_condition, gr.eye_condition, gr.health_flags,
                   gr.groomer_private_note, gr.next_recommended_groom,
                   p.photo_url, p.caption
            FROM bookings b
            JOIN groomers g ON b.groomer_id = g.id
            JOIN services s ON b.service_id = s.id
            LEFT JOIN groom_records gr ON gr.booking_id = b.id
            LEFT JOIN groom_photos p ON p.booking_id = b.id
            WHERE b.dog_id=? AND b.status='completed'
            ORDER BY b.date DESC LIMIT 5
        """, (dog_id,)).fetchall()

        return {
            "dog": {
                "id":                       dog["id"],
                "name":                     dog["name"],
                "breed":                    dog["breed"],
                "age_years":                dog["age_years"],
                "weight_lbs":               dog["weight_lbs"],
                "coat_type":                dog["coat_type"],
                "temperament":              json.loads(dog["temperament_tags"]),
                "default_special_requests": dog["default_special_requests"],
            },
            "owner": {"name": owner["name"], "phone": owner["phone"]},
            "groom_history": [dict(h) for h in history],
        }


def add_availability(groomer_id: int, date: str, time_slots: list) -> dict:
    with get_conn() as conn:
        added, skipped = [], []
        for slot in time_slots:
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO availability (groomer_id,date,time_slot,is_booked) VALUES (?,?,?,0)",
                    (groomer_id, date, slot),
                )
                added.append(slot)
            except Exception:
                skipped.append(slot)
        conn.commit()
        return {"date": date, "added": added, "skipped": skipped}


def remove_availability(groomer_id: int, date: str, time_slot: str) -> dict:
    with get_conn() as conn:
        slot = conn.execute(
            "SELECT is_booked FROM availability WHERE groomer_id=? AND date=? AND time_slot=?",
            (groomer_id, date, time_slot),
        ).fetchone()
        if not slot:
            return {"error": f"No slot found for {date} at {time_slot}."}
        if slot["is_booked"]:
            return {"error": f"Cannot remove {time_slot} on {date} — there's a booking in that slot."}
        conn.execute(
            "DELETE FROM availability WHERE groomer_id=? AND date=? AND time_slot=?",
            (groomer_id, date, time_slot),
        )
        conn.commit()
        return {"success": True, "message": f"{time_slot} on {date} removed from your calendar."}


def complete_booking(
    booking_id: str,
    coat_condition: str,
    skin_condition: str,
    ear_condition: str,
    nail_condition: str,
    eye_condition: str,
    health_flags: str = "",
    groomer_private_note: str = "",
    next_recommended_groom: str = "",
    photo_url: str = "",
    cut_style: str = "",
) -> dict:
    with get_conn() as conn:
        b = conn.execute("SELECT * FROM bookings WHERE id=?", (booking_id,)).fetchone()
        if not b:
            return {"error": f"Booking {booking_id} not found."}
        if b["status"] == "completed":
            return {"error": "This booking is already marked complete."}
        if b["status"] == "cancelled":
            return {"error": "Cannot complete a cancelled booking."}

        conn.execute("UPDATE bookings SET status='completed' WHERE id=?", (booking_id,))

        conn.execute("""
            INSERT INTO groom_records
              (booking_id,dog_id,groomer_id,
               coat_condition,skin_condition,ear_condition,nail_condition,eye_condition,
               health_flags,groomer_private_note,next_recommended_groom,completed_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            booking_id, b["dog_id"], b["groomer_id"],
            coat_condition, skin_condition, ear_condition, nail_condition, eye_condition,
            health_flags, groomer_private_note, next_recommended_groom,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ))

        if photo_url:
            effective_cut = cut_style or b["cut_style"]
            conn.execute("""
                INSERT INTO groom_photos
                  (booking_id,dog_id,groomer_id,photo_url,cut_style,is_portfolio,verified)
                VALUES (?,?,?,?,?,1,1)
            """, (booking_id, b["dog_id"], b["groomer_id"], photo_url, effective_cut))

        conn.commit()

        dog = conn.execute("SELECT name FROM dogs WHERE id=?", (b["dog_id"],)).fetchone()
        owner = conn.execute(
            "SELECT name FROM owners WHERE id=?", (b["owner_id"],)
        ).fetchone()

        result = {
            "success":          True,
            "booking_id":       booking_id,
            "dog":              dog["name"],
            "payment_released": f"${b['groomer_earnings']} will be deposited within 24 hours.",
            "health_summary": {
                "coat":  coat_condition,
                "skin":  skin_condition,
                "ears":  ear_condition,
                "nails": nail_condition,
                "eyes":  eye_condition,
            },
        }
        if health_flags:
            result["owner_notification"] = (
                f"A gentle notification has been sent to {owner['name']}: \"{health_flags}\""
            )
        if next_recommended_groom:
            result["next_groom_reminder"] = (
                f"Reminder set for {owner['name']}: next groom recommended {next_recommended_groom}."
            )
        return result


def add_service(groomer_id: int, name: str, price: float,
                duration_mins: int, description: str = "") -> dict:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO services (groomer_id,name,description,price,duration_mins) VALUES (?,?,?,?,?)",
            (groomer_id, name, description, price, duration_mins),
        )
        conn.commit()
        svc_id = conn.execute(
            "SELECT id FROM services WHERE groomer_id=? ORDER BY id DESC LIMIT 1", (groomer_id,)
        ).fetchone()["id"]
        return {"success": True, "service_id": svc_id, "name": name, "price": price, "duration_mins": duration_mins}


def view_my_reviews(groomer_id: int) -> dict:
    with get_conn() as conn:
        reviews = conn.execute("""
            SELECT r.rating, r.review_text, r.cut_style, r.created_at,
                   d.name AS dog_name, d.breed,
                   o.name AS owner_name
            FROM reviews r
            JOIN dogs d ON r.dog_id = d.id
            JOIN owners o ON r.owner_id = o.id
            WHERE r.groomer_id=?
            ORDER BY r.created_at DESC
        """, (groomer_id,)).fetchall()

        g = conn.execute(
            "SELECT avg_rating, total_reviews FROM groomers WHERE id=?", (groomer_id,)
        ).fetchone()

        return {
            "avg_rating":    g["avg_rating"],
            "total_reviews": g["total_reviews"],
            "reviews":       [dict(r) for r in reviews],
        }


# ---------------------------------------------------------------------------
# Tool dispatch
# ---------------------------------------------------------------------------

TOOL_MAP = {
    "view_my_schedule":  lambda i: view_my_schedule(**i),
    "get_dog_card":      lambda i: get_dog_card(**i),
    "add_availability":  lambda i: add_availability(**i),
    "remove_availability": lambda i: remove_availability(**i),
    "complete_booking":  lambda i: complete_booking(**i),
    "add_service":       lambda i: add_service(**i),
    "view_my_reviews":   lambda i: view_my_reviews(**i),
}

TOOLS = [
    {
        "name": "view_my_schedule",
        "description": "View upcoming confirmed bookings. Optionally filter by a specific date.",
        "input_schema": {
            "type": "object",
            "properties": {
                "groomer_id": {"type": "integer"},
                "date":       {"type": "string", "description": "Optional YYYY-MM-DD to view a specific day"},
            },
            "required": ["groomer_id"],
        },
    },
    {
        "name": "get_dog_card",
        "description": "Pull the full dog passport before an appointment — breed, temperament, special requests, and health history from every past groom.",
        "input_schema": {
            "type": "object",
            "properties": {"dog_id": {"type": "integer"}},
            "required": ["dog_id"],
        },
    },
    {
        "name": "add_availability",
        "description": "Open time slots in your calendar for a specific date.",
        "input_schema": {
            "type": "object",
            "properties": {
                "groomer_id": {"type": "integer"},
                "date":       {"type": "string", "description": "YYYY-MM-DD"},
                "time_slots": {"type": "array", "items": {"type": "string"}, "description": "e.g. ['09:00','10:00']"},
            },
            "required": ["groomer_id", "date", "time_slots"],
        },
    },
    {
        "name": "remove_availability",
        "description": "Block a time slot. Will not remove if there is already a booking.",
        "input_schema": {
            "type": "object",
            "properties": {
                "groomer_id": {"type": "integer"},
                "date":       {"type": "string", "description": "YYYY-MM-DD"},
                "time_slot":  {"type": "string", "description": "HH:MM"},
            },
            "required": ["groomer_id", "date", "time_slot"],
        },
    },
    {
        "name": "complete_booking",
        "description": (
            "Mark a booking complete and record health observations. "
            "Triggers payment release. Health flags are sent as a gentle notification to the owner."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "booking_id":            {"type": "string"},
                "coat_condition":        {"type": "string", "enum": ["healthy", "dry", "matted", "thinning"]},
                "skin_condition":        {"type": "string", "enum": ["normal", "irritated", "flaky", "parasites spotted"]},
                "ear_condition":         {"type": "string", "enum": ["clean", "buildup", "odor"]},
                "nail_condition":        {"type": "string", "enum": ["good", "overgrown", "dew claws need attention"]},
                "eye_condition":         {"type": "string", "enum": ["clear", "mild discharge", "tear staining"]},
                "health_flags":          {"type": "string", "description": "Anything to flag to the owner. Leave empty if none."},
                "groomer_private_note":  {"type": "string", "description": "Private note for your records only."},
                "next_recommended_groom":{"type": "string", "description": "YYYY-MM-DD — when this dog should come back."},
                "photo_url":             {"type": "string", "description": "Completion photo URL (optional for demo)."},
                "cut_style":             {"type": "string", "description": "Cut style performed, e.g. 'teddy bear'."},
            },
            "required": ["booking_id", "coat_condition", "skin_condition",
                         "ear_condition", "nail_condition", "eye_condition"],
        },
    },
    {
        "name": "add_service",
        "description": "Add a new service to your KindPaw profile.",
        "input_schema": {
            "type": "object",
            "properties": {
                "groomer_id":   {"type": "integer"},
                "name":         {"type": "string"},
                "description":  {"type": "string"},
                "price":        {"type": "number"},
                "duration_mins":{"type": "integer"},
            },
            "required": ["groomer_id", "name", "price", "duration_mins"],
        },
    },
    {
        "name": "view_my_reviews",
        "description": "See your star rating and all reviews left by clients.",
        "input_schema": {
            "type": "object",
            "properties": {"groomer_id": {"type": "integer"}},
            "required": ["groomer_id"],
        },
    },
]


def build_system(groomer_id: int, groomer_name: str, business_name: str) -> str:
    return f"""You are the KindPaw Groomer Assistant for {groomer_name} at {business_name}.

KindPaw's mission: healthy dogs first, beautiful dogs second. The owners who book through KindPaw care deeply about their pets — help {groomer_name} reflect that same care.

Your role:
1. Surface the dog card before every appointment — temperament, special requests, health history
2. Walk through health observations when completing a groom (coat, skin, ears, nails, eyes)
3. Help manage the availability calendar
4. Track services and reviews

Principles:
- Always remind {groomer_name} to check the dog card before the appointment arrives
- When completing a groom, ask about each health observation category — this protects the dog and builds trust with owners
- Word health flags to owners with care: factual but gentle, not alarming
- The next recommended groom date shows up on the owner's dashboard — always set it
- Private notes stay between {groomer_name} and KindPaw; they never go to owners

Groomer ID for all tool calls: {groomer_id}

Today is {datetime.now().strftime('%Y-%m-%d (%A)')}."""


# ---------------------------------------------------------------------------
# Chat loop
# ---------------------------------------------------------------------------

def run_tool(name: str, inputs: dict) -> str:
    fn = TOOL_MAP.get(name)
    if fn:
        return json.dumps(fn(inputs))
    return json.dumps({"error": f"Unknown tool: {name}"})


def chat(messages: list, system: str) -> tuple[str, list]:
    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=system,
            tools=TOOLS,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            text = next(b.text for b in response.content if hasattr(b, "text"))
            return text, messages

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            result = run_tool(block.name, block.input)
            tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": result})
        messages.append({"role": "user", "content": tool_results})


def main(groomer_id: int):
    with get_conn() as conn:
        g = conn.execute(
            "SELECT name, business_name FROM groomers WHERE id=?", (groomer_id,)
        ).fetchone()
        if not g:
            print(f"Groomer ID {groomer_id} not found.")
            return

    system = build_system(groomer_id, g["name"], g["business_name"])

    print("=" * 55)
    print(f"  KindPaw — Groomer Dashboard")
    print(f"  {g['name']} @ {g['business_name']}")
    print("=" * 55)
    print("Type 'quit' to exit.\n")

    messages = []
    reply, messages = chat(
        [{"role": "user", "content": "Show me what's on my schedule today and tomorrow."}],
        system,
    )
    print(f"Assistant: {reply}\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("quit", "exit"):
            print("Assistant: Have a great day — your dogs are in good hands!")
            break
        if not user_input:
            continue
        messages.append({"role": "user", "content": user_input})
        reply, messages = chat(messages, system)
        print(f"\nAssistant: {reply}\n")
