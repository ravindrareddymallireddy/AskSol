// frontend/src/App.jsx
import React, { useState, useEffect, useRef } from "react";
export default function App() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState([
    { who: "bot", text: "Hello — ask me anything about courses, admissions or campus life!", confidence: 10 },
  ]);
  const messagesRef = useRef(null);

  useEffect(() => {
    const el = messagesRef.current;
    if (!el) return;
    setTimeout(() => {
      el.scrollTop = el.scrollHeight;
    }, 60);
  }, [messages]);

  async function sendQuery(q) {
    if (!q || q.trim() === "") return;
    const userMsg = { who: "user", text: q };
    setMessages((m) => [...m, userMsg]);
    setQuery("");
    setLoading(true);
    try {
      const res = await fetch("http://localhost:5000/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: q }),
      });
      if (!res.ok) throw new Error(`Server returned ${res.status}`);
      const data = await res.json();
      // server returns { answer: "...", confidence: N }
      const botText = data.answer || "Sorry, no answer.";
      const confidence = typeof data.confidence === "number" ? data.confidence : null;
      const botMsg = { who: "bot", text: botText, confidence: confidence };
      setMessages((m) => [...m, botMsg]);
    } catch (err) {
      const errMsg = { who: "bot", text: "Error: " + err.message, confidence: 0 };
      setMessages((m) => [...m, errMsg]);
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(e) { e.preventDefault(); sendQuery(query); }

  return (
    <div className="page">
      <div className="card">
        <header className="card-header">
          <h1>CollegeBot</h1>
          <h2>Ask about courses, admissions, fees and campus life</h2>
        </header>

        <main className="chat-area">
          <div className="messages" ref={messagesRef}>
            {messages.map((m, idx) => (
              <div key={idx} className={`message-row ${m.who === "bot" ? "bot" : "user"}`}>
                <div className="avatar">{m.who === "bot" ? "B" : "U"}</div>
                <div className="bubble">
                  {/* preserve newlines and bullets */}
                  <div style={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}>{m.text}</div>
                  {m.confidence !== undefined && m.confidence !== null && (
                    <div style={{ marginTop: "8px", fontSize: "0.85rem", color: "#475569" }}>
                      <strong>Confidence:</strong> {m.confidence}/10
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          <form className="input-area" onSubmit={handleSubmit}>
            <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Type your question..." aria-label="Type your question" />
            <button type="submit" disabled={loading}>{loading ? "Thinking..." : "Send"}</button>
          </form>
        </main>
      </div>
    </div>
  );
}
