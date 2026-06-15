"""
KindPaw — SQLite database setup, seed data, and connection helper.
"""

import json
import os
import random
import sqlite3
import string
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "kindpaw.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS owners (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    phone      TEXT NOT NULL UNIQUE,
    email      TEXT DEFAULT '',
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS dogs (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id                INTEGER REFERENCES owners(id),
    name                    TEXT NOT NULL,
    breed                   TEXT NOT NULL,
    age_years               REAL DEFAULT 0,
    weight_lbs              REAL DEFAULT 0,
    coat_type               TEXT DEFAULT '',
    temperament_tags        TEXT DEFAULT '[]',
    default_special_requests TEXT DEFAULT '',
    created_at              TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS groomers (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    name                TEXT NOT NULL,
    business_name       TEXT NOT NULL,
    location            TEXT NOT NULL,
    phone               TEXT NOT NULL,
    email               TEXT DEFAULT '',
    bio                 TEXT DEFAULT '',
    certification_tags  TEXT DEFAULT '[]',
    specialization_tags TEXT DEFAULT '[]',
    breed_expertise     TEXT DEFAULT '[]',
    cut_specialties     TEXT DEFAULT '[]',
    avg_rating          REAL DEFAULT 0.0,
    total_reviews       INTEGER DEFAULT 0,
    verified            INTEGER DEFAULT 0,
    created_at          TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS services (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    groomer_id    INTEGER NOT NULL REFERENCES groomers(id),
    name          TEXT NOT NULL,
    description   TEXT DEFAULT '',
    price         REAL NOT NULL,
    duration_mins INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS availability (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    groomer_id INTEGER NOT NULL REFERENCES groomers(id),
    date       TEXT NOT NULL,
    time_slot  TEXT NOT NULL,
    is_booked  INTEGER DEFAULT 0,
    UNIQUE(groomer_id, date, time_slot)
);

CREATE TABLE IF NOT EXISTS bookings (
    id               TEXT PRIMARY KEY,
    owner_id         INTEGER REFERENCES owners(id),
    dog_id           INTEGER REFERENCES dogs(id),
    groomer_id       INTEGER REFERENCES groomers(id),
    service_id       INTEGER REFERENCES services(id),
    date             TEXT NOT NULL,
    time             TEXT NOT NULL,
    special_requests TEXT DEFAULT '',
    cut_style        TEXT DEFAULT '',
    status           TEXT DEFAULT 'confirmed',
    deposit_paid     REAL DEFAULT 0.0,
    total_price      REAL DEFAULT 0.0,
    platform_fee     REAL DEFAULT 0.0,
    groomer_earnings REAL DEFAULT 0.0,
    created_at       TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS groom_records (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id              TEXT UNIQUE REFERENCES bookings(id),
    dog_id                  INTEGER REFERENCES dogs(id),
    groomer_id              INTEGER REFERENCES groomers(id),
    coat_condition          TEXT DEFAULT '',
    skin_condition          TEXT DEFAULT '',
    ear_condition           TEXT DEFAULT '',
    nail_condition          TEXT DEFAULT '',
    eye_condition           TEXT DEFAULT '',
    health_flags            TEXT DEFAULT '',
    groomer_private_note    TEXT DEFAULT '',
    next_recommended_groom  TEXT DEFAULT '',
    completed_at            TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS groom_photos (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id   TEXT REFERENCES bookings(id),
    dog_id       INTEGER REFERENCES dogs(id),
    groomer_id   INTEGER REFERENCES groomers(id),
    photo_url    TEXT NOT NULL,
    caption      TEXT DEFAULT '',
    cut_style    TEXT DEFAULT '',
    is_portfolio INTEGER DEFAULT 0,
    verified     INTEGER DEFAULT 1,
    created_at   TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS reviews (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id  TEXT UNIQUE REFERENCES bookings(id),
    owner_id    INTEGER REFERENCES owners(id),
    groomer_id  INTEGER REFERENCES groomers(id),
    dog_id      INTEGER REFERENCES dogs(id),
    photo_id    INTEGER REFERENCES groom_photos(id),
    rating      INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
    review_text TEXT DEFAULT '',
    cut_style   TEXT DEFAULT '',
    created_at  TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS breed_cuts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    breed       TEXT NOT NULL,
    cut_style   TEXT NOT NULL,
    description TEXT DEFAULT '',
    UNIQUE(breed, cut_style)
);
"""

BREED_CUTS_SEED = [
    ("Goldendoodle", "Teddy Bear",  "Rounded fluffy face and even body — the most popular Doodle style"),
    ("Goldendoodle", "Puppy Cut",   "Short, uniform trim all over — low-maintenance and practical"),
    ("Goldendoodle", "Lamb Cut",    "Short body with fluffy leg furnishings — dramatic contrast"),
    ("Goldendoodle", "Kennel Cut",  "Very short all over for maximum easy-care maintenance"),
    ("Poodle", "Continental",       "Classic show style with shaved hindquarters and pompoms on hips and ankles"),
    ("Poodle", "Puppy Cut",         "Even, fluffy trim all over — most popular pet Poodle style"),
    ("Poodle", "Sporting Clip",     "Short body, slightly longer legs — athletic and neat"),
    ("Poodle", "English Saddle",    "Traditional show cut with a curved saddle shape on the back"),
    ("Poodle", "Teddy Bear",        "Rounded face and fluffy body — softer than classic show styles"),
    ("Shih Tzu", "Puppy Cut",       "Short easy-care trim all over — best for active dogs"),
    ("Shih Tzu", "Top Knot Show",   "Full floor-length coat with topknot — traditional show style"),
    ("Shih Tzu", "Lion Cut",        "Shaved body with a full fluffy mane and face"),
    ("Shih Tzu", "Teddy Bear",      "Rounded face with medium body length — adorable and practical"),
    ("Shih Tzu", "Practical Top Knot", "Moderate length with topknot — low-maintenance show look"),
    ("Labrador Retriever", "Bath & Deshed", "Deep clean with professional deshedding — essential coat maintenance"),
    ("Labrador Retriever", "Tidy Trim",     "Neatening paws, ears, and tail; full bath and blow-out"),
    ("Golden Retriever", "Bath & Blow-Out", "Deep clean with professional blow-dry to manage shedding"),
    ("Golden Retriever", "Feathering Trim", "Neatening of ears, tail, legs, and belly feathering"),
    ("Golden Retriever", "Tidy Up",         "Light scissor trim to neaten the natural Golden coat"),
    ("German Shepherd", "Deshed & Bath",    "Professional deshedding to reduce shedding and promote coat health"),
    ("German Shepherd", "Sanitary Trim",    "Light trim around sanitary areas and paws"),
    ("Siberian Husky", "Deshed & Bath",     "Essential maintenance — never shave a Husky; deshedding only"),
    ("Siberian Husky", "Blow-Out",          "High-velocity drying removes dead undercoat dramatically"),
    ("Schnauzer", "Traditional Schnauzer",  "Classic beard, eyebrows, and leg furnishings; short body"),
    ("Schnauzer", "Puppy Cut",              "Even trim all over with a soft beard and brows"),
    ("Schnauzer", "Neaten",                 "Light tidy-up of existing Schnauzer cut between full grooms"),
    ("Bichon Frise", "Show Bichon",         "Traditional round powder-puff head; fluffy even body"),
    ("Bichon Frise", "Puppy Cut",           "Shorter easy-care version of the classic round Bichon style"),
    ("Maltese", "Puppy Cut",                "Short practical trim — keeps the floor-length coat manageable"),
    ("Maltese", "Show Coat",                "Full-length silky coat with center part — traditional show style"),
    ("Yorkshire Terrier", "Puppy Cut",      "Short practical trim all over"),
    ("Yorkshire Terrier", "Traditional",    "Floor-length silky coat with bows — classic Yorkie show style"),
    ("Cocker Spaniel", "Puppy Cut",         "Short practical trim all over"),
    ("Cocker Spaniel", "Traditional Cocker","Long ears with full feathering on legs and body"),
    ("Cocker Spaniel", "Sporting Clip",     "Short body with natural feathering — athletic and neat"),
]


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def new_booking_id() -> str:
    return "KP-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)
        conn.commit()


def seed_db():
    with get_conn() as conn:
        if conn.execute("SELECT COUNT(*) FROM groomers").fetchone()[0] > 0:
            return

        # --- Groomers ---
        conn.execute("""
            INSERT INTO groomers
              (name, business_name, location, phone, email, bio,
               certification_tags, specialization_tags, breed_expertise, cut_specialties,
               avg_rating, total_reviews, verified)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            "Sarah Chen", "Gentle Paws Studio", "Portland, OR",
            "(503) 555-0011", "sarah@gentlepaws.com",
            "12 years grooming with a focus on anxious and sensitive dogs. "
            "Every dog deserves to feel safe — I take my time and never rush.",
            json.dumps(["Fear Free Certified", "NDGAA"]),
            json.dumps(["anxious dogs", "puppies", "sensitive breeds"]),
            json.dumps(["Goldendoodle", "Labradoodle", "Poodle", "Cockapoo", "Cavapoo"]),
            json.dumps(["teddy bear", "puppy cut", "lamb cut"]),
            4.9, 87, 1,
        ))  # groomer_id = 1

        conn.execute("""
            INSERT INTO groomers
              (name, business_name, location, phone, email, bio,
               certification_tags, specialization_tags, breed_expertise, cut_specialties,
               avg_rating, total_reviews, verified)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            "Marcus Webb", "The Grooming Gallery", "Portland, OR",
            "(503) 555-0022", "marcus@grooominggallery.com",
            "15 years of competitive show grooming. I bring competition-level "
            "precision to every pet groom. Flawless and technically perfect.",
            json.dumps(["IPG Certified", "NDGAA"]),
            json.dumps(["show cuts", "hand-stripping", "large breeds", "breed standard"]),
            json.dumps(["Poodle", "Schnauzer", "Airedale Terrier", "German Shepherd", "Golden Retriever"]),
            json.dumps(["continental", "show cut", "sporting clip", "hand-strip", "traditional schnauzer"]),
            4.8, 134, 1,
        ))  # groomer_id = 2

        conn.execute("""
            INSERT INTO groomers
              (name, business_name, location, phone, email, bio,
               certification_tags, specialization_tags, breed_expertise, cut_specialties,
               avg_rating, total_reviews, verified)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            "Jen Park", "Cozy Coat Grooming", "Portland, OR",
            "(503) 555-0033", "jen@cozycoat.com",
            "Senior dogs and double-coat breeds are my specialty. Older dogs "
            "need extra patience and gentleness — I treat every dog like my own.",
            json.dumps(["Fear Free Certified"]),
            json.dumps(["senior dogs", "double coats", "gentle handling"]),
            json.dumps(["Siberian Husky", "Corgi", "Shih Tzu", "Maltese", "Bichon Frise", "Golden Retriever"]),
            json.dumps(["puppy cut", "deshed", "bath & trim", "round head", "teddy bear"]),
            4.9, 62, 1,
        ))  # groomer_id = 3

        # --- Services ---
        # Sarah (groomer_id=1): service IDs 1-5
        for row in [
            (1, "Bath & Dry",            "Full bath, blow-dry, and brush-out",                        50,  60),
            (1, "Teddy Bear Full Groom", "Bath, dry, and teddy bear scissor trim",                    85,  90),
            (1, "Puppy First Groom",     "Gentle first-groom introduction — bath, dry, light tidy",   65,  75),
            (1, "Nail Trim",             "Trim and file all nails",                                   20,  20),
            (1, "De-shed Treatment",     "Deep deshedding bath, high-velocity blow-out, brush-out",   70,  90),
        ]:
            conn.execute(
                "INSERT INTO services (groomer_id,name,description,price,duration_mins) VALUES (?,?,?,?,?)", row
            )

        # Marcus (groomer_id=2): service IDs 6-10
        for row in [
            (2, "Show Groom",       "Full breed-standard competition groom",                    120, 120),
            (2, "Full Groom",       "Bath, dry, breed-specific scissor trim",                    80,  90),
            (2, "Hand Strip",       "Hand-stripping for wire-coated breeds",                    150, 150),
            (2, "Bath & Dry",       "Full bath, blow-dry, and brush-out",                        55,  60),
            (2, "Nail & Ear Clean", "Nail trim plus ear cleaning",                               35,  30),
        ]:
            conn.execute(
                "INSERT INTO services (groomer_id,name,description,price,duration_mins) VALUES (?,?,?,?,?)", row
            )

        # Jen (groomer_id=3): service IDs 11-15
        for row in [
            (3, "Senior Dog Spa",  "Gentle full groom with joint-aware handling and soothing rinse", 65, 90),
            (3, "Deshed & Bath",   "Deshedding treatment, bath, blow-out — ideal for double coats",  75, 90),
            (3, "Full Groom",      "Bath, dry, and scissor or clipper trim",                         70, 90),
            (3, "Bath & Tidy",     "Bath, blow-dry, and light tidy of paws, face, and sanitary",     45, 60),
            (3, "Nail Trim",       "Trim and file all nails",                                        20, 20),
        ]:
            conn.execute(
                "INSERT INTO services (groomer_id,name,description,price,duration_mins) VALUES (?,?,?,?,?)", row
            )

        # --- Owners ---
        conn.execute(
            "INSERT INTO owners (name, phone, email) VALUES (?,?,?)",
            ("Emma Torres", "(503) 555-0101", "emma@example.com"),
        )  # owner_id = 1
        conn.execute(
            "INSERT INTO owners (name, phone, email) VALUES (?,?,?)",
            ("James Kim", "(503) 555-0202", "james@example.com"),
        )  # owner_id = 2

        # --- Dogs ---
        conn.execute("""
            INSERT INTO dogs (owner_id,name,breed,age_years,weight_lbs,coat_type,
                              temperament_tags,default_special_requests)
            VALUES (?,?,?,?,?,?,?,?)
        """, (
            1, "Max", "Goldendoodle", 3.0, 45.0, "curly",
            json.dumps(["anxious", "gentle", "dislikes dryers"]),
            "Always use fragrance-free shampoo. Go slow with the dryer — Max gets nervous. Give him a treat at the start.",
        ))  # dog_id = 1

        conn.execute("""
            INSERT INTO dogs (owner_id,name,breed,age_years,weight_lbs,coat_type,
                              temperament_tags,default_special_requests)
            VALUES (?,?,?,?,?,?,?,?)
        """, (
            2, "Bella", "Shih Tzu", 6.0, 12.0, "long",
            json.dumps(["gentle", "patient", "good with other dogs"]),
            "Keep topknot area clean. Bella likes being talked to during grooming.",
        ))  # dog_id = 2

        conn.execute("""
            INSERT INTO dogs (owner_id,name,breed,age_years,weight_lbs,coat_type,
                              temperament_tags,default_special_requests)
            VALUES (?,?,?,?,?,?,?,?)
        """, (
            2, "Buddy", "Labrador Retriever", 1.0, 65.0, "short",
            json.dumps(["energetic", "friendly", "mouthy when excited"]),
            "Buddy is still learning to stay still — patience appreciated!",
        ))  # dog_id = 3

        # --- Availability: next 7 days (Mon–Sat) for all groomers ---
        today = datetime(2026, 6, 15)
        slots = ["09:00", "10:00", "11:00", "13:00", "14:00", "15:00", "16:00"]
        for groomer_id in (1, 2, 3):
            for offset in range(1, 8):
                day = today + timedelta(days=offset)
                if day.weekday() == 6:  # skip Sunday
                    continue
                date_str = day.strftime("%Y-%m-%d")
                for slot in slots:
                    conn.execute(
                        "INSERT OR IGNORE INTO availability (groomer_id,date,time_slot,is_booked) VALUES (?,?,?,0)",
                        (groomer_id, date_str, slot),
                    )

        # --- Past bookings (completed) ---
        def _make_booking(bid, owner, dog, groomer, service, date, time, requests, cut, price):
            fee = round(price * 0.15, 2)
            earn = round(price - fee, 2)
            dep = round(price * 0.30, 2)
            conn.execute("""
                INSERT INTO bookings
                  (id,owner_id,dog_id,groomer_id,service_id,date,time,
                   special_requests,cut_style,status,deposit_paid,total_price,platform_fee,groomer_earnings)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (bid, owner, dog, groomer, service, date, time,
                  requests, cut, "completed", dep, price, fee, earn))

        # Max + Sarah: Teddy Bear Full Groom (service 2)
        _make_booking("KP-A1001", 1, 1, 1, 2,
                      "2026-06-08", "10:00",
                      "Go slow with the dryer, fragrance-free shampoo please",
                      "teddy bear", 85.0)

        # Bella + Jen: Full Groom (service 13)
        _make_booking("KP-A1002", 2, 2, 3, 13,
                      "2026-06-01", "14:00",
                      "Keep topknot area clean",
                      "puppy cut", 70.0)

        # Buddy upcoming booking with Jen: Bath & Tidy (service 14)
        fee = round(45.0 * 0.15, 2)
        earn = round(45.0 - fee, 2)
        dep = round(45.0 * 0.30, 2)
        conn.execute("""
            INSERT INTO bookings
              (id,owner_id,dog_id,groomer_id,service_id,date,time,
               special_requests,cut_style,status,deposit_paid,total_price,platform_fee,groomer_earnings)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, ("KP-A1003", 2, 3, 3, 14,
              "2026-06-18", "11:00",
              "Buddy is still learning to stay still!", "",
              "confirmed", dep, 45.0, fee, earn))
        conn.execute(
            "UPDATE availability SET is_booked=1 WHERE groomer_id=3 AND date='2026-06-18' AND time_slot='11:00'"
        )

        # --- Groom records (health observations) ---
        conn.execute("""
            INSERT INTO groom_records
              (booking_id,dog_id,groomer_id,
               coat_condition,skin_condition,ear_condition,nail_condition,eye_condition,
               health_flags,groomer_private_note,next_recommended_groom,completed_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            "KP-A1001", 1, 1,
            "healthy", "normal", "clean", "good", "clear",
            "",
            "Max did great! Took it slow with the dryer and he calmed right down. "
            "Beautiful dense curls. Coat is in excellent condition.",
            "2026-07-20", "2026-06-08 11:30:00",
        ))

        conn.execute("""
            INSERT INTO groom_records
              (booking_id,dog_id,groomer_id,
               coat_condition,skin_condition,ear_condition,nail_condition,eye_condition,
               health_flags,groomer_private_note,next_recommended_groom,completed_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            "KP-A1002", 2, 3,
            "healthy", "slightly dry", "clean", "good", "mild tear staining",
            "Mild tear staining around eyes — worth mentioning to vet if it worsens.",
            "Bella was an absolute angel. Recommend moisturizing shampoo next visit. "
            "Tear staining is mild but owner should be aware.",
            "2026-07-13", "2026-06-01 15:30:00",
        ))

        # --- Photos ---
        conn.execute("""
            INSERT INTO groom_photos
              (booking_id,dog_id,groomer_id,photo_url,caption,cut_style,is_portfolio,verified)
            VALUES (?,?,?,?,?,?,?,?)
        """, (
            "KP-A1001", 1, 1,
            "https://kindpaw.app/photos/max_teddy_bear_20260608.jpg",
            "Max's teddy bear cut — June 8", "teddy bear", 1, 1,
        ))  # photo_id = 1

        conn.execute("""
            INSERT INTO groom_photos
              (booking_id,dog_id,groomer_id,photo_url,caption,cut_style,is_portfolio,verified)
            VALUES (?,?,?,?,?,?,?,?)
        """, (
            "KP-A1002", 2, 3,
            "https://kindpaw.app/photos/bella_puppy_cut_20260601.jpg",
            "Bella's puppy cut — June 1", "puppy cut", 1, 1,
        ))  # photo_id = 2

        # --- Reviews ---
        conn.execute("""
            INSERT INTO reviews (booking_id,owner_id,groomer_id,dog_id,photo_id,rating,review_text,cut_style)
            VALUES (?,?,?,?,?,?,?,?)
        """, (
            "KP-A1001", 1, 1, 1, 1, 5,
            "Sarah is incredible with Max. He's always been anxious at the groomer but she was so patient "
            "and gentle. The teddy bear cut came out perfect. She even noticed he was stressed and took a "
            "little break to let him calm down. Will absolutely be back!",
            "teddy bear",
        ))

        conn.execute("""
            INSERT INTO reviews (booking_id,owner_id,groomer_id,dog_id,photo_id,rating,review_text,cut_style)
            VALUES (?,?,?,?,?,?,?,?)
        """, (
            "KP-A1002", 2, 3, 2, 2, 5,
            "Jen is so gentle with Bella. She noticed some mild tear staining and flagged it for us — "
            "that level of care is exactly why we're on KindPaw. Bella came home happy and smelling amazing.",
            "puppy cut",
        ))

        # --- Breed cuts ---
        for breed, cut_style, description in BREED_CUTS_SEED:
            conn.execute(
                "INSERT OR IGNORE INTO breed_cuts (breed,cut_style,description) VALUES (?,?,?)",
                (breed, cut_style, description),
            )

        conn.commit()


def bootstrap():
    """Initialize and seed the database. Call once at startup."""
    init_db()
    seed_db()


if __name__ == "__main__":
    bootstrap()
    print(f"KindPaw database ready: {DB_PATH}")
