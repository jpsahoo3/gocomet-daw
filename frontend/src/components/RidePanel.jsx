import { useState, useCallback } from "react";
import { createRide, estimateFare } from "../services/api";

const LOCATION_PRESETS = [
  { label: "Koramangala", lat: "12.9279", lon: "77.6271" },
  { label: "Whitefield",  lat: "12.9698", lon: "77.7499" },
  { label: "Indiranagar", lat: "12.9784", lon: "77.6408" },
  { label: "MG Road",     lat: "12.9756", lon: "77.6097" },
];

export default function RidePanel({ onEvent, onRideCreated }) {
  const [pickupLat, setPickupLat] = useState("12.9716");
  const [pickupLon, setPickupLon] = useState("77.5946");
  const [dropLat, setDropLat]     = useState("12.9279");
  const [dropLon, setDropLon]     = useState("77.6271");

  const [estimate, setEstimate]   = useState(null);
  const [estimating, setEstimating] = useState(false);
  const [loading, setLoading]     = useState(false);
  const [lastStatus, setLastStatus] = useState(null);

  const applyPickupPreset = useCallback((p) => {
    setPickupLat(p.lat); setPickupLon(p.lon); setEstimate(null);
  }, []);

  const applyDropPreset = useCallback((p) => {
    setDropLat(p.lat); setDropLon(p.lon); setEstimate(null);
  }, []);

  async function handleEstimate() {
    setEstimating(true);
    setEstimate(null);
    try {
      const res = await estimateFare(pickupLat, pickupLon, dropLat, dropLon);
      setEstimate(res);
      onEvent(`Fare estimate: ₹${res.estimated_fare} | ${res.distance_km} km | surge ${res.surge_multiplier}x`);
    } catch (err) {
      onEvent(`Estimate failed: ${err.message}`);
    } finally {
      setEstimating(false);
    }
  }

  async function handleCreateRide() {
    setLoading(true);
    setLastStatus(null);
    try {
      const res = await createRide(pickupLat, pickupLon, dropLat, dropLon);
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

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-icon indigo">🚕</div>
        <h3 className="card-title">Ride Request</h3>
      </div>

      {/* Pickup */}
      <div className="field-group">
        <label className="field-label">Pickup Location</label>
        <div className="presets" style={{ marginBottom: 6 }}>
          {LOCATION_PRESETS.map((p) => (
            <button key={`pu-${p.label}`} className="preset-btn" onClick={() => applyPickupPreset(p)}>
              {p.label}
            </button>
          ))}
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <input style={{ flex: 1 }} placeholder="Pickup lat" value={pickupLat}
            onChange={(e) => { setPickupLat(e.target.value); setEstimate(null); }} />
          <input style={{ flex: 1 }} placeholder="Pickup lon" value={pickupLon}
            onChange={(e) => { setPickupLon(e.target.value); setEstimate(null); }} />
        </div>
      </div>

      {/* Drop-off */}
      <div className="field-group">
        <label className="field-label">Drop-off Location</label>
        <div className="presets" style={{ marginBottom: 6 }}>
          {LOCATION_PRESETS.map((p) => (
            <button key={`dr-${p.label}`} className="preset-btn" onClick={() => applyDropPreset(p)}>
              {p.label}
            </button>
          ))}
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <input style={{ flex: 1 }} placeholder="Drop lat" value={dropLat}
            onChange={(e) => { setDropLat(e.target.value); setEstimate(null); }} />
          <input style={{ flex: 1 }} placeholder="Drop lon" value={dropLon}
            onChange={(e) => { setDropLon(e.target.value); setEstimate(null); }} />
        </div>
      </div>

      {/* Fare estimate result */}
      {estimate && (
        <div style={{
          background: "rgba(99,102,241,0.1)",
          border: "1px solid rgba(99,102,241,0.3)",
          borderRadius: 10,
          padding: "10px 14px",
          display: "flex",
          flexDirection: "column",
          gap: 4,
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontSize: 12, color: "var(--text-muted)" }}>Estimated Fare</span>
            <strong style={{ fontSize: 20, color: "var(--accent)" }}>₹{estimate.estimated_fare}</strong>
          </div>
          <div style={{ display: "flex", gap: 14, fontSize: 11, color: "var(--text-muted)", flexWrap: "wrap" }}>
            <span>{estimate.distance_km} km</span>
            <span>Surge {estimate.surge_multiplier}x</span>
            <span>Base ₹{estimate.breakdown.base_fare} + ₹{estimate.breakdown.distance_charge}</span>
          </div>
        </div>
      )}

      <div style={{ display: "flex", gap: 8 }}>
        <button
          onClick={handleEstimate}
          disabled={estimating}
          style={{
            flex: "none", padding: "10px 14px", fontSize: 13, borderRadius: 8,
            background: "rgba(255,255,255,0.06)", color: "var(--text-muted)",
            border: "1px solid rgba(255,255,255,0.1)", cursor: "pointer",
            display: "flex", alignItems: "center", gap: 5,
          }}
        >
          {estimating ? <span className="spinner" /> : "≈"} Estimate
        </button>
        <button className="btn-primary" style={{ flex: 1 }} onClick={handleCreateRide} disabled={loading}>
          {loading && <span className="spinner" />}
          {loading ? "Requesting..." : "Request Ride"}
        </button>
      </div>

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
