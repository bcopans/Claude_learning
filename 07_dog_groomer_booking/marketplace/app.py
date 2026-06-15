"""
KindPaw — Flask web app

Routes:
  GET  /              landing page (choose owner or groomer)
  GET  /owner         pet owner chat
  GET  /groomer/<id>  groomer dashboard chat
  POST /api/chat      send a message, get a reply
  GET  /api/groomers  list groomers (for landing page)
"""

import os
import sys
import uuid

from flask import Flask, jsonify, render_template, request, session

sys.path.insert(0, os.path.dirname(__file__))

from db import bootstrap, get_conn
import owner_bot
import groomer_bot

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))

# In-memory conversation store: session_id → {messages, role, groomer_id?, ...}
# (fine for a demo — resets on restart)
conversations: dict = {}


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


@app.route("/api/chat", methods=["POST"])
def chat():
    sid = session.get("id")
    if not sid or sid not in conversations:
        return jsonify({"error": "Session expired — please refresh the page."}), 400

    conv = conversations[sid]
    message = (request.json or {}).get("message", "").strip()
    if not message:
        return jsonify({"error": "Empty message."}), 400

    conv["messages"].append({"role": "user", "content": message})

    try:
        if conv["role"] == "owner":
            reply, updated = owner_bot.chat(conv["messages"])
        else:
            system = groomer_bot.build_system(
                conv["groomer_id"], conv["groomer_name"], conv["business_name"]
            )
            reply, updated = groomer_bot.chat(conv["messages"], system)

        conv["messages"] = updated
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/groomers")
def list_groomers():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, name, business_name, avg_rating, total_reviews, specialization_tags FROM groomers ORDER BY id"
        ).fetchall()
    import json
    return jsonify([
        {**dict(r), "specialization_tags": json.loads(r["specialization_tags"])}
        for r in rows
    ])


if __name__ == "__main__":
    bootstrap()
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
