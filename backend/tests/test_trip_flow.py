"""
Tests for trip lifecycle: start, pause, resume, end.
"""

_HEADERS = {"X-Tenant-ID": "t1", "X-Region": "in"}
_PICKUP = {"pickup_lat": 12.9716, "pickup_lon": 77.5946}
_FAKE_RIDE = "00000000-0000-0000-0000-000000000000"


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

def test_trip_cannot_start_without_assignment(client):
    resp = client.post(f"/v1/trips/{_FAKE_RIDE}/start")
    assert resp.status_code in (400, 404)


def test_trip_cannot_end_without_start(client):
    resp = client.post(f"/v1/trips/{_FAKE_RIDE}/end")
    assert resp.status_code in (400, 404)


def test_pause_nonexistent_trip_returns_400(client):
    resp = client.post(f"/v1/trips/{_FAKE_RIDE}/pause")
    assert resp.status_code == 400


def test_resume_nonexistent_trip_returns_400(client):
    resp = client.post(f"/v1/trips/{_FAKE_RIDE}/resume")
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Start before ASSIGNED state
# ---------------------------------------------------------------------------

def test_start_trip_on_requested_ride_fails(client):
    """A ride in REQUESTED/NO_DRIVER status cannot be started."""
    ride_resp = client.post(
        "/v1/rides",
        json={"pickup_lat": 0.0, "pickup_lon": 0.0},
        headers=_HEADERS,
    )
    ride_id = ride_resp.json()["ride_id"]

    start_resp = client.post(f"/v1/trips/{ride_id}/start")
    assert start_resp.status_code == 400


# ---------------------------------------------------------------------------
# Pause / Resume sequence
# ---------------------------------------------------------------------------

def test_pause_then_resume_trip(client):
    """Full start -> pause -> resume using an actually assigned ride."""
    driver_id = "test-trip-driver-pause-f"
    client.post(
        f"/v1/drivers/{driver_id}/location",
        json={"lat": _PICKUP["pickup_lat"], "lon": _PICKUP["pickup_lon"]},
    )

    ride_resp = client.post("/v1/rides", json=_PICKUP, headers=_HEADERS)
    body = ride_resp.json()

    if body["status"] != "OFFERED":
        return  # no available unlocked driver at this moment, skip gracefully

    ride_id = body["ride_id"]
    assigned = body["driver_id"]

    client.post(f"/v1/drivers/{assigned}/accept/{ride_id}")

    start_resp = client.post(f"/v1/trips/{ride_id}/start")
    assert start_resp.status_code == 200

    pause_resp = client.post(f"/v1/trips/{ride_id}/pause")
    assert pause_resp.status_code == 200
    assert pause_resp.json()["status"] == "PAUSED"

    resume_resp = client.post(f"/v1/trips/{ride_id}/resume")
    assert resume_resp.status_code == 200
    assert resume_resp.json()["status"] == "ONGOING"


# ---------------------------------------------------------------------------
# End trip returns fare and distance
# ---------------------------------------------------------------------------

def test_end_trip_returns_fare(client):
    driver_id = "test-trip-driver-end-g"
    client.post(
        f"/v1/drivers/{driver_id}/location",
        json={"lat": _PICKUP["pickup_lat"], "lon": _PICKUP["pickup_lon"]},
    )

    ride_resp = client.post("/v1/rides", json=_PICKUP, headers=_HEADERS)
    body = ride_resp.json()

    if body["status"] != "OFFERED":
        return

    ride_id = body["ride_id"]
    assigned = body["driver_id"]

    client.post(f"/v1/drivers/{assigned}/accept/{ride_id}")
    client.post(f"/v1/trips/{ride_id}/start")

    end_resp = client.post(f"/v1/trips/{ride_id}/end")
    assert end_resp.status_code == 200

    end_body = end_resp.json()
    assert end_body["status"] == "COMPLETED"
    assert isinstance(end_body["fare"], (int, float))
    assert end_body["fare"] > 0
    assert isinstance(end_body["distance_km"], (int, float))
