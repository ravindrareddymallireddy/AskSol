# backend/server.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import pandas as pd
from difflib import SequenceMatcher
from backend.preprocessing import ensure_nltk_data
from backend.retrieval import Retriever, fuzzy_score  # uses SequenceMatcher-based fuzzy_score

app = Flask(__name__)
CORS(app)

GREETING_PATTERNS = re.compile(r"\b(hi|hello|hey|good morning|good afternoon|good evening|greetings)\b", flags=re.I)
SMALLTALK_PATTERNS = re.compile(r"\b(how are you|how's it going|how are u|what's up|whats up|how you doing)\b", flags=re.I)
CAMPUS_PATTERNS = re.compile(r"\b(campus|hostel|library|canteen|mess|clubs|societies|wifi|wi-fi|sports|safety|medical|clinic|transport|counseling|counsellor)\b", flags=re.I)

COURSE_TOKENS = ["msc", "m.sc", "bsc", "b.sc", "phd", "b.tech", "m.tech", "mba", "llb", "llm", "mca", "beng", "bcom", "bba"]

def detect_intent(text):
    if GREETING_PATTERNS.search(text):
        return "greet"
    if SMALLTALK_PATTERNS.search(text):
        return "smalltalk"
    if CAMPUS_PATTERNS.search(text):
        return "campus"
    return "unknown"

def looks_like_course_list(answer_text):
    if not answer_text or not isinstance(answer_text, str):
        return False
    lower = answer_text.lower()
    token_hits = sum(1 for t in COURSE_TOKENS if t in lower)
    comma_count = lower.count(",")
    return token_hits >= 1 and comma_count >= 3

def format_as_bullets(answer_text):
    if ":" in answer_text:
        lead, rest = answer_text.split(":", 1)
        items = [s.strip().rstrip(".") for s in re.split(r",|;|\n", rest) if s.strip()]
        if not items:
            return answer_text
        bullets = "\n".join(f"- {it}" for it in items)
        return f"{lead.strip()}:\n{bullets}"
    else:
        items = [s.strip().rstrip(".") for s in re.split(r",|;|\n", answer_text) if s.strip()]
        if len(items) <= 1:
            return answer_text
        return "\n".join(f"- {it}" for it in items)

# Helpful fuzzy matcher
def similar(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

# Load dataset (full dataframe) from CSV in backend
DATA_PATH = "college_dataset_final.csv"
df_full = pd.read_csv(DATA_PATH).fillna("")

# Prepare canonical lists the retriever will use if needed
questions = df_full["question"].astype(str).tolist()
answers = df_full["answer"].astype(str).tolist()

# NLTK setup - optional
try:
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer
    stop_words = set(stopwords.words("english"))
    lemmatizer = WordNetLemmatizer()
    ensure_nltk_data()
except Exception:
    stop_words, lemmatizer = None, None

# Build the global retriever (on entire dataset)
global_retriever = Retriever(questions, answers, use_wordnet=True, stop_words=stop_words, lemmatizer=lemmatizer)

# Build a list of unique clean course names for detection
course_names = df_full["course_name"].astype(str).unique().tolist()
# Normalize for faster checks
course_names_normal = [c.strip().lower() for c in course_names if c and c.strip() and c.strip().lower() != "n/a"]

def detect_course_in_query(query):
    """Try to find a specific course name mentioned in the user query.
       Returns the best course_name or None."""
    q = query.lower()
    # simple substring match first (exact phrase)
    best = None
    best_score = 0.0
    for cname in course_names_normal:
        if cname in q:
            # strong hit
            return cname
        # fuzzy fallback - partial similarity
        s = similar(q, cname)
        if s > best_score:
            best_score = s; best = cname
    # If fuzzy similarity is reasonably high, accept it
    if best_score >= 0.65:
        return best
    return None

@app.route("/api/ask", methods=["POST"])
def ask():
    data = request.json or {}
    q = data.get("query", "").strip()
    if not q:
        return jsonify({"error": "missing query"}), 400

    intent = detect_intent(q)
    if intent == "greet":
        return jsonify({"answer": "Hello 👋 I'm AskSol. What questions do you have about courses, admissions, fees, or campus life?", "confidence": 10})
    if intent == "smalltalk":
        return jsonify({"answer": "I'm doing great! Thanks for asking. How can I help with your college-related queries?", "confidence": 8})
    if intent == "campus":
        campus_ans = "Our campus has hostels, a central library, Wi-Fi, a canteen, clubs & societies, sports facilities, and an on-site medical clinic. Which of these would you like to know more about?"
        return jsonify({"answer": campus_ans, "confidence": 8})

    # 1) Check if the user explicitly mentioned a course name
    course_detected = detect_course_in_query(q)

    # If a course was detected, restrict to entries for that course and prefer course-level answers
    if course_detected:
        # rows where course_name contains that detected name (case-insensitive)
        mask = df_full["course_name"].astype(str).str.lower().str.contains(re.escape(course_detected))
        df_subset = df_full[mask]
        if not df_subset.empty:
            # Build a temporary retriever for this subset to find the best answer among that course's QAs
            sub_questions = df_subset["question"].astype(str).tolist()
            sub_answers = df_subset["answer"].astype(str).tolist()
            temp_retriever = Retriever(sub_questions, sub_answers, use_wordnet=True, stop_words=stop_words, lemmatizer=lemmatizer)
            accepted, results = temp_retriever.retrieve(q, top_k=3, threshold=0.0)
            top_entry = None
            if results:
                top_entry = results[0]
            # if we found a top entry in subset, use it
            if top_entry:
                score = float(top_entry.get("score", 0.0))
                confidence = int(round(max(0.0, min(1.0, score)) * 10))
                ans_text = str(top_entry.get("answer","")).strip()
                # selective bullets if it's a course-list wording
                if looks_like_course_list(ans_text):
                    ans_text = format_as_bullets(ans_text)
                return jsonify({"answer": ans_text, "confidence": confidence})

    # 2) Otherwise, fallback to global retriever behavior (top 1 only)
    accepted, results = global_retriever.retrieve(q, top_k=5, threshold=0.0)
    top_entry = None
    if results and len(results) > 0:
        top_entry = results[0]
    if not top_entry:
        fuzzy = global_retriever.fuzzy_fallback(q, top_k=1)
        if fuzzy:
            top_entry = fuzzy[0]
    if not top_entry:
        return jsonify({"answer": "Sorry, I don't have an answer. Try rephrasing.", "confidence": 0})

    score = float(top_entry.get("score", 0.0))
    confidence = int(round(max(0.0, min(1.0, score)) * 10))
    ans_text = str(top_entry.get("answer","")).strip()
    if looks_like_course_list(ans_text):
        ans_text = format_as_bullets(ans_text)

    return jsonify({"answer": ans_text, "confidence": confidence})

if __name__ == "__main__":
    print(f"Loaded dataset with {len(df_full)} rows from {DATA_PATH}")
    app.run(host="0.0.0.0", port=5000, debug=True)
