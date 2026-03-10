import { useState, useEffect, useRef } from "react";
import { acceptRide, declineRide, cancelRide, startTrip, endTrip } from "../services/tripApi";
import { payForRide } from "../services/paymentApi";

const TRIP_STEPS = ["OFFERED", "ACCEPTED", "ONGOING", "COMPLETED", "PAID"];
const OFFER_TTL_SECONDS = 60;

function getStepIndex(status) {
  const idx = TRIP_STEPS.indexOf(status);
  return idx === -1 ? 0 : idx;
}

function StepProgress({ status }) {
  const current = getStepIndex(status);
  return (
    <div className="step-progress">
      {TRIP_STEPS.map((step, i) => {
        const state = i < current ? "done" : i === current ? "active" : "pending";
        return (
          <div key={step} style={{ display: "flex", alignItems: "center", flex: 1 }}>
            <div className="step" style={{ flex: "none", alignItems: "center" }}>
              <div className={`step-circle ${state}`}>
                {state === "done" ? "✓" : i + 1}
              </div>
              <span className={`step-label ${state}`}>{step}</span>
            </div>
            {i < TRIP_STEPS.length - 1 && (
              <div className={`step-line ${i < current ? "filled" : ""}`} style={{ flex: 1 }} />
            )}
          </div>
        );
      })}
    </div>
  );
}

function OfferCountdown({ onExpire }) {
  const [remaining, setRemaining] = useState(OFFER_TTL_SECONDS);
  const timerRef = useRef(null);

  useEffect(() => {
    timerRef.current = setInterval(() => {
      setRemaining((r) => {
        if (r <= 1) {
          clearInterval(timerRef.current);
          onExpire();
          return 0;
        }
        return r - 1;
      });
    }, 1000);
    return () => clearInterval(timerRef.current);
  }, [onExpire]);

  const pct = (remaining / OFFER_TTL_SECONDS) * 100;
  const urgent = remaining <= 15;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: urgent ? "var(--danger)" : "var(--text-muted)" }}>
        <span>Offer expires in</span>
        <strong style={{ fontFamily: "monospace" }}>{remaining}s</strong>
      </div>
      <div style={{ height: 4, borderRadius: 99, background: "rgba(255,255,255,0.08)", overflow: "hidden" }}>
        <div style={{
          height: "100%",
          width: `${pct}%`,
          borderRadius: 99,
          background: urgent ? "var(--danger)" : "linear-gradient(90deg, var(--accent), var(--accent-2))",
          transition: "width 1s linear, background 0.3s",
        }} />
      </div>
    </div>
  );
}

function RideCard({ ride, onTripEnd, onEvent, onRemove }) {
  const [status, setStatus] = useState(ride.status || "OFFERED");
  const [driverId, setDriverId] = useState(ride.driver_id || "driver-1");
  const [fare, setFare] = useState(null);
  const [loading, setLoading] = useState(null);
  const [offerExpired, setOfferExpired] = useState(false);

  const isOffered = status === "OFFERED" && !offerExpired;

  async function withLoading(key, fn) {
    setLoading(key);
    try {
      await fn();
    } catch (err) {
      onEvent?.(`Error (${key}): ${err.message || err}`);
    } finally {
      setLoading(null);
    }
  }

  const handleAccept = () => withLoading("accept", async () => {
    await acceptRide(ride.ride_id, driverId);
    setStatus("ACCEPTED");
    onEvent?.(`Ride ${ride.ride_id.slice(0, 8)} accepted by ${driverId}`);
  });

  const handleDecline = () => withLoading("decline", async () => {
    const res = await declineRide(ride.ride_id, driverId);

    if (res.status === "NO_DRIVER") {
      onEvent?.(`No drivers available for ride ${ride.ride_id.slice(0, 8)} — removing`);
      setTimeout(() => onRemove(ride.ride_id), 1500);
      setStatus("NO_DRIVER");
      return;
    }

    if (res.status === "REOFFERED" && res.driver_id) {
      setDriverId(res.driver_id);
      setOfferExpired(false);
      setStatus("OFFERED");
      onEvent?.(`Ride ${ride.ride_id.slice(0, 8)} re-offered to ${res.driver_id}`);
    }
  });

  const handleStart = () => withLoading("start", async () => {
    await startTrip(ride.ride_id);
    setStatus("ONGOING");
    onEvent?.(`Trip started: ${ride.ride_id.slice(0, 8)}`);
  });

  const handleEnd = () => withLoading("end", async () => {
    const res = await endTrip(ride.ride_id);
    setFare(res.fare);
    setStatus("COMPLETED");
    onEvent?.(`Trip ended: ${ride.ride_id.slice(0, 8)} — Fare ₹${res.fare}`);
  });

  const handlePay = () => withLoading("pay", async () => {
    const res = await payForRide(ride.ride_id, fare);
    setStatus("PAID");
    onEvent?.(`Payment ${res.status} for ride ${ride.ride_id.slice(0, 8)} — ₹${res.amount}`);
    setTimeout(() => onRemove(ride.ride_id), 1200);
  });

  const handleExpired = () => {
    setOfferExpired(true);
    onEvent?.(`Offer expired for ride ${ride.ride_id.slice(0, 8)}`);
  };

  const handleCancel = () => withLoading("cancel", async () => {
    const res = await cancelRide(ride.ride_id);
    setStatus("CANCELLED");
    onEvent?.(
      `Ride ${ride.ride_id.slice(0, 8)} cancelled` +
      (res.cancellation_fee > 0 ? ` — fee ₹${res.cancellation_fee}` : "")
    );
    setTimeout(() => onRemove(ride.ride_id), 1500);
  });

  const displayStatus = offerExpired && status === "OFFERED" ? "EXPIRED" : status;

  return (
    <div className="ride-card">
      <div className="ride-card-header">
        <span className="ride-id">{ride.ride_id?.slice(0, 12)}…</span>
        <span className={`status-badge ${displayStatus === "EXPIRED" ? "ERROR" : displayStatus}`}>
          {displayStatus}
        </span>
      </div>

      <div className="info-row">
        <span>Driver</span>
        <strong>{driverId}</strong>
      </div>

      {/* Estimated fare from booking (shown before actual fare is known) */}
      {ride.estimated_fare && !fare && (
        <div className="info-row" style={{ opacity: 0.75 }}>
          <span>Est. Fare</span>
          <span style={{ color: "var(--accent)" }}>₹{ride.estimated_fare}</span>
        </div>
      )}

      {isOffered && (
        <OfferCountdown onExpire={handleExpired} />
      )}

      {offerExpired && status === "OFFERED" && (
        <div style={{ fontSize: 12, color: "var(--danger)", textAlign: "center", padding: "6px 0" }}>
          Offer expired — driver did not respond in time
        </div>
      )}

      {!offerExpired && status !== "OFFERED" && (
        <StepProgress status={status} />
      )}

      {fare && (
        <div className="fare-display">
          <span>Fare</span>
          <strong>₹{fare}</strong>
        </div>
      )}

      <div className="ride-actions">
        {/* Accept — available only when offer is live */}
        <button
          className="btn-action accept"
          onClick={handleAccept}
          disabled={!isOffered || loading !== null}
          title={offerExpired ? "Offer has expired" : "Accept this ride"}
        >
          {loading === "accept" ? "…" : "Accept"}
        </button>

        {/* Decline — available only when offer is live */}
        <button
          className="btn-action end"
          onClick={handleDecline}
          disabled={!isOffered || loading !== null}
          title="Decline and re-dispatch to another driver"
        >
          {loading === "decline" ? "…" : "Decline"}
        </button>

        {/* Start — only after accepted */}
        <button
          className="btn-action start"
          onClick={handleStart}
          disabled={status !== "ACCEPTED" || loading !== null}
        >
          {loading === "start" ? "…" : "Start"}
        </button>

        {/* End Trip — only when ongoing */}
        <button
          className="btn-action end"
          onClick={handleEnd}
          disabled={status !== "ONGOING" || loading !== null}
        >
          {loading === "end" ? "…" : "End"}
        </button>

        {/* Pay — only after completion */}
        <button
          className="btn-action pay"
          onClick={handlePay}
          disabled={status !== "COMPLETED" || !fare || loading !== null}
        >
          {loading === "pay" ? "…" : "Pay"}
        </button>

        {/* Cancel — available before trip starts (OFFERED or ASSIGNED) */}
        {["OFFERED", "ACCEPTED"].includes(status) && !offerExpired && (
          <button
            className="btn-action"
            style={{
              borderColor: "rgba(239,68,68,0.35)",
              color: "#f87171",
              background: "rgba(239,68,68,0.06)",
            }}
            onClick={handleCancel}
            disabled={loading !== null}
            title={status === "ACCEPTED" ? "Cancel (₹50 fee applies)" : "Cancel for free"}
          >
            {loading === "cancel" ? "…" : status === "ACCEPTED" ? "Cancel (₹50)" : "Cancel"}
          </button>
        )}

        {/* Dismiss — for expired or no-driver state */}
        {(offerExpired || status === "NO_DRIVER") && (
          <button
            className="btn-action accept"
            style={{ borderColor: "rgba(100,116,139,0.4)", color: "var(--text-muted)" }}
            onClick={() => onRemove(ride.ride_id)}
          >
            Dismiss
          </button>
        )}
      </div>
    </div>
  );
}

export default function TripControls({ activeRides = [], onTripEnd, onEvent }) {
  if (!activeRides.length) {
    return (
      <div className="card">
        <div className="card-header">
          <div className="card-icon amber">🚦</div>
          <h3 className="card-title">Trip Controls</h3>
        </div>
        <div className="empty-state">
          <div className="empty-state-icon">🛣</div>
          <p className="empty-state-text">No active rides yet.<br />Request a ride to get started.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-icon amber">🚦</div>
        <h3 className="card-title">Trip Controls</h3>
        <span style={{ marginLeft: "auto", fontSize: 12, color: "var(--text-muted)" }}>
          {activeRides.length} active
        </span>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 12, maxHeight: 480, overflowY: "auto", paddingRight: 2 }}>
        {activeRides.map((ride) => (
          <RideCard
            key={ride.ride_id}
            ride={ride}
            onTripEnd={onTripEnd}
            onEvent={onEvent}
            onRemove={onTripEnd}
          />
        ))}
      </div>
    </div>
  );
}
