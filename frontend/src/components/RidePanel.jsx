import { useState } from "react";
import { createRide, endTrip } from "../services/api";

export default function RidePanel({ onEvent }) {
  const [lat, setLat] = useState("12.9716");
  const [lon, setLon] = useState("77.5946");
  const [activeRide, setActiveRide] = useState(null);

  async function handleCreateRide() {
    const res = await createRide(lat, lon);
    onEvent(`Ride status: ${res.status}`);

    if (res.status === "ASSIGNED") {
      setActiveRide(res);
    }
  }

  async function handleEndTrip() {
    if (!activeRide) return;

    await endTrip(activeRide.ride_id, activeRide.driver_id);
    onEvent(`Trip ${activeRide.ride_id} completed`);
    setActiveRide(null);
  }

  return (
    <div className="card">
      <h3>🚕 Ride</h3>

      <input value={lat} onChange={e => setLat(e.target.value)} />
      <input value={lon} onChange={e => setLon(e.target.value)} />

      <button onClick={handleCreateRide}>Create Ride</button>

      {activeRide && (
        <>
          <p><strong>Ride ID:</strong> {activeRide.ride_id}</p>
          <p><strong>Driver:</strong> {activeRide.driver_id}</p>

          <button
            style={{ background: "#dc2626" }}
            onClick={handleEndTrip}
          >
            End Trip
          </button>
        </>
      )}
    </div>
  );
}
