import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

// StrictMode omitted intentionally: its double-mount in dev opens two WebSocket
// connections against the module-level singleton in socket.js, causing every
// server broadcast to appear twice in LiveEvents.
createRoot(document.getElementById('root')).render(<App />)
