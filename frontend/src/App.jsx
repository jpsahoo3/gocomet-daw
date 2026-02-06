import { useEffect, useState } from "react";
import RidePanel from "./components/RidePanel";
import DriverPanel from "./components/DriverPanel";
import LiveEvents from "./components/LiveEvents";
import TripControls from "./components/TripControls";
import { connectSocket } from "./services/socket";
import "./styles/app.css";

export default function App() {
  const [events, setEvents] = useState([]);
  const [activeRides, setActiveRides] = useState([]);

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
        <RidePanel onEvent={addEvent} onRideCreated={(ride) => setActiveRides(r => [ride, ...r])} />
        <DriverPanel onEvent={addEvent} />
        <LiveEvents events={events} />
        <TripControls activeRides={activeRides} onTripEnd={(rideId) => setActiveRides(r => r.filter(x => x.ride_id !== rideId))} onEvent={addEvent} />
      </div>
    </div>
  );
}
