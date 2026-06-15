"""
KindPaw — Pet Owner AI Assistant

Helps owners find groomers, browse portfolios by breed & cut style,
book appointments, and view their dog's health passport.
"""

import json
from datetime import datetime

import anthropic

from db import bootstrap, get_conn, new_booking_id

client = anthropic.Anthropic()

# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def get_breed_cuts(breed: str) -> dict:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT cut_style, description FROM breed_cuts WHERE LOWER(breed)=LOWER(?) ORDER BY cut_style",
            (breed,),
        ).fetchall()
        if not rows:
            rows = conn.execute(
                "SELECT breed, cut_style, description FROM breed_cuts "
                "WHERE LOWER(breed) LIKE LOWER(?) ORDER BY breed, cut_style",
                (f"%{breed}%",),
            ).fetchall()
            if not rows:
                return {"error": f"No cut catalog found for '{breed}'. Try a breed like 'Goldendoodle' or 'Poodle'."}
            return {"cuts": [dict(r) for r in rows]}
        return {"breed": breed, "cuts": [{"cut_style": r["cut_style"], "description": r["description"]} for r in rows]}


def search_groomers(location: str, breed: str = None, specialization: str = None, cut_style: str = None) -> dict:
    with get_conn() as conn:
        groomers = conn.execute("SELECT * FROM groomers WHERE verified=1").fetchall()
        results = []
        for g in groomers:
            if location.lower() not in g["location"].lower():
                continue
            if breed:
                expertise = json.loads(g["breed_expertise"])
                if not any(breed.lower() in e.lower() for e in expertise):
                    continue
            if specialization:
                specs = json.loads(g["specialization_tags"])
                if not any(specialization.lower() in s.lower() for s in specs):
                    continue
            if cut_style:
                cuts = json.loads(g["cut_specialties"])
                if not any(cut_style.lower() in c.lower() for c in cuts):
                    continue

            services = conn.execute(
                "SELECT id, name, price, duration_mins FROM services WHERE groomer_id=? ORDER BY price",
                (g["id"],),
            ).fetchall()

            results.append({
                "groomer_id":          g["id"],
                "name":                g["name"],
                "business_name":       g["business_name"],
                "location":            g["location"],
                "avg_rating":          g["avg_rating"],
                "total_reviews":       g["total_reviews"],
                "certifications":      json.loads(g["certification_tags"]),
                "specializations":     json.loads(g["specialization_tags"]),
                "breed_expertise":     json.loads(g["breed_expertise"]),
                "cut_specialties":     json.loads(g["cut_specialties"]),
                "services":            [dict(s) for s in services],
            })

        if not results:
            return {"message": "No groomers found matching your criteria.", "results": []}
        return {"count": len(results), "results": results}


def get_groomer_profile(groomer_id: int) -> dict:
    with get_conn() as conn:
        g = conn.execute("SELECT * FROM groomers WHERE id=?", (groomer_id,)).fetchone()
        if not g:
            return {"error": f"Groomer {groomer_id} not found."}

        services = conn.execute(
            "SELECT id, name, description, price, duration_mins FROM services WHERE groomer_id=? ORDER BY price",
            (groomer_id,),
        ).fetchall()

        reviews = conn.execute("""
            SELECT r.rating, r.review_text, r.cut_style, r.created_at,
                   d.name AS dog_name, d.breed
            FROM reviews r
            JOIN dogs d ON r.dog_id = d.id
            WHERE r.groomer_id=?
            ORDER BY r.created_at DESC LIMIT 5
        """, (groomer_id,)).fetchall()

        return {
            "groomer_id":      g["id"],
            "name":            g["name"],
            "business_name":   g["business_name"],
            "location":        g["location"],
            "phone":           g["phone"],
            "bio":             g["bio"],
            "certifications":  json.loads(g["certification_tags"]),
            "specializations": json.loads(g["specialization_tags"]),
            "breed_expertise": json.loads(g["breed_expertise"]),
            "cut_specialties": json.loads(g["cut_specialties"]),
            "avg_rating":      g["avg_rating"],
            "total_reviews":   g["total_reviews"],
            "services":        [dict(s) for s in services],
            "recent_reviews":  [dict(r) for r in reviews],
        }


def browse_portfolio(groomer_id: int, breed: str = None, cut_style: str = None) -> dict:
    with get_conn() as conn:
        query = """
            SELECT p.id, p.photo_url, p.caption, p.cut_style, p.created_at,
                   d.name AS dog_name, d.breed,
                   r.rating, r.review_text
            FROM groom_photos p
            JOIN dogs d ON p.dog_id = d.id
            LEFT JOIN reviews r ON r.booking_id = p.booking_id
            WHERE p.groomer_id=? AND p.verified=1
        """
        params = [groomer_id]
        if breed:
            query += " AND LOWER(d.breed) LIKE LOWER(?)"
            params.append(f"%{breed}%")
        if cut_style:
            query += " AND LOWER(p.cut_style) LIKE LOWER(?)"
            params.append(f"%{cut_style}%")
        query += " ORDER BY p.created_at DESC"

        photos = conn.execute(query, params).fetchall()
        if not photos:
            return {"message": "No portfolio photos found for those filters.", "photos": []}
        return {"count": len(photos), "photos": [dict(p) for p in photos]}


def check_availability(groomer_id: int, date: str) -> dict:
    with get_conn() as conn:
        g = conn.execute("SELECT name, business_name FROM groomers WHERE id=?", (groomer_id,)).fetchone()
        if not g:
            return {"error": f"Groomer {groomer_id} not found."}

        slots = conn.execute(
            "SELECT time_slot FROM availability WHERE groomer_id=? AND date=? AND is_booked=0 ORDER BY time_slot",
            (groomer_id, date),
        ).fetchall()

        return {
            "groomer":         g["name"],
            "date":            date,
            "available_slots": [s["time_slot"] for s in slots],
            "available":       len(slots) > 0,
        }


def find_owner(phone: str) -> dict:
    with get_conn() as conn:
        owner = conn.execute("SELECT * FROM owners WHERE phone=?", (phone,)).fetchone()
        if not owner:
            return {"found": False, "message": "No account found with that phone number."}
        dogs = conn.execute("SELECT id, name, breed, age_years FROM dogs WHERE owner_id=?", (owner["id"],)).fetchall()
        return {
            "found":    True,
            "owner_id": owner["id"],
            "name":     owner["name"],
            "phone":    owner["phone"],
            "email":    owner["email"],
            "dogs":     [dict(d) for d in dogs],
        }


def register_owner(name: str, phone: str, email: str = "") -> dict:
    with get_conn() as conn:
        try:
            conn.execute(
                "INSERT INTO owners (name, phone, email) VALUES (?,?,?)",
                (name, phone, email),
            )
            conn.commit()
            owner_id = conn.execute("SELECT id FROM owners WHERE phone=?", (phone,)).fetchone()["id"]
            return {"success": True, "owner_id": owner_id, "name": name, "message": "Account created!"}
        except Exception as e:
            return {"error": str(e)}


def add_dog(owner_id: int, name: str, breed: str, age_years: float = 0,
            weight_lbs: float = 0, coat_type: str = "",
            temperament_tags: list = None, default_special_requests: str = "") -> dict:
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO dogs (owner_id,name,breed,age_years,weight_lbs,coat_type,
                              temperament_tags,default_special_requests)
            VALUES (?,?,?,?,?,?,?,?)
        """, (
            owner_id, name, breed, age_years, weight_lbs, coat_type,
            json.dumps(temperament_tags or []), default_special_requests,
        ))
        conn.commit()
        dog_id = conn.execute(
            "SELECT id FROM dogs WHERE owner_id=? ORDER BY id DESC LIMIT 1", (owner_id,)
        ).fetchone()["id"]
        return {"success": True, "dog_id": dog_id, "name": name, "breed": breed}


def book_appointment(owner_id: int, dog_id: int, groomer_id: int, service_id: int,
                     date: str, time: str, special_requests: str = "", cut_style: str = "") -> dict:
    with get_conn() as conn:
        slot = conn.execute(
            "SELECT id, is_booked FROM availability WHERE groomer_id=? AND date=? AND time_slot=?",
            (groomer_id, date, time),
        ).fetchone()
        if not slot:
            return {"error": f"No availability slot found for {date} at {time}."}
        if slot["is_booked"]:
            return {"error": f"The {time} slot on {date} was just taken — please choose another time."}

        svc = conn.execute("SELECT * FROM services WHERE id=? AND groomer_id=?", (service_id, groomer_id)).fetchone()
        if not svc:
            return {"error": "Service not found for that groomer."}

        # Merge dog's default special requests with one-time requests
        dog = conn.execute("SELECT * FROM dogs WHERE id=?", (dog_id,)).fetchone()
        merged_requests = dog["default_special_requests"]
        if special_requests:
            merged_requests = f"{merged_requests}\nThis visit: {special_requests}".strip()

        price = svc["price"]
        fee   = round(price * 0.15, 2)
        earn  = round(price - fee, 2)
        dep   = round(price * 0.30, 2)
        bid   = new_booking_id()

        conn.execute("""
            INSERT INTO bookings
              (id,owner_id,dog_id,groomer_id,service_id,date,time,
               special_requests,cut_style,status,deposit_paid,total_price,platform_fee,groomer_earnings)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (bid, owner_id, dog_id, groomer_id, service_id, date, time,
              merged_requests, cut_style, "confirmed", dep, price, fee, earn))
        conn.execute(
            "UPDATE availability SET is_booked=1 WHERE groomer_id=? AND date=? AND time_slot=?",
            (groomer_id, date, time),
        )
        conn.commit()

        groomer = conn.execute("SELECT name, business_name, phone FROM groomers WHERE id=?", (groomer_id,)).fetchone()
        return {
            "success":           True,
            "booking_id":        bid,
            "dog":               dog["name"],
            "groomer":           groomer["name"],
            "business":          groomer["business_name"],
            "groomer_phone":     groomer["phone"],
            "service":           svc["name"],
            "cut_style":         cut_style,
            "date":              date,
            "time":              time,
            "deposit_charged":   f"${dep}",
            "total_price":       f"${price}",
            "remaining_due":     f"${round(price - dep, 2)}",
            "special_requests":  merged_requests,
            "summary": (
                f"{dog['name']} is booked for {svc['name']} with {groomer['name']} "
                f"on {date} at {time}. Deposit ${dep} charged. Booking ref: {bid}."
            ),
        }


def list_my_bookings(owner_id: int) -> dict:
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT b.id, b.date, b.time, b.status, b.cut_style, b.total_price,
                   d.name AS dog_name, d.breed,
                   g.name AS groomer_name, g.business_name,
                   s.name AS service_name
            FROM bookings b
            JOIN dogs d ON b.dog_id = d.id
            JOIN groomers g ON b.groomer_id = g.id
            JOIN services s ON b.service_id = s.id
            WHERE b.owner_id=?
            ORDER BY b.date DESC
        """, (owner_id,)).fetchall()
        return {"bookings": [dict(r) for r in rows]}


def get_dog_history(dog_id: int) -> dict:
    with get_conn() as conn:
        dog = conn.execute("SELECT * FROM dogs WHERE id=?", (dog_id,)).fetchone()
        if not dog:
            return {"error": f"Dog {dog_id} not found."}

        records = conn.execute("""
            SELECT b.id AS booking_id, b.date, b.time, b.cut_style, b.special_requests,
                   g.name AS groomer_name, s.name AS service_name,
                   gr.coat_condition, gr.skin_condition, gr.ear_condition,
                   gr.nail_condition, gr.eye_condition, gr.health_flags,
                   gr.next_recommended_groom,
                   p.photo_url, p.caption,
                   r.rating, r.review_text
            FROM bookings b
            JOIN groomers g ON b.groomer_id = g.id
            JOIN services s ON b.service_id = s.id
            LEFT JOIN groom_records gr ON gr.booking_id = b.id
            LEFT JOIN groom_photos p ON p.booking_id = b.id
            LEFT JOIN reviews r ON r.booking_id = b.id
            WHERE b.dog_id=? AND b.status='completed'
            ORDER BY b.date DESC
        """, (dog_id,)).fetchall()

        return {
            "dog": {
                "id":                      dog["id"],
                "name":                    dog["name"],
                "breed":                   dog["breed"],
                "age_years":               dog["age_years"],
                "weight_lbs":              dog["weight_lbs"],
                "coat_type":               dog["coat_type"],
                "temperament":             json.loads(dog["temperament_tags"]),
                "default_special_requests": dog["default_special_requests"],
            },
            "groom_history": [dict(r) for r in records],
        }


def cancel_booking(booking_id: str) -> dict:
    with get_conn() as conn:
        b = conn.execute("SELECT * FROM bookings WHERE id=?", (booking_id,)).fetchone()
        if not b:
            return {"error": f"No booking found with ID {booking_id}."}
        if b["status"] == "cancelled":
            return {"error": "This booking is already cancelled."}
        if b["status"] == "completed":
            return {"error": "Completed bookings cannot be cancelled."}

        conn.execute("UPDATE bookings SET status='cancelled' WHERE id=?", (booking_id,))
        conn.execute(
            "UPDATE availability SET is_booked=0 WHERE groomer_id=? AND date=? AND time_slot=?",
            (b["groomer_id"], b["date"], b["time"]),
        )
        conn.commit()
        return {
            "success":    True,
            "booking_id": booking_id,
            "message":    f"Booking {booking_id} on {b['date']} at {b['time']} has been cancelled.",
        }


def leave_review(booking_id: str, rating: int, review_text: str) -> dict:
    with get_conn() as conn:
        b = conn.execute("SELECT * FROM bookings WHERE id=?", (booking_id,)).fetchone()
        if not b:
            return {"error": f"Booking {booking_id} not found."}
        if b["status"] != "completed":
            return {"error": "Reviews can only be left for completed bookings."}

        existing = conn.execute("SELECT id FROM reviews WHERE booking_id=?", (booking_id,)).fetchone()
        if existing:
            return {"error": "You've already left a review for this booking."}

        photo = conn.execute(
            "SELECT id FROM groom_photos WHERE booking_id=? LIMIT 1", (booking_id,)
        ).fetchone()
        photo_id = photo["id"] if photo else None

        conn.execute("""
            INSERT INTO reviews (booking_id,owner_id,groomer_id,dog_id,photo_id,rating,review_text,cut_style)
            VALUES (?,?,?,?,?,?,?,?)
        """, (booking_id, b["owner_id"], b["groomer_id"], b["dog_id"],
              photo_id, rating, review_text, b["cut_style"]))

        total = conn.execute(
            "SELECT AVG(rating) AS avg, COUNT(*) AS cnt FROM reviews WHERE groomer_id=?",
            (b["groomer_id"],),
        ).fetchone()
        conn.execute(
            "UPDATE groomers SET avg_rating=ROUND(?,1), total_reviews=? WHERE id=?",
            (total["avg"], total["cnt"], b["groomer_id"]),
        )
        conn.commit()
        return {"success": True, "message": f"Review submitted — {rating}/5 stars. Thank you!"}


# ---------------------------------------------------------------------------
# Tool dispatch
# ---------------------------------------------------------------------------

TOOL_MAP = {
    "get_breed_cuts":     lambda i: get_breed_cuts(**i),
    "search_groomers":    lambda i: search_groomers(**i),
    "get_groomer_profile":lambda i: get_groomer_profile(**i),
    "browse_portfolio":   lambda i: browse_portfolio(**i),
    "check_availability": lambda i: check_availability(**i),
    "find_owner":         lambda i: find_owner(**i),
    "register_owner":     lambda i: register_owner(**i),
    "add_dog":            lambda i: add_dog(**i),
    "book_appointment":   lambda i: book_appointment(**i),
    "list_my_bookings":   lambda i: list_my_bookings(**i),
    "get_dog_history":    lambda i: get_dog_history(**i),
    "cancel_booking":     lambda i: cancel_booking(**i),
    "leave_review":       lambda i: leave_review(**i),
}

TOOLS = [
    {
        "name": "get_breed_cuts",
        "description": "Return the catalog of standard cut styles for a dog breed.",
        "input_schema": {
            "type": "object",
            "properties": {"breed": {"type": "string"}},
            "required": ["breed"],
        },
    },
    {
        "name": "search_groomers",
        "description": "Search verified groomers by location, breed expertise, specialization, or cut style.",
        "input_schema": {
            "type": "object",
            "properties": {
                "location":       {"type": "string"},
                "breed":          {"type": "string"},
                "specialization": {"type": "string"},
                "cut_style":      {"type": "string"},
            },
            "required": ["location"],
        },
    },
    {
        "name": "get_groomer_profile",
        "description": "Get a groomer's full profile, services, and recent reviews.",
        "input_schema": {
            "type": "object",
            "properties": {"groomer_id": {"type": "integer"}},
            "required": ["groomer_id"],
        },
    },
    {
        "name": "browse_portfolio",
        "description": "Browse a groomer's verified portfolio photos with linked reviews. Filter by breed or cut style.",
        "input_schema": {
            "type": "object",
            "properties": {
                "groomer_id": {"type": "integer"},
                "breed":      {"type": "string"},
                "cut_style":  {"type": "string"},
            },
            "required": ["groomer_id"],
        },
    },
    {
        "name": "check_availability",
        "description": "Check open time slots for a groomer on a given date.",
        "input_schema": {
            "type": "object",
            "properties": {
                "groomer_id": {"type": "integer"},
                "date":       {"type": "string", "description": "YYYY-MM-DD"},
            },
            "required": ["groomer_id", "date"],
        },
    },
    {
        "name": "find_owner",
        "description": "Look up an owner account by phone number.",
        "input_schema": {
            "type": "object",
            "properties": {"phone": {"type": "string"}},
            "required": ["phone"],
        },
    },
    {
        "name": "register_owner",
        "description": "Create a new KindPaw account for a pet owner.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name":  {"type": "string"},
                "phone": {"type": "string"},
                "email": {"type": "string"},
            },
            "required": ["name", "phone"],
        },
    },
    {
        "name": "add_dog",
        "description": "Add a dog to an owner's passport.",
        "input_schema": {
            "type": "object",
            "properties": {
                "owner_id":                 {"type": "integer"},
                "name":                     {"type": "string"},
                "breed":                    {"type": "string"},
                "age_years":                {"type": "number"},
                "weight_lbs":               {"type": "number"},
                "coat_type":                {"type": "string", "description": "e.g. curly, long, short, double"},
                "temperament_tags":         {"type": "array", "items": {"type": "string"}},
                "default_special_requests": {"type": "string"},
            },
            "required": ["owner_id", "name", "breed"],
        },
    },
    {
        "name": "book_appointment",
        "description": "Book a grooming appointment. Confirm all details with the owner before calling this.",
        "input_schema": {
            "type": "object",
            "properties": {
                "owner_id":        {"type": "integer"},
                "dog_id":          {"type": "integer"},
                "groomer_id":      {"type": "integer"},
                "service_id":      {"type": "integer"},
                "date":            {"type": "string", "description": "YYYY-MM-DD"},
                "time":            {"type": "string", "description": "HH:MM (24-hour)"},
                "special_requests":{"type": "string"},
                "cut_style":       {"type": "string"},
            },
            "required": ["owner_id", "dog_id", "groomer_id", "service_id", "date", "time"],
        },
    },
    {
        "name": "list_my_bookings",
        "description": "List all bookings for an owner.",
        "input_schema": {
            "type": "object",
            "properties": {"owner_id": {"type": "integer"}},
            "required": ["owner_id"],
        },
    },
    {
        "name": "get_dog_history",
        "description": "Get a dog's full passport: groom history, health records, photos, and reviews.",
        "input_schema": {
            "type": "object",
            "properties": {"dog_id": {"type": "integer"}},
            "required": ["dog_id"],
        },
    },
    {
        "name": "cancel_booking",
        "description": "Cancel a booking by its KP- reference ID.",
        "input_schema": {
            "type": "object",
            "properties": {"booking_id": {"type": "string"}},
            "required": ["booking_id"],
        },
    },
    {
        "name": "leave_review",
        "description": "Leave a star rating and review for a completed booking.",
        "input_schema": {
            "type": "object",
            "properties": {
                "booking_id":  {"type": "string"},
                "rating":      {"type": "integer", "description": "1 to 5"},
                "review_text": {"type": "string"},
            },
            "required": ["booking_id", "rating", "review_text"],
        },
    },
]

SYSTEM = f"""You are Sage, KindPaw's pet care coordinator — warm, fast, and focused on getting things done.

KindPaw: healthy dogs first, beautiful second. Dogs are family.

## Speed rules — follow exactly

**Gather everything in one message.** Never ask for information one piece at a time. If you need a phone number AND what they want, ask for both together. Example first message: "Hi! What's your phone number, which dog are you booking for, and what do you need today?"

**After login, act immediately.** Call find_owner, then list their dogs and offer direct choices — don't ask open-ended questions. Example: "Welcome back Emma! I see Max (Goldendoodle) and Bella (Shih Tzu). Book a groom, view history, or something else?"

**One confirmation before booking.** Gather all details first (groomer, service, date, time), then one confirmation message: "Booking Max's teddy bear cut with Sarah — June 17 at 10am, $85 total, $25.50 deposit due now. Confirm?" Book immediately on yes.

**No filler phrases.** Skip "Great!", "Sure!", "Of course!", "Absolutely!" — just act.

**One-shot commands work.** "Book Max's teddy bear cut with Sarah next Tuesday at 10" → check that slot → confirm once → book. Don't ask clarifying questions you can infer.

**Breed mentioned without cut style?** Call get_breed_cuts immediately and present the options in the same response.

**"Do this cut again"** → call get_dog_history → pre-fill groomer, service, cut style → go straight to date/time selection.

## Health first
- Surface Fear Free certified groomers for anxious or senior dogs
- If past groom records have health flags, mention them: "Bella's last groomer noted mild tear staining — worth keeping an eye on"
- Merge dog's default special requests into every booking automatically

After booking always confirm: groomer, date, time, service, cut style, deposit charged, remaining balance, booking reference.

Today is {datetime.now().strftime('%Y-%m-%d (%A)')}."""


# ---------------------------------------------------------------------------
# Chat loop
# ---------------------------------------------------------------------------

def run_tool(name: str, inputs: dict) -> str:
    fn = TOOL_MAP.get(name)
    if fn:
        return json.dumps(fn(inputs))
    return json.dumps({"error": f"Unknown tool: {name}"})


def chat(messages: list) -> tuple[str, list]:
    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=SYSTEM,
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


def main():
    print("=" * 55)
    print("  KindPaw — Pet Owner Booking Assistant")
    print("=" * 55)
    print("Type 'quit' to exit.\n")

    messages = []
    reply, messages = chat([{"role": "user", "content": "Hello!"}])
    print(f"Sage: {reply}\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("quit", "exit", "bye"):
            print("Sage: Take care — give your pup a hug from KindPaw!")
            break
        if not user_input:
            continue
        messages.append({"role": "user", "content": user_input})
        reply, messages = chat(messages)
        print(f"\nSage: {reply}\n")


if __name__ == "__main__":
    bootstrap()
    main()
