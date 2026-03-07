let ws = null;
let messageListeners = [];
let statusListeners = [];
let reconnectTimer = null;
let intentionallyClosed = false;

function notifyStatus(connected) {
  for (const cb of statusListeners.slice()) {
    try { cb(connected); } catch (e) { /* ignore */ }
  }
}

function scheduleReconnect() {
  if (intentionallyClosed || reconnectTimer) return;
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null;
    if (!intentionallyClosed && messageListeners.length > 0) {
      ensureSocket();
    }
  }, 3000);
}

function ensureSocket() {
  if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
    return;
  }

  const socket = new WebSocket("ws://localhost:8000/ws");
  ws = socket; // assign before attaching callbacks

  socket.onmessage = (event) => {
    for (const cb of messageListeners.slice()) {
      try { cb(event.data); } catch (e) { console.error('ws listener error', e); }
    }
  };

  socket.onopen = () => {
    console.info('WebSocket connected');
    notifyStatus(true);
  };

  socket.onclose = () => {
    // Guard: only act if this is still the current socket.
    // React StrictMode double-mounts cause a second socket to be created
    // before the first one's onclose fires. Without this guard, the stale
    // onclose would null-out the new socket and trigger a spurious reconnect,
    // resulting in 2+ simultaneous connections and duplicate broadcast events.
    if (ws === socket) {
      ws = null;
      notifyStatus(false);
      scheduleReconnect();
    }
  };
}

export function connectSocket(onMessage, onStatus) {
  if (onMessage) messageListeners.push(onMessage);
  if (onStatus) statusListeners.push(onStatus);

  intentionallyClosed = false;
  ensureSocket();

  return {
    close() {
      if (onMessage) messageListeners = messageListeners.filter((l) => l !== onMessage);
      if (onStatus) statusListeners = statusListeners.filter((l) => l !== onStatus);

      if (messageListeners.length === 0) {
        intentionallyClosed = true;
        if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null; }

        // Disown before closing so the stale onclose handler (ws === socket check)
        // becomes a no-op and does not null-out any future socket.
        const toClose = ws;
        ws = null;
        if (toClose) {
          try { toClose.close(); } catch (e) { /* ignore */ }
        }
      }
    },
  };
}
