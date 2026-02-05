import { useState } from "react";
import { updateDriverLocation } from "../services/api";

export default function DriverPanel({ onEvent }) {
  const [driverId, setDriverId] = useState("driver-1");
  const [lat, setLat] = useState("12.9716");
  const [lon, setLon] = useState("77.5946");

  async function sendLocation() {
    await updateDriverLocation(driverId, lat, lon);
    onEvent(`Driver ${driverId} location updated`);
  }

  return (
    <div className="card">
      <h3>🚗 Driver Location</h3>

      <input value={driverId} onChange={e => setDriverId(e.target.value)} placeholder="Driver ID" />
      <input value={lat} onChange={e => setLat(e.target.value)} placeholder="Latitude" />
      <input value={lon} onChange={e => setLon(e.target.value)} placeholder="Longitude" />

      <button onClick={sendLocation}>Send Location</button>
    </div>
  );
}
