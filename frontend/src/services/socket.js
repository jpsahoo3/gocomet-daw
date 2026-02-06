let ws = null;
let listeners = [];

function ensureSocket() {
  if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
    return ws;
  }

  ws = new WebSocket("ws://localhost:8000/ws");

  ws.onmessage = (event) => {
    for (const cb of listeners.slice()) {
      try {
        cb(event.data);
      } catch (e) {
        // ignore listener errors
        console.error('ws listener error', e);
      }
    }
  };

  ws.onopen = () => {
    console.info('WebSocket connected');
  };

  ws.onclose = () => {
    // clear socket so it can be recreated
    ws = null;
  };

  return ws;
}

export function connectSocket(onMessage) {
  listeners.push(onMessage);
  ensureSocket();

  return {
    close() {
      listeners = listeners.filter((l) => l !== onMessage);
      // if no listeners, close underlying socket
      if (listeners.length === 0 && ws) {
        try {
          ws.close();
        } catch (e) {
          // ignore
        }
        ws = null;
      }
    },
  };
}
