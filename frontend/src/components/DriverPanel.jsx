import { useState } from "react";
import { updateDriverLocation } from "../services/api";

const DRIVER_PRESETS = ["driver-1", "driver-2", "driver-3"];

const LOCATION_PRESETS = [
  { label: "Koramangala", lat: "12.9279", lon: "77.6271" },
  { label: "Whitefield",  lat: "12.9698", lon: "77.7499" },
  { label: "MG Road",     lat: "12.9756", lon: "77.6097" },
];

export default function DriverPanel({ onEvent }) {
  const [driverId, setDriverId] = useState("driver-1");
  const [lat, setLat] = useState("12.9716");
  const [lon, setLon] = useState("77.5946");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  async function sendLocation() {
    setLoading(true);
    setSent(false);
    try {
      await updateDriverLocation(driverId, lat, lon);
      setSent(true);
      onEvent(`Driver ${driverId} location updated → (${lat}, ${lon})`);
      setTimeout(() => setSent(false), 2000);
    } catch (err) {
      onEvent(`Location update failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-icon green">🚗</div>
        <h3 className="card-title">Driver Location</h3>
      </div>

      <div className="field-group">
        <label className="field-label">Driver</label>
        <input
          value={driverId}
          onChange={(e) => setDriverId(e.target.value)}
          placeholder="Driver ID"
        />
        <div className="presets" style={{ marginTop: 6 }}>
          {DRIVER_PRESETS.map((d) => (
            <button
              key={d}
              className="preset-btn"
              onClick={() => setDriverId(d)}
              style={driverId === d ? { background: "rgba(99,102,241,0.25)", borderColor: "var(--accent)", color: "#fff" } : {}}
            >
              {d}
            </button>
          ))}
        </div>
      </div>

      <div>
        <div className="field-label" style={{ marginBottom: 6 }}>Quick Locations</div>
        <div className="presets">
          {LOCATION_PRESETS.map((p) => (
            <button
              key={p.label}
              className="preset-btn"
              onClick={() => { setLat(p.lat); setLon(p.lon); }}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      <div style={{ display: "flex", gap: 10 }}>
        <div className="field-group" style={{ flex: 1 }}>
          <label className="field-label">Latitude</label>
          <input value={lat} onChange={(e) => setLat(e.target.value)} placeholder="Lat" />
        </div>
        <div className="field-group" style={{ flex: 1 }}>
          <label className="field-label">Longitude</label>
          <input value={lon} onChange={(e) => setLon(e.target.value)} placeholder="Lon" />
        </div>
      </div>

      <button
        className="btn-primary"
        onClick={sendLocation}
        disabled={loading}
        style={sent ? { background: "linear-gradient(135deg, #10b981, #059669)" } : {}}
      >
        {loading && <span className="spinner" />}
        {sent ? "✓ Location Sent!" : loading ? "Sending..." : "Update Location"}
      </button>
    </div>
  );
}
