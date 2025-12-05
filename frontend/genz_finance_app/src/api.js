const API_BASE = process.env.REACT_APP_API_BASE || "http://localhost:8000";

async function request(path, { method = "GET", body, signal } = {}) {
  const opts = { method, headers: {}, signal };
  if (body !== undefined) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(`${API_BASE}${path}`, opts);
  if (!res.ok) {
    const txt = await res.text().catch(()=>"");
    throw new Error(`${res.status} ${res.statusText} - ${txt}`);
  }
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) return res.json();
  return null;
}

export async function createUser({ name, email }) {
  return request("/user/create", { method: "POST", body: { name, email } });
}

export async function getUser(userId) {
  return request(`/user?user_id=${encodeURIComponent(userId)}`);
}

export async function runOnboarding(userId, answers) {
  return request(`/onboarding?userId=${encodeURIComponent(userId)}`, {
    method: "POST",
    body: { answers },
  });
}

export async function createGoal({ userId, name, targetAmount, durationDays }) {
  return request("/goal/create", {
    method: "POST",
    body: { userId, name, targetAmount, durationDays },
  });
}

export async function deposit({ userId, goalId, amount }) {
  return request("/deposit", {
    method: "POST",
    body: { userId, goalId, amount },
  });
}

export async function invite({ hostId, goalId, friendId, friendName }) {
  return request("/invite", {
    method: "POST",
    body: { hostId, goalId, friendId, friendName },
  });
}

export async function acceptChallenge(challengeId, userId) {
  return request(`/challenge/accept?challengeId=${encodeURIComponent(challengeId)}&userId=${encodeURIComponent(userId)}`, {
    method: "POST",
  });
}

export async function getLeaderboard(challengeId) {
  return request(`/leaderboard?challengeId=${encodeURIComponent(challengeId)}`);
}
// Ensure chat is exported (this was missing)
export async function chat(userId, text) {
  return request("/chat", { method: "POST", body: { userId, text } });
}

export async function getStats(userId) {
  return request(`/stats?userId=${encodeURIComponent(userId)}`);
}