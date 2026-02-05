export function connectSocket(onMessage) {
  const ws = new WebSocket("ws://localhost:8000/ws");

  ws.onmessage = (event) => {
    onMessage(event.data);
  };

  return ws;
}
