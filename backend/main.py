from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from bson import ObjectId
import google as genai

import requests
import os
import uuid
import math
app = FastAPI()
# Allow React dev server and localhost — adjust or tighten for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        # "http://your-dev-host:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
#uri = 'mongodb+srv://' + username + ':' + password + '@' + cluster + '/?appName=' + appName

uri = "<get_from_siby>"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

db = client["moneyverse"]

# Gemini / Generative Language configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "<get_from_siby>")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "models/text-bison-001")

#client = genai.Client()

def call_llm(system_prompt, user_prompt):
    """
    Try Gemini via google.genai client (preferred) -> local LLM -> deterministic fallback.
    Always returns a string and never raises.
    """
    prompt_text = f"{system_prompt}\n\n{user_prompt}"
    print("[call_llm] Prompt:", prompt_text)
    # 1) Gemini via genai client
    if GEMINI_API_KEY:
        try:
            client = genai.Client(api_key=GEMINI_API_KEY)

            resp = client.models.generate_content(
                model="gemini-2.0-flash", contents=prompt_text
            )
            print(resp.text)
            
            # genai response often exposes .text
            if hasattr(resp, "text") and resp.text:
                print("[call_llm] Gemini text:", resp.text)
                return resp.text
            # try to coerce to dict-like
            try:
                rdict = resp.to_dict() if hasattr(resp, "to_dict") else (resp if isinstance(resp, dict) else None)
            except Exception:
                rdict = None
            if rdict:
                if "candidates" in rdict and rdict["candidates"]:
                    return rdict["candidates"][0].get("content", "")
                if "output" in rdict and isinstance(rdict["output"], dict):
                    return rdict["output"].get("text") or rdict["output"].get("content") or str(rdict["output"])
            # last-resort stringification
            return str(resp)
        except Exception as e:
            print("[call_llm] Gemini call failed:", e)

    

### ========== MODELS ==========
class UserCreate(BaseModel):
    name: str
    email: str | None = None

class QuizInput(BaseModel):
    answers: list

class GoalInput(BaseModel):
    userId: str
    name: str | None = "Save Goal"
    targetAmount: int
    durationDays: int

class ChatMessage(BaseModel):
    userId: str
    text: str

class InviteInput(BaseModel):
    hostId: str
    goalId: str
    friendId: str | None = None
    friendName: str | None = None

class DepositInput(BaseModel):
    userId: str
    goalId: str
    amount: int

### ========== PROMPTS / AGENT TEMPLATES ==========
BUDDY_SYSTEM = """You are Milo, a friendly Gen-AI financial buddy for young people.
Write short, upbeat, empathetic replies (<= 2 sentences). Use informal tone and emojis sparingly.
Provide one actionable micro-step and one micro-learning (1 line). Ask a low-friction follow-up question.
If user requests risky financial advice (invest, loans, high leverage), use safety fallback."""

ONBOARDING_SYSTEM = """You are an assessment engine. Ask 4 quick multiple-choice questions about spending habits.
Score answers and return one label among {Saver Shark, Vibe Spender, Balanced Builder, Explorer}.
Return JSON: { "persona": "...", "reason": "...", "tip": "..." }"""

GOAL_SYSTEM = """You are GoalPlanner. Input: targetAmount, durationDays.
Output JSON: { "daily": [int,...], "motivation": "...", "mid_reward": "..." }"""

CHALLENGE_SYSTEM = """You're a friendly challenge host that writes short invite messages.
Input: hostName, goalName, targetAmount, durationDays.
Output JSON: {"playful":"...", "competitive":"..."}"""

SAFETY_KEYWORDS = ["invest", "stocks", "crypto", "loan", "borrow", "mortgage", "interest rate", "leverage"]

def sanitize_value(v):
    if isinstance(v, ObjectId):
        return str(v)
    if isinstance(v, datetime):
        return v.isoformat()
    if isinstance(v, list):
        return [sanitize_value(x) for x in v]
    if isinstance(v, dict):
        return sanitize_doc(v)
    return v

def sanitize_doc(doc):
    # handle None / non-dict / ObjectId safely
    if doc is None:
        return None
    if isinstance(doc, ObjectId):
        return str(doc)
    if not isinstance(doc, dict):
        return sanitize_value(doc)

    out = {}
    for k, v in doc.items():
        if k == "_id":
            continue
        out[k] = sanitize_value(v)
    return out

def sanitize_list(docs):
    if not docs:
        return []
    return [sanitize_doc(d) for d in docs]

### ========== PERSISTENCE HELPERS (Persistence Agent) ==========
def create_user(name, email=None):
    user = {
        "id": str(uuid.uuid4()),
        "name": name,
        "email": email,
        "persona_label": None,
        "avatar_state": "starter",
        "points": 0,
        "friends": [],
        "createdAt": datetime.utcnow()
    }
    db.users.insert_one(user)
    return sanitize_doc(user)

def get_user(user_id):
    doc = db.users.find_one({"id": user_id}, {"_id":0}) 
    return sanitize_doc(doc)

def upsert_user_persona(user_id, persona, reason, tip):
    db.users.update_one({"id": user_id}, {"$set": {"persona_label": persona, "persona_reason": reason, "persona_tip": tip}})
    # return updated user for convenience
    return get_user(user_id)

def persist_goal(goal):
    db.goals.insert_one(goal)
    return sanitize_doc(goal)

def get_goal(goal_id):
    doc = db.goals.find_one({"id": goal_id})
    return sanitize_doc(doc)

def update_goal_progress(goal_id, amount):
    g = db.goals.find_one({"id": goal_id})
    if not g: return None
    saved = g.get("savedSoFar", 0) + amount
    status = "active"
    if saved >= g["targetAmount"]:
        status = "completed"
    db.goals.update_one({"id": goal_id}, {"$set": {"savedSoFar": saved, "status": status}})
    updated = db.goals.find_one({"id": goal_id})
    return sanitize_doc(updated)

def record_event(userId, type_, amount=0):
    ev = {"userId": userId, "type": type_, "amount": amount, "timestamp": datetime.utcnow()}
    db.events.insert_one(ev)
    return sanitize_doc(ev)

def add_convo(userId, message):
    db.convos.update_one({"userId": userId}, {"$push": {"messages": {"text": message, "time": datetime.utcnow()}}}, upsert=True)
    c = db.convos.find_one({"userId": userId})
    return sanitize_doc(c)

### ========== AGENTS ==========
def onboarding_agent_local(answers:list):
    # simple scoring: map choices to numeric scores and classify
    # answers assumed: [plan, pick, extra, budget]
    score = 0
    mapping = {
        "Always": 2, "Sometimes":1, "Never":0,
        "Investments":2, "Experiences":1, "Shopping":0,
        "Save":2, "Split":1, "Spend":0,
        "Yes":2, "No":0
    }
    for a in answers:
        score += mapping.get(a, 1)
    # map to persona
    if score >= 7:
        persona = "Saver Shark"
        tip = "Auto-save small amounts daily to keep momentum."
    elif score >=5:
        persona = "Balanced Builder"
        tip = "Keep a split: save, spend, invest a small %."
    elif score >=3:
        persona = "Explorer"
        tip = "Try short-term goals to build saving habit."
    else:
        persona = "Vibe Spender"
        tip = "Set a tiny daily save (₹50) to start."
    reason = f"score={score}"
    return {"persona": persona, "reason": reason, "tip": tip}

def safety_check(text):
    t = text.lower()
    for kw in SAFETY_KEYWORDS:
        if kw in t:
            return False, kw
    return True, None

def buddy_agent(userId, user_text):
    ok, kw = safety_check(user_text)
    if not ok:
        msg = "I’m not licensed to give investment advice — here's a general explainer. Consult a certified advisor."
        print(f"[buddy_agent] SAFETY BLOCK for user={userId}, kw={kw}")
        add_convo(userId, msg)
        return msg, True

    print(f"[buddy_agent] calling LLM for user={userId} text={user_text!r}")
    system = BUDDY_SYSTEM
    prompt = user_text
    resp = call_llm(system, prompt)
    print(f"[buddy_agent] LLM resp (raw): {resp!r}")
    if not resp or str(resp).strip() == "" or resp.startswith("[LLM error]"):
        # friendly deterministic fallback so UI always shows something
        fallback = "Hey — Milo here. Quick tip: automate a small daily transfer. Want a 7-day plan?"
        print(f"[buddy_agent] using fallback reply for user={userId}")
        add_convo(userId, fallback)
        return fallback, False

    # store convo
    add_convo(userId, resp)
    return resp, False

def goal_agent_plan(targetAmount:int, durationDays:int):
    # simple equal split with small rounding
    base = targetAmount // durationDays
    daily = [base]*durationDays
    remainder = targetAmount - base*durationDays
    for i in range(remainder):
        daily[i] += 1
    motivation = f"You got this! Save ₹{base} - keep streaks to earn style badges."
    reward = "Badge: Halfway Hero" if durationDays >=5 else "Badge: Quick Saver"
    return {"daily": daily, "motivation": motivation, "mid_reward": reward}

def challenge_agent_invite(hostName, goalName, targetAmount, durationDays):
    system = CHALLENGE_SYSTEM
    prompt = f"{hostName}|{goalName}|{targetAmount}|{durationDays}"
    # we can mock two variants locally without LLM for predictability
    playful = f"Yo! I'm saving ₹{targetAmount} in {durationDays} days — join my squad? 🧠💪"
    competitive = f"Save ₹{targetAmount} in {durationDays} days. Think you can beat my streak? Leaderboard on!"
    return {"playful":playful, "competitive":competitive}

### ========== ORCHESTRATOR ==========
def orchestrator_on_goal_create(user, goal):
    # create plan via Goal Agent
    plan = goal_agent_plan(goal["targetAmount"], goal["durationDays"])
    # persist and get sanitized goal
    persisted_goal = persist_goal(goal)
    # initial buddy message
    buddy_msg = f"Plan made: ₹{plan['daily'][0]} per day. {plan['motivation']}"
    add_convo(user["id"], buddy_msg)
    return {"plan": plan, "buddy_msg": buddy_msg, "goal": persisted_goal}

def orchestrator_on_deposit(user, goal, amount):
    # update goal progress
    updated = update_goal_progress(goal["id"], amount)
    record_event(user["id"], "deposit", amount)
    # compute percent and avatar
    pct = min(100, int(100 * (updated.get("savedSoFar",0) / updated["targetAmount"])))
    avatar = "starter"
    if pct >= 66:
        avatar = "level-up"
    elif pct >= 33:
        avatar = "growing"
    db.users.update_one({"id": user["id"]}, {"$set": {"avatar_state": avatar}})
    # points
    pts = int(amount/10)
    db.users.update_one({"id": user["id"]}, {"$inc": {"points": pts}})
    # create buddy celebratory message
    buddy = f"Nice! ₹{amount} added. Progress: {pct}% — { 'You hit a milestone!' if pct>=66 else 'Keep going!' }"
    add_convo(user["id"], buddy)
    return {"updated": updated, "avatar": avatar, "points_awarded": pts, "buddy_msg": buddy}

### ========== ENDPOINTS (API surface) ==========
@app.post("/user/create")
def api_create_user(data: UserCreate):
    user = create_user(data.name, data.email)
    return {"user": user}

@app.get("/user")
def api_get_user(user_id: str):
    u = get_user(user_id)
    if not u: raise HTTPException(status_code=404, detail="user not found")
    return u

@app.post("/onboarding")
def api_onboarding(data: QuizInput, userId: str | None = None):
    # compute persona locally and persist
    res = onboarding_agent_local(data.answers)
    if userId:
        upsert_user_persona(userId, res["persona"], res["reason"], res["tip"])
        return {"persona": res["persona"], "reason": res["reason"], "tip": res["tip"]}
    return res

@app.post("/goal/create")
def api_create_goal(data: GoalInput):
    user = get_user(data.userId)
    if not user: raise HTTPException(status_code=404, detail="user not found")
    goal = {
        "id": str(uuid.uuid4()),
        "userId": data.userId,
        "name": data.name or "Save Goal",
        "targetAmount": data.targetAmount,
        "durationDays": data.durationDays,
        "startDate": datetime.utcnow(),
        "dailyTarget": math.ceil(data.targetAmount / data.durationDays),
        "savedSoFar": 0,
        "status": "active"
    }
    orchestrator_res = orchestrator_on_goal_create(user, goal)
    # orchestrator now returns sanitized goal
    return {"goal": orchestrator_res["goal"], "plan": orchestrator_res["plan"], "buddy_msg": orchestrator_res["buddy_msg"]}

@app.post("/deposit")
def api_deposit(data: DepositInput):
    user = get_user(data.userId)
    if not user: raise HTTPException(status_code=404, detail="user not found")
    goal = get_goal(data.goalId)
    if not goal: raise HTTPException(status_code=404, detail="goal not found")
    res = orchestrator_on_deposit(user, goal, data.amount)
    return res

@app.post("/chat")
def api_chat(data: ChatMessage):
    print(f"[api_chat] incoming: userId={data.userId} text={data.text!r}")
    user = get_user(data.userId)
    if not user:
        print("[api_chat] user not found")
        raise HTTPException(status_code=404, detail="user not found")
    ok, kw = safety_check(data.text)
    if not ok:
        msg = "I’m not licensed to give investment advice — here's an explainer and safe next steps."
        add_convo(data.userId, msg)
        print(f"[api_chat] safety fallback returned for user={data.userId}")
        return {"reply": msg}
    resp, flagged = buddy_agent(data.userId, data.text)
    print(f"[api_chat] reply to user={data.userId}: {resp!r}, flagged={flagged}")
    return {"reply": resp, "flagged": flagged}

@app.post("/invite")
def api_invite(data: InviteInput):
    host = get_user(data.hostId)
    if not host: raise HTTPException(status_code=404, detail="host not found")
    goal = get_goal(data.goalId)
    if not goal: raise HTTPException(status_code=404, detail="goal not found")
    challenge = {
        "id": str(uuid.uuid4()),
        "hostId": data.hostId,
        "participants": [data.hostId],
        "goalId": data.goalId,
        "createdAt": datetime.utcnow()
    }
    db.challenges.insert_one(challenge)
    # fetch back and sanitize to avoid ObjectId leaking
    ch_doc = db.challenges.find_one({"id": challenge["id"]})
    ch_sanitized = sanitize_doc(ch_doc)
    copies = challenge_agent_invite(host["name"], goal["name"], goal["targetAmount"], goal["durationDays"])
    return {"challenge": ch_sanitized, "invites": copies, "link": f"invite://{challenge['id']}"}

@app.post("/challenge/accept")
def api_challenge_accept(challengeId: str, userId: str):
    ch = sanitize_doc(db.challenges.find_one({"id": challengeId}))
    if not ch: raise HTTPException(status_code=404, detail="challenge not found")
    if userId not in ch.get("participants", []):
        db.challenges.update_one({"id": challengeId}, {"$push": {"participants": userId}})
        ch = sanitize_doc(db.challenges.find_one({"id": challengeId}))

    participants = ch.get("participants", [])
    board = []
    for pid in participants:
        g_doc = db.goals.find_one({"userId": pid, "id": ch["goalId"]})
        g = sanitize_doc(g_doc) if g_doc else None
        pct = 0
        if g:
            pct = int(100 * (g.get("savedSoFar",0) / g["targetAmount"]))
        board.append({"userId": pid, "progress": pct})
    return {"leaderboard": sorted(board, key=lambda x: -x["progress"])}

@app.get("/leaderboard")
def api_leaderboard(challengeId: str):
    ch = sanitize_doc(db.challenges.find_one({"id": challengeId}))
    if not ch: raise HTTPException(status_code=404, detail="challenge not found")
    participants = ch.get("participants", [])
    board = []
    for pid in participants:
        g_doc = db.goals.find_one({"userId": pid, "id": ch["goalId"]})
        g = sanitize_doc(g_doc) if g_doc else None
        pct = 0
        if g:
            pct = int(100 * (g.get("savedSoFar",0) / g["targetAmount"]))
        user = get_user(pid) or {"name": "anon"}
        board.append({"userId": pid, "name": user.get("name"), "progress": pct})
    return {"leaderboard": sorted(board, key=lambda x: -x["progress"])}

@app.get("/stats")
def api_stats(userId: str):
    user = get_user(userId)
    if not user: raise HTTPException(status_code=404, detail="user not found")
    goals_cursor = db.goals.find({"userId": userId})
    goals = sanitize_list(list(goals_cursor))
    convos_doc = db.convos.find_one({"userId": userId}) or {"messages": []}
    convos = sanitize_doc(convos_doc)
    events_cursor = db.events.find({"userId": userId})
    events = sanitize_list(list(events_cursor))
    return {"user": user, "goals": goals, "convos": convos, "events": events}
