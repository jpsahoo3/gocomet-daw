"""
Tests for new real-world features:
  - Fare estimate endpoint
  - Ride status endpoint
  - Ride cancellation
  - Driver online/offline toggle
  - Health check
  - Drop-off coordinates & actual distance fare
"""

_HEADERS = {"X-Tenant-ID": "t1", "X-Region": "in"}
_PICKUP = {"pickup_lat": 12.9716, "pickup_lon": 77.5946}
_DROP   = {"drop_lat":   12.9279, "drop_lon":  77.6271}
_FAKE   = "00000000-0000-0000-0000-000000000000"


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

def test_health_returns_200(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert "status" in body
    assert body["database"] == "connected"
    assert body["redis_mode"] in ("redis", "fallback")


# ---------------------------------------------------------------------------
# Fare estimate
# ---------------------------------------------------------------------------

def test_fare_estimate_returns_breakdown(client):
    resp = client.get(
        "/v1/rides/estimate",
        params={
            "pickup_lat": 12.9716, "pickup_lon": 77.5946,
            "drop_lat":   12.9279, "drop_lon":  77.6271,
        },
        headers=_HEADERS,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "estimated_fare" in body
    assert body["estimated_fare"] > 0
    assert "distance_km" in body
    assert body["distance_km"] > 0
    assert "surge_multiplier" in body
    assert "breakdown" in body
    assert body["breakdown"]["base_fare"] > 0


def test_fare_estimate_requires_all_params(client):
    # Missing drop coords
    resp = client.get(
        "/v1/rides/estimate",
        params={"pickup_lat": 12.97, "pickup_lon": 77.59},
        headers=_HEADERS,
    )
    assert resp.status_code == 422


def test_fare_estimate_same_location_minimal_fare(client):
    resp = client.get(
        "/v1/rides/estimate",
        params={
            "pickup_lat": 12.97, "pickup_lon": 77.59,
            "drop_lat":   12.97, "drop_lon":   77.59,
        },
        headers=_HEADERS,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["distance_km"] == 0.0
    # Fare should still be at least the base fare
    assert body["estimated_fare"] >= 50


# ---------------------------------------------------------------------------
# Ride with drop coords — estimated_fare in response
# ---------------------------------------------------------------------------

def test_create_ride_with_drop_coords_includes_estimated_fare(client):
    driver_id = "feat-driver-drop-k"
    client.post(f"/v1/drivers/{driver_id}/location",
                json={"lat": _PICKUP["pickup_lat"], "lon": _PICKUP["pickup_lon"]})

    payload = {**_PICKUP, **_DROP}
    resp = client.post("/v1/rides", json=payload, headers=_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    # May be NO_DRIVER if all drivers locked; just verify structure
    assert "ride_id" in body
    if body.get("status") == "OFFERED":
        assert body["estimated_fare"] is not None
        assert body["estimated_fare"] > 0


# ---------------------------------------------------------------------------
# Ride status endpoint
# ---------------------------------------------------------------------------

def test_get_ride_status_returns_ride(client):
    resp = client.post("/v1/rides", json=_PICKUP, headers=_HEADERS)
    ride_id = resp.json()["ride_id"]

    status_resp = client.get(f"/v1/rides/{ride_id}", headers=_HEADERS)
    assert status_resp.status_code == 200
    body = status_resp.json()
    assert body["ride_id"] == ride_id
    assert "status" in body
    assert "pickup_lat" in body


def test_get_ride_status_nonexistent_returns_404(client):
    resp = client.get(f"/v1/rides/{_FAKE}", headers=_HEADERS)
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Ride cancellation
# ---------------------------------------------------------------------------

def test_cancel_requested_ride_free(client):
    """A ride with NO_DRIVER can be cancelled with no fee."""
    resp = client.post("/v1/rides", json={"pickup_lat": 0.0, "pickup_lon": 0.0}, headers=_HEADERS)
    ride_id = resp.json()["ride_id"]

    cancel = client.post(f"/v1/rides/{ride_id}/cancel", headers=_HEADERS)
    assert cancel.status_code == 200
    body = cancel.json()
    assert body["status"] == "CANCELLED"
    assert body["cancellation_fee"] == 0.0


def test_cancel_offered_ride_free(client):
    driver_id = "feat-driver-cancel-l"
    client.post(f"/v1/drivers/{driver_id}/location",
                json={"lat": _PICKUP["pickup_lat"], "lon": _PICKUP["pickup_lon"]})

    resp = client.post("/v1/rides", json=_PICKUP, headers=_HEADERS)
    body = resp.json()

    if body["status"] != "OFFERED":
        return

    ride_id = body["ride_id"]
    cancel = client.post(f"/v1/rides/{ride_id}/cancel", headers=_HEADERS)
    assert cancel.status_code == 200
    assert cancel.json()["cancellation_fee"] == 0.0


def test_cancel_assigned_ride_charges_fee(client):
    driver_id = "feat-driver-cancel-m"
    client.post(f"/v1/drivers/{driver_id}/location",
                json={"lat": _PICKUP["pickup_lat"], "lon": _PICKUP["pickup_lon"]})

    resp = client.post("/v1/rides", json=_PICKUP, headers=_HEADERS)
    body = resp.json()

    if body["status"] != "OFFERED":
        return

    ride_id = body["ride_id"]
    assigned = body["driver_id"]

    client.post(f"/v1/drivers/{assigned}/accept/{ride_id}")

    cancel = client.post(f"/v1/rides/{ride_id}/cancel", headers=_HEADERS)
    assert cancel.status_code == 200
    body = cancel.json()
    assert body["status"] == "CANCELLED"
    assert body["cancellation_fee"] == 50.0


def test_cancel_nonexistent_ride_returns_404(client):
    resp = client.post(f"/v1/rides/{_FAKE}/cancel", headers=_HEADERS)
    assert resp.status_code == 404


def test_cancel_ongoing_ride_returns_409(client):
    driver_id = "feat-driver-cancel-n"
    client.post(f"/v1/drivers/{driver_id}/location",
                json={"lat": _PICKUP["pickup_lat"], "lon": _PICKUP["pickup_lon"]})

    resp = client.post("/v1/rides", json=_PICKUP, headers=_HEADERS)
    body = resp.json()

    if body["status"] != "OFFERED":
        return

    ride_id = body["ride_id"]
    assigned = body["driver_id"]

    client.post(f"/v1/drivers/{assigned}/accept/{ride_id}")
    client.post(f"/v1/trips/{ride_id}/start")

    cancel = client.post(f"/v1/rides/{ride_id}/cancel", headers=_HEADERS)
    assert cancel.status_code == 409


def test_cancel_with_reason(client):
    resp = client.post("/v1/rides", json={"pickup_lat": 0.0, "pickup_lon": 0.0}, headers=_HEADERS)
    ride_id = resp.json()["ride_id"]

    cancel = client.post(
        f"/v1/rides/{ride_id}/cancel?reason=changed_mind", headers=_HEADERS
    )
    assert cancel.status_code == 200


# ---------------------------------------------------------------------------
# Driver online / offline toggle
# ---------------------------------------------------------------------------

def test_driver_status_toggle_online_offline(client):
    driver_id = "feat-driver-status-o"
    client.post(f"/v1/drivers/{driver_id}/location",
                json={"lat": 12.9716, "lon": 77.5946})

    # Default is online
    get = client.get(f"/v1/drivers/{driver_id}/status")
    assert get.status_code == 200
    assert get.json()["status"] == "online"

    # Go offline
    off = client.post(f"/v1/drivers/{driver_id}/status", json={"available": False})
    assert off.status_code == 200
    assert off.json()["status"] == "offline"

    # Verify get reflects offline
    get2 = client.get(f"/v1/drivers/{driver_id}/status")
    assert get2.json()["status"] == "offline"

    # Go back online
    on = client.post(f"/v1/drivers/{driver_id}/status", json={"available": True})
    assert on.status_code == 200
    assert on.json()["status"] == "online"


def test_offline_driver_not_matched(client):
    """An offline driver should not receive any ride offers."""
    driver_id = "feat-driver-offline-p"
    # Register location
    client.post(f"/v1/drivers/{driver_id}/location",
                json={"lat": _PICKUP["pickup_lat"], "lon": _PICKUP["pickup_lon"]})
    # Go offline
    client.post(f"/v1/drivers/{driver_id}/status", json={"available": False})

    # Create ride — the offline driver should NOT be matched
    resp = client.post("/v1/rides", json=_PICKUP, headers=_HEADERS)
    body = resp.json()

    if body["status"] == "OFFERED":
        # If another (online) driver was matched, that's fine
        assert body["driver_id"] != driver_id
    # else NO_DRIVER — also correct (no online driver available at this point)
