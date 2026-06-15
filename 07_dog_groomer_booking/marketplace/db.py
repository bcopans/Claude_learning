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
    lat                 REAL DEFAULT 0,
    lng                 REAL DEFAULT 0,
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
    duration_mins INTEGER NOT NULL,
    price_type    TEXT DEFAULT 'flat'
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


def _needs_reset() -> bool:
    """Return True if the DB is missing or needs a schema upgrade."""
    if not os.path.exists(DB_PATH):
        return True
    try:
        conn = sqlite3.connect(DB_PATH)
        count = conn.execute("SELECT COUNT(*) FROM groomers").fetchone()[0]
        if count < 6:
            conn.close()
            return True
        # Check for lat column
        cols = [row[1] for row in conn.execute("PRAGMA table_info(groomers)").fetchall()]
        conn.close()
        if "lat" not in cols:
            return True
        return False
    except Exception:
        return True


def seed_db():
    with get_conn() as conn:
        if conn.execute("SELECT COUNT(*) FROM groomers").fetchone()[0] > 0:
            return

        # ------------------------------------------------------------------ #
        # GROOMERS
        # ------------------------------------------------------------------ #
        groomer_rows = [
            # (name, business_name, location, lat, lng, phone, email, bio,
            #  cert_tags, spec_tags, breed_expertise, cut_specialties, avg_rating, total_reviews, verified)
            (
                "Sarah Chen", "Gentle Paws Studio", "Pearl District, Portland, OR",
                45.5279, -122.6862,
                "(503) 555-0011", "sarah@gentlepaws.com",
                "12 years grooming with a focus on anxious and sensitive dogs. "
                "Every dog deserves to feel safe — I take my time and never rush.",
                json.dumps(["Fear Free Certified", "NDGAA"]),
                json.dumps(["anxious dogs", "puppies", "sensitive breeds"]),
                json.dumps(["Goldendoodle", "Poodle", "Cockapoo", "Cavapoo", "Labradoodle"]),
                json.dumps(["teddy bear", "puppy cut", "lamb cut"]),
                4.9, 87, 1,
            ),
            (
                "Marcus Webb", "The Grooming Gallery", "Alberta Arts District, Portland, OR",
                45.5603, -122.6397,
                "(503) 555-0022", "marcus@grooominggallery.com",
                "15 years of competitive show grooming. I bring competition-level "
                "precision to every pet groom. Flawless and technically perfect.",
                json.dumps(["IPG Certified", "NDGAA"]),
                json.dumps(["show cuts", "hand-stripping", "large breeds", "breed standard"]),
                json.dumps(["Poodle", "Schnauzer", "Airedale", "German Shepherd", "Golden Retriever"]),
                json.dumps(["continental", "show cut", "hand-strip", "sporting clip"]),
                4.8, 134, 1,
            ),
            (
                "Jen Park", "Cozy Coat Grooming", "Lake Oswego, OR",
                45.4175, -122.6856,
                "(503) 555-0033", "jen@cozycoat.com",
                "Senior dogs and double-coat breeds are my specialty. Older dogs "
                "need extra patience and gentleness — I treat every dog like my own.",
                json.dumps(["Fear Free Certified"]),
                json.dumps(["senior dogs", "double coats", "gentle handling"]),
                json.dumps(["Siberian Husky", "Corgi", "Shih Tzu", "Maltese", "Bichon Frise"]),
                json.dumps(["puppy cut", "deshed", "round head", "teddy bear"]),
                4.9, 62, 1,
            ),
            (
                "Kai Okonkwo", "Paw & Play Grooming", "North Portland, OR",
                45.5798, -122.6809,
                "(503) 555-0044", "kai@pawandplay.com",
                "I specialize in puppies and high-energy dogs. First grooms should be "
                "fun and positive — I build trust from day one so every future visit is easier.",
                json.dumps(["Fear Free Certified"]),
                json.dumps(["puppies", "first grooms", "energetic dogs"]),
                json.dumps(["Labrador", "Golden Retriever", "Bernese Mountain Dog", "Boxer"]),
                json.dumps(["bath & brush", "puppy cut", "breed trim"]),
                4.7, 41, 1,
            ),
            (
                "Sofia Martinez", "Bella Vita Pets", "SE Portland, OR",
                45.5051, -122.6367,
                "(503) 555-0055", "sofia@bellavitapets.com",
                "Small breeds and detailed scissor work are my passion. I also offer "
                "spa add-ons — blueberry facials, aromatherapy rinses, and paw balm treatments.",
                json.dumps(["NCMG Certified"]),
                json.dumps(["small breeds", "detailed scissor work", "spa treatments"]),
                json.dumps(["Maltese", "Bichon Frise", "Yorkshire Terrier", "Cavapoo", "Shih Tzu"]),
                json.dumps(["teddy bear", "puppy cut", "show bichon", "lamb cut"]),
                4.8, 78, 1,
            ),
            (
                "David Kim", "ProGroom PDX", "Beaverton, OR",
                45.4871, -122.8037,
                "(503) 555-0066", "david@progroompdx.com",
                "Competition prep and breed-standard grooming for owners who demand the best. "
                "Wire-coat specialist with 10 years of AKC show experience.",
                json.dumps(["IPG Certified", "AKC S.A.F.E."]),
                json.dumps(["breed standards", "competition prep", "wire coats"]),
                json.dumps(["Poodle", "Schnauzer", "Terriers", "Cocker Spaniel", "Doodles"]),
                json.dumps(["continental", "hand-strip", "sporting clip", "traditional schnauzer"]),
                4.9, 103, 1,
            ),
        ]

        for row in groomer_rows:
            conn.execute("""
                INSERT INTO groomers
                  (name, business_name, location, lat, lng, phone, email, bio,
                   certification_tags, specialization_tags, breed_expertise, cut_specialties,
                   avg_rating, total_reviews, verified)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, row)

        # ------------------------------------------------------------------ #
        # SERVICES
        # service IDs are assigned sequentially by insertion order:
        #   Sarah  (groomer 1): 1–5
        #   Marcus (groomer 2): 6–10
        #   Jen    (groomer 3): 11–15
        #   Kai    (groomer 4): 16–20
        #   Sofia  (groomer 5): 21–24
        #   David  (groomer 6): 25–30
        # ------------------------------------------------------------------ #
        service_rows = [
            # Sarah (groomer_id=1)
            (1, "Bath & Dry",            "Full bath, blow-dry, and brush-out",                        50,  60,  "flat"),
            (1, "Teddy Bear Full Groom", "Bath, dry, and teddy bear scissor trim",                    85,  90,  "flat"),
            (1, "Puppy First Groom",     "Gentle first-groom introduction — bath, dry, light tidy",   65,  75,  "flat"),
            (1, "Nail Trim",             "Trim and file all nails",                                   20,  20,  "flat"),
            (1, "De-shed Treatment",     "Deep deshedding bath, high-velocity blow-out, brush-out",   70,  90,  "from"),
            # Marcus (groomer_id=2)
            (2, "Show Groom",       "Full breed-standard competition groom",                    120, 120, "from"),
            (2, "Full Groom",       "Bath, dry, breed-specific scissor trim",                    80,  90,  "flat"),
            (2, "Hand Strip",       "Hand-stripping for wire-coated breeds",                    150, 150, "from"),
            (2, "Bath & Dry",       "Full bath, blow-dry, and brush-out",                        55,  60,  "flat"),
            (2, "Nail & Ear Clean", "Nail trim plus ear cleaning",                               35,  30,  "flat"),
            # Jen (groomer_id=3)
            (3, "Senior Dog Spa",  "Gentle full groom with joint-aware handling and soothing rinse", 65, 90, "flat"),
            (3, "Deshed & Bath",   "Deshedding treatment, bath, blow-out — ideal for double coats",  75, 90, "flat"),
            (3, "Full Groom",      "Bath, dry, and scissor or clipper trim",                         70, 90, "flat"),
            (3, "Bath & Tidy",     "Bath, blow-dry, and light tidy of paws, face, and sanitary",     45, 60, "flat"),
            (3, "Nail Trim",       "Trim and file all nails",                                        20, 20, "flat"),
            # Kai (groomer_id=4)
            (4, "Bath & Brush",       "Full bath, blow-dry, and thorough brush-out",                    45, 60,  "flat"),
            (4, "Full Groom",         "Bath, dry, and breed-appropriate trim",                          75, 90,  "flat"),
            (4, "Puppy Package",      "Fun, positive first-groom experience — bath, dry, light trim",    55, 75,  "flat"),
            (4, "Deshed Treatment",   "High-velocity blow-out plus thorough deshedding brush",           60, 90,  "from"),
            (4, "Teeth Brushing",     "Enzymatic toothpaste brush — add-on or standalone",              15, 15,  "flat"),
            # Sofia (groomer_id=5)
            (5, "Signature Groom", "Full spa groom with scissor finish and aromatherapy rinse",   90, 90, "flat"),
            (5, "Bath & Style",    "Bath, blow-dry, and light scissor style",                     55, 75, "flat"),
            (5, "Express Groom",   "Quick full groom — bath, dry, tidy trim, nails",              70, 75, "flat"),
            (5, "Nail & Ear Care", "Nail trim, ear clean, and paw balm",                          30, 30, "flat"),
            # David (groomer_id=6)
            (6, "Competition Prep",   "Full competition-ready groom to breed standard",            130, 150, "from"),
            (6, "Full Groom",         "Bath, dry, and breed-standard scissor trim",                 85,  90, "flat"),
            (6, "Hand Strip",         "Hand-stripping for wire and rough coats",                   145, 150, "from"),
            (6, "Bath & Dry",         "Full bath, blow-dry, and brush-out",                         60,  60, "flat"),
            (6, "Breed Trim",         "Breed-standard clipper and scissor trim",                    95,  90, "from"),
        ]

        for row in service_rows:
            conn.execute(
                "INSERT INTO services (groomer_id,name,description,price,duration_mins,price_type) VALUES (?,?,?,?,?,?)",
                row,
            )

        # ------------------------------------------------------------------ #
        # OWNERS
        # ------------------------------------------------------------------ #
        owner_rows = [
            ("Emma Torres",    "(503) 555-0101", "emma@example.com"),
            ("James Kim",      "(503) 555-0202", "james@example.com"),
            ("Mia Jackson",    "(503) 555-0303", "mia@example.com"),
            ("Carlos Rivera",  "(503) 555-0404", "carlos@example.com"),
            ("Aisha Thompson", "(503) 555-0505", "aisha@example.com"),
            ("Ryan Chen",      "(503) 555-0606", "ryan@example.com"),
            ("Lisa Park",      "(503) 555-0707", "lisa@example.com"),
        ]
        for row in owner_rows:
            conn.execute("INSERT INTO owners (name, phone, email) VALUES (?,?,?)", row)

        # ------------------------------------------------------------------ #
        # DOGS
        # ------------------------------------------------------------------ #
        dog_rows = [
            # (owner_id, name, breed, age_years, weight_lbs, coat_type, temperament_tags, special_requests)
            (1, "Max",    "Goldendoodle",       3.0,  45.0, "curly",
             json.dumps(["anxious", "dislikes dryers", "gentle"]),
             "Always use fragrance-free shampoo. Go slow with the dryer — Max gets nervous. Give him a treat at the start."),
            (2, "Bella",  "Shih Tzu",           6.0,  12.0, "long",
             json.dumps(["gentle", "patient"]),
             "Keep topknot area clean. Bella likes being talked to during grooming."),
            (2, "Buddy",  "Labrador Retriever", 1.0,  65.0, "short",
             json.dumps(["energetic", "mouthy when excited"]),
             "Buddy is still learning to stay still — patience appreciated!"),
            (3, "Nala",   "Golden Retriever",   5.0,  58.0, "medium",
             json.dumps(["calm", "loves treats"]),
             "Nala loves a good treat after each step. She's very cooperative."),
            (3, "Mochi",  "Miniature Poodle",   2.0,   8.0, "curly",
             json.dumps(["spirited", "good with handling"]),
             "Mochi likes music playing. She does great with handling."),
            (4, "Duke",   "German Shepherd",    4.0,  70.0, "double",
             json.dumps(["stoic", "nervous with strangers"]),
             "Duke warms up slowly — please give him time to settle before starting."),
            (5, "Luna",   "Siberian Husky",     3.0,  52.0, "double",
             json.dumps(["energetic", "heavy shedder"]),
             "Luna is a big shedder. Please do not shave — deshed only."),
            (5, "Teddy",  "Bichon Frise",       8.0,  14.0, "curly",
             json.dumps(["senior", "gentle", "easy to groom"]),
             "Teddy is a senior — please keep sessions calm and unhurried."),
            (6, "Charlie","Miniature Schnauzer", 2.0, 16.0, "wiry",
             json.dumps(["alert", "cooperative"]),
             "Charlie likes the traditional schnauzer look — keep the beard full."),
            (6, "Ruby",   "Cavapoo",            1.0,  12.0, "wavy",
             json.dumps(["puppy", "excitable", "mouthy"]),
             "Ruby is only 1 — please be patient. She's still learning to stand still."),
            (7, "Zeus",   "Labrador Retriever", 4.0,  72.0, "short",
             json.dumps(["friendly", "calm", "treat-motivated"]),
             "Zeus is very treat-motivated — feel free to use treats freely."),
            (7, "Coco",   "Maltese",           10.0,   7.0, "long",
             json.dumps(["senior", "arthritic", "very gentle needed"]),
             "Coco has arthritis in her hips — please handle her very gently and avoid long standing periods."),
        ]
        for row in dog_rows:
            conn.execute("""
                INSERT INTO dogs (owner_id,name,breed,age_years,weight_lbs,coat_type,
                                  temperament_tags,default_special_requests)
                VALUES (?,?,?,?,?,?,?,?)
            """, row)

        # ------------------------------------------------------------------ #
        # AVAILABILITY — next 14 days (09:00–16:00 hourly, skip Sundays)
        # ------------------------------------------------------------------ #
        today = datetime(2026, 6, 15)
        slots = ["09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00"]
        for groomer_id in range(1, 7):
            for offset in range(1, 15):
                day = today + timedelta(days=offset)
                if day.weekday() == 6:   # skip Sunday
                    continue
                date_str = day.strftime("%Y-%m-%d")
                for slot in slots:
                    conn.execute(
                        "INSERT OR IGNORE INTO availability (groomer_id,date,time_slot,is_booked) VALUES (?,?,?,0)",
                        (groomer_id, date_str, slot),
                    )

        # ------------------------------------------------------------------ #
        # BOOKINGS helper
        # ------------------------------------------------------------------ #
        def _book(bid, owner, dog, groomer, service, date, time, requests, cut, price, status="completed"):
            fee  = round(price * 0.15, 2)
            earn = round(price - fee, 2)
            dep  = round(price * 0.30, 2)
            conn.execute("""
                INSERT INTO bookings
                  (id,owner_id,dog_id,groomer_id,service_id,date,time,
                   special_requests,cut_style,status,deposit_paid,total_price,platform_fee,groomer_earnings)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (bid, owner, dog, groomer, service, date, time,
                  requests, cut, status, dep, price, fee, earn))

        # ------------------------------------------------------------------ #
        # ALL BOOKINGS
        # dog IDs:    Max=1,Bella=2,Buddy=3,Nala=4,Mochi=5,Duke=6,Luna=7,
        #             Teddy=8,Charlie=9,Ruby=10,Zeus=11,Coco=12
        # owner IDs:  Emma=1,James=2,Mia=3,Carlos=4,Aisha=5,Ryan=6,Lisa=7
        # groomer IDs: Sarah=1,Marcus=2,Jen=3,Kai=4,Sofia=5,David=6
        # service IDs as documented above
        # ------------------------------------------------------------------ #

        # Original 3 bookings (kept)
        _book("KP-A1001", 1, 1, 1, 2,
              "2026-06-08", "10:00",
              "Go slow with the dryer, fragrance-free shampoo please",
              "teddy bear", 85.0)

        _book("KP-A1002", 2, 2, 3, 13,
              "2026-06-01", "14:00",
              "Keep topknot area clean",
              "puppy cut", 70.0)

        _book("KP-A1003", 2, 3, 3, 14,
              "2026-06-18", "11:00",
              "Buddy is still learning to stay still!",
              "", 45.0, status="confirmed")
        conn.execute(
            "UPDATE availability SET is_booked=1 WHERE groomer_id=3 AND date='2026-06-18' AND time_slot='11:00'"
        )

        # New B-series bookings (all completed)
        _book("KP-B2001", 3, 4, 1, 1,
              "2026-05-15", "10:00", "Nala loves treats — feel free!", "bath & brush", 50.0)
        _book("KP-B2002", 3, 5, 1, 2,
              "2026-05-22", "13:00", "Mochi likes music playing", "teddy bear", 85.0)
        _book("KP-B2003", 6, 10, 1, 3,
              "2026-06-01", "09:00", "Ruby is excitable — be patient please", "puppy cut", 65.0)
        _book("KP-B2004", 6, 9, 1, 4,
              "2026-06-10", "11:00", "Just a nail trim", "", 20.0)
        _book("KP-B2005", 4, 6, 2, 7,
              "2026-05-20", "14:00", "Duke needs time to settle — go slow", "full groom", 80.0)
        _book("KP-B2006", 3, 4, 2, 9,
              "2026-06-03", "10:00", "Nala is very cooperative", "bath & dry", 55.0)
        _book("KP-B2007", 7, 11, 2, 7,
              "2026-06-10", "13:00", "Zeus loves treats", "full groom", 80.0)
        _book("KP-B2008", 5, 8, 3, 11,
              "2026-05-18", "09:00", "Teddy is a senior — keep it calm", "senior spa", 65.0)
        _book("KP-B2009", 7, 12, 3, 11,
              "2026-06-05", "10:00", "Coco has arthritis — handle very gently", "senior spa", 65.0)
        _book("KP-B2010", 5, 7, 3, 12,
              "2026-05-25", "13:00", "Do not shave — deshed only", "deshed", 75.0)
        _book("KP-B2011", 1, 1, 4, 16,
              "2026-04-15", "09:00", "Max is anxious — go slow", "bath & brush", 45.0)
        _book("KP-B2012", 4, 6, 4, 17,
              "2026-05-10", "14:00", "Duke needs time to warm up", "full groom", 75.0)
        _book("KP-B2013", 3, 5, 5, 22,
              "2026-05-28", "11:00", "Mochi does great — treat freely", "bath & style", 55.0)
        _book("KP-B2014", 7, 12, 5, 22,
              "2026-06-08", "10:00", "Coco is arthritic — very gentle please", "bath & style", 55.0)
        _book("KP-B2015", 4, 6, 6, 26,
              "2026-05-12", "10:00", "Duke needs time to warm up to strangers", "full groom", 85.0)
        _book("KP-B2016", 3, 4, 6, 26,
              "2026-06-02", "13:00", "Nala is treat-motivated and cooperative", "full groom", 85.0)
        _book("KP-B2017", 7, 11, 4, 17,
              "2026-06-11", "09:00", "Zeus is very easygoing", "full groom", 75.0)
        _book("KP-B2018", 2, 2, 5, 22,
              "2026-06-12", "11:00", "Keep topknot area clean", "bath & style", 55.0)
        _book("KP-B2019", 5, 7, 4, 19,
              "2026-06-09", "10:00", "Do NOT shave Luna — deshed only", "deshed", 60.0)

        # C-series: upcoming confirmed bookings
        _book("KP-C3001", 6, 9, 1, 2,
              "2026-06-19", "10:00", "Keep the beard full, traditional schnauzer look",
              "teddy bear", 85.0, status="confirmed")
        conn.execute(
            "UPDATE availability SET is_booked=1 WHERE groomer_id=1 AND date='2026-06-19' AND time_slot='10:00'"
        )

        _book("KP-C3002", 3, 4, 2, 7,
              "2026-06-20", "14:00", "Nala loves treats — feel free to use them",
              "full groom", 80.0, status="confirmed")
        conn.execute(
            "UPDATE availability SET is_booked=1 WHERE groomer_id=2 AND date='2026-06-20' AND time_slot='14:00'"
        )

        # ------------------------------------------------------------------ #
        # GROOM RECORDS for all completed bookings
        # ------------------------------------------------------------------ #
        groom_records = [
            # (booking_id, dog_id, groomer_id,
            #  coat, skin, ear, nail, eye,
            #  health_flags, private_note, next_recommended, completed_at)
            ("KP-A1001", 1, 1,
             "excellent — dense curls, no matting", "healthy, no irritation", "clean", "good length", "clear",
             "",
             "Max did great once I used a diffuser on the dryer. Took a couple of short breaks. Beautiful teddy bear. "
             "Coat is in excellent shape — clearly being brushed at home.",
             "2026-07-20", "2026-06-08 11:30:00"),

            ("KP-A1002", 2, 3,
             "healthy, medium length", "slightly dry around muzzle", "clean", "slightly long", "mild tear staining",
             "Mild tear staining around inner corners — worth monitoring.",
             "Bella was an absolute angel. Recommend moisturizing shampoo next visit. "
             "Nail trim included — they were just starting to curl.",
             "2026-07-13", "2026-06-01 15:30:00"),

            ("KP-B2001", 4, 1,
             "healthy medium coat, light seasonal shed", "normal", "clean", "good", "clear",
             "",
             "Nala was a dream — stood perfectly still the whole time. Treat rewards worked great. "
             "Very cooperative Golden. Some light shedding but nothing unusual for the season.",
             "2026-06-26", "2026-05-15 11:00:00"),

            ("KP-B2002", 5, 1,
             "excellent curly coat, no matting", "healthy", "clean, slight wax", "good", "clear",
             "Slight ear wax buildup — recommend ear cleaning at next visit.",
             "Mochi was spirited but handled everything well. Music definitely helped — she visibly relaxed. "
             "Teddy bear came out adorable. Flag ear wax for owner.",
             "2026-06-26", "2026-05-22 14:15:00"),

            ("KP-B2003", 10, 1,
             "wavy, puppy coat — some tangles at ears", "healthy", "clean", "good", "clear",
             "Mild ear tangles — recommend more frequent brushing around ear folds.",
             "Ruby was wiggly but so sweet! Took three short breaks and she settled each time. "
             "Puppy first groom was a success. Owner should brush ears daily.",
             "2026-07-06", "2026-06-01 10:15:00"),

            ("KP-B2004", 9, 1,
             "n/a — nail trim only", "n/a", "n/a", "nails were long, now trimmed", "n/a",
             "Nails were getting quite long — recommend 6-week nail schedule.",
             "Quick and easy nail trim. Charlie was cooperative. Recommend sticking to 6-week intervals.",
             "2026-07-22", "2026-06-10 11:20:00"),

            ("KP-B2005", 6, 2,
             "healthy double coat, moderate shed", "normal", "clean", "slightly long", "clear",
             "Nails on the longer side — owner should book nail trim soon.",
             "Duke took about 10 minutes to settle but was cooperative once he relaxed. "
             "Good coat condition overall. Noted slightly long nails — mentioned to owner.",
             "2026-07-01", "2026-05-20 16:00:00"),

            ("KP-B2006", 4, 2,
             "healthy, light seasonal shedding", "normal", "clean", "good", "clear",
             "",
             "Nala is a joy — easy bath and blow-dry. No issues at all. Light seasonal shedding is normal. "
             "Owner's consistent grooming routine is clearly working.",
             "2026-07-15", "2026-06-03 11:00:00"),

            ("KP-B2007", 11, 2,
             "healthy short coat, minimal shedding", "normal", "clean", "good", "clear",
             "",
             "Zeus was perfect — treat-motivated and completely cooperative. One of the easiest Labs I've groomed. "
             "Short coat in great condition. No concerns.",
             "2026-07-22", "2026-06-10 14:30:00"),

            ("KP-B2008", 8, 3,
             "curly, slight felting behind ears", "normal for age, mild dryness", "clean", "good", "mild tear staining",
             "Mild felting behind ears — owner should check and brush weekly. Mild tear staining typical for senior Bichons.",
             "Teddy is such a sweet senior. Went very slowly — he appreciated it. "
             "Found slight felting behind ears. Gently worked it out. Recommend weekly ear-area brushing.",
             "2026-06-29", "2026-05-18 10:30:00"),

            ("KP-B2009", 12, 3,
             "long silky coat, some matting at hips", "thin coat typical of age", "clean", "slightly long", "clear",
             "Hip area matting from lying down. Arthritic — handled with extreme care. Nails slightly long.",
             "Coco was incredibly patient. Used extra padding on the table. Gently worked out hip matting. "
             "She needs more frequent grooming to prevent mat buildup given her arthritis limits at-home brushing.",
             "2026-07-17", "2026-06-05 11:15:00"),

            ("KP-B2010", 7, 3,
             "thick double coat, heavy seasonal blow", "healthy", "clean", "good", "clear",
             "Peak seasonal shedding — recommend deshed every 6 weeks through summer.",
             "Luna had SO much coat to come out! High-velocity dryer did most of the work. "
             "She's healthy and energetic — great double coat underneath. Did not clip — deshed only as requested.",
             "2026-07-06", "2026-05-25 14:45:00"),

            ("KP-B2011", 1, 4,
             "curly, light tangles at legs", "normal", "clean", "good", "clear",
             "Light leg tangles — recommend owner brush legs 2x weekly.",
             "Max was anxious at first but warmed up well. Went slow with the dryer as noted. "
             "Good bath and brush. Coat is healthy. Leg tangles noted — mentioned to owner.",
             "2026-05-27", "2026-04-15 10:30:00"),

            ("KP-B2012", 6, 4,
             "healthy double coat, moderate shedding", "normal", "clean", "good", "clear",
             "",
             "Duke took a while to warm up but was fine once settled. Good groom. "
             "Double coat in healthy condition. Owner mentioned he's better with familiar groomers — building trust.",
             "2026-06-21", "2026-05-10 15:30:00"),

            ("KP-B2013", 5, 5,
             "excellent curly coat, no matting", "healthy", "clean, slight wax", "good", "clear",
             "Minor ear wax — recommend ear cleaning add-on at next visit.",
             "Mochi was so fun! Played music and she loved it. Lovely little Poodle. "
             "Coat is in great shape. Minor ear wax noted — will mention to owner.",
             "2026-07-09", "2026-05-28 12:15:00"),

            ("KP-B2014", 12, 5,
             "silky, some hip matting from lying", "thin, age-appropriate", "clean", "slightly long", "clear",
             "Arthritic — used foam support pad. Hip matting recurrence — owner needs daily brushing routine.",
             "Sweet little Coco. Used the foam mat so she could lie down comfortably. "
             "Worked slowly and gently. Hip mats are recurring — I've recommended a daily brushing routine to the owner.",
             "2026-07-20", "2026-06-08 11:00:00"),

            ("KP-B2015", 6, 6,
             "healthy double coat, light shedding", "normal", "clean", "good", "clear",
             "",
             "Duke was cautious but professional handling won him over by the end. "
             "Breed-standard trim looks excellent. Owner was thrilled with the result.",
             "2026-06-23", "2026-05-12 11:30:00"),

            ("KP-B2016", 4, 6,
             "healthy medium coat, seasonal shed", "normal", "clean", "good", "clear",
             "",
             "Nala is an ideal client — cooperative, treat-motivated, and calm. "
             "Breed-standard trim came out great. Light seasonal shedding, nothing concerning.",
             "2026-07-14", "2026-06-02 14:30:00"),

            ("KP-B2017", 11, 4,
             "healthy short coat", "normal", "clean", "good", "clear",
             "",
             "Zeus was an absolute gentleman. Treat-motivated and completely relaxed. "
             "One of the easiest grooms I've done. Short coat in perfect condition.",
             "2026-07-23", "2026-06-11 10:00:00"),

            ("KP-B2018", 2, 5,
             "healthy, medium length, soft texture", "normal", "clean", "good", "mild tear staining",
             "Mild tear staining — recommend blueberry facial add-on next visit.",
             "Bella was very sweet and patient. Classic Shih Tzu tear staining — flagged for owner. "
             "Coat texture is lovely. Topknot area kept clean as requested.",
             "2026-07-24", "2026-06-12 12:15:00"),

            ("KP-B2019", 7, 4,
             "thick double coat, heavy blow — summer peak", "healthy", "clean", "good", "clear",
             "Peak summer shedding — book deshed every 5-6 weeks through August.",
             "Luna had a LOT of coat. Deshed treatment really paid off — owner will notice a huge difference. "
             "Did not clip as requested. High-energy girl but well-behaved on table.",
             "2026-07-21", "2026-06-09 11:15:00"),
        ]

        for rec in groom_records:
            conn.execute("""
                INSERT INTO groom_records
                  (booking_id,dog_id,groomer_id,
                   coat_condition,skin_condition,ear_condition,nail_condition,eye_condition,
                   health_flags,groomer_private_note,next_recommended_groom,completed_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """, rec)

        # ------------------------------------------------------------------ #
        # GROOM PHOTOS (one per completed booking that included a cut/style)
        # Nail-only and bath-only bookings excluded where noted.
        # photo_url = '' — frontend fetches from dog.ceo
        # ------------------------------------------------------------------ #
        # Returns inserted photo rowid for use in reviews
        def _photo(booking_id, dog_id, groomer_id, caption, cut_style, is_portfolio=1):
            cur = conn.execute("""
                INSERT INTO groom_photos
                  (booking_id,dog_id,groomer_id,photo_url,caption,cut_style,is_portfolio,verified)
                VALUES (?,?,?,?,?,?,?,?)
            """, (booking_id, dog_id, groomer_id, "", caption, cut_style, is_portfolio, 1))
            return cur.lastrowid

        photo_map = {}  # booking_id -> photo_id (for linking in reviews)

        photo_map["KP-A1001"] = _photo("KP-A1001", 1, 1,
            "Max's teddy bear cut — June 8", "teddy bear")
        photo_map["KP-A1002"] = _photo("KP-A1002", 2, 3,
            "Bella's puppy cut — June 1", "puppy cut")
        photo_map["KP-B2001"] = _photo("KP-B2001", 4, 1,
            "Nala after her bath & brush — May 15", "bath & brush")
        photo_map["KP-B2002"] = _photo("KP-B2002", 5, 1,
            "Mochi's teddy bear full groom — May 22", "teddy bear")
        photo_map["KP-B2003"] = _photo("KP-B2003", 10, 1,
            "Ruby's first puppy groom — June 1", "puppy cut")
        # KP-B2004 is nail-only — no photo
        photo_map["KP-B2005"] = _photo("KP-B2005", 6, 2,
            "Duke's full groom — May 20", "full groom")
        photo_map["KP-B2006"] = _photo("KP-B2006", 4, 2,
            "Nala's bath & dry — June 3", "bath & dry")
        photo_map["KP-B2007"] = _photo("KP-B2007", 11, 2,
            "Zeus's full groom — June 10", "full groom")
        photo_map["KP-B2008"] = _photo("KP-B2008", 8, 3,
            "Teddy's senior spa groom — May 18", "senior spa")
        photo_map["KP-B2009"] = _photo("KP-B2009", 12, 3,
            "Coco's senior spa groom — June 5", "senior spa")
        photo_map["KP-B2010"] = _photo("KP-B2010", 7, 3,
            "Luna's deshed treatment — May 25", "deshed")
        photo_map["KP-B2011"] = _photo("KP-B2011", 1, 4,
            "Max's bath & brush — April 15", "bath & brush")
        photo_map["KP-B2012"] = _photo("KP-B2012", 6, 4,
            "Duke's full groom — May 10", "full groom")
        photo_map["KP-B2013"] = _photo("KP-B2013", 5, 5,
            "Mochi's bath & style — May 28", "bath & style")
        photo_map["KP-B2014"] = _photo("KP-B2014", 12, 5,
            "Coco's bath & style — June 8", "bath & style")
        photo_map["KP-B2015"] = _photo("KP-B2015", 6, 6,
            "Duke's breed-standard full groom — May 12", "full groom")
        photo_map["KP-B2016"] = _photo("KP-B2016", 4, 6,
            "Nala's full groom — June 2", "full groom")
        photo_map["KP-B2017"] = _photo("KP-B2017", 11, 4,
            "Zeus's full groom — June 11", "full groom")
        photo_map["KP-B2018"] = _photo("KP-B2018", 2, 5,
            "Bella's bath & style — June 12", "bath & style")
        photo_map["KP-B2019"] = _photo("KP-B2019", 7, 4,
            "Luna's deshed treatment — June 9", "deshed")

        # ------------------------------------------------------------------ #
        # REVIEWS for all completed bookings
        # ------------------------------------------------------------------ #
        reviews = [
            # (booking_id, owner_id, groomer_id, dog_id, photo_id, rating, review_text, cut_style)
            ("KP-A1001", 1, 1, 1, photo_map["KP-A1001"], 5,
             "Sarah is incredible with Max. He's always been anxious at groomers but she was so patient. "
             "Took extra time with the dryer and let him set the pace. The teddy bear cut came out perfect. "
             "Will absolutely be back!", "teddy bear"),

            ("KP-A1002", 2, 3, 2, photo_map["KP-A1002"], 5,
             "Jen is so gentle with Bella. She noticed some mild tear staining and flagged it for us — "
             "that level of care is exactly why we use KindPaw. Bella came home happy and smelling amazing.",
             "puppy cut"),

            ("KP-B2001", 3, 1, 4, photo_map["KP-B2001"], 5,
             "Sarah did a wonderful job with Nala's bath and brush-out. Nala came home gleaming and "
             "smelling fresh. Sarah even gave her extra treats throughout. Very professional and warm.",
             "bath & brush"),

            ("KP-B2002", 3, 1, 5, photo_map["KP-B2002"], 5,
             "Mochi's teddy bear groom was flawless. Sarah clearly has an eye for doodle cuts — the "
             "shaping around the face was perfect. Mochi was relaxed the whole time apparently. We're "
             "booking monthly from now on.", "teddy bear"),

            ("KP-B2003", 6, 1, 10, photo_map["KP-B2003"], 4,
             "Ruby's first groom went really well! She was a wiggle monster but Sarah handled it "
             "beautifully. Ruby came home looking so grown-up. Took a little longer than expected "
             "but that was totally fine for a puppy first groom.", "puppy cut"),

            ("KP-B2004", 6, 1, 9, None, 5,
             "Quick, easy nail trim for Charlie. Sarah was fast and efficient — in and out in 15 minutes. "
             "Charlie didn't even flinch. Great for a standalone nail appointment.", ""),

            ("KP-B2005", 4, 2, 6, photo_map["KP-B2005"], 4,
             "Marcus did a solid job with Duke. Duke can be standoffish with strangers but Marcus gave "
             "him time to settle before starting. The groom looks clean and neat. Docked one star only "
             "because pick-up was a bit rushed, but the work itself was great.", "full groom"),

            ("KP-B2006", 3, 2, 4, photo_map["KP-B2006"], 5,
             "Fast, professional bath and blow-dry. Marcus clearly knows what he's doing. Nala came "
             "back looking pristine. Easy booking experience too.", "bath & dry"),

            ("KP-B2007", 7, 2, 11, photo_map["KP-B2007"], 5,
             "Marcus was fantastic with Zeus. He was in and out efficiently and Zeus looked amazing. "
             "The full groom was thorough — ears, nails, coat all done. Very impressed.",
             "full groom"),

            ("KP-B2008", 5, 3, 8, photo_map["KP-B2008"], 5,
             "Jen is a gem with senior dogs. Teddy is 8 and can be slow — she never rushed him. "
             "She also spotted some early matting behind his ears and gently worked it out. "
             "Teddy came home relaxed and looking beautiful.", "senior spa"),

            ("KP-B2009", 7, 3, 12, photo_map["KP-B2009"], 5,
             "Coco is 10 with arthritis and Jen handled her with such care. She used extra padding "
             "and let Coco lie down whenever needed. I cried a little picking her up — she looked "
             "so happy and beautiful. Jen is exactly who you want for a senior dog.", "senior spa"),

            ("KP-B2010", 5, 3, 7, photo_map["KP-B2010"], 4,
             "Great deshed treatment for Luna. The amount of fur Jen removed was truly unbelievable. "
             "Coat looks so much lighter and healthier. Only giving 4 stars because we had a slight "
             "wait at drop-off, but the groom itself was excellent.", "deshed"),

            ("KP-B2011", 1, 4, 1, photo_map["KP-B2011"], 4,
             "Kai was good with Max though Max was nervous. He used treats frequently which helped. "
             "The bath and brush were done well. I've since switched Max to Sarah who specializes in "
             "anxious dogs, but Kai was perfectly kind and capable.", "bath & brush"),

            ("KP-B2012", 4, 4, 6, photo_map["KP-B2012"], 5,
             "Kai did a great job with Duke. He gave him plenty of time to warm up and Duke actually "
             "did really well. Full groom looks clean and even. Will bring Duke back to Kai for sure.",
             "full groom"),

            ("KP-B2013", 3, 5, 5, photo_map["KP-B2013"], 5,
             "Sofia is wonderful! Mochi's bath and style was done with such attention to detail. "
             "She played music and Mochi was totally relaxed apparently. The finish on the coat was "
             "beautiful. Already booked our next appointment.", "bath & style"),

            ("KP-B2014", 7, 5, 12, photo_map["KP-B2014"], 5,
             "Sofia was incredibly gentle with Coco. She used a foam mat so Coco could rest "
             "comfortably and worked around her arthritic hips with so much care. Coco looked "
             "beautiful and wasn't stressed at all. Sofia is amazing with senior dogs.",
             "bath & style"),

            ("KP-B2015", 4, 6, 6, photo_map["KP-B2015"], 5,
             "David is the real deal. Duke's full groom was precise and professional. "
             "He also gave Duke the time he needed to settle, which I really appreciate. "
             "The finish was cleaner than any groom Duke has had before.", "full groom"),

            ("KP-B2016", 3, 6, 4, photo_map["KP-B2016"], 5,
             "David did a fantastic job with Nala. Professional, efficient, and the result "
             "was immaculate. Nala was happy and relaxed at pick-up. Highly recommend for "
             "owners who want precise breed-appropriate grooming.", "full groom"),

            ("KP-B2017", 7, 4, 11, photo_map["KP-B2017"], 5,
             "Kai was great with Zeus! Easygoing and professional. Zeus came home looking "
             "fantastic and very happy. Kai clearly loves big dogs — Zeus took to him immediately. "
             "Will definitely book again.", "full groom"),

            ("KP-B2018", 2, 5, 2, photo_map["KP-B2018"], 5,
             "Sofia did a beautiful job with Bella's bath and style. She flagged some mild tear "
             "staining and suggested a blueberry facial add-on next time — that kind of "
             "personalized care is exactly what we love. Bella smelled amazing all week.",
             "bath & style"),

            ("KP-B2019", 5, 4, 7, photo_map["KP-B2019"], 4,
             "Kai did a solid deshed on Luna. She shed half her body weight apparently! "
             "Coat looked so much healthier. He respected our no-clip request. "
             "Drop-off was a tiny bit chaotic but pick-up was smooth and Luna was happy.",
             "deshed"),
        ]

        for rev in reviews:
            conn.execute("""
                INSERT INTO reviews
                  (booking_id,owner_id,groomer_id,dog_id,photo_id,rating,review_text,cut_style)
                VALUES (?,?,?,?,?,?,?,?)
            """, rev)

        # ------------------------------------------------------------------ #
        # BREED CUTS
        # ------------------------------------------------------------------ #
        for breed, cut_style, description in BREED_CUTS_SEED:
            conn.execute(
                "INSERT OR IGNORE INTO breed_cuts (breed,cut_style,description) VALUES (?,?,?)",
                (breed, cut_style, description),
            )

        conn.commit()


def bootstrap():
    """Initialize and seed the database. Call once at startup."""
    if _needs_reset() and os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()
    seed_db()


if __name__ == "__main__":
    bootstrap()
    print(f"KindPaw database ready: {DB_PATH}")
