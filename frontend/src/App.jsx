import { useEffect, useState, useCallback } from "react";
import RidePanel from "./components/RidePanel";
import DriverPanel from "./components/DriverPanel";
import LiveEvents from "./components/LiveEvents";
import TripControls from "./components/TripControls";
import { connectSocket } from "./services/socket";
import "./styles/app.css";

export default function App() {
  const [events, setEvents] = useState([]);
  const [activeRides, setActiveRides] = useState([]);
  const [wsConnected, setWsConnected] = useState(false);
  const [stats, setStats] = useState({ total: 0, completed: 0, active: 0 });

  useEffect(() => {
    const ws = connectSocket(
      (msg) => addEvent(msg),
      (connected) => setWsConnected(connected)
    );
    return () => ws.close();
  }, []);

  const addEvent = useCallback((text) => {
    const event = { text: String(text), time: new Date() };
    setEvents((e) => [event, ...e.slice(0, 49)]);
  }, []);

  const handleRideCreated = useCallback((ride) => {
    setActiveRides((r) => [ride, ...r]);
    setStats((s) => ({ ...s, total: s.total + 1, active: s.active + 1 }));
  }, []);

  const handleTripEnd = useCallback((rideId) => {
    setActiveRides((r) => r.filter((x) => x.ride_id !== rideId));
    setStats((s) => ({ ...s, completed: s.completed + 1, active: Math.max(0, s.active - 1) }));
  }, []);

  const clearEvents = useCallback(() => setEvents([]), []);

  return (
    <div className="container">
      <header className="header">
        <div className="header-top">
          <div className="logo">
            <div className="logo-icon">🚖</div>
            <div className="logo-text">
              <span className="logo-title">GoComet Dispatch</span>
              <span className="logo-subtitle">Ride-Hailing Operations Center</span>
            </div>
          </div>

          <div className={`ws-badge ${wsConnected ? "connected" : "disconnected"}`}>
            <span className="ws-dot" />
            {wsConnected ? "Live" : "Connecting..."}
          </div>
        </div>

        <div className="stats-bar">
          <div className="stat-item">
            <span className="stat-value">{stats.total}</span>
            <span className="stat-label">Total Rides</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{stats.active}</span>
            <span className="stat-label">Active</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{stats.completed}</span>
            <span className="stat-label">Completed</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{events.length}</span>
            <span className="stat-label">Events</span>
          </div>
        </div>
      </header>

      <div className="grid">
        <RidePanel onEvent={addEvent} onRideCreated={handleRideCreated} />
        <DriverPanel onEvent={addEvent} />
        <LiveEvents events={events} onClear={clearEvents} />
        <TripControls
          activeRides={activeRides}
          onTripEnd={handleTripEnd}
          onEvent={addEvent}
        />
      </div>
    </div>
  );
}
