# AskSol

Got it 👍 — let’s keep it **very simple** so you can run the chatbot without worrying about virtual environments.
Here’s a clean `README.md` you can use:

---

# College Chatbot — README

This is a simple chatbot that answers student queries about courses, admissions, fees, and campus life.
It uses a CSV dataset, Python (Flask + scikit-learn + NLTK), and an optional React frontend.

---

## 🖥️ Requirements

* Python 3.8 or later installed.
* pip (comes with Python).
* (Optional) Node.js + npm if you want to run the React frontend.

---

## ⚙️ Setup

1. Install Python dependencies (directly, no virtualenv needed):

```bash
pip install -r requirements.txt
```

2. Download NLTK data (only once):

```bash
python - <<PY
import nltk
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
PY
```

---

## 🚀 Run the Backend (Flask API)

```bash
python server.py
```

The server will start at:
👉 [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 💻 Run the Chatbot in CLI (optional)

If you want to test from the terminal:

```bash
python chatbot_enhanced.py --data data/college_dataset_final.csv
```

---

## 🌐 Run the Frontend (optional)

If you want a web UI:

```bash
cd frontend
npm install
npm run dev
```

Then open the URL shown (usually [http://localhost:5173](http://localhost:5173)).

---

## 🧪 Example API Test

```bash
curl -X POST http://127.0.0.1:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query":"What is the fee for MSc AI?"}'
```

Expected response:

```json
{
  "answer": "The fee for MSc Applied AI and Data Science is GBP 17,000 per year.",
  "confidence": 9
}
```

---

That’s it ✅ — no virtualenv, no extra steps.

👉 Do you want me to also make a **one-click batch file (run.bat for Windows)** or **shell script (run.sh for Linux/macOS)** so you don’t even have to type commands?
