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


def bootstrap():
    """Initialize and seed the database. Call once at startup."""
    try:
        if os.path.exists(DB_PATH):
            conn = sqlite3.connect(DB_PATH)
            count = conn.execute("SELECT COUNT(*) FROM groomers").fetchone()[0]
            cols = [row[1] for row in conn.execute("PRAGMA table_info(groomers)").fetchall()]
            conn.close()
            if count < 8 or "lat" not in cols:
                os.remove(DB_PATH)
    except Exception:
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
    init_db()
    seed_db()


def seed_db():
    with get_conn() as conn:
        if conn.execute("SELECT COUNT(*) FROM groomers").fetchone()[0] > 0:
            return

        # ------------------------------------------------------------------ #
        # GROOMERS — 8 NYC groomers
        # ------------------------------------------------------------------ #
        # (name, business_name, location, lat, lng, phone, email, bio,
        #  cert_tags, spec_tags, breed_expertise, cut_specialties,
        #  avg_rating, total_reviews, verified)
        groomer_rows = [
            (
                "Maya Chen", "Paws on the Park", "Upper West Side, NYC",
                40.7870, -73.9754,
                "(212)555-0011", "maya@pawsonthepark.com",
                "10 years grooming Manhattan's most anxious pups. Quiet studio, no cage dryers, "
                "one dog at a time. I grew up with a fearful rescue and built my whole practice "
                "around making dogs feel safe.",
                json.dumps(["Fear Free Certified", "NDGAA"]),
                json.dumps(["anxious dogs", "puppies", "noise-sensitive"]),
                json.dumps(["Goldendoodle", "Poodle", "Cockapoo", "Cavapoo", "Labradoodle"]),
                json.dumps(["teddy bear", "puppy cut", "lamb cut"]),
                4.9, 112, 1,
            ),
            (
                "James Rivera", "Brooklyn Groom Co.", "Park Slope, Brooklyn, NYC",
                40.6681, -73.9797,
                "(718)555-0022", "james@brooklyngroomco.com",
                "Park Slope's most-booked groomer for three years running. I do everything from "
                "competition-prep Poodles to your neighbor's scruffy rescue. Precision scissor "
                "work and a genuinely fun experience.",
                json.dumps(["IPG Certified", "NDGAA"]),
                json.dumps(["doodles", "show cuts", "breed standard", "large breeds"]),
                json.dumps(["Poodle", "Golden Retriever", "German Shepherd", "Bernese Mountain Dog", "Doodles"]),
                json.dumps(["teddy bear", "continental", "show cut", "sporting clip"]),
                4.8, 189, 1,
            ),
            (
                "Priya Patel", "Tribeca Tails", "Tribeca, NYC",
                40.7195, -74.0089,
                "(212)555-0033", "priya@tribecatails.com",
                "Boutique grooming for the dogs who deserve the best. Aromatherapy rinses, "
                "blueberry facials, and scissor-only styling. My clients are small, precious, "
                "and usually more well-dressed than I am.",
                json.dumps(["NCMG Certified"]),
                json.dumps(["small breeds", "luxury spa", "detailed scissor work", "sensitive skin"]),
                json.dumps(["Maltese", "Yorkshire Terrier", "Shih Tzu", "Bichon Frise", "Cavapoo", "Havanese"]),
                json.dumps(["puppy cut", "teddy bear", "show bichon", "traditional yorkie", "top knot"]),
                4.9, 94, 1,
            ),
            (
                "Marcus Johnson", "Queens Paws", "Astoria, Queens, NYC",
                40.7721, -73.9303,
                "(718)555-0044", "marcus@queenspaws.com",
                "Queens's go-to for the big dogs. I specialize in high-shedding working breeds "
                "— Huskies, Shepherds, Labs. High-velocity dryers, thorough deshed treatments, "
                "and a huge workspace so your big dog isn't cramped.",
                json.dumps(["Fear Free Certified"]),
                json.dumps(["working breeds", "deshed", "large breeds", "double coats"]),
                json.dumps(["Siberian Husky", "German Shepherd", "Labrador Retriever", "Golden Retriever", "Boxer", "Australian Shepherd"]),
                json.dumps(["deshed", "bath & trim", "breed trim", "sanitary clip"]),
                4.7, 67, 1,
            ),
            (
                "Sofia Klein", "Village Grooming Studio", "West Village, NYC",
                40.7336, -74.0027,
                "(212)555-0055", "sofia@villagegroomingstudio.com",
                "Senior dogs are my specialty and my joy. I adjust every aspect of the groom "
                "for older dogs — longer breaks, anti-fatigue mats, warm rinses. They deserve "
                "just as much care as the young ones, maybe more.",
                json.dumps(["Fear Free Certified", "NDGAA"]),
                json.dumps(["senior dogs", "gentle handling", "arthritic dogs", "small breeds"]),
                json.dumps(["Shih Tzu", "Maltese", "Bichon Frise", "Poodle", "Cocker Spaniel", "Cavalier King Charles Spaniel"]),
                json.dumps(["puppy cut", "teddy bear", "round head", "bath & trim"]),
                4.9, 78, 1,
            ),
            (
                "David Park", "ProGroom NYC", "Upper East Side, NYC",
                40.7741, -73.9566,
                "(212)555-0066", "david@progroomnyc.com",
                "Former AKC handler turned full-time groomer. I compete, I judge, and I bring "
                "that same eye to every pet groom. If you want your Poodle's topknot to be "
                "geometrically perfect, I'm your groomer.",
                json.dumps(["IPG Certified", "AKC S.A.F.E."]),
                json.dumps(["competition prep", "breed standard", "hand-stripping", "wire coats"]),
                json.dumps(["Poodle", "Schnauzer", "Airedale Terrier", "Wire Fox Terrier", "Cocker Spaniel"]),
                json.dumps(["continental", "hand-strip", "sporting clip", "traditional schnauzer", "show cut"]),
                4.9, 143, 1,
            ),
            (
                "Aisha Williams", "Williamsburg Wags", "Williamsburg, Brooklyn, NYC",
                40.7081, -73.9571,
                "(718)555-0077", "aisha@williamsburgwags.com",
                "I specialize in first grooms and reactive dogs. Building a good association "
                "early changes a dog's whole life. Lots of treats, lots of patience, zero rush. "
                "Williamsburg pickup available.",
                json.dumps(["Fear Free Certified"]),
                json.dumps(["puppies", "first grooms", "reactive dogs", "positive reinforcement"]),
                json.dumps(["Goldendoodle", "Labrador Retriever", "Golden Retriever", "Mixed Breed", "Cockapoo"]),
                json.dumps(["puppy cut", "teddy bear", "bath & tidy", "deshed"]),
                4.8, 55, 1,
            ),
            (
                "Carlos Mendez", "Bronx Pro Groomers", "Riverdale, Bronx, NYC",
                40.8965, -73.9086,
                "(718)555-0088", "carlos@bronxprogroomers.com",
                "Serving the Bronx for 8 years. Honest pricing, no upsells, big hearts for "
                "big dogs. I work with families who want quality care without Manhattan prices.",
                json.dumps(["NDGAA"]),
                json.dumps(["large breeds", "budget-friendly", "families", "double coats"]),
                json.dumps(["Labrador Retriever", "German Shepherd", "Golden Retriever", "Boxer", "Pitbull", "Rottweiler"]),
                json.dumps(["bath & dry", "deshed", "breed trim", "puppy cut"]),
                4.6, 84, 1,
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
        # Service IDs assigned sequentially:
        #   Maya    (groomer 1): svc  1–6
        #   James   (groomer 2): svc  7–11
        #   Priya   (groomer 3): svc 12–16
        #   Marcus  (groomer 4): svc 17–21
        #   Sofia   (groomer 5): svc 22–26
        #   David   (groomer 6): svc 27–31
        #   Aisha   (groomer 7): svc 32–36
        #   Carlos  (groomer 8): svc 37–41
        # ------------------------------------------------------------------ #
        service_rows = [
            # Maya (groomer_id=1) — svc 1-6
            (1, "Bath & Dry",          "Full bath, blow-dry, and brush-out",                                   55,  60, "flat"),
            (1, "Teddy Bear Groom",    "Bath, dry, and teddy bear scissor trim",                               90,  90, "flat"),
            (1, "Puppy First Groom",   "Gentle first-groom introduction — bath, dry, light tidy",              70,  75, "flat"),
            (1, "Nail Trim",           "Trim and file all nails",                                              25,  20, "flat"),
            (1, "De-shed Treatment",   "Deep deshedding bath, high-velocity blow-out, brush-out",              75,  90, "from"),
            (1, "Lamb Cut",            "Short body with fluffy leg furnishings — dramatic contrast style",     100, 105, "flat"),
            # James (groomer_id=2) — svc 7-11
            (2, "Teddy Bear Full Groom", "Bath, dry, and teddy bear scissor trim",                             95,  90, "flat"),
            (2, "Show Groom",            "Full breed-standard competition groom",                             135, 120, "from"),
            (2, "Full Groom",            "Bath, dry, breed-specific scissor trim",                             85,  90, "flat"),
            (2, "Bath & Brush Out",      "Full bath, blow-dry, and thorough brush-out",                        60,  60, "flat"),
            (2, "Nail & Ear Clean",      "Nail trim plus ear cleaning",                                        35,  30, "flat"),
            # Priya (groomer_id=3) — svc 12-16
            (3, "Signature Spa Groom", "Full spa groom with scissor finish and aromatherapy rinse",           110,  90, "flat"),
            (3, "Bath & Style",        "Bath, blow-dry, and light scissor style",                              65,  75, "flat"),
            (3, "Blueberry Facial Add-on", "Brightening blueberry facial and gentle eye area cleaning",        20,  15, "flat"),
            (3, "Nail & Ear Care",     "Nail trim, ear clean, and paw balm",                                   30,  30, "flat"),
            (3, "Full Scissor Groom",  "Complete scissor-only finish — no clippers, purely hand-styled",      125, 120, "flat"),
            # Marcus (groomer_id=4) — svc 17-21
            (4, "Bath & Dry",      "Full bath, blow-dry, and brush-out",                                       55,  60, "flat"),
            (4, "Deshed & Bath",   "High-velocity deshed treatment with deep-clean bath",                      80,  90, "from"),
            (4, "Full Groom",      "Bath, dry, and breed-appropriate trim",                                    75,  90, "flat"),
            (4, "Nail Trim",       "Trim and file all nails",                                                  20,  20, "flat"),
            (4, "Breed Trim",      "Breed-standard clipper and scissor trim",                                  85,  90, "flat"),
            # Sofia (groomer_id=5) — svc 22-26
            (5, "Senior Dog Spa",      "Gentle full groom with joint-aware handling and warm rinse",            70,  90, "flat"),
            (5, "Gentle Full Groom",   "Full groom with extra time, breaks, and careful positioning",           80,  90, "flat"),
            (5, "Bath & Tidy",         "Bath, blow-dry, and light tidy of paws, face, and sanitary",            50,  60, "flat"),
            (5, "Nail Trim",           "Trim and file all nails",                                              20,  20, "flat"),
            (5, "Cocker Spaniel Groom","Traditional Cocker groom with ear, feathering, and body scissor work", 90,  90, "flat"),
            # David (groomer_id=6) — svc 27-31
            (6, "Competition Prep", "Full competition-ready groom to breed standard",                         145, 150, "from"),
            (6, "Full Groom",       "Bath, dry, and breed-standard scissor trim",                              95,  90, "flat"),
            (6, "Hand Strip",       "Hand-stripping for wire and rough coats — no clippers",                  160, 150, "from"),
            (6, "Bath & Dry",       "Full bath, blow-dry, and brush-out",                                      65,  60, "flat"),
            (6, "Breed Trim",       "Breed-standard clipper and scissor trim",                                 110,  90, "from"),
            # Aisha (groomer_id=7) — svc 32-36
            (7, "Puppy First Groom",   "Fun, treat-based first groom — bath, dry, light tidy",                 65,  75, "flat"),
            (7, "Bath & Tidy",         "Bath, blow-dry, and light tidy of paws, face, and sanitary",            50,  60, "flat"),
            (7, "Full Groom",          "Bath, dry, and breed-appropriate trim",                                 80,  90, "flat"),
            (7, "Deshed Treatment",    "High-velocity deshed with thorough brush-out",                          70,  90, "from"),
            (7, "Nail Trim",           "Trim and file all nails",                                              20,  20, "flat"),
            # Carlos (groomer_id=8) — svc 37-41
            (8, "Bath & Dry",       "Full bath, blow-dry, and brush-out",                                      45,  60, "flat"),
            (8, "Full Groom",       "Bath, dry, and breed-appropriate trim",                                   65,  90, "flat"),
            (8, "Deshed & Bath",    "High-velocity deshed with deep-clean bath",                               70,  90, "from"),
            (8, "Nail Trim",        "Trim and file all nails",                                                 18,  20, "flat"),
            (8, "Large Breed Groom","Full groom for large and extra-large breeds, extra time included",         85, 120, "flat"),
        ]

        for row in service_rows:
            conn.execute(
                "INSERT INTO services (groomer_id,name,description,price,duration_mins,price_type) VALUES (?,?,?,?,?,?)",
                row,
            )

        # ------------------------------------------------------------------ #
        # OWNERS — 12 NYC owners
        # ------------------------------------------------------------------ #
        owner_rows = [
            ("Emma Torres",    "(212) 555-0101", "emma@example.com"),
            ("James Kim",      "(718) 555-0202", "james@example.com"),
            ("Mia Jackson",    "(646) 555-0303", "mia@example.com"),
            ("Carlos Rivera",  "(929) 555-0404", "carlos@example.com"),
            ("Aisha Thompson", "(212) 555-0505", "aisha@example.com"),
            ("Ryan Chen",      "(718) 555-0606", "ryan@example.com"),
            ("Lisa Park",      "(646) 555-0707", "lisa@example.com"),
            ("Marcus Davis",   "(929) 555-0808", "marcus@example.com"),
            ("Sophie Laurent", "(212) 555-0909", "sophie@example.com"),
            ("Tom Nguyen",     "(718) 555-1010", "tom@example.com"),
            ("Jennifer Walsh", "(646) 555-1111", "jennifer@example.com"),
            ("Alex Santos",    "(929) 555-1212", "alex@example.com"),
        ]
        for row in owner_rows:
            conn.execute("INSERT INTO owners (name, phone, email) VALUES (?,?,?)", row)

        # ------------------------------------------------------------------ #
        # DOGS — 18 dogs with varied breeds, ages, temperaments
        # dog IDs assigned sequentially 1-18
        # owner_id: Emma=1, James=2, Mia=3, Carlos=4, Aisha=5, Ryan=6,
        #           Lisa=7, Marcus=8, Sophie=9, Tom=10, Jennifer=11, Alex=12
        # ------------------------------------------------------------------ #
        dog_rows = [
            # (owner_id, name, breed, age_years, weight_lbs, coat_type, temperament_tags, special_requests)
            (1,  "Max",    "Goldendoodle",             3.0,  45.0, "curly",
             json.dumps(["anxious", "dislikes dryers", "gentle"]),
             "Fragrance-free shampoo, go slow with dryer"),
            (2,  "Bella",  "Shih Tzu",                 6.0,  12.0, "long",
             json.dumps(["gentle", "patient", "good with handling"]),
             "Keep topknot clean, she likes being talked to"),
            (2,  "Buddy",  "Labrador Retriever",        1.0,  68.0, "short",
             json.dumps(["energetic", "mouthy when excited", "treat-motivated"]),
             "Bring extra treats, he's learning to stay still"),
            (3,  "Nala",   "Golden Retriever",          5.0,  58.0, "medium",
             json.dumps(["calm", "loves treats", "occasional ear sensitivity"]),
             "Check ears gently, she had an infection last year"),
            (3,  "Mochi",  "Miniature Poodle",          2.0,   8.0, "curly",
             json.dumps(["spirited", "cooperative", "loves the dryer"]),
             ""),
            (4,  "Duke",   "German Shepherd",           4.0,  70.0, "double",
             json.dumps(["stoic", "nervous with strangers", "warms up slowly"]),
             "Let him sniff you first. Doesn't like face handling initially."),
            (5,  "Luna",   "Siberian Husky",            3.0,  52.0, "double",
             json.dumps(["energetic", "heavy shedder", "hates standing still"]),
             "She blows coat twice a year, needs full deshed"),
            (5,  "Teddy",  "Bichon Frise",              8.0,  14.0, "curly",
             json.dumps(["senior", "arthritis in hips", "very gentle needed"]),
             "Needs anti-fatigue mat. Hip joints are stiff. Keep groom short if needed."),
            (6,  "Charlie","Miniature Schnauzer",        2.0,  16.0, "wiry",
             json.dumps(["alert", "cooperative", "barks at clippers initially"]),
             ""),
            (6,  "Ruby",   "Cavapoo",                   1.0,  12.0, "wavy",
             json.dumps(["puppy", "excitable", "mouthy"]),
             "First few grooms — lots of treats and breaks"),
            (7,  "Zeus",   "Labrador Retriever",        4.0,  72.0, "short",
             json.dumps(["friendly", "calm", "easy"]),
             ""),
            (7,  "Coco",   "Maltese",                  10.0,   7.0, "long",
             json.dumps(["senior", "arthritic", "very gentle handling essential"]),
             "She is 10 and arthritic. Short sessions, she gets tired quickly."),
            (8,  "Rosie",  "Golden Retriever",          2.0,  54.0, "medium",
             json.dumps(["playful", "wiggly", "good-natured"]),
             ""),
            (9,  "Finn",   "Bernese Mountain Dog",      3.0,  88.0, "double",
             json.dumps(["gentle giant", "nervous in new places", "treats help"]),
             "Finn is big but gentle. Needs patience settling in."),
            (10, "Daisy",  "Yorkshire Terrier",         4.0,   6.0, "long",
             json.dumps(["sassy", "doesn't like paws touched", "cooperative otherwise"]),
             "Go slowly on paw handling — she's getting better with training"),
            (11, "Cooper", "Australian Shepherd",       5.0,  55.0, "double",
             json.dumps(["energetic", "smart", "high energy"]),
             ""),
            (12, "Stella", "French Bulldog",            2.0,  24.0, "short",
             json.dumps(["sensitive skin", "skin folds need cleaning", "good with handling"]),
             "Clean skin folds carefully. She has sensitive skin — no harsh products."),
            (4,  "Bruno",  "Boxer",                     3.0,  65.0, "short",
             json.dumps(["friendly", "wiggly", "strong"]),
             "He's strong so secure the table. Very friendly though!"),
        ]
        for row in dog_rows:
            conn.execute("""
                INSERT INTO dogs (owner_id,name,breed,age_years,weight_lbs,coat_type,
                                  temperament_tags,default_special_requests)
                VALUES (?,?,?,?,?,?,?,?)
            """, row)

        # ------------------------------------------------------------------ #
        # AVAILABILITY — 14 days starting 2026-06-15
        # Slots: 08:00,09:00,10:00,11:00,13:00,14:00,15:00,16:00
        # Skip Sundays
        # ------------------------------------------------------------------ #
        today = datetime(2026, 6, 15)
        slots = ["08:00", "09:00", "10:00", "11:00", "13:00", "14:00", "15:00", "16:00"]
        for groomer_id in range(1, 9):
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
        # dog IDs:   Max=1,Bella=2,Buddy=3,Nala=4,Mochi=5,Duke=6,Luna=7,
        #            Teddy=8,Charlie=9,Ruby=10,Zeus=11,Coco=12,Rosie=13,
        #            Finn=14,Daisy=15,Cooper=16,Stella=17,Bruno=18
        # owner IDs: Emma=1,James=2,Mia=3,Carlos=4,Aisha=5,Ryan=6,
        #            Lisa=7,Marcus=8,Sophie=9,Tom=10,Jennifer=11,Alex=12
        # groomer IDs: Maya=1,James=2,Priya=3,Marcus=4,Sofia=5,David=6,Aisha=7,Carlos=8
        # service IDs: Maya(1):1-6, James(2):7-11, Priya(3):12-16,
        #              Marcus(4):17-21, Sofia(5):22-26, David(6):27-31,
        #              Aisha(7):32-36, Carlos(8):37-41
        # ------------------------------------------------------------------ #

        # --- Mandatory bookings ---
        _book("KP-A1001", 1, 1, 1, 2,
              "2026-06-08", "10:00",
              "Fragrance-free shampoo, go slow with dryer",
              "teddy bear", 90.0)

        _book("KP-A1002", 2, 2, 5, 23,
              "2026-06-01", "14:00",
              "Keep topknot clean, she likes being talked to",
              "gentle full groom", 80.0)

        _book("KP-A1003", 2, 3, 7, 33,
              "2026-06-18", "11:00",
              "Bring extra treats, he's learning to stay still",
              "", 50.0, status="confirmed")
        conn.execute(
            "UPDATE availability SET is_booked=1 WHERE groomer_id=7 AND date='2026-06-18' AND time_slot='11:00'"
        )

        # --- Completed bookings (B-series, going back to 2026-03-01) ---

        # Maya (groomer 1)
        _book("KP-B2001", 1, 1, 1, 1,
              "2026-03-10", "09:00",
              "Fragrance-free shampoo, go slow with dryer",
              "bath & dry", 55.0)
        _book("KP-B2002", 3, 5, 1, 2,
              "2026-03-20", "13:00",
              "Mochi loves the dryer, she's very cooperative",
              "teddy bear", 90.0)
        _book("KP-B2003", 6, 10, 1, 3,
              "2026-04-05", "10:00",
              "First few grooms — lots of treats and breaks",
              "puppy cut", 70.0)
        _book("KP-B2004", 1, 1, 1, 6,
              "2026-04-22", "11:00",
              "Fragrance-free shampoo, go slow with dryer",
              "lamb cut", 100.0)
        _book("KP-B2005", 3, 5, 1, 4,
              "2026-05-08", "14:00",
              "Just a nail trim",
              "", 25.0)
        _book("KP-B2006", 6, 9, 1, 2,
              "2026-05-25", "10:00",
              "Barks at clippers initially but settles",
              "teddy bear", 90.0)

        # James Rivera (groomer 2)
        _book("KP-B2007", 4, 6, 2, 9,
              "2026-03-15", "13:00",
              "Let him sniff you first, doesn't like face handling initially",
              "full groom", 85.0)
        _book("KP-B2008", 9, 14, 2, 9,
              "2026-03-28", "10:00",
              "Finn is big but gentle. Needs patience settling in.",
              "full groom", 85.0)
        _book("KP-B2009", 3, 4, 2, 10,
              "2026-04-12", "14:00",
              "Check ears gently, she had an infection last year",
              "bath & brush out", 60.0)
        _book("KP-B2010", 2, 2, 2, 7,
              "2026-05-05", "11:00",
              "Keep topknot clean",
              "show groom", 135.0)
        _book("KP-B2011", 4, 6, 2, 11,
              "2026-05-18", "09:00",
              "Let him sniff you first",
              "nail & ear clean", 35.0)

        # Priya (groomer 3)
        _book("KP-B2012", 2, 2, 3, 12,
              "2026-03-08", "11:00",
              "Keep topknot clean, she likes being talked to",
              "signature spa", 110.0)
        _book("KP-B2013", 10, 15, 3, 16,
              "2026-03-22", "14:00",
              "Go slowly on paw handling",
              "full scissor groom", 125.0)
        _book("KP-B2014", 3, 5, 3, 13,
              "2026-04-18", "10:00",
              "Mochi is very cooperative",
              "bath & style", 65.0)
        _book("KP-B2015", 7, 12, 3, 15,
              "2026-05-02", "09:00",
              "She is 10 and arthritic. Short sessions.",
              "nail & ear care", 30.0)
        _book("KP-B2016", 10, 15, 3, 12,
              "2026-05-30", "13:00",
              "Go slowly on paw handling — she's getting better with training",
              "signature spa", 110.0)

        # Marcus Johnson (groomer 4)
        _book("KP-B2017", 5, 7, 4, 18,
              "2026-03-05", "10:00",
              "She blows coat twice a year, needs full deshed. Do NOT shave.",
              "deshed & bath", 80.0)
        _book("KP-B2018", 4, 6, 4, 19,
              "2026-04-01", "13:00",
              "Let him sniff you first. Doesn't like face handling initially.",
              "full groom", 75.0)
        _book("KP-B2019", 11, 16, 4, 21,
              "2026-04-20", "09:00",
              "High energy, keep him moving",
              "breed trim", 85.0)
        _book("KP-B2020", 5, 7, 4, 18,
              "2026-05-15", "10:00",
              "Do NOT shave — deshed only",
              "deshed & bath", 80.0)
        _book("KP-B2021", 4, 18, 4, 19,
              "2026-06-03", "13:00",
              "He's strong so secure the table. Very friendly though!",
              "full groom", 75.0)

        # Sofia Klein (groomer 5)
        _book("KP-B2022", 5, 8, 5, 22,
              "2026-03-12", "11:00",
              "Needs anti-fatigue mat. Hip joints are stiff.",
              "senior dog spa", 70.0)
        _book("KP-B2023", 7, 12, 5, 22,
              "2026-03-26", "10:00",
              "She is 10 and arthritic. Short sessions, she gets tired quickly.",
              "senior dog spa", 70.0)
        _book("KP-B2024", 2, 2, 5, 23,
              "2026-04-14", "14:00",
              "Keep topknot clean, she likes being talked to",
              "gentle full groom", 80.0)
        _book("KP-B2025", 5, 8, 5, 22,
              "2026-05-10", "09:00",
              "Needs anti-fatigue mat. Hip very stiff lately.",
              "senior dog spa", 70.0)

        # David Park (groomer 6)
        _book("KP-B2026", 6, 9, 6, 28,
              "2026-03-18", "10:00",
              "Barks at clippers initially",
              "full groom", 95.0)
        _book("KP-B2027", 3, 5, 6, 27,
              "2026-04-08", "14:00",
              "Mochi is very cooperative",
              "competition prep", 145.0)
        _book("KP-B2028", 6, 9, 6, 31,
              "2026-05-20", "11:00",
              "Keep traditional schnauzer look — beard full",
              "breed trim", 110.0)

        # Aisha Williams (groomer 7)
        _book("KP-B2029", 8, 13, 7, 34,
              "2026-03-25", "10:00",
              "Rosie is wiggly but good-natured",
              "full groom", 80.0)
        _book("KP-B2030", 12, 17, 7, 32,
              "2026-04-10", "13:00",
              "Clean skin folds carefully. Sensitive skin — no harsh products.",
              "puppy first groom", 65.0)
        _book("KP-B2031", 8, 13, 7, 33,
              "2026-05-05", "10:00",
              "Playful and wiggly, treat-motivated",
              "bath & tidy", 50.0)
        _book("KP-B2032", 1, 1, 7, 34,
              "2026-05-28", "14:00",
              "Go slow with the dryer, anxious dog",
              "full groom", 80.0)

        # Carlos Mendez (groomer 8)
        _book("KP-B2033", 4, 18, 8, 41,
              "2026-03-30", "09:00",
              "He's strong so secure the table. Very friendly though!",
              "large breed groom", 85.0)
        _book("KP-B2034", 4, 6, 8, 39,
              "2026-04-25", "10:00",
              "Let him sniff you first",
              "deshed & bath", 70.0)
        _book("KP-B2035", 11, 16, 8, 41,
              "2026-05-22", "13:00",
              "High energy Australian Shepherd",
              "large breed groom", 85.0)

        # --- Upcoming confirmed bookings (C-series) ---
        _book("KP-C3001", 6, 9, 1, 2,
              "2026-06-19", "10:00",
              "Keep the beard full, traditional schnauzer look",
              "teddy bear", 90.0, status="confirmed")
        conn.execute(
            "UPDATE availability SET is_booked=1 WHERE groomer_id=1 AND date='2026-06-19' AND time_slot='10:00'"
        )

        _book("KP-C3002", 9, 14, 2, 9,
              "2026-06-20", "14:00",
              "Finn is big but gentle. Needs patience settling in.",
              "full groom", 85.0, status="confirmed")
        conn.execute(
            "UPDATE availability SET is_booked=1 WHERE groomer_id=2 AND date='2026-06-20' AND time_slot='14:00'"
        )

        _book("KP-C3003", 5, 7, 4, 18,
              "2026-06-22", "09:00",
              "Do NOT shave — deshed only. Summer peak shedding.",
              "deshed & bath", 80.0, status="confirmed")
        conn.execute(
            "UPDATE availability SET is_booked=1 WHERE groomer_id=4 AND date='2026-06-22' AND time_slot='09:00'"
        )

        _book("KP-C3004", 7, 12, 5, 22,
              "2026-06-23", "11:00",
              "She is 10 and arthritic. Short sessions.",
              "senior dog spa", 70.0, status="confirmed")
        conn.execute(
            "UPDATE availability SET is_booked=1 WHERE groomer_id=5 AND date='2026-06-23' AND time_slot='11:00'"
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
             "Max did great once I used a diffuser on the dryer. Took a couple of short breaks. "
             "Beautiful teddy bear. Coat is in excellent shape — clearly being brushed at home.",
             "2026-07-20", "2026-06-08 11:30:00"),

            ("KP-A1002", 2, 5,
             "healthy, medium length, good texture", "slightly dry around muzzle", "clean", "slightly long", "mild tear staining",
             "Mild tear staining around inner corners — worth monitoring.",
             "Bella was an absolute angel. Kept topknot pristine as requested. "
             "Recommend moisturizing shampoo next visit. Nails were just starting to curl.",
             "2026-07-13", "2026-06-01 15:30:00"),

            ("KP-B2001", 1, 1,
             "dense curls, light tangles at chest", "healthy", "clean", "good", "clear",
             "Light tangles at chest and armpits — recommend daily brushing there.",
             "Max was nervous with the dryer as expected. Used lowest setting and took breaks. "
             "Chest area had some tangles — flagged for owner. Coat otherwise very healthy.",
             "2026-04-21", "2026-03-10 10:00:00"),

            ("KP-B2002", 5, 1,
             "excellent curly coat, no matting", "healthy", "clean, slight wax", "good", "clear",
             "Slight ear wax buildup — recommend ear cleaning at next visit.",
             "Mochi was spirited but handled everything perfectly. She loved the dryer! "
             "Teddy bear came out adorable. Minor ear wax noted — will flag for owner.",
             "2026-05-01", "2026-03-20 14:15:00"),

            ("KP-B2003", 10, 1,
             "wavy puppy coat, some tangles at ears", "healthy", "clean", "good", "clear",
             "Ear area tangles — recommend daily brushing around ear folds.",
             "Ruby was wiggly and mouthy but so sweet. Took four short breaks and used lots of treats. "
             "Puppy first groom was a success. Owner should brush ears daily.",
             "2026-05-16", "2026-04-05 11:00:00"),

            ("KP-B2004", 1, 1,
             "excellent curly coat", "healthy", "clean", "good", "clear",
             "",
             "Max was calmer today than last time — building trust! Lamb cut came out beautifully. "
             "Coat in great shape. Anxious-dog handling protocol is working well.",
             "2026-06-03", "2026-04-22 12:30:00"),

            ("KP-B2005", 9, 1,
             "n/a — nail trim only", "n/a", "n/a", "nails trimmed, were slightly long", "n/a",
             "Nails were getting long — recommend 6-week nail schedule.",
             "Quick nail trim. Charlie barked at the sound initially but settled fast. Very cooperative.",
             "2026-06-19", "2026-05-08 14:20:00"),

            ("KP-B2006", 9, 1,
             "wiry, good condition, some wispy overgrowth", "healthy", "clean", "good", "clear",
             "",
             "Charlie was great today — minimal barking at clippers compared to last time. "
             "Traditional schnauzer look came out sharp. Building a good routine with him.",
             "2026-07-06", "2026-05-25 11:00:00"),

            ("KP-B2007", 6, 2,
             "healthy double coat, moderate shed", "normal", "clean", "slightly long", "clear",
             "Nails on the longer side — owner should book nail trim soon.",
             "Duke took about 10 minutes to settle but was cooperative once he relaxed. "
             "Good coat condition overall. Noted slightly long nails — mentioned to owner.",
             "2026-04-26", "2026-03-15 14:30:00"),

            ("KP-B2008", 14, 2,
             "thick double coat, some matting behind ears", "healthy", "mild redness", "good", "clear",
             "Mild ear redness — recommend vet check if persists. Matting behind ears worked out gently.",
             "Finn is a sweetheart but was very nervous coming in. Took time settling. "
             "Found some matting behind ears and mild ear redness — flagged for owner to monitor.",
             "2026-05-09", "2026-03-28 11:30:00"),

            ("KP-B2009", 4, 2,
             "healthy medium coat, light seasonal shed", "normal", "clean", "good", "clear",
             "",
             "Nala was a dream — cooperative and treat-motivated throughout. "
             "Light seasonal shedding is completely normal. Easy bath and brush-out.",
             "2026-05-24", "2026-04-12 15:00:00"),

            ("KP-B2010", 2, 2,
             "long coat, excellent condition, slight wave at ears", "normal", "clean", "good", "mild tear staining",
             "Mild tear staining — mention blueberry facial option to owner.",
             "Bella's show groom came out beautifully. She was patient and loved being talked to. "
             "Tear staining noted — will mention spa add-on to owner at pickup.",
             "2026-06-16", "2026-05-05 12:30:00"),

            ("KP-B2011", 6, 2,
             "n/a — nail & ear only", "n/a", "clean", "nails trimmed", "n/a",
             "",
             "Quick nail and ear clean. Duke was more relaxed than his full groom — familiar now. "
             "Ears clean. Nails done. Easy appointment.",
             "2026-06-29", "2026-05-18 09:30:00"),

            ("KP-B2012", 2, 3,
             "long silky coat, slight tangles at belly", "normal", "clean", "good", "mild tear staining",
             "Belly tangles from collar friction — recommend wider collar or daily belly brushing.",
             "Bella was wonderful — chatted to her throughout and she loved it. "
             "Belly tangles from collar noted. Tear staining mild but persistent — recommended facial add-on.",
             "2026-04-19", "2026-03-08 12:30:00"),

            ("KP-B2013", 15, 3,
             "long silky coat, healthy", "normal", "clean", "slightly long", "clear",
             "Nails slightly long. Paw handling took patience but she eventually cooperated.",
             "Daisy was sassy about her paws but I took it very slowly with breaks and treats. "
             "Full scissor groom came out beautifully — she's a stunning Yorkie. "
             "Nails trimmed with care. Owner is doing great work with paw desensitization.",
             "2026-05-03", "2026-03-22 15:30:00"),

            ("KP-B2014", 5, 3,
             "excellent curly coat, no matting", "healthy", "clean", "good", "clear",
             "",
             "Mochi was a total joy — cooperative, loved the dryer, loved the attention. "
             "Bath and style came out clean and polished. No concerns at all.",
             "2026-05-30", "2026-04-18 11:00:00"),

            ("KP-B2015", 12, 3,
             "n/a — nail & ear only", "n/a", "clean", "nails trimmed — overgrown", "n/a",
             "Nails were overgrown — arthritic dogs often resist nail trims so they get neglected. "
             "Recommend monthly nail appointments to stay on top of it.",
             "Coco was patient and cooperative considering her arthritis. "
             "Nails were quite long — mentioned to owner that monthly trims will help her comfort walking.",
             "2026-06-13", "2026-05-02 09:30:00"),

            ("KP-B2016", 15, 3,
             "long silky coat, beautiful condition", "normal", "clean", "good", "clear",
             "",
             "Daisy was much better with paw handling this visit! Owner's training is paying off. "
             "Signature spa groom — coat is gleaming. She smells amazing. No concerns.",
             "2026-07-11", "2026-05-30 14:30:00"),

            ("KP-B2017", 7, 4,
             "thick double coat, heavy seasonal blow", "healthy", "clean", "good", "clear",
             "Peak seasonal shedding — recommend deshed every 6 weeks through summer.",
             "Luna had an enormous amount of coat to come out. High-velocity dryer was essential. "
             "She's energetic and hates standing still but managed well with breaks. "
             "Did not clip — deshed only as requested. Owner will notice a huge difference.",
             "2026-04-16", "2026-03-05 11:30:00"),

            ("KP-B2018", 6, 4,
             "healthy double coat, moderate shedding", "normal", "clean", "good", "clear",
             "",
             "Duke took a while to warm up but was cooperative once he relaxed. "
             "Full groom looks clean and even. Building trust with each visit.",
             "2026-05-13", "2026-04-01 14:30:00"),

            ("KP-B2019", 16, 4,
             "thick double coat, some matting at flanks", "healthy", "clean", "good", "clear",
             "Flank matting found — recommend more frequent brushing or more regular grooming appointments.",
             "Cooper was bouncy and smart — needed to be kept mentally engaged. "
             "Found some flank matting, worked it out carefully. Breed trim came out sharp. "
             "Owner should increase brushing frequency for this coat type.",
             "2026-06-01", "2026-04-20 10:30:00"),

            ("KP-B2020", 7, 4,
             "thick double coat, summer peak shedding", "healthy", "clean", "good", "clear",
             "Summer peak blow — recommend deshed every 5-6 weeks through August.",
             "Luna again with massive summer shedding! She hates standing still but we got through it. "
             "High-velocity dryer removed an incredible amount of undercoat. Coat looks so much lighter. "
             "Did not clip as per owner request.",
             "2026-06-26", "2026-05-15 11:30:00"),

            ("KP-B2021", 18, 4,
             "short smooth coat, healthy", "normal", "clean", "good", "clear",
             "",
             "Bruno was strong and wiggly but totally friendly — exactly as owner described. "
             "Secured the table as requested. Full groom easy on short coat. No concerns.",
             "2026-07-15", "2026-06-03 14:30:00"),

            ("KP-B2022", 8, 5,
             "curly coat, slight felting behind ears", "normal for age, mild dryness", "clean", "good", "mild tear staining",
             "Felting behind ears — owner should check and brush weekly. Tear staining mild but typical for senior Bichons.",
             "Teddy is such a sweet senior. Went very slowly with extra breaks and warm water for the rinse. "
             "Found felting behind ears — gently worked it out. Used anti-fatigue mat throughout. "
             "He was comfortable and calm by the end.",
             "2026-04-23", "2026-03-12 12:30:00"),

            ("KP-B2023", 12, 5,
             "long silky coat, hip area matting", "thin coat typical of age", "clean", "slightly long", "clear",
             "Hip area matting from lying down. Arthritic — handled with extreme care. Nails slightly long.",
             "Coco was incredibly patient. Used foam mat and let her lie down when needed. "
             "Gently worked out hip matting — she needs more frequent grooming to prevent recurrence "
             "since arthritis limits at-home brushing. Mentioned daily gentle brushing to owner.",
             "2026-05-07", "2026-03-26 11:30:00"),

            ("KP-B2024", 2, 5,
             "healthy long coat, clean texture", "normal", "clean", "good", "mild tear staining",
             "Mild tear staining — blueberry facial would help, recommend as add-on.",
             "Bella was lovely — patient and cooperative. Kept topknot area pristine as always. "
             "Tear staining continuing — reminded owner about facial add-on. Easy, pleasant groom.",
             "2026-05-26", "2026-04-14 15:30:00"),

            ("KP-B2025", 8, 5,
             "curly coat, good condition", "normal, age-appropriate dryness", "clean", "good", "clear",
             "Hip stiffness more noticeable than last visit — owner should mention to vet.",
             "Teddy was more stiff than usual today. Lots of breaks, anti-fatigue mat the whole time. "
             "He was relaxed but tired quickly. Hip stiffness worth flagging to the vet. Sweet senior boy.",
             "2026-06-21", "2026-05-10 10:30:00"),

            ("KP-B2026", 9, 6,
             "wiry coat, good texture", "healthy", "clean", "good", "clear",
             "",
             "Charlie was alert and initially barked at the clippers but settled. "
             "Full groom with traditional schnauzer look — beard and brows looking sharp. "
             "David's precision work is well-suited for this breed.",
             "2026-04-29", "2026-03-18 11:30:00"),

            ("KP-B2027", 5, 6,
             "excellent curly coat, no matting", "healthy", "clean", "good", "clear",
             "",
             "Mochi was an absolute dream for competition prep. Cooperative, patient, and clearly "
             "well-socialized. The topknot geometry came out perfectly. Miniature Poodle precision work.",
             "2026-05-19", "2026-04-08 16:00:00"),

            ("KP-B2028", 9, 6,
             "wiry coat, excellent condition", "healthy", "clean", "good", "clear",
             "",
             "Charlie is getting better with each visit — barely barked at clippers today. "
             "Breed trim looks immaculate. Traditional schnauzer silhouette with full beard as owner wants. "
             "Consistent grooming schedule is clearly benefiting his coat and temperament.",
             "2026-07-01", "2026-05-20 12:30:00"),

            ("KP-B2029", 13, 7,
             "medium coat, healthy", "normal", "clean", "good", "clear",
             "",
             "Rosie was playful and wiggly but so good-natured — impossible not to love. "
             "Full groom came out clean and polished. Coat has a lovely natural sheen. No concerns.",
             "2026-05-06", "2026-03-25 11:30:00"),

            ("KP-B2030", 17, 7,
             "short smooth coat, skin folds checked", "mild redness in one facial fold", "clean", "good", "clear",
             "Mild redness in one facial fold — recommend vet check and regular fold cleaning at home.",
             "Stella was calm and cooperative — great with handling. Checked all skin folds carefully "
             "as requested with gentle, fragrance-free products. Found mild redness in one facial fold — "
             "flagged for owner. Puppy first groom went really well.",
             "2026-05-21", "2026-04-10 14:30:00"),

            ("KP-B2031", 13, 7,
             "medium coat, healthy with light shedding", "normal", "clean", "good", "clear",
             "",
             "Rosie was great as always — wiggly and sweet. Bath and tidy quick and easy. "
             "Light seasonal shedding normal for this coat type. No concerns.",
             "2026-06-16", "2026-05-05 11:30:00"),

            ("KP-B2032", 1, 7,
             "curly coat, some tangles at armpits", "healthy", "clean", "good", "clear",
             "Armpit tangles recurring — daily brushing in that area essential.",
             "Max was anxious with the dryer but Aisha's positive reinforcement approach helped a lot. "
             "Lots of treats and breaks. Armpit tangles again — recommended daily brushing to owner. "
             "Coat otherwise healthy. Full groom came out well.",
             "2026-07-09", "2026-05-28 15:30:00"),

            ("KP-B2033", 18, 8,
             "short smooth coat, healthy", "normal", "clean", "good", "clear",
             "",
             "Bruno is strong — secured the table as owner said. Very friendly and wiggly though! "
             "Large breed groom easy on his short coat. In and out efficiently. No concerns.",
             "2026-05-11", "2026-03-30 10:30:00"),

            ("KP-B2034", 6, 8,
             "healthy double coat, heavy shedding", "normal", "clean", "good", "clear",
             "Heavy seasonal shedding — recommend deshed every 6 weeks.",
             "Duke was cautious at first but settled well — becoming more comfortable with each visit. "
             "Deshed treatment removed a significant amount of undercoat. Owner will notice less shedding. "
             "Coat underneath is healthy and dense.",
             "2026-06-06", "2026-04-25 11:30:00"),

            ("KP-B2035", 16, 8,
             "thick double coat, some matting at collar", "healthy", "clean", "good", "clear",
             "Collar matting found — recommend checking and loosening collar regularly.",
             "Cooper was high-energy but manageable. Kept him mentally engaged throughout. "
             "Found collar matting — mentioned to owner. Large breed groom came out well. "
             "Coat is thick and healthy underneath the shed.",
             "2026-07-03", "2026-05-22 14:30:00"),
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
        # GROOM PHOTOS — one per completed booking with a cut/style
        # photo_url = '' — frontend fetches from dog.ceo
        # ------------------------------------------------------------------ #
        def _photo(booking_id, dog_id, groomer_id, caption, cut_style, is_portfolio=1):
            cur = conn.execute("""
                INSERT INTO groom_photos
                  (booking_id,dog_id,groomer_id,photo_url,caption,cut_style,is_portfolio,verified)
                VALUES (?,?,?,?,?,?,?,?)
            """, (booking_id, dog_id, groomer_id, "", caption, cut_style, is_portfolio, 1))
            return cur.lastrowid

        photo_map = {}  # booking_id -> photo_id (for linking in reviews)

        photo_map["KP-A1001"] = _photo("KP-A1001", 1, 1,
            "Max's teddy bear groom — June 8, Upper West Side", "teddy bear")
        photo_map["KP-A1002"] = _photo("KP-A1002", 2, 5,
            "Bella's gentle full groom — June 1, West Village", "gentle full groom")
        photo_map["KP-B2001"] = _photo("KP-B2001", 1, 1,
            "Max's bath & dry — March 10", "bath & dry")
        photo_map["KP-B2002"] = _photo("KP-B2002", 5, 1,
            "Mochi's teddy bear full groom — March 20", "teddy bear")
        photo_map["KP-B2003"] = _photo("KP-B2003", 10, 1,
            "Ruby's puppy first groom — April 5", "puppy cut")
        photo_map["KP-B2004"] = _photo("KP-B2004", 1, 1,
            "Max's lamb cut — April 22", "lamb cut")
        # KP-B2005 is nail-only — no photo
        photo_map["KP-B2006"] = _photo("KP-B2006", 9, 1,
            "Charlie's teddy bear groom — May 25", "teddy bear")
        photo_map["KP-B2007"] = _photo("KP-B2007", 6, 2,
            "Duke's full groom — March 15, Park Slope", "full groom")
        photo_map["KP-B2008"] = _photo("KP-B2008", 14, 2,
            "Finn's full groom — March 28, Park Slope", "full groom")
        photo_map["KP-B2009"] = _photo("KP-B2009", 4, 2,
            "Nala's bath & brush out — April 12", "bath & brush out")
        photo_map["KP-B2010"] = _photo("KP-B2010", 2, 2,
            "Bella's show groom — May 5, Park Slope", "show groom")
        # KP-B2011 is nail & ear only — no photo
        photo_map["KP-B2012"] = _photo("KP-B2012", 2, 3,
            "Bella's signature spa groom — March 8, Tribeca", "signature spa")
        photo_map["KP-B2013"] = _photo("KP-B2013", 15, 3,
            "Daisy's full scissor groom — March 22, Tribeca", "full scissor groom")
        photo_map["KP-B2014"] = _photo("KP-B2014", 5, 3,
            "Mochi's bath & style — April 18, Tribeca", "bath & style")
        # KP-B2015 is nail & ear only — no photo
        photo_map["KP-B2016"] = _photo("KP-B2016", 15, 3,
            "Daisy's signature spa groom — May 30, Tribeca", "signature spa")
        photo_map["KP-B2017"] = _photo("KP-B2017", 7, 4,
            "Luna's deshed & bath — March 5, Astoria", "deshed & bath")
        photo_map["KP-B2018"] = _photo("KP-B2018", 6, 4,
            "Duke's full groom — April 1, Astoria", "full groom")
        photo_map["KP-B2019"] = _photo("KP-B2019", 16, 4,
            "Cooper's breed trim — April 20, Astoria", "breed trim")
        photo_map["KP-B2020"] = _photo("KP-B2020", 7, 4,
            "Luna's deshed & bath — May 15, Astoria", "deshed & bath")
        photo_map["KP-B2021"] = _photo("KP-B2021", 18, 4,
            "Bruno's full groom — June 3, Astoria", "full groom")
        photo_map["KP-B2022"] = _photo("KP-B2022", 8, 5,
            "Teddy's senior dog spa — March 12, West Village", "senior dog spa")
        photo_map["KP-B2023"] = _photo("KP-B2023", 12, 5,
            "Coco's senior dog spa — March 26, West Village", "senior dog spa")
        photo_map["KP-B2024"] = _photo("KP-B2024", 2, 5,
            "Bella's gentle full groom — April 14, West Village", "gentle full groom")
        photo_map["KP-B2025"] = _photo("KP-B2025", 8, 5,
            "Teddy's senior dog spa — May 10, West Village", "senior dog spa")
        photo_map["KP-B2026"] = _photo("KP-B2026", 9, 6,
            "Charlie's full groom — March 18, Upper East Side", "full groom")
        photo_map["KP-B2027"] = _photo("KP-B2027", 5, 6,
            "Mochi's competition prep — April 8, Upper East Side", "competition prep")
        photo_map["KP-B2028"] = _photo("KP-B2028", 9, 6,
            "Charlie's breed trim — May 20, Upper East Side", "breed trim")
        photo_map["KP-B2029"] = _photo("KP-B2029", 13, 7,
            "Rosie's full groom — March 25, Williamsburg", "full groom")
        photo_map["KP-B2030"] = _photo("KP-B2030", 17, 7,
            "Stella's puppy first groom — April 10, Williamsburg", "puppy first groom")
        photo_map["KP-B2031"] = _photo("KP-B2031", 13, 7,
            "Rosie's bath & tidy — May 5, Williamsburg", "bath & tidy")
        photo_map["KP-B2032"] = _photo("KP-B2032", 1, 7,
            "Max's full groom — May 28, Williamsburg", "full groom")
        photo_map["KP-B2033"] = _photo("KP-B2033", 18, 8,
            "Bruno's large breed groom — March 30, Riverdale", "large breed groom")
        photo_map["KP-B2034"] = _photo("KP-B2034", 6, 8,
            "Duke's deshed & bath — April 25, Riverdale", "deshed & bath")
        photo_map["KP-B2035"] = _photo("KP-B2035", 16, 8,
            "Cooper's large breed groom — May 22, Riverdale", "large breed groom")

        # ------------------------------------------------------------------ #
        # REVIEWS for all completed bookings
        # ------------------------------------------------------------------ #
        reviews = [
            # (booking_id, owner_id, groomer_id, dog_id, photo_id, rating, review_text, cut_style)
            ("KP-A1001", 1, 1, 1, photo_map["KP-A1001"], 5,
             "Maya is incredible with Max. He's always been anxious at groomers but she was so patient — "
             "no cage dryers, one dog at a time, and she let him set the pace with the blow dryer. "
             "The teddy bear cut is the best he's ever had. Already rebooked.",
             "teddy bear"),

            ("KP-A1002", 2, 5, 2, photo_map["KP-A1002"], 5,
             "Sofia was so gentle with Bella. She flagged some tear staining and suggested a follow-up — "
             "that kind of attentiveness is exactly what we love. Bella came home happy and beautiful. "
             "West Village is the perfect little boutique grooming studio.",
             "gentle full groom"),

            ("KP-B2001", 1, 1, 1, photo_map["KP-B2001"], 4,
             "Maya did a great bath and dry for Max on his first visit. He was nervous but she handled it well. "
             "Used the lowest dryer setting and took breaks. Flagged some chest tangles to brush at home. "
             "Building trust slowly — will keep coming back.",
             "bath & dry"),

            ("KP-B2002", 3, 1, 5, photo_map["KP-B2002"], 5,
             "Mochi's teddy bear came out perfect. Maya has such an eye for Poodle cuts. "
             "Mochi loves the dryer so this was an easy one apparently — she just stood there happily. "
             "Coat shaping around the face was exactly right. Booking monthly.",
             "teddy bear"),

            ("KP-B2003", 6, 1, 10, photo_map["KP-B2003"], 5,
             "Ruby's first groom ever and Maya made it magical. Lots of treats, four short breaks, "
             "and zero stress. Ruby came home looking so grown-up and smelling amazing. "
             "If you have a puppy or an anxious dog, Maya on the Upper West Side is your groomer.",
             "puppy cut"),

            ("KP-B2004", 1, 1, 1, photo_map["KP-B2004"], 5,
             "The lamb cut on Max is stunning — best groom he's ever had. Maya keeps getting better "
             "with him as he builds trust. He was calmer this visit than ever before. "
             "The no-cage-dryer policy makes such a difference for anxious dogs.",
             "lamb cut"),

            ("KP-B2005", 6, 1, 9, None, 5,
             "Quick and clean nail trim for Charlie. Maya was fast and efficient — done in under 15 minutes. "
             "Charlie barely barked. Great for a standalone nail appointment between full grooms.",
             ""),

            ("KP-B2006", 6, 1, 9, photo_map["KP-B2006"], 5,
             "Charlie's schnauzer cut looked immaculate. Maya really understands the breed standard. "
             "His beard is full and his eyebrows are perfectly shaped. Much less fuss with the clippers "
             "this visit — he's clearly getting comfortable with Maya.",
             "teddy bear"),

            ("KP-B2007", 4, 2, 6, photo_map["KP-B2007"], 4,
             "James did a solid job with Duke. Duke is standoffish with strangers but James gave him "
             "10 minutes to sniff and settle before starting — really appreciated that. "
             "Groom looks clean and even. Mentioned Duke's nails were getting long too, which was helpful.",
             "full groom"),

            ("KP-B2008", 9, 2, 14, photo_map["KP-B2008"], 4,
             "James was great with Finn but Finn had a rough time settling in. James was very patient. "
             "He did flag some ear redness which we've since had checked — caught early, good outcome. "
             "Would book again, just know Finn needs extra time.",
             "full groom"),

            ("KP-B2009", 3, 2, 4, photo_map["KP-B2009"], 5,
             "Easy, professional bath and brush-out for Nala. James is efficient and thorough. "
             "Nala was cooperative as always and came back looking pristine. "
             "Brooklyn Groom Co. in Park Slope is super convenient.",
             "bath & brush out"),

            ("KP-B2010", 2, 2, 2, photo_map["KP-B2010"], 5,
             "Bella's show groom was genuinely impressive. James clearly knows what he's doing "
             "with Shih Tzus — the coat was perfect and the topknot impeccable. "
             "He also noticed the tear staining and mentioned a facial add-on, which was thoughtful. "
             "Best groom Bella has had anywhere.",
             "show groom"),

            ("KP-B2011", 4, 2, 6, None, 5,
             "Quick nail and ear clean for Duke. James is familiar with him now and Duke was much more relaxed. "
             "Fast, professional, and reasonably priced. Easy add-on appointment.",
             ""),

            ("KP-B2012", 2, 3, 2, photo_map["KP-B2012"], 5,
             "Tribeca Tails is exactly the boutique experience we wanted for Bella. Priya was wonderful — "
             "she talked to Bella the whole time and Bella was totally relaxed. The aromatherapy rinse "
             "was a lovely touch. Noticed belly tangles from the collar and gave great advice.",
             "signature spa"),

            ("KP-B2013", 10, 3, 15, photo_map["KP-B2013"], 5,
             "Priya did a beautiful scissor-only groom on Daisy. The precision is incredible — "
             "she took her time with the paw handling and was patient when Daisy got sassy about it. "
             "Daisy looked like she'd just come from a show ring. Worth every penny.",
             "full scissor groom"),

            ("KP-B2014", 3, 3, 5, photo_map["KP-B2014"], 5,
             "Mochi is an easy client but Priya still went above and beyond. Bath and style was "
             "polished and precise. Priya clearly loves her work — the attention to detail shows. "
             "Already booked next appointment.",
             "bath & style"),

            ("KP-B2015", 7, 3, 12, None, 5,
             "Priya was incredibly gentle with Coco for her nail and ear appointment. "
             "She spotted that the nails were overgrown — not surprising given Coco's arthritis — "
             "and recommended monthly trims going forward. Very thoughtful care.",
             ""),

            ("KP-B2016", 10, 3, 15, photo_map["KP-B2016"], 5,
             "Daisy's second visit to Priya and she was so much better with her paws this time! "
             "Priya said our training is paying off. The signature spa is gorgeous — "
             "Daisy smelled incredible for days. Tribeca Tails is our forever groomer.",
             "signature spa"),

            ("KP-B2017", 5, 4, 7, photo_map["KP-B2017"], 5,
             "Marcus at Queens Paws is the best for Huskies. He really understands double coats — "
             "never suggested shaving and used the high-velocity dryer expertly. "
             "The amount of undercoat he removed was genuinely shocking. Luna felt so much lighter.",
             "deshed & bath"),

            ("KP-B2018", 4, 4, 6, photo_map["KP-B2018"], 4,
             "Marcus did a good job with Duke. He gave him room to settle which I appreciated. "
             "Full groom came out clean. Big workspace in Astoria is perfect for large breeds — "
             "Duke wasn't cramped at all. Will bring him back.",
             "full groom"),

            ("KP-B2019", 11, 4, 16, photo_map["KP-B2019"], 4,
             "Marcus handled Cooper's energy well — kept him engaged and moving. "
             "Found some flank matting I didn't know about and worked it out. Breed trim looks sharp. "
             "Astoria is a bit far for us but the quality is worth it.",
             "breed trim"),

            ("KP-B2020", 5, 4, 7, photo_map["KP-B2020"], 5,
             "Second deshed for Luna's summer blow and it was just as impressive as the first. "
             "Marcus never pushes shaving — he gets that Huskies shouldn't be clipped. "
             "Luna came home looking and feeling so much better. Booking every 6 weeks through summer.",
             "deshed & bath"),

            ("KP-B2021", 4, 4, 18, photo_map["KP-B2021"], 5,
             "Marcus handled Bruno like a pro. Bruno is a handful — strong and wiggly — but Marcus "
             "secured everything properly and Bruno came through fine. Full groom was thorough and "
             "quick given his short coat. Great value in Astoria.",
             "full groom"),

            ("KP-B2022", 5, 5, 8, photo_map["KP-B2022"], 5,
             "Sofia is exactly who you want for a senior dog. Teddy gets stiff and slow and she "
             "never rushed him for a second. She used an anti-fatigue mat, took breaks, and used "
             "warm water for the rinse. He came home so relaxed. Found ear felting too — very observant.",
             "senior dog spa"),

            ("KP-B2023", 7, 5, 12, photo_map["KP-B2023"], 5,
             "I have taken Coco to many groomers and Sofia at Village Grooming Studio is in a different league. "
             "She let Coco lie down on a foam mat, worked around her stiff hips, and never once rushed her. "
             "Coco came home happy and beautiful. This is the groomer for senior dogs in NYC.",
             "senior dog spa"),

            ("KP-B2024", 2, 5, 2, photo_map["KP-B2024"], 5,
             "Another beautiful groom from Sofia for Bella. She remembered all the details from before — "
             "topknot pristine, talked to her throughout. Flagged tear staining again and suggested "
             "the blueberry facial. Will add it next time. Consistently excellent.",
             "gentle full groom"),

            ("KP-B2025", 5, 5, 8, photo_map["KP-B2025"], 5,
             "Sofia noticed Teddy's hip stiffness was worse than before and gently mentioned we should "
             "bring it up with our vet. That kind of attentiveness from a groomer is rare. "
             "He came home looking beautiful and she made sure he was comfortable the whole time.",
             "senior dog spa"),

            ("KP-B2026", 6, 6, 9, photo_map["KP-B2026"], 5,
             "David at ProGroom NYC is exceptional. Charlie's full groom was precise — "
             "the schnauzer cut was geometrically perfect. David handled the initial clipper barking "
             "with calm authority and Charlie settled fast. Upper East Side convenience is a bonus.",
             "full groom"),

            ("KP-B2027", 3, 6, 5, photo_map["KP-B2027"], 5,
             "We took Mochi in for competition prep on a whim and the result was incredible. "
             "David's background as an AKC handler is obvious — the topknot was geometrically perfect. "
             "Mochi was cooperative and David was meticulous. Worth the premium price.",
             "competition prep"),

            ("KP-B2028", 6, 6, 9, photo_map["KP-B2028"], 5,
             "Charlie barely reacted to the clippers this visit. David's consistency is building "
             "a great relationship with him. The breed trim is always immaculate — traditional schnauzer "
             "look with a full beard exactly as we want. ProGroom NYC is Charlie's permanent groomer.",
             "breed trim"),

            ("KP-B2029", 8, 7, 13, photo_map["KP-B2029"], 5,
             "Aisha was wonderful with Rosie. Rosie is wiggly and full of energy but Aisha handled "
             "it with patience and humor. Full groom looked beautiful. Williamsburg pickup was super "
             "convenient. Already booked the next appointment.",
             "full groom"),

            ("KP-B2030", 12, 7, 17, photo_map["KP-B2030"], 5,
             "Stella's first groom and Aisha made it such a positive experience. She checked every "
             "skin fold carefully with fragrance-free products as requested. Found mild redness in one "
             "fold we didn't know about — that observation was incredibly helpful. Stella loved her.",
             "puppy first groom"),

            ("KP-B2031", 8, 7, 13, photo_map["KP-B2031"], 5,
             "Quick bath and tidy for Rosie — clean, professional, and easy. Aisha knows Rosie now "
             "so drop-off is a breeze. Rosie runs in happily. Exactly what you want in a local groomer.",
             "bath & tidy"),

            ("KP-B2032", 1, 7, 1, photo_map["KP-B2032"], 4,
             "Aisha was really patient with Max's dryer anxiety. Lots of treats, no rush, positive "
             "reinforcement throughout. Full groom came out well. Max was anxious but Aisha never "
             "forced anything. Will keep coming back as he builds confidence.",
             "full groom"),

            ("KP-B2033", 4, 8, 18, photo_map["KP-B2033"], 5,
             "Carlos at Bronx Pro Groomers is exactly what we needed. Honest pricing, no upsells, "
             "and he clearly loves big dogs. Bruno is a handful but Carlos managed him perfectly — "
             "secured the table as we mentioned and got through the whole groom without incident.",
             "large breed groom"),

            ("KP-B2034", 4, 8, 6, photo_map["KP-B2034"], 4,
             "Good deshed treatment for Duke in Riverdale. Carlos gave him time to settle "
             "and the deshed made a noticeable difference in shedding at home. "
             "Great pricing for quality work — not everyone needs to go to Manhattan.",
             "deshed & bath"),

            ("KP-B2035", 11, 8, 16, photo_map["KP-B2035"], 5,
             "Carlos handled Cooper's energy really well. Found collar matting I didn't know about "
             "and gave great advice about checking it regularly. Large breed groom was thorough and "
             "reasonably priced. The Bronx finally has a great groomer for big dogs.",
             "large breed groom"),
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


if __name__ == "__main__":
    bootstrap()
    print(f"KindPaw database ready: {DB_PATH}")
