import React, { useState } from "react";
import { createGoal } from "./api";

export default function Goal({ user, setGoal }) {
  const [name, setName] = useState("Save 5k");
  const [amount, setAmount] = useState(5000);
  const [days, setDays] = useState(10);
  const [loading, setLoading] = useState(false);

  async function handleCreate(e) {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await createGoal({
        userId: user.id,
        name,
        targetAmount: Number(amount),
        durationDays: Number(days),
      });
      setGoal(res.goal);
      // optionally show plan or buddy_msg
      alert(res.buddy_msg || "Goal created");
    } catch (err) {
      console.error(err);
      alert("Create goal failed: " + err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card onboarding">
      <h2>Create a Goal</h2>
      <form onSubmit={handleCreate}>
        <label>Goal name</label>
        <input className="input" value={name} onChange={(e) => setName(e.target.value)} />
        <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
          <div style={{ flex: 1 }}>
            <label>Target amount</label>
            <input className="input" type="number" value={amount} onChange={(e) => setAmount(e.target.value)} />
          </div>
          <div style={{ width: 140 }}>
            <label>Days</label>
            <input className="input" type="number" value={days} onChange={(e) => setDays(e.target.value)} />
          </div>
        </div>
        <div style={{ marginTop: 12 }}>
          <button className="btn primary" type="submit" disabled={loading}>
            {loading ? "Creating…" : "Create Goal"}
          </button>
        </div>
      </form>
    </div>
  );
}