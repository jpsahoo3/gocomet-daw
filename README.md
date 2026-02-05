# Real-Time Ride Dispatch System

A full-stack real-time ride dispatch platform designed for:

- Low-latency driver matching
- Strong transactional trip lifecycle
- Horizontal scalability
- Real-time UI updates

The system demonstrates production-style architecture using:

- **FastAPI + PostgreSQL + Redis** (backend)
- **React + Vite + WebSockets** (frontend)


---

## Core Capabilities

- Real-time nearest-driver discovery via Redis Geo
- Deterministic ride → trip → payment lifecycle
- Idempotent ride creation & transactional safety
- WebSocket-based live ride updates
- Load-tested concurrent request handling

See **SYSTEM_DESIGN.md** for architecture and scalability details.

---

## Quick Start (Full Stack)

### 1. Start Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

#### Backend runs on:
```bash
http://localhost:8000
```

### 2. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

#### Frontend runs on:
```bash
http://localhost:5173
```


