const BASE = "http://localhost:8000";

const headers = {
  "Content-Type": "application/json",
  "X-Tenant-ID": "t1",
  "X-Region": "in",
};

async function parseError(res, fallback) {
  try {
    const body = await res.json();
    return body.detail || body.message || fallback;
  } catch {
    return fallback;
  }
}

export const acceptRide = async (rideId, driverId) => {
  const res = await fetch(
    `${BASE}/v1/drivers/${driverId}/accept/${rideId}`,
    { method: "POST", headers }
  );
  if (!res.ok) {
    const detail = await parseError(res, "Accept failed");
    throw new Error(detail);
  }
  return res.json();
};

export const declineRide = async (rideId, driverId) => {
  const res = await fetch(
    `${BASE}/v1/drivers/${driverId}/decline/${rideId}`,
    { method: "POST", headers }
  );
  if (!res.ok) {
    const detail = await parseError(res, "Decline failed");
    throw new Error(detail);
  }
  return res.json();
};

export const startTrip = async (rideId) => {
  const res = await fetch(`${BASE}/v1/trips/${rideId}/start`, {
    method: "POST",
    headers,
  });
  if (!res.ok) {
    const detail = await parseError(res, "Start trip failed");
    throw new Error(detail);
  }
  return res.json();
};

export const endTrip = async (rideId) => {
  const res = await fetch(`${BASE}/v1/trips/${rideId}/end`, {
    method: "POST",
    headers,
  });
  if (!res.ok) {
    const detail = await parseError(res, "End trip failed");
    throw new Error(detail);
  }
  return res.json();
};
