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
  GET  /api/groomers                  all groomers (search page)
  GET  /api/groomer/<id>              single groomer full detail
  GET  /api/slots/<id>/<date>         available time slots
  GET  /api/profile                   owner lookup by phone
  POST /api/book                      submit booking from UI
  POST /api/upload                    upload an image, returns {url}
  POST /api/groomer/<id>/photo        set groomer profile photo
  POST /api/dog/<id>/photo            set dog profile photo
  POST /api/portfolio-photo           add a portfolio groom photo
  POST /api/chat/stream               streaming chat (SSE)
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

# ── Ensure photo_url columns exist (migration for existing DBs) ───────────────
def _add_photo_columns():
    with get_conn() as conn:
        for sql in [
            "ALTER TABLE groomers ADD COLUMN photo_url TEXT DEFAULT ''",
            "ALTER TABLE dogs     ADD COLUMN photo_url TEXT DEFAULT ''",
        ]:
            try:
                conn.execute(sql)
                conn.commit()
            except Exception:
                pass  # column already exists

_add_photo_columns()

UPLOAD_DIR      = os.path.join(os.path.dirname(__file__), "static", "uploads")
ALLOWED_EXTS    = {"png", "jpg", "jpeg", "gif", "webp"}
MAX_UPLOAD_BYTES = 8 * 1024 * 1024  # 8 MB


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


@app.route("/groomer/<int:groomer_id>/earnings")
def groomer_earnings_page(groomer_id):
    with get_conn() as conn:
        g = conn.execute("SELECT * FROM groomers WHERE id=?", (groomer_id,)).fetchone()
    if not g:
        return "Groomer not found", 404
    return render_template("groomer_earnings.html", groomer_id=groomer_id, groomer_name=g["name"])


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
        groomer_id=groomer_id,
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
                "id":                  g["id"],
                "name":                g["name"],
                "business_name":       g["business_name"],
                "location":            g["location"],
                "bio":                 g["bio"],
                "avg_rating":          g["avg_rating"],
                "total_reviews":       g["total_reviews"],
                "certification_tags":  json.loads(g["certification_tags"]),
                "specialization_tags": json.loads(g["specialization_tags"]),
                "breed_expertise":     json.loads(g["breed_expertise"]),
                "cut_specialties":     json.loads(g["cut_specialties"]),
                "starting_from":       min_price,
                "lat":                 g["lat"] if g["lat"] else 0,
                "lng":                 g["lng"] if g["lng"] else 0,
                "photo_url":           g["photo_url"] or "",
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
        "id":                  g["id"],
        "name":                g["name"],
        "business_name":       g["business_name"],
        "location":            g["location"],
        "phone":               g["phone"],
        "bio":                 g["bio"],
        "avg_rating":          g["avg_rating"],
        "total_reviews":       g["total_reviews"],
        "certification_tags":  json.loads(g["certification_tags"]),
        "specialization_tags": json.loads(g["specialization_tags"]),
        "breed_expertise":     json.loads(g["breed_expertise"]),
        "cut_specialties":     json.loads(g["cut_specialties"]),
        "photo_url":           g["photo_url"] or "",
        "services":            [dict(s) for s in services],
        "portfolio":           [dict(p) for p in photos],
        "reviews":             [dict(r) for r in reviews],
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
        "found":  True,
        "owner":  {"id": owner["id"], "name": owner["name"], "phone": owner["phone"]},
        "dogs":   [{**dict(d), "temperament_tags": json.loads(d["temperament_tags"]), "photo_url": d["photo_url"] or ""} for d in dogs],
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


@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.json or {}
    name     = (data.get("name") or "").strip()
    phone    = (data.get("phone") or "").strip()
    dog_name = (data.get("dog_name") or "").strip()
    breed    = (data.get("breed") or "").strip()

    if not name or not phone:
        return jsonify({"error": "Name and phone are required."}), 400

    with get_conn() as conn:
        existing = conn.execute("SELECT id FROM owners WHERE phone=?", (phone,)).fetchone()
        if existing:
            return jsonify({"error": "An account with that phone number already exists."}), 400

        conn.execute("INSERT INTO owners (name, phone) VALUES (?,?)", (name, phone))
        owner_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        dogs = []
        if dog_name and breed:
            conn.execute(
                "INSERT INTO dogs (owner_id, name, breed, temperament_tags) VALUES (?,?,?,?)",
                (owner_id, dog_name, breed, "[]"),
            )
            dog_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            dogs = [{"id": dog_id, "name": dog_name, "breed": breed, "age_years": None, "temperament_tags": []}]

        conn.commit()

    return jsonify({
        "success": True,
        "owner":   {"id": owner_id, "name": name, "phone": phone},
        "dogs":    dogs,
    })


# ─── Photo upload APIs ───────────────────────────────────────────────────────

@app.route("/api/upload", methods=["POST"])
def api_upload():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "No file selected"}), 400

    ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else ""
    if ext not in ALLOWED_EXTS:
        return jsonify({"error": "Images only (jpg, png, gif, webp)"}), 400

    f.seek(0, 2)
    size = f.tell()
    f.seek(0)
    if size > MAX_UPLOAD_BYTES:
        return jsonify({"error": "File too large (max 8 MB)"}), 400

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.{ext}"
    f.save(os.path.join(UPLOAD_DIR, filename))
    return jsonify({"url": f"/static/uploads/{filename}"})


@app.route("/api/groomer/<int:groomer_id>/photo", methods=["POST"])
def api_groomer_photo(groomer_id):
    url = (request.json or {}).get("url", "").strip()
    with get_conn() as conn:
        conn.execute("UPDATE groomers SET photo_url=? WHERE id=?", (url, groomer_id))
        conn.commit()
    return jsonify({"success": True})


@app.route("/api/dog/<int:dog_id>/photo", methods=["POST"])
def api_dog_photo(dog_id):
    url = (request.json or {}).get("url", "").strip()
    with get_conn() as conn:
        conn.execute("UPDATE dogs SET photo_url=? WHERE id=?", (url, dog_id))
        conn.commit()
    return jsonify({"success": True})


@app.route("/api/portfolio-photo", methods=["POST"])
def api_portfolio_photo():
    data = request.json or {}
    required = ["groomer_id", "dog_id", "url"]
    missing  = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing: {', '.join(missing)}"}), 400
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO groom_photos
              (dog_id, groomer_id, photo_url, caption, cut_style, is_portfolio, verified)
            VALUES (?,?,?,?,?,1,0)
        """, (data["dog_id"], data["groomer_id"], data["url"],
              data.get("caption", ""), data.get("cut_style", "")))
        conn.commit()
    return jsonify({"success": True})


# ─── Earnings API ────────────────────────────────────────────────────────────

@app.route("/api/groomer/<int:groomer_id>/earnings")
def api_groomer_earnings(groomer_id):
    from datetime import date, timedelta
    today = date.today()
    week_ago  = (today - timedelta(days=7)).isoformat()
    month_ago = (today - timedelta(days=30)).isoformat()

    with get_conn() as conn:
        bookings = conn.execute("""
            SELECT b.id, b.date, b.time, b.total_price, b.cut_style,
                   d.name AS dog_name, d.breed,
                   o.name AS owner_name,
                   s.name AS service_name
            FROM bookings b
            JOIN dogs d ON b.dog_id = d.id
            JOIN owners o ON b.owner_id = o.id
            JOIN services s ON b.service_id = s.id
            WHERE b.groomer_id=? AND b.status='completed'
            ORDER BY b.date DESC, b.time DESC
        """, (groomer_id,)).fetchall()

        service_rows = conn.execute("""
            SELECT s.name, COUNT(*) as count, SUM(b.total_price) as total
            FROM bookings b
            JOIN services s ON b.service_id = s.id
            WHERE b.groomer_id=? AND b.status='completed'
            GROUP BY s.name
            ORDER BY total DESC
        """, (groomer_id,)).fetchall()

    all_bookings = [dict(b) for b in bookings]

    def _sum(rows):
        return round(sum(r["total_price"] or 0 for r in rows), 2)

    week_b  = [b for b in all_bookings if b["date"] >= week_ago]
    month_b = [b for b in all_bookings if b["date"] >= month_ago]

    # Weekly buckets for last 8 weeks
    weekly = []
    for w in range(7, -1, -1):
        start = (today - timedelta(days=(w + 1) * 7)).isoformat()
        end   = (today - timedelta(days=w * 7)).isoformat()
        label = (today - timedelta(days=w * 7)).strftime("%-m/%-d") if w > 0 else "This wk"
        bucket = [b for b in all_bookings if start <= b["date"] < end]
        weekly.append({"label": label, "total": _sum(bucket), "count": len(bucket)})

    return jsonify({
        "this_week":  {"total": _sum(week_b),  "count": len(week_b)},
        "this_month": {"total": _sum(month_b), "count": len(month_b)},
        "all_time":   {"total": _sum(all_bookings), "count": len(all_bookings)},
        "weekly":     weekly,
        "by_service": [dict(r) for r in service_rows],
        "recent":     all_bookings[:20],
    })


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
