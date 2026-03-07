import { useState } from "react";
import { createRide } from "../services/api";

const LOCATION_PRESETS = [
  { label: "Koramangala", lat: "12.9279", lon: "77.6271" },
  { label: "Whitefield",  lat: "12.9698", lon: "77.7499" },
  { label: "Indiranagar", lat: "12.9784", lon: "77.6408" },
  { label: "MG Road",     lat: "12.9756", lon: "77.6097" },
];

export default function RidePanel({ onEvent, onRideCreated }) {
  const [lat, setLat] = useState("12.9716");
  const [lon, setLon] = useState("77.5946");
  const [loading, setLoading] = useState(false);
  const [lastStatus, setLastStatus] = useState(null);

  async function handleCreateRide() {
    setLoading(true);
    setLastStatus(null);
    try {
      const res = await createRide(lat, lon);
      setLastStatus(res.status);
      onEvent(`Ride created: ${res.status} — ID: ${res.ride_id}`);

      if (res.status === "OFFERED" || res.status === "ASSIGNED") {
        onRideCreated(res);
      }
    } catch (err) {
      setLastStatus("ERROR");
      onEvent(`Ride creation failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  function applyPreset(preset) {
    setLat(preset.lat);
    setLon(preset.lon);
    setLastStatus(null);
  }

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-icon indigo">🚕</div>
        <h3 className="card-title">Ride Request</h3>
      </div>

      <div>
        <div className="field-label" style={{ marginBottom: 6 }}>Quick Locations</div>
        <div className="presets">
          {LOCATION_PRESETS.map((p) => (
            <button key={p.label} className="preset-btn" onClick={() => applyPreset(p)}>
              {p.label}
            </button>
          ))}
        </div>
      </div>

      <div className="field-group">
        <label className="field-label">Pickup Latitude</label>
        <input
          placeholder="e.g. 12.9716"
          value={lat}
          onChange={(e) => setLat(e.target.value)}
        />
      </div>

      <div className="field-group">
        <label className="field-label">Pickup Longitude</label>
        <input
          placeholder="e.g. 77.5946"
          value={lon}
          onChange={(e) => setLon(e.target.value)}
        />
      </div>

      <button className="btn-primary" onClick={handleCreateRide} disabled={loading}>
        {loading && <span className="spinner" />}
        {loading ? "Requesting..." : "Request Ride"}
      </button>

      {lastStatus && (
        <div style={{ display: "flex", justifyContent: "center" }}>
          <span className={`status-badge ${lastStatus}`}>
            {lastStatus === "ERROR" ? "✕" : "✓"} {lastStatus}
          </span>
        </div>
      )}
    </div>
  );
}
