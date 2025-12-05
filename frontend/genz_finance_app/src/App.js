// ...existing code...
import React, { useState } from 'react';
import Login from './Login';
import Quiz from './Quiz';
import Goal from './Goal';
import Chat from './Chat';
import './App.css';

function TopBar({ user, onLogout, selectedTab, setSelectedTab }) {
  return (
    <header className="topbar">
      <div className="brand">
        <div className="logo">BN</div>
        <div>
          <div className="title">BankNova</div>
          <div className="tag">Smart banking • youthful vibes</div>
        </div>
      </div>

      <nav style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
        {['Home', 'Accounts', 'Payments', 'MoneyVerse', 'Support'].map((t) => (
          <button
            key={t}
            className={`btn ${selectedTab === t ? 'primary' : ''}`}
            onClick={() => setSelectedTab(t)}
            style={{ padding: '8px 12px', fontWeight: 600 }}
          >
            {t}
          </button>
        ))}
        <div style={{ width: 12 }} />
        {user ? (
          <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
            <div className="avatar-wrap" style={{ marginRight: 8 }}>
              <div className="avatar-emoji" style={{ fontSize: 20 }}>😎</div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontWeight: 700 }}>{user.name}</div>
              <div className="muted" style={{ fontSize: 12 }}>Member</div>
            </div>
            <button className="btn" onClick={onLogout} style={{ marginLeft: 12 }}>Logout</button>
          </div>
        ) : null}
      </nav>
    </header>
  );
}

function Placeholder({ title, children }) {
  return (
    <div className="card">
      <h3>{title}</h3>
      <div style={{ marginTop: 12 }}>{children}</div>
    </div>
  );
}

export default function App() {
  const [user, setUser] = useState(null);
  const [persona, setPersona] = useState("");
  const [goal, setGoal] = useState(null);
  const [selectedTab, setSelectedTab] = useState('Home');

  function handleLogout() {
    setUser(null);
    setPersona("");
    setGoal(null);
    setSelectedTab('Home');
  }

  return (
    <div className="app">
      <TopBar
        user={user}
        onLogout={handleLogout}
        selectedTab={selectedTab}
        setSelectedTab={setSelectedTab}
      />

      <main className="main">
        {selectedTab !== 'MoneyVerse' ? (
          <div className="split">
            <div className="left">
              <Placeholder title="Welcome to BankNova">
                <p className="muted">A modern demo banking portal. Use the MoneyVerse tab to try the Gen-AI savings journey.</p>
                <div style={{ display: 'flex', gap: 12, marginTop: 12 }}>
                  <button className="btn primary" onClick={() => setSelectedTab('MoneyVerse')}>Open MoneyVerse</button>
                  <button className="btn" onClick={() => alert('Accounts demo')}>View Accounts</button>
                </div>
              </Placeholder>

              <Placeholder title="Quick Actions">
                <div style={{ display: 'flex', gap: 8 }}>
                  <button className="btn">Transfer</button>
                  <button className="btn">Pay Bills</button>
                  <button className="btn">Cards</button>
                </div>
              </Placeholder>
            </div>

            <aside className="right">
              <Placeholder title="News & Tips">
                <ul style={{ paddingLeft: 18 }}>
                  <li>Tip: Save small, save often.</li>
                  <li>Offer: 0% fee on P2P for demo users.</li>
                </ul>
              </Placeholder>

              <Placeholder title="Support">
                <p className="muted">Chat with support or Milo on the MoneyVerse tab.</p>
              </Placeholder>
            </aside>
          </div>
        ) : (
          // MoneyVerse area: preserve your existing onboarding -> quiz -> goal -> chat flow
          <>
            {!user ? (
              <div className="centered"><Login setUser={setUser} /></div>
            ) : !persona ? (
              <div className="centered"><Quiz user={user} setPersona={setPersona} /></div>
            ) : !goal ? (
              <div className="centered"><Goal user={user} setGoal={setGoal} /></div>
            ) : (
              <div className="split">
                <div className="left">
                  <div className="card userbox">
                    <div>
                      <h2>Hello, {user.name}</h2>
                      <div className="muted">Persona: <strong>{persona}</strong></div>
                    </div>
                    <div>
                      <button className="btn" onClick={() => { setUser(null); setPersona(""); setGoal(null); }}>Sign out</button>
                    </div>
                  </div>

                  {/* Goal summary */}
                  <div className="card goal-card">
                    <h4>Active Goal</h4>
                    <div style={{ marginTop: 8 }}>
                      <div><strong>{goal?.name || 'Save Goal'}</strong></div>
                      <div className="muted">Target: ₹{goal?.targetAmount} • {goal?.durationDays} days</div>
                      <div className="progress" style={{ marginTop: 12 }}>
                        <i style={{ width: `${Math.min(100, Math.round(((goal?.savedSoFar||0)/Math.max(1, goal?.targetAmount||1))*100))}%` }} />
                      </div>
                    </div>
                  </div>

                  <div className="card">
                    <h3>Social Challenge</h3>
                    <p className="muted">Share invite link to challenge friends on this goal.</p>
                    <code>invite://demo/{user.id}</code>
                  </div>
                </div>

                <aside className="right">
                  <Chat user={user} />
                </aside>
              </div>
            )}
          </>
        )}
      </main>

      <footer className="footer">BankNova • MoneyVerse demo — for hackathon use only</footer>
    </div>
  );
}
// ...existing code...