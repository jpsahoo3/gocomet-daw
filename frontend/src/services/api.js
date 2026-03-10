const API_BASE = "http://localhost:8000";

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

export async function createRide(pickupLat, pickupLon, dropLat, dropLon) {
  const body = {
    pickup_lat: Number(pickupLat),
    pickup_lon: Number(pickupLon),
  };
  if (dropLat != null && dropLon != null) {
    body.drop_lat = Number(dropLat);
    body.drop_lon = Number(dropLon);
  }

  const res = await fetch(`${API_BASE}/v1/rides`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = await parseError(res, "Create ride failed");
    throw new Error(detail);
  }
  return res.json();
}

export async function estimateFare(pickupLat, pickupLon, dropLat, dropLon) {
  const params = new URLSearchParams({
    pickup_lat: pickupLat,
    pickup_lon: pickupLon,
    drop_lat: dropLat,
    drop_lon: dropLon,
  });
  const res = await fetch(`${API_BASE}/v1/rides/estimate?${params}`, { headers });
  if (!res.ok) {
    const detail = await parseError(res, "Estimate failed");
    throw new Error(detail);
  }
  return res.json();
}

export async function getRideStatus(rideId) {
  const res = await fetch(`${API_BASE}/v1/rides/${rideId}`, { headers });
  if (!res.ok) {
    const detail = await parseError(res, "Get status failed");
    throw new Error(detail);
  }
  return res.json();
}

export async function updateDriverLocation(driverId, lat, lon) {
  const res = await fetch(`${API_BASE}/v1/drivers/${driverId}/location`, {
    method: "POST",
    headers,
    body: JSON.stringify({ lat: Number(lat), lon: Number(lon) }),
  });
  if (!res.ok) {
    const detail = await parseError(res, "Update location failed");
    throw new Error(detail);
  }
  return res.json();
}

export async function setDriverStatus(driverId, available) {
  const res = await fetch(`${API_BASE}/v1/drivers/${driverId}/status`, {
    method: "POST",
    headers,
    body: JSON.stringify({ available }),
  });
  if (!res.ok) {
    const detail = await parseError(res, "Set driver status failed");
    throw new Error(detail);
  }
  return res.json();
}

export async function getHealth() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error("Health check failed");
  return res.json();
}
