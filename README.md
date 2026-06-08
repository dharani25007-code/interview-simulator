<div align="center">
<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0f1117,50:6366f1,100:0f1117&height=200&section=header&text=Interview%20Simulator&fontSize=52&fontColor=ffffff&fontAlignY=40&desc=AI-Powered%20Interview%20Practice%20%7C%20Adaptive%20%7C%20Full-Stack&descAlignY=60&descSize=17&animation=fadeIn"/>
</div>

<div align="center">

![React](https://img.shields.io/badge/React_18-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-llama--3.3--70b-FF6B00?style=for-the-badge)
![JWT](https://img.shields.io/badge/JWT-Auth-d63aff?style=for-the-badge&logo=jsonwebtokens&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-6366f1?style=for-the-badge)

> 🎯 Full-stack AI interview practice app — adaptive questions, per-answer scoring, and a final report with learning tips.

</div>

---

## ✨ Features

- 🔐 **JWT Authentication** — secure register/login with token-based sessions
- 🎯 **Adaptive Interview Flow** — questions adjust based on your answers
- 📊 **Per-Answer Scoring** — instant AI feedback after every response
- 📋 **Final Report** — complete interview summary with learning tips
- 📈 **Dashboard** — track your progress and history with Recharts
- ✨ **Smooth UI** — Framer Motion animations throughout

---

## 🗂️ Project Structure

```
interview-simulator/
├── backend/
│   ├── app.py              # All Flask routes
│   ├── ai_engine.py        # Groq API — question gen, evaluation
│   ├── analytics.py        # Score computation & stats
│   ├── database.py         # SQLAlchemy models
│   ├── requirements.txt
│   └── instance/           # SQLite DB auto-created here
├── frontend/
│   ├── public/
│   └── src/                # React pages and components
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- Python **3.9+**
- Node.js **18+** + npm
- Free [Groq API key](https://console.groq.com)

---

### 1. Backend Setup

```bash
cd backend
python -m venv .venv

# Windows
.\.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

Create `backend/.env`:

```env
GROQ_API_KEY=your_groq_api_key_here
JWT_SECRET_KEY=your_long_random_secret_here
```

Start backend:

```bash
python app.py
# Runs at http://127.0.0.1:5000
```

---

### 2. Frontend Setup

Open a **new terminal**:

```bash
cd frontend
npm install
npm start
# Runs at http://localhost:3000
```

> The `proxy` field in `package.json` routes all `/api/*` calls to `http://localhost:5000` automatically.

---

## 🔌 API Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register` | ✗ | Register new user |
| POST | `/api/auth/login` | ✗ | Login, returns JWT |
| GET | `/api/auth/me` | ✓ | Get current user |
| GET | `/api/dashboard` | ✓ | Stats and history |
| POST | `/api/interviews/start` | ✓ | Start new session |
| POST | `/api/interviews/<id>/answer` | ✓ | Submit answer + get feedback |
| POST | `/api/interviews/<id>/end` | ✓ | End session early |
| GET | `/api/interviews/<id>/report` | ✓ | Get full report |

---

## 🧰 Tech Stack

| Layer | Tech |
|---|---|
| Frontend | React 18 · React Router · Recharts · Framer Motion |
| Backend | Flask · Flask-JWT-Extended · Flask-SQLAlchemy · Flask-CORS |
| Database | SQLite (auto-created on first run) |
| AI | Groq — `llama-3.3-70b-versatile` |

---

## ⚙️ Notes

- SQLite DB is created automatically at first backend run inside `backend/instance/`
- CORS is configured for `http://localhost:3000`
- Swap `GROQ_MODEL` in `ai_engine.py` to `llama-3.1-8b-instant` for faster responses

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

<div align="center">
<img src="https://capsule-render.vercel.app/api?type=waving&color=0:6366f1,100:0f1117&height=120&section=footer"/>

**Built by [Dharanidharan M](https://github.com/dharani25007-code) **
</div>