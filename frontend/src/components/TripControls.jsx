import { useState } from "react";
import { acceptRide, startTrip, endTrip } from "../services/tripApi";
import { payForRide } from "../services/paymentApi";

export default function TripControls({ activeRides = [], onTripEnd, onEvent }) {
  const [fares, setFares] = useState({});
  const [statuses, setStatuses] = useState({});

  const handleAccept = async (ride) => {
    const driverId = ride.driver_id || "driver-1";
    try {
      await acceptRide(ride.ride_id, driverId);
      setStatuses(s => ({ ...s, [ride.ride_id]: "ACCEPTED" }));
    } catch (err) {
      console.error("Accept failed:", err);
      onEvent?.(`Accept failed: ${err.message || err}`);
    }
  };

  const handleStart = async (ride) => {
    try {
      await startTrip(ride.ride_id);
      setStatuses(s => ({ ...s, [ride.ride_id]: "ONGOING" }));
    } catch (err) {
      console.error("Start trip failed:", err);
      onEvent?.(`Start trip failed: ${err.message || err}`);
    }
  };

  const handleEnd = async (ride) => {
    try {
      const res = await endTrip(ride.ride_id);
      setFares(f => ({ ...f, [ride.ride_id]: res.fare }));
      setStatuses(s => ({ ...s, [ride.ride_id]: "COMPLETED" }));
    } catch (err) {
      console.error("End trip failed:", err);
      onEvent?.(`End trip failed: ${err.message || err}`);
    }
  };

  const handlePay = async (ride) => {
    try {
      const res = await payForRide(ride.ride_id, fares[ride.ride_id]);
      onEvent?.(`Payment ${res.status} for ride ${ride.ride_id}, amount=${res.amount}`);
      onTripEnd(ride.ride_id);
      setStatuses(s => { const ns = { ...s }; delete ns[ride.ride_id]; return ns; });
      setFares(f => { const nf = { ...f }; delete nf[ride.ride_id]; return nf; });
    } catch (err) {
      console.error("Payment failed:", err);
      onEvent?.(`Payment failed: ${err.message || err}`);
    }
  };

  if (!activeRides.length) {
    return (
      <div className="card">
        <h3>🚦 Trip Controls</h3>
        <p style={{ color: "#888" }}>Waiting for ride offer...</p>
      </div>
    );
  }

  return (
    <div className="card">
      <h3>🚦 Trip Controls</h3>
      {activeRides.map(ride => (
        <div key={ride.ride_id} style={{ marginBottom: 12, paddingBottom: 8, borderBottom: '1px solid #eee' }}>
          <p><strong>Ride ID:</strong> {ride.ride_id}</p>
          <p><strong>Driver:</strong> {ride.driver_id}</p>
          <p><strong>Status:</strong> {statuses[ride.ride_id] || ride.status}</p>

          <button onClick={() => handleAccept(ride)} disabled={statuses[ride.ride_id] !== undefined}>
            Accept Ride
          </button>

          <button onClick={() => handleStart(ride)} disabled={statuses[ride.ride_id] !== "ACCEPTED"} style={{ marginLeft: 8 }}>
            Start Trip
          </button>

          <button onClick={() => handleEnd(ride)} disabled={statuses[ride.ride_id] !== "ONGOING"} style={{ marginLeft: 8 }}>
            End Trip
          </button>

          <button onClick={() => handlePay(ride)} disabled={!fares[ride.ride_id]} style={{ marginLeft: 8 }}>
            Pay
          </button>

          {fares[ride.ride_id] && <p>Fare: ₹{fares[ride.ride_id]}</p>}
        </div>
      ))}
    </div>
  );
}
