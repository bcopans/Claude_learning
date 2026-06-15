"""
KindPaw — Flask web app

Pages:
  GET  /                      landing
  GET  /search                groomer search + cards
  GET  /groomer/<id>/profile  groomer profile + portfolio
  GET  /book/<groomer_id>     booking flow (UI)
  GET  /owner                 owner chat (discovery / complex questions)
  GET  /groomer/<id>          groomer chat dashboard
  GET  /profile               owner profile lookup

APIs:
  GET  /api/groomers               all groomers (search page)
  GET  /api/groomer/<id>           single groomer full detail
  GET  /api/slots/<id>/<date>      available time slots
  GET  /api/profile                owner lookup by phone
  POST /api/book                   submit booking from UI
  POST /api/chat/stream            streaming chat (SSE)
"""

import json
import os
import sys
import uuid

from flask import Flask, Response, jsonify, render_template, request, session, stream_with_context

sys.path.insert(0, os.path.dirname(__file__))

from db import bootstrap, get_conn
import owner_bot
import groomer_bot
from stream_utils import stream_chat

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))

bootstrap()


# ─── Pages ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search")
def search():
    return render_template("search.html")


@app.route("/groomer/<int:groomer_id>/profile")
def groomer_profile_page(groomer_id):
    return render_template("groomer_profile.html", groomer_id=groomer_id)


@app.route("/book/<int:groomer_id>")
def book_page(groomer_id):
    return render_template("book.html", groomer_id=groomer_id)


@app.route("/owner")
def owner():
    sid = str(uuid.uuid4())
    session["id"] = sid
    conversations[sid] = {"messages": [], "role": "owner"}
    return render_template(
        "chat.html",
        title="Sage — Pet Care Coordinator",
        role="owner",
        initial_message="Hello!",
    )


@app.route("/groomer/<int:groomer_id>")
def groomer_chat(groomer_id):
    with get_conn() as conn:
        g = conn.execute("SELECT * FROM groomers WHERE id=?", (groomer_id,)).fetchone()
    if not g:
        return "Groomer not found", 404
    sid = str(uuid.uuid4())
    session["id"] = sid
    conversations[sid] = {
        "messages":      [],
        "role":          "groomer",
        "groomer_id":    groomer_id,
        "groomer_name":  g["name"],
        "business_name": g["business_name"],
    }
    return render_template(
        "chat.html",
        title=f"{g['name']} — Groomer Dashboard",
        role="groomer",
        initial_message="Show me what's on my schedule today and tomorrow.",
    )


@app.route("/profile")
def profile():
    return render_template("profile.html")


conversations: dict = {}


# ─── Data APIs ───────────────────────────────────────────────────────────────

@app.route("/api/groomers")
def api_groomers():
    with get_conn() as conn:
        groomers = conn.execute("SELECT * FROM groomers WHERE verified=1 ORDER BY avg_rating DESC").fetchall()
        result = []
        for g in groomers:
            min_price = conn.execute(
                "SELECT MIN(price) as p FROM services WHERE groomer_id=?", (g["id"],)
            ).fetchone()["p"]
            result.append({
                "id":                g["id"],
                "name":              g["name"],
                "business_name":     g["business_name"],
                "location":          g["location"],
                "bio":               g["bio"],
                "avg_rating":        g["avg_rating"],
                "total_reviews":     g["total_reviews"],
                "certification_tags": json.loads(g["certification_tags"]),
                "specialization_tags": json.loads(g["specialization_tags"]),
                "breed_expertise":   json.loads(g["breed_expertise"]),
                "cut_specialties":   json.loads(g["cut_specialties"]),
                "starting_from":     min_price,
            })
    return jsonify(result)


@app.route("/api/groomer/<int:groomer_id>")
def api_groomer(groomer_id):
    with get_conn() as conn:
        g = conn.execute("SELECT * FROM groomers WHERE id=?", (groomer_id,)).fetchone()
        if not g:
            return jsonify({"error": "Not found"}), 404

        services = conn.execute(
            "SELECT * FROM services WHERE groomer_id=? ORDER BY price", (groomer_id,)
        ).fetchall()

        photos = conn.execute("""
            SELECT p.id, p.photo_url, p.caption, p.cut_style, p.created_at,
                   d.name AS dog_name, d.breed,
                   r.rating, r.review_text
            FROM groom_photos p
            JOIN dogs d ON p.dog_id = d.id
            LEFT JOIN reviews r ON r.booking_id = p.booking_id
            WHERE p.groomer_id=? AND p.verified=1
            ORDER BY p.created_at DESC
        """, (groomer_id,)).fetchall()

        reviews = conn.execute("""
            SELECT r.rating, r.review_text, r.cut_style, r.created_at,
                   d.name AS dog_name, d.breed, o.name AS owner_name
            FROM reviews r
            JOIN dogs d ON r.dog_id = d.id
            JOIN owners o ON r.owner_id = o.id
            WHERE r.groomer_id=? ORDER BY r.created_at DESC
        """, (groomer_id,)).fetchall()

    return jsonify({
        "id":                g["id"],
        "name":              g["name"],
        "business_name":     g["business_name"],
        "location":          g["location"],
        "phone":             g["phone"],
        "bio":               g["bio"],
        "avg_rating":        g["avg_rating"],
        "total_reviews":     g["total_reviews"],
        "certification_tags": json.loads(g["certification_tags"]),
        "specialization_tags": json.loads(g["specialization_tags"]),
        "breed_expertise":   json.loads(g["breed_expertise"]),
        "cut_specialties":   json.loads(g["cut_specialties"]),
        "services":          [dict(s) for s in services],
        "portfolio":         [dict(p) for p in photos],
        "reviews":           [dict(r) for r in reviews],
    })


@app.route("/api/slots/<int:groomer_id>/<date>")
def api_slots(groomer_id, date):
    with get_conn() as conn:
        slots = conn.execute(
            "SELECT time_slot FROM availability WHERE groomer_id=? AND date=? AND is_booked=0 ORDER BY time_slot",
            (groomer_id, date),
        ).fetchall()
    return jsonify({"slots": [s["time_slot"] for s in slots]})


@app.route("/api/profile")
def api_profile():
    phone = request.args.get("phone", "").strip()
    if not phone:
        return jsonify({"error": "Phone number required."}), 400
    with get_conn() as conn:
        owner = conn.execute("SELECT * FROM owners WHERE phone=?", (phone,)).fetchone()
        if not owner:
            return jsonify({"found": False}), 404
        dogs = conn.execute(
            "SELECT id, name, breed, age_years, coat_type, temperament_tags, default_special_requests FROM dogs WHERE owner_id=?",
            (owner["id"],),
        ).fetchall()
        bookings = conn.execute("""
            SELECT b.id, b.date, b.time, b.status, b.cut_style, b.total_price,
                   d.name AS dog_name, d.breed,
                   g.name AS groomer_name, g.business_name,
                   s.name AS service_name, gr.health_flags, gr.next_recommended_groom
            FROM bookings b
            JOIN dogs d ON b.dog_id = d.id
            JOIN groomers g ON b.groomer_id = g.id
            JOIN services s ON b.service_id = s.id
            LEFT JOIN groom_records gr ON gr.booking_id = b.id
            WHERE b.owner_id=? ORDER BY b.date DESC LIMIT 10
        """, (owner["id"],)).fetchall()
    return jsonify({
        "found":    True,
        "owner":    {"id": owner["id"], "name": owner["name"], "phone": owner["phone"]},
        "dogs":     [{**dict(d), "temperament_tags": json.loads(d["temperament_tags"])} for d in dogs],
        "bookings": [dict(b) for b in bookings],
    })


@app.route("/api/book", methods=["POST"])
def api_book():
    data = request.json or {}
    required = ["owner_id", "dog_id", "groomer_id", "service_id", "date", "time"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing: {', '.join(missing)}"}), 400

    from owner_bot import book_appointment
    result = book_appointment(
        owner_id=data["owner_id"],
        dog_id=data["dog_id"],
        groomer_id=data["groomer_id"],
        service_id=data["service_id"],
        date=data["date"],
        time=data["time"],
        special_requests=data.get("special_requests", ""),
        cut_style=data.get("cut_style", ""),
    )
    status = 200 if result.get("success") else 400
    return jsonify(result), status


# ─── Streaming chat ───────────────────────────────────────────────────────────

@app.route("/api/chat/stream", methods=["POST"])
def chat_stream():
    sid = session.get("id")
    if not sid or sid not in conversations:
        def expired():
            yield f"data: {json.dumps({'type': 'error', 'data': 'Session expired — please refresh.'})}\n\n"
        return Response(expired(), mimetype="text/event-stream")

    conv = conversations[sid]
    message = (request.json or {}).get("message", "").strip()
    if not message:
        def empty():
            yield f"data: {json.dumps({'type': 'error', 'data': 'Empty message.'})}\n\n"
        return Response(empty(), mimetype="text/event-stream")

    conv["messages"].append({"role": "user", "content": message})

    if conv["role"] == "owner":
        system   = owner_bot.SYSTEM
        tools    = owner_bot.TOOLS
        run_tool = owner_bot.run_tool
    else:
        system   = groomer_bot.build_system(conv["groomer_id"], conv["groomer_name"], conv["business_name"])
        tools    = groomer_bot.TOOLS
        run_tool = groomer_bot.run_tool

    messages = conv["messages"]

    @stream_with_context
    def generate():
        for event_type, data in stream_chat(messages, system, tools, run_tool):
            yield f"data: {json.dumps({'type': event_type, 'data': data})}\n\n"

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
