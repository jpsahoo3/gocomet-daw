# Ride Dispatch Backend — System Design

## 1. High-Level Architecture

This system is a real-time ride dispatch backend built for:

- Low latency driver matching
- High concurrency trip handling
- Transactional lifecycle guarantees
- Horizontal scalability

### Core Flow

1. Rider creates a ride request  
2. Ride stored in PostgreSQL  
3. Nearby drivers resolved using Redis Geo index  
4. Driver accepts → trip lifecycle begins  
5. Trip completion → fare calculation → payment record  
6. Real-time updates pushed via WebSockets  

---

## 2. Core Components

### API Layer
- FastAPI stateless services
- Handles rides, trips, drivers, and payments
- Horizontally scalable behind load balancer

### Matching Layer
- Redis **GEOSEARCH** for nearest-driver lookup
- Millisecond-level proximity resolution
- Avoids database distance scans

### Persistence Layer
- PostgreSQL with:
  - Transactional integrity
  - Indexed lifecycle tables
  - Connection pooling

Guarantees atomic state transitions and consistency.

### Realtime Layer
- WebSocket broadcast manager
- Publishes:
  - Ride offered
  - Trip started
  - Trip completed

Keeps UI state synchronized in real time.

---

## 3. Low-Level Design

### Ride Service
Responsibilities:
- Create ride
- Handle idempotency
- Trigger driver matching
- Emit realtime events

Guarantee:
- Ride is persisted before matching begins.

---

### Dispatch Logic
Responsibilities:
- Atomic driver assignment
- Prevent multi-accept race conditions

Mechanism:
- Transactional DB update with status guards.

---

### Trip Lifecycle

State machine:

REQUESTED → OFFERED → ONGOING → COMPLETED


Rules:
- Cannot start without assignment
- Cannot end before start
- Fare computed exactly once

Ensures lifecycle correctness.

---

### Payment Processing
Triggered **only after trip completion**.

Guarantees:
- No premature charge
- Immutable final fare
- Auditable payment record

---

### Driver Location Service
- Stores coordinates in Redis Geo index
- Enables constant-time proximity search

---

## 4. Performance Characteristics

### Load Profile Tested
- 50 concurrent users
- ~30 requests/second sustained

### Latency
- Median ≈ 13 ms  
- p95 ≈ 36 ms  
- p99 < 300 ms  

Meets real-time system expectations.

### Reliability
- 0% failure rate under sustained load
- No DB pool exhaustion
- No lifecycle race conditions

### Bottlenecks
Primary cost sources:
- Network latency
- JSON serialization
- DB commit round-trip

Driver matching is **not** the bottleneck → confirms Redis efficiency.

---

## 5. Scalability Model (100k Drivers)

### API Scaling
- Multiple stateless FastAPI instances
- Load-balanced deployment
- Linear horizontal scaling

### Redis Geo Scaling
- In-memory geo index
- Logarithmic lookup complexity
- Sub-100 ms matching at 100k drivers

### Database Growth Path

**Stage 1 — Vertical scaling**
- Larger instance
- Read replicas

**Stage 2 — Partitioning**
- Shard by region or tenant

**Stage 3 — Event-driven services**
- Async trip/payment workers

Supports millions of trips per day.

### Realtime Scaling
- Multiple WebSocket nodes
- Redis pub/sub fan-out

Enables city-scale live updates.
