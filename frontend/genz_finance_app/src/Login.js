import React, { useState } from "react";
import { createUser } from "./api";

export default function Login({ setUser }) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSignup(e) {
    e?.preventDefault();
    if (!name.trim()) return alert("Please enter a name");
    setLoading(true);
    try {
      const res = await createUser({ name: name.trim(), email: email.trim() || undefined });
      // backend returns { user: {...} }
      if (res && res.user) {
        setUser(res.user);
      } else {
        // fallback local user
        setUser({ id: "local_" + Date.now(), name: name.trim(), email: email.trim() });
      }
    } catch (err) {
      console.error(err);
      // fallback: still set local user so dev demo can continue
      setUser({ id: "local_" + Date.now(), name: name.trim(), email: email.trim() });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card onboarding">
      <h2>Welcome to MoneyVerse</h2>
      <p className="muted">Create a quick profile to get your AI buddy.</p>
      <form onSubmit={handleSignup}>
        <input className="input" placeholder="Your name" value={name} onChange={(e) => setName(e.target.value)} />
        <input className="input" placeholder="Email (optional)" value={email} onChange={(e) => setEmail(e.target.value)} />
        <div className="actions" style={{ marginTop: 12 }}>
          <button className="btn primary" type="submit" disabled={loading}>
            {loading ? "Creating..." : "Get started"}
          </button>
        </div>
      </form>
    </div>
  );
}