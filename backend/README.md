# Real-Time Ride Dispatch Backend

A production-oriented backend service for real-time ride matching, trip lifecycle management, and fare computation.

Designed for **low latency, strong consistency, and horizontal scalability**.

---

## Features

- Real-time nearest-driver matching using Redis Geo
- Transaction-safe trip lifecycle management
- WebSocket-based live ride updates
- Idempotent ride creation
- PostgreSQL persistence with connection pooling
- Load-tested for concurrent traffic

---

## Architecture Overview

Core components:

- **FastAPI services** — stateless REST APIs  
- **Redis** — geo indexing & realtime messaging  
- **PostgreSQL** — transactional data storage  
- **WebSockets** — live state updates  

See `SYSTEM_DESIGN.md` for detailed architecture.

---

## API Modules

### Rides
- Create ride request
- Trigger driver matching
- Emit realtime offer events

### Trips
- Start / pause / resume / end lifecycle
- Fare computation on completion

### Drivers
- Real-time location updates via Redis Geo

---

## Performance Snapshot

Tested with:

- 50 concurrent users  
- ~30 requests/sec sustained  

Observed:

- Median latency ~13 ms  
- p95 latency ~36 ms  
- 0% failures under load  

Indicates readiness for horizontal scaling.

---

## Scalability Strategy

Supports growth through:

- Stateless API replication
- Redis in-memory geo search for 100k+ drivers
- Database read replicas and regional sharding
- Event-driven async processing for heavy workloads

---

## Local Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

Create `.env` in project root:

```
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
REDIS_URL=redis://localhost:6379
```

### 3. Run server

```bash
uvicorn app.main:app --reload
```

### 4. Load testing (optional)

```bash
locust
```

Open:

```
http://localhost:8089
```

---

## Project Structure

```
app/
 ├── api/
 ├── services/
 ├── db/
 ├── models/
 ├── websocket/
 └── core/
```

---

## Design Goals

* Deterministic trip lifecycle
* Sub-second driver matching
* Fault-tolerant request handling
* Horizontal scalability from day one

---
