const API_BASE = "http://localhost:8000";

const headers = {
  "Content-Type": "application/json",
  "X-Tenant-ID": "t1",
  "X-Region": "in",
};

export async function createRide(lat, lon) {
  const res = await fetch(`${API_BASE}/v1/rides`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      pickup_lat: Number(lat),
      pickup_lon: Number(lon),
    }),
  });
  if (!res.ok) throw new Error(`Create ride failed: ${res.statusText}`);
  return res.json();
}

export async function updateDriverLocation(driverId, lat, lon) {
  const res = await fetch(`${API_BASE}/v1/drivers/${driverId}/location`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      lat: Number(lat),
      lon: Number(lon),
    }),
  });
  if (!res.ok) throw new Error(`Update location failed: ${res.statusText}`);
  return res.json();
}
