"""
KindPaw — Flask web app

Routes:
  GET  /                  landing page
  GET  /owner             pet owner chat
  GET  /groomer/<id>      groomer dashboard chat
  GET  /profile           owner profile page (lookup by phone)
  POST /api/chat/stream   streaming chat endpoint (SSE)
  GET  /api/groomers      list groomers
  GET  /api/profile       owner profile data (JSON)
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

# In-memory conversation store: session_id → {messages, role, ...}
conversations: dict = {}


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


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
def groomer(groomer_id):
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


# ---------------------------------------------------------------------------
# Streaming chat
# ---------------------------------------------------------------------------

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
        system    = owner_bot.SYSTEM
        tools     = owner_bot.TOOLS
        run_tool  = owner_bot.run_tool
    else:
        system    = groomer_bot.build_system(conv["groomer_id"], conv["groomer_name"], conv["business_name"])
        tools     = groomer_bot.TOOLS
        run_tool  = groomer_bot.run_tool

    messages = conv["messages"]

    @stream_with_context
    def generate():
        for event_type, data in stream_chat(messages, system, tools, run_tool):
            yield f"data: {json.dumps({'type': event_type, 'data': data})}\n\n"

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control":    "no-cache",
            "X-Accel-Buffering": "no",
            "Connection":       "keep-alive",
        },
    )


# ---------------------------------------------------------------------------
# Data APIs
# ---------------------------------------------------------------------------

@app.route("/api/groomers")
def list_groomers():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, name, business_name, avg_rating, total_reviews, specialization_tags FROM groomers ORDER BY id"
        ).fetchall()
    return jsonify([
        {**dict(r), "specialization_tags": json.loads(r["specialization_tags"])}
        for r in rows
    ])


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
            "SELECT id, name, breed, age_years, coat_type, temperament_tags FROM dogs WHERE owner_id=?",
            (owner["id"],),
        ).fetchall()

        bookings = conn.execute("""
            SELECT b.id, b.date, b.time, b.status, b.cut_style, b.total_price,
                   d.name AS dog_name, d.breed,
                   g.name AS groomer_name, g.business_name,
                   s.name AS service_name,
                   gr.health_flags, gr.next_recommended_groom
            FROM bookings b
            JOIN dogs d ON b.dog_id = d.id
            JOIN groomers g ON b.groomer_id = g.id
            JOIN services s ON b.service_id = s.id
            LEFT JOIN groom_records gr ON gr.booking_id = b.id
            WHERE b.owner_id=?
            ORDER BY b.date DESC LIMIT 10
        """, (owner["id"],)).fetchall()

    return jsonify({
        "found":    True,
        "owner":    {"id": owner["id"], "name": owner["name"], "phone": owner["phone"]},
        "dogs":     [
            {**dict(d), "temperament_tags": json.loads(d["temperament_tags"])}
            for d in dogs
        ],
        "bookings": [dict(b) for b in bookings],
    })


if __name__ == "__main__":
    bootstrap()
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
