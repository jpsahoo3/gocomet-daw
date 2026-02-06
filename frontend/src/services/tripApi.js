const BASE = "http://localhost:8000";

const headers = {
  "Content-Type": "application/json",
  "X-Tenant-ID": "t1",
  "X-Region": "in",
};

export const acceptRide = async (rideId, driverId) => {
  const res = await fetch(
    `${BASE}/v1/drivers/${driverId}/accept/${rideId}`,
    { method: "POST", headers }
  );
  if (!res.ok) throw new Error(`Accept ride failed: ${res.statusText}`);
  return res.json();
};

export const startTrip = async (rideId) => {
  const res = await fetch(`${BASE}/v1/trips/${rideId}/start`, {
    method: "POST",
    headers,
  });
  if (!res.ok) throw new Error(`Start trip failed: ${res.statusText}`);
  return res.json();
};

export const endTrip = async (rideId) => {
  const res = await fetch(`${BASE}/v1/trips/${rideId}/end`, {
    method: "POST",
    headers,
  });
  if (!res.ok) throw new Error(`End trip failed: ${res.statusText}`);
  return res.json();
};
