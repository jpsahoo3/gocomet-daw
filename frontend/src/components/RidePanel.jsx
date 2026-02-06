import { useState } from "react";
import { createRide } from "../services/api";

export default function RidePanel({ onEvent, onRideCreated }) {
  const [lat, setLat] = useState("12.9716");
  const [lon, setLon] = useState("77.5946");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(null);

  async function handleCreateRide() {
    setLoading(true);
    try {
      const res = await createRide(lat, lon);
      setStatus(res.status);
      onEvent(`Ride created: ${res.status}`);

      if (res.status === "OFFERED" || res.status === "ASSIGNED") {
        onRideCreated(res);
      }
    } catch (err) {
      setStatus("ERROR");
      onEvent(`Ride creation failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card">
      <h3>🚕 Ride Request</h3>

      <input placeholder="Latitude" value={lat} onChange={e => setLat(e.target.value)} />
      <input placeholder="Longitude" value={lon} onChange={e => setLon(e.target.value)} />

      <button onClick={handleCreateRide} disabled={loading}>
        {loading ? "Creating..." : "Create Ride"}
      </button>

      {status && <p style={{ color: status === "ERROR" ? "#dc2626" : "#2563eb" }}>
        Status: {status}
      </p>}
    </div>
  );
}
