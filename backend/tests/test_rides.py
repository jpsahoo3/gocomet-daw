"""
Tests for ride creation: validation, NO_DRIVER, OFFERED, idempotency.
"""

_HEADERS = {"X-Tenant-ID": "t1", "X-Region": "in"}
# Koramangala, Bangalore - used for geo-proximity tests
_PICKUP = {"pickup_lat": 12.9716, "pickup_lon": 77.5946}
# Null Island - no drivers here → guarantees NO_DRIVER response
_PICKUP_REMOTE = {"pickup_lat": 0.0, "pickup_lon": 0.0}


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def test_create_ride_missing_body(client):
    resp = client.post("/v1/rides", json={})
    assert resp.status_code == 422


def test_create_ride_missing_pickup_lon(client):
    resp = client.post("/v1/rides", json={"pickup_lat": 12.9}, headers=_HEADERS)
    assert resp.status_code == 422


def test_create_ride_invalid_types(client):
    resp = client.post(
        "/v1/rides",
        json={"pickup_lat": "not-a-number", "pickup_lon": "bad"},
        headers=_HEADERS,
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# NO_DRIVER path (pickup far from any registered driver)
# ---------------------------------------------------------------------------

def test_create_ride_no_driver_returns_200(client):
    resp = client.post("/v1/rides", json=_PICKUP_REMOTE, headers=_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "NO_DRIVER"
    assert "ride_id" in body


# ---------------------------------------------------------------------------
# OFFERED path (driver registered close to pickup)
# ---------------------------------------------------------------------------

def test_create_ride_offered_when_driver_nearby(client):
    driver_id = "test-rides-driver-a"

    # Register driver at the same coords as the pickup
    client.post(
        f"/v1/drivers/{driver_id}/location",
        json={"lat": _PICKUP["pickup_lat"], "lon": _PICKUP["pickup_lon"]},
    )

    resp = client.post("/v1/rides", json=_PICKUP, headers=_HEADERS)
    assert resp.status_code == 200
    body = resp.json()

    assert body["status"] == "OFFERED"
    assert "ride_id" in body
    assert "driver_id" in body


def test_create_ride_response_has_required_fields(client):
    resp = client.post("/v1/rides", json=_PICKUP_REMOTE, headers=_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert "ride_id" in body
    assert "status" in body


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------

def test_create_ride_idempotency_same_key_deduplicates(client):
    idem_key = "idem-test-key-001"
    headers = {**_HEADERS, "idempotency-key": idem_key}

    resp1 = client.post("/v1/rides", json=_PICKUP_REMOTE, headers=headers)
    resp2 = client.post("/v1/rides", json=_PICKUP_REMOTE, headers=headers)

    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp1.json()["ride_id"] == resp2.json()["ride_id"]


def test_create_ride_different_keys_produce_different_rides(client):
    resp1 = client.post(
        "/v1/rides", json=_PICKUP_REMOTE, headers={**_HEADERS, "idempotency-key": "k-001"}
    )
    resp2 = client.post(
        "/v1/rides", json=_PICKUP_REMOTE, headers={**_HEADERS, "idempotency-key": "k-002"}
    )

    assert resp1.json()["ride_id"] != resp2.json()["ride_id"]
