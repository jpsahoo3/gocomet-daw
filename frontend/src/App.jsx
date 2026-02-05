import { useEffect, useState } from "react";
import RidePanel from "./components/RidePanel";
import DriverPanel from "./components/DriverPanel";
import LiveEvents from "./components/LiveEvents";
import { connectSocket } from "./services/socket";
import "./styles/app.css";

export default function App() {
  const [events, setEvents] = useState([]);

  useEffect(() => {
    const ws = connectSocket((msg) => {
      setEvents(e => [msg, ...e.slice(0, 20)]);
    });

    return () => ws.close();
  }, []);

  function addEvent(msg) {
    setEvents(e => [msg, ...e.slice(0, 20)]);
  }

  return (
    <div className="container">
      <h1>GoComet Ride-Hailing Dashboard</h1>

      <div className="grid">
        <RidePanel onEvent={addEvent} />
        <DriverPanel onEvent={addEvent} />
        <LiveEvents events={events} />
      </div>
    </div>
  );
}
