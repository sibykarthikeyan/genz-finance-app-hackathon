import React, { useState } from "react";
import { chat as apiChat } from "./api";

export default function Chat({ user }) {
  const [messages, setMessages] = useState([{ from: "bot", text: "Hey! I'm Milo — your money buddy." }]);
  const [text, setText] = useState("");
  const [sending, setSending] = useState(false);

  function addMessage(m) {
    setMessages((s) => [...s, m]);
  }

  async function handleSend(e) {
    e?.preventDefault();
    if (!text?.trim()) return;
    const msg = text.trim();
    addMessage({ from: "you", text: msg });
    setText("");
    setSending(true);
    try {
      const res = await apiChat(user.id, msg);
      addMessage({ from: "bot", text: res.reply || "No reply" });
    } catch (err) {
      console.error(err);
      addMessage({ from: "bot", text: "Network error: " + err.message });
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="card chat">
      <h3>Buddy Chat</h3>
      <div className="chat-window">
        {messages.map((m, i) => (
          <div key={i} className={`chat-msg ${m.from}`}>
            <div className="bubble">{m.text}</div>
          </div>
        ))}
      </div>
      <form className="chat-input" onSubmit={handleSend}>
        <input className="input" value={text} onChange={(e) => setText(e.target.value)} placeholder="Ask Milo..." />
        <button className="btn primary" type="submit" disabled={sending}>
          {sending ? "..." : "Send"}
        </button>
      </form>
    </div>
  );
}