const API_BASE = "http://localhost:8000";

export async function createRide(lat, lon) {
  const res = await fetch(`${API_BASE}/v1/rides`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      pickup_lat: Number(lat),
      pickup_lon: Number(lon),
    }),
  });
  return res.json();
}

export async function updateDriverLocation(driverId, lat, lon) {
  const res = await fetch(`${API_BASE}/v1/drivers/${driverId}/location`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      lat: Number(lat),
      lon: Number(lon),
    }),
  });
  return res.json();
}

export async function endTrip(rideId, driverId) {
  const res = await fetch(
    `http://localhost:8000/v1/trips/${rideId}/end?driver_id=${driverId}`,
    {
      method: "POST",
    }
  );
  return res.json();
}
