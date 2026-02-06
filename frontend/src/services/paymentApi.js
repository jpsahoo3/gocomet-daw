const BASE = "http://localhost:8000";

const headers = {
  "Content-Type": "application/json",
  "X-Tenant-ID": "t1",
  "X-Region": "in",
};

export const payForRide = async (rideId, amount) => {
  const res = await fetch(`${BASE}/v1/payments/${rideId}`, {
    method: "POST",
    headers,
    // backend does not expect amount in body currently, but include for future
    body: JSON.stringify({ amount }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }

  return res.json();
};
