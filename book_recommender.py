"""
AI Based Book Recommendations Systems
=====================================
100% offline - no API, no internet, no extra packages (Python 3 + tkinter only).

Pipeline (follows the project chart):

    Environment -> Sensor -> Data collect -> Decision
                -> Actuators -> Database -> Analysis

    Environment : the book catalog (books.csv) + the reader's world
    Sensor      : reads what the user types / selects in the window
    Data collect: cleans + validates the input into one "record"
    Decision    : AI engine (TF-IDF + cosine similarity) ranks the books
    Actuators   : show the recommendations in the window
    Database    : history.csv stores every recommendation made
    Analysis    : statistics + bar charts built from history.csv
                  (can be exported to analysis_report.csv)

Run:  python book_recommender.py
"""

import csv
import math
import os
import re
import tkinter as tk
from collections import Counter
from datetime import datetime
from tkinter import messagebox, ttk

BASE = os.path.dirname(os.path.abspath(__file__))
BOOKS_CSV = os.path.join(BASE, "books.csv")
HISTORY_CSV = os.path.join(BASE, "history.csv")
REPORT_CSV = os.path.join(BASE, "analysis_report.csv")

BOOK_FIELDS = ["id", "title", "author", "genre", "year", "rating", "description"]
HISTORY_FIELDS = ["timestamp", "interests", "genre_filter", "min_rating",
                  "liked_book", "rank", "title", "author", "genre", "rating",
                  "match_percent"]

# ----------------------------------------------------------------------------
# Built-in starter catalog (written to books.csv the first time you run it).
# You can open books.csv and add your own rows - the app reloads it on start.
# ----------------------------------------------------------------------------
STARTER_BOOKS = [
    ("The Hobbit", "J.R.R. Tolkien", "Fantasy", 1937, 4.7, "A hobbit joins dwarves and a wizard on an adventure to reclaim treasure from a dragon."),
    ("Harry Potter and the Sorcerer's Stone", "J.K. Rowling", "Fantasy", 1997, 4.7, "A young orphan discovers he is a wizard and attends a magic school full of friendship and danger."),
    ("The Name of the Wind", "Patrick Rothfuss", "Fantasy", 2007, 4.5, "A gifted musician and magician tells the story of his life, learning magic at a university and chasing legends."),
    ("A Game of Thrones", "George R.R. Martin", "Fantasy", 1996, 4.6, "Noble families fight for the throne in a brutal medieval world of politics, war and dragons."),
    ("Mistborn: The Final Empire", "Brandon Sanderson", "Fantasy", 2006, 4.6, "A thief with metal-burning magic leads a rebellion against an immortal tyrant emperor."),
    ("Dune", "Frank Herbert", "Science Fiction", 1965, 4.5, "A noble family fights for control of a desert planet that produces the most valuable spice in the universe."),
    ("Foundation", "Isaac Asimov", "Science Fiction", 1951, 4.3, "A mathematician predicts the fall of a galactic empire and plans to preserve human knowledge."),
    ("Neuromancer", "William Gibson", "Science Fiction", 1984, 4.0, "A washed-up hacker is hired for a cyberspace heist involving artificial intelligence."),
    ("The Martian", "Andy Weir", "Science Fiction", 2011, 4.7, "An astronaut stranded on Mars uses science and humor to survive until rescue."),
    ("Ender's Game", "Orson Scott Card", "Science Fiction", 1985, 4.4, "A gifted child is trained in a military space academy to fight an alien invasion."),
    ("Project Hail Mary", "Andy Weir", "Science Fiction", 2021, 4.8, "A lone astronaut wakes with amnesia on a spaceship and must save Earth using science and an alien friend."),
    ("The Girl with the Dragon Tattoo", "Stieg Larsson", "Mystery", 2005, 4.2, "A journalist and a hacker investigate a decades-old disappearance inside a wealthy family."),
    ("And Then There Were None", "Agatha Christie", "Mystery", 1939, 4.6, "Ten strangers on an island are killed one by one in a classic murder puzzle."),
    ("Gone Girl", "Gillian Flynn", "Thriller", 2012, 4.1, "A husband becomes the suspect when his wife vanishes, revealing dark marriage secrets."),
    ("The Da Vinci Code", "Dan Brown", "Thriller", 2003, 4.0, "A symbologist races to decode secret history, art and religion clues in a fast chase."),
    ("The Silent Patient", "Alex Michaelides", "Thriller", 2019, 4.2, "A therapist is obsessed with a painter who refuses to speak after murdering her husband."),
    ("Pride and Prejudice", "Jane Austen", "Romance", 1813, 4.6, "A witty young woman and a proud wealthy man overcome class and misunderstanding to fall in love."),
    ("Outlander", "Diana Gabaldon", "Romance", 1991, 4.4, "A nurse travels back in time to eighteenth century Scotland and falls in love with a warrior."),
    ("The Notebook", "Nicholas Sparks", "Romance", 1996, 4.1, "A touching love story between two young lovers separated by class and war and reunited later in life."),
    ("Me Before You", "Jojo Moyes", "Romance", 2012, 4.3, "A cheerful caregiver and a paralyzed man change each other's lives in an emotional love story."),
    ("All the Light We Cannot See", "Anthony Doerr", "Historical", 2014, 4.5, "A blind French girl and a German boy collide during World War Two."),
    ("The Book Thief", "Markus Zusak", "Historical", 2005, 4.7, "A girl in Nazi Germany steals books and shares stories while hiding a Jewish man."),
    ("Pillars of the Earth", "Ken Follett", "Historical", 1989, 4.5, "Builders, monks and nobles struggle during the construction of a medieval cathedral."),
    ("Atomic Habits", "James Clear", "Self-Help", 2018, 4.8, "Small habits and daily systems create remarkable change, productivity and self improvement."),
    ("The 7 Habits of Highly Effective People", "Stephen Covey", "Self-Help", 1989, 4.4, "Principles for personal effectiveness, leadership, goals and character."),
    ("Mindset", "Carol Dweck", "Self-Help", 2006, 4.3, "How a growth mindset helps people learn, succeed and overcome failure."),
    ("Deep Work", "Cal Newport", "Self-Help", 2016, 4.3, "Rules for focused success and productivity in a distracted world."),
    ("Sapiens", "Yuval Noah Harari", "Non-Fiction", 2011, 4.6, "A brief history of humankind from the stone age to modern society, culture and technology."),
    ("Educated", "Tara Westover", "Biography", 2018, 4.7, "A memoir of a woman raised in a survivalist family who teaches herself and earns a university education."),
    ("Steve Jobs", "Walter Isaacson", "Biography", 2011, 4.4, "The life of the Apple founder, a genius of technology, design and business."),
    ("Long Walk to Freedom", "Nelson Mandela", "Biography", 1994, 4.6, "The autobiography of Nelson Mandela and his struggle against apartheid and for freedom."),
    ("A Brief History of Time", "Stephen Hawking", "Science", 1988, 4.4, "Black holes, the big bang, space, time and the universe explained for everyone."),
    ("Cosmos", "Carl Sagan", "Science", 1980, 4.7, "A journey through the universe, stars, planets and the history of science."),
    ("The Selfish Gene", "Richard Dawkins", "Science", 1976, 4.2, "Evolution seen from the perspective of genes, biology and natural selection."),
    ("Life 3.0", "Max Tegmark", "Science", 2017, 4.1, "Being human in the age of artificial intelligence, machines, future and technology."),
    ("Dracula", "Bram Stoker", "Horror", 1897, 4.2, "A vampire count travels from Transylvania to England, hunted by a group of determined friends."),
    ("It", "Stephen King", "Horror", 1986, 4.3, "A group of friends confront a shape-shifting evil clown that terrorizes their town."),
    ("Frankenstein", "Mary Shelley", "Horror", 1818, 4.1, "A scientist creates a living creature and suffers the terrible consequences."),
    ("1984", "George Orwell", "Classic", 1949, 4.7, "A man rebels against a totalitarian government that watches and controls everything."),
    ("To Kill a Mockingbird", "Harper Lee", "Classic", 1960, 4.8, "A lawyer defends an innocent man in a racist southern town seen through his daughter's eyes."),
    ("The Great Gatsby", "F. Scott Fitzgerald", "Classic", 1925, 4.2, "A mysterious millionaire chases love and the American dream in the jazz age."),
    ("The Alchemist", "Paulo Coelho", "Classic", 1988, 4.3, "A shepherd boy follows his dream on a journey to Egypt, learning about destiny and life."),
]

STOPWORDS = set(
    "a an the and or of to in on for with is are was were be it this that i me my "
    "want like some about book books read reading story stories good best from as "
    "at by who his her their into over than then when where how what will can have "
    "has had not but all any one two".split()
)


def tokenize(text):
    """Lower-case words, drop stop-words, light stemming (plural -> singular)."""
    out = []
    for w in re.findall(r"[a-z]+", text.lower()):
        if w in STOPWORDS or len(w) < 3:
            continue
        if w.endswith("ies") and len(w) > 4:
            w = w[:-3] + "y"
        elif w.endswith("s") and not w.endswith("ss") and len(w) > 3:
            w = w[:-1]
        out.append(w)
    return out


# ============================================================================
# 1. ENVIRONMENT  - the world the system lives in: the book catalog
# ============================================================================
class Environment:
    def __init__(self, path=BOOKS_CSV):
        self.path = path
        self._ensure_catalog()
        self.books = self._load()

    def _ensure_catalog(self):
        if os.path.exists(self.path):
            return
        with open(self.path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(BOOK_FIELDS)
            for i, b in enumerate(STARTER_BOOKS, start=1):
                w.writerow([i, *b])

    def _load(self):
        with open(self.path, newline="", encoding="utf-8") as f:
            return [row for row in csv.DictReader(f)]

    @property
    def genres(self):
        return sorted({b["genre"] for b in self.books})

    @property
    def titles(self):
        return sorted(b["title"] for b in self.books)


# ============================================================================
# 2. SENSOR  - captures raw input from the user interface
# ============================================================================
class Sensor:
    @staticmethod
    def read(interests_var, genre_var, rating_var, liked_var):
        return {
            "interests": interests_var.get(),
            "genre": genre_var.get(),
            "min_rating": rating_var.get(),
            "liked_book": liked_var.get(),
        }


# ============================================================================
# 3. DATA COLLECT  - cleans and validates sensor data into one record
# ============================================================================
class DataCollector:
    @staticmethod
    def collect(raw):
        try:
            min_rating = float(raw["min_rating"])
        except ValueError:
            min_rating = 0.0
        record = {
            "interests": " ".join(raw["interests"].split()),
            "genre": raw["genre"] or "Any",
            "min_rating": max(0.0, min(5.0, min_rating)),
            "liked_book": raw["liked_book"].strip(),
        }
        valid = bool(record["interests"] or record["liked_book"] or record["genre"] != "Any")
        return record, valid


# ============================================================================
# 4. DECISION  - the AI engine (TF-IDF vectors + cosine similarity)
# ============================================================================
class DecisionEngine:
    def __init__(self, books):
        self.books = books
        self.docs = [
            tokenize(f"{b['title']} {(b['genre'] + ' ') * 2} {b['description']}")
            for b in books
        ]
        n = len(self.docs)
        df = Counter()
        for d in self.docs:
            df.update(set(d))
        self.idf = {t: math.log((n + 1) / (c + 1)) + 1 for t, c in df.items()}
        self.vecs = [self._vector(d) for d in self.docs]

    def _vector(self, tokens):
        tf = Counter(tokens)
        v = {t: (1 + math.log(c)) * self.idf.get(t, 1.0) for t, c in tf.items()}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        return {t: x / norm for t, x in v.items()}

    @staticmethod
    def _cosine(a, b):
        if len(a) > len(b):
            a, b = b, a
        return sum(x * b.get(t, 0.0) for t, x in a.items())

    def decide(self, record, top_n=8):
        query_vec = self._vector(tokenize(record["interests"])) if record["interests"] else {}
        liked_idx = next((i for i, b in enumerate(self.books)
                          if b["title"] == record["liked_book"]), None)

        candidates = []
        for i, b in enumerate(self.books):
            if i == liked_idx:
                continue
            if float(b["rating"]) < record["min_rating"]:
                continue
            if record["genre"] != "Any" and b["genre"] != record["genre"]:
                continue
            parts = []
            if query_vec:
                parts.append((0.65, self._cosine(query_vec, self.vecs[i])))
            if liked_idx is not None:
                parts.append((0.35, self._cosine(self.vecs[liked_idx], self.vecs[i])))
            content = (sum(w * s for w, s in parts) / sum(w for w, _ in parts)) if parts else 0.0
            candidates.append((i, content))

        if not candidates:
            return []
        top_content = max(c for _, c in candidates) or 1.0

        results = []
        for i, content in candidates:
            b = self.books[i]
            rating_score = float(b["rating"]) / 5.0
            if top_content > 0 and (query_vec or liked_idx is not None):
                score = 0.85 * (content / top_content) + 0.15 * rating_score
            else:
                score = rating_score           # no text signal: rank by rating
            results.append({**b, "score": round(min(score, 1.0) * 100, 1)})

        results.sort(key=lambda r: (-r["score"], -float(r["rating"])))
        return results[:top_n]


# ============================================================================
# 6. DATABASE  - history.csv keeps every recommendation made
# ============================================================================
class Database:
    def __init__(self, path=HISTORY_CSV):
        self.path = path

    def store(self, record, results):
        new_file = not os.path.exists(self.path)
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.path, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if new_file:
                w.writerow(HISTORY_FIELDS)
            for rank, r in enumerate(results, start=1):
                w.writerow([stamp, record["interests"], record["genre"],
                            record["min_rating"], record["liked_book"], rank,
                            r["title"], r["author"], r["genre"], r["rating"], r["score"]])

    def read(self):
        if not os.path.exists(self.path):
            return []
        with open(self.path, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))


# ============================================================================
# 7. ANALYSIS  - statistics over the stored history
# ============================================================================
class Analysis:
    @staticmethod
    def run(rows):
        if not rows:
            return None
        sessions = {r["timestamp"] for r in rows}
        words = Counter()
        for r in rows:
            if r["rank"] == "1":
                words.update(tokenize(r["interests"]))
        return {
            "sessions": len(sessions),
            "rows": len(rows),
            "avg_match": sum(float(r["match_percent"]) for r in rows) / len(rows),
            "top_books": Counter(r["title"] for r in rows).most_common(6),
            "top_genres": Counter(r["genre"] for r in rows).most_common(6),
            "top_keywords": words.most_common(6),
        }

    @staticmethod
    def export(stats, path=REPORT_CSV):
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["section", "name", "value"])
            w.writerow(["summary", "search sessions", stats["sessions"]])
            w.writerow(["summary", "recommendations stored", stats["rows"]])
            w.writerow(["summary", "average match %", round(stats["avg_match"], 1)])
            for key, label in (("top_books", "top book"), ("top_genres", "top genre"),
                               ("top_keywords", "top keyword")):
                for name, count in stats[key]:
                    w.writerow([label, name, count])


# ============================================================================
# 5. ACTUATORS  - what the system DOES: shows results to the user
# ============================================================================
class Actuator:
    @staticmethod
    def display(tree, results):
        tree.delete(*tree.get_children())
        for rank, r in enumerate(results, start=1):
            tree.insert("", "end", values=(rank, r["title"], r["author"],
                                           r["genre"], r["rating"], f"{r['score']}%"))


# ============================================================================
# GUI window
# ============================================================================
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AI Based Book Recommendations Systems")
        self.geometry("920x660")
        self.minsize(820, 600)
        try:
            ttk.Style(self).theme_use("clam")
        except tk.TclError:
            pass

        # system parts (the chart blocks)
        self.environment = Environment()
        self.engine = DecisionEngine(self.environment.books)
        self.database = Database()

        self._build_ui()
        self.log(f"[Environment] Loaded {len(self.environment.books)} books from books.csv")
        self.refresh_analysis()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        tk.Label(self, text="AI Based Book Recommendations Systems",
                 font=("Segoe UI", 16, "bold")).pack(pady=(10, 0))
        tk.Label(self, text="Offline AI  |  no API  |  data stored in CSV",
                 font=("Segoe UI", 9)).pack(pady=(0, 8))

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.tab_rec = ttk.Frame(nb)
        self.tab_cat = ttk.Frame(nb)
        self.tab_ana = ttk.Frame(nb)
        nb.add(self.tab_rec, text="  Recommend  ")
        nb.add(self.tab_cat, text="  Catalog (books.csv)  ")
        nb.add(self.tab_ana, text="  Analysis (history.csv)  ")

        self._build_recommend_tab()
        self._build_catalog_tab()
        self._build_analysis_tab()

    def _build_recommend_tab(self):
        f = ttk.Frame(self.tab_rec, padding=10)
        f.pack(fill="x")

        self.v_interests = tk.StringVar()
        self.v_genre = tk.StringVar(value="Any")
        self.v_rating = tk.StringVar(value="0")
        self.v_liked = tk.StringVar()

        ttk.Label(f, text="What do you want to read about?").grid(row=0, column=0, sticky="w")
        e = ttk.Entry(f, textvariable=self.v_interests, width=60)
        e.grid(row=0, column=1, columnspan=3, sticky="we", padx=6, pady=3)
        e.bind("<Return>", lambda _e: self.on_recommend())
        e.focus_set()

        ttk.Label(f, text="Genre").grid(row=1, column=0, sticky="w")
        ttk.Combobox(f, textvariable=self.v_genre, state="readonly", width=22,
                     values=["Any"] + self.environment.genres
                     ).grid(row=1, column=1, sticky="w", padx=6, pady=3)

        ttk.Label(f, text="Minimum rating (0-5)").grid(row=1, column=2, sticky="e")
        ttk.Spinbox(f, from_=0, to=5, increment=0.1, textvariable=self.v_rating,
                    width=6).grid(row=1, column=3, sticky="w", padx=6)

        ttk.Label(f, text="A book I already liked").grid(row=2, column=0, sticky="w")
        ttk.Combobox(f, textvariable=self.v_liked, width=40,
                     values=[""] + self.environment.titles
                     ).grid(row=2, column=1, columnspan=2, sticky="w", padx=6, pady=3)

        ttk.Button(f, text="Recommend books", command=self.on_recommend
                   ).grid(row=2, column=3, sticky="e", padx=6)
        f.columnconfigure(1, weight=1)

        cols = ("Rank", "Title", "Author", "Genre", "Rating", "Match")
        widths = (50, 280, 160, 110, 60, 70)
        self.tree = ttk.Treeview(self.tab_rec, columns=cols, show="headings", height=10)
        for c, w in zip(cols, widths):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor="w" if c in ("Title", "Author") else "center")
        self.tree.pack(fill="both", expand=True, padx=10, pady=4)

        tk.Label(self.tab_rec, text="System pipeline log:", anchor="w",
                 font=("Segoe UI", 9, "bold")).pack(fill="x", padx=10)
        self.log_box = tk.Text(self.tab_rec, height=8, state="disabled",
                               font=("Consolas", 9), bg="#f4f6fa")
        self.log_box.pack(fill="x", padx=10, pady=(0, 10))

    def _build_catalog_tab(self):
        cols = ("id", "title", "author", "genre", "year", "rating")
        tree = ttk.Treeview(self.tab_cat, columns=cols, show="headings")
        for c, w in zip(cols, (40, 300, 180, 110, 60, 60)):
            tree.heading(c, text=c.title())
            tree.column(c, width=w, anchor="w")
        sb = ttk.Scrollbar(self.tab_cat, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        sb.pack(side="right", fill="y", pady=10, padx=(0, 10))
        for b in self.environment.books:
            tree.insert("", "end", values=[b[c] for c in cols])

    def _build_analysis_tab(self):
        top = ttk.Frame(self.tab_ana, padding=10)
        top.pack(fill="x")
        self.lbl_summary = ttk.Label(top, text="", font=("Segoe UI", 10, "bold"))
        self.lbl_summary.pack(side="left")
        ttk.Button(top, text="Export analysis_report.csv",
                   command=self.on_export).pack(side="right")
        ttk.Button(top, text="Refresh", command=self.refresh_analysis
                   ).pack(side="right", padx=6)

        self.canvas_books = tk.Canvas(self.tab_ana, height=190, bg="white", highlightthickness=0)
        self.canvas_genres = tk.Canvas(self.tab_ana, height=190, bg="white", highlightthickness=0)
        self.canvas_books.pack(fill="x", padx=10, pady=4)
        self.canvas_genres.pack(fill="x", padx=10, pady=4)

    # ------------------------------------------------------------ helpers
    def log(self, text):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    @staticmethod
    def draw_bars(canvas, title, data):
        canvas.delete("all")
        canvas.create_text(10, 12, text=title, anchor="w", font=("Segoe UI", 10, "bold"))
        if not data:
            canvas.create_text(10, 50, text="No data yet - make some recommendations first.",
                               anchor="w", fill="#777")
            return
        max_v = max(v for _, v in data) or 1
        for i, (label, value) in enumerate(data):
            y = 36 + i * 24
            canvas.create_text(10, y, text=label[:32], anchor="w", font=("Segoe UI", 9))
            length = 300 * value / max_v
            canvas.create_rectangle(250, y - 8, 250 + length, y + 8, fill="#4f7cff", outline="")
            canvas.create_text(256 + length, y, text=str(value), anchor="w", font=("Segoe UI", 9))

    # ---------------------------------------------------------- pipeline
    def on_recommend(self):
        # SENSOR
        raw = Sensor.read(self.v_interests, self.v_genre, self.v_rating, self.v_liked)
        self.log("[Sensor]       captured user input")

        # DATA COLLECT
        record, valid = DataCollector.collect(raw)
        if not valid:
            messagebox.showinfo("Need input", "Type what you like, pick a genre, or choose a book you liked.")
            self.log("[Data collect] input empty - waiting for the user")
            return
        self.log(f"[Data collect] record -> interests='{record['interests']}', "
                 f"genre={record['genre']}, min_rating={record['min_rating']}, "
                 f"liked='{record['liked_book']}'")

        # DECISION
        results = self.engine.decide(record)
        self.log(f"[Decision]     TF-IDF + cosine similarity ranked books, {len(results)} matches")

        # ACTUATORS
        Actuator.display(self.tree, results)
        self.log("[Actuators]    recommendations shown in the table")
        if not results:
            messagebox.showinfo("No matches", "No books matched. Try a lower rating or another genre.")
            return

        # DATABASE
        self.database.store(record, results)
        self.log("[Database]     saved to history.csv")

        # ANALYSIS
        self.refresh_analysis()
        self.log("[Analysis]     statistics updated")

    def refresh_analysis(self):
        stats = Analysis.run(self.database.read())
        if not stats:
            self.lbl_summary.configure(text="No history yet.")
            self.draw_bars(self.canvas_books, "Most recommended books", [])
            self.draw_bars(self.canvas_genres, "Most recommended genres", [])
            return
        self.lbl_summary.configure(
            text=f"Searches: {stats['sessions']}   |   Recommendations stored: {stats['rows']}"
                 f"   |   Average match: {stats['avg_match']:.1f}%")
        self.draw_bars(self.canvas_books, "Most recommended books", stats["top_books"])
        self.draw_bars(self.canvas_genres, "Most recommended genres", stats["top_genres"])

    def on_export(self):
        stats = Analysis.run(self.database.read())
        if not stats:
            messagebox.showinfo("Nothing to export", "Make some recommendations first.")
            return
        Analysis.export(stats)
        messagebox.showinfo("Exported", f"Saved:\n{REPORT_CSV}")


if __name__ == "__main__":
    App().mainloop()
