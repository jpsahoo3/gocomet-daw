# Real-Time Ride Dispatch Frontend

A lightweight real-time UI for interacting with the ride dispatch backend.

Built to **demonstrate end-to-end ride lifecycle visibility, realtime updates, and API integration** in a clean, minimal interface.

---

## Features

- Create ride requests from the browser
- View driver assignment status in real time
- Start and end trips from the UI
- Live ride updates via WebSockets
- Simple, responsive demo interface
- Direct integration with FastAPI backend

---

## Architecture Overview

Core pieces:

- **React (Vite)** — fast client-side UI
- **REST API calls** — ride & trip operations
- **WebSocket client** — realtime lifecycle updates
- **Stateless UI layer** — scalable behind CDN if needed

Frontend is intentionally minimal to focus on **system behavior rather than UI complexity**.

---

## User Flow

1. User creates a ride request  
2. Backend performs nearest-driver matching  
3. Driver assignment appears live in UI  
4. Trip can be started and ended  
5. Final fare is displayed after completion  

Demonstrates the **full real-time dispatch lifecycle**.

---

## Tech Stack

- React (functional components)
- Vite development server
- Native Fetch API for HTTP calls
- WebSocket client for realtime events
- Basic CSS for layout

---

## Local Setup

### 1. Install dependencies

```bash
npm install
```

### 2. Run development server
```bash
npm run dev
```

#### Frontend runs on:

```bash
http://localhost:5173
```

#### Ensure backend is running on:

```bash
http://localhost:8000
```

### Production Build

```bash
npm run build
npm run preview
```

#### This generates an optimized static bundle suitable for:

- CDN hosting
- Static site deployment
- Reverse-proxy integration with backend

### Project Structure
```
src/
 ├── components/
 ├── pages/
 ├── services/
 ├── websocket/
 └── main.jsx
```

### Design Goals

- Clear visualization of ride lifecycle
- Real-time backend communication
- Minimal, fast-loading UI
- Easy deployability as static assets

### Scope

- The frontend intentionally avoids heavy UI frameworks or complex state management.

- Goal is to show system correctness, realtime behavior, and API design clarity rather than visual polish.