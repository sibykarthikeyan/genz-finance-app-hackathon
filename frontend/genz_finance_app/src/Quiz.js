import React, { useState } from "react";
import { runOnboarding } from "./api";

const QUESTIONS = [
  { key: "plan", q: "Do you plan purchases ahead?", opts: ["Always", "Sometimes", "Never"] },
  { key: "pick", q: "Pick one:", opts: ["Investments", "Experiences", "Shopping"] },
  { key: "extra", q: "When you get ₹1000 extra, you:", opts: ["Save", "Split", "Spend"] },
  { key: "budget", q: "Do you use budgets?", opts: ["Yes", "No"] }
];

export default function Quiz({ user, setPersona }) {
  const [answers, setAnswers] = useState(Array(QUESTIONS.length).fill(""));
  const [loading, setLoading] = useState(false);

  function pick(i, v) {
    const copy = [...answers];
    copy[i] = v;
    setAnswers(copy);
  }

  async function handleSubmit(e) {
    e?.preventDefault();
    if (answers.some((a) => !a)) return alert("Please answer all questions");
    setLoading(true);
    try {
      const res = await runOnboarding(user.id, answers);
      if (res && res.persona) {
        setPersona(res.persona);
      } else {
        // fallback mapping if backend not available
        setPersona("Balanced Builder");
      }
    } catch (err) {
      console.error(err);
      setPersona("Balanced Builder");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card onboarding">
      <h2>Quick Spend Personality Quiz</h2>
      <p className="muted">4 quick Qs — helps Milo give better tips</p>
      <form onSubmit={handleSubmit}>
        {QUESTIONS.map((qq, i) => (
          <div key={qq.key} className="question" style={{ marginTop: 12 }}>
            <div className="qtext">{qq.q}</div>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap", width: "55%" }}>
              {qq.opts.map((opt) => (
                <button
                  key={opt}
                  type="button"
                  className={`option ${answers[i] === opt ? "selected" : ""}`}
                  onClick={() => pick(i, opt)}
                >
                  {opt}
                </button>
              ))}
            </div>
          </div>
        ))}
        <div className="actions" style={{ marginTop: 16 }}>
          <button className="btn primary" type="submit" disabled={loading}>
            {loading ? "Saving..." : "Finish"}
          </button>
        </div>
      </form>
    </div>
  );
}