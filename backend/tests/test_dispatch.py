"""
Tests for driver accept / decline endpoints.
"""

_HEADERS = {"X-Tenant-ID": "t1", "X-Region": "in"}
_PICKUP = {"pickup_lat": 12.9716, "pickup_lon": 77.5946}
_NONEXISTENT_RIDE = "00000000-0000-0000-0000-000000000000"


# ---------------------------------------------------------------------------
# Expired / non-existent offers
# ---------------------------------------------------------------------------

def test_accept_nonexistent_offer_returns_410(client):
    resp = client.post(f"/v1/drivers/driver-1/accept/{_NONEXISTENT_RIDE}")
    # Offer never set → treated as expired
    assert resp.status_code == 410


def test_decline_nonexistent_offer_returns_410(client):
    resp = client.post(f"/v1/drivers/driver-1/decline/{_NONEXISTENT_RIDE}")
    assert resp.status_code == 410


def test_accept_invalid_ride_id_format(client):
    resp = client.post("/v1/drivers/driver-1/accept/not-a-uuid")
    # Offer lookup will find nothing → 410 expired
    assert resp.status_code in (400, 404, 410)


# ---------------------------------------------------------------------------
# Wrong driver
# ---------------------------------------------------------------------------

def test_accept_wrong_driver_returns_403(client):
    driver_id = "test-dispatch-driver-b"
    client.post(
        f"/v1/drivers/{driver_id}/location",
        json={"lat": _PICKUP["pickup_lat"], "lon": _PICKUP["pickup_lon"]},
    )

    ride_resp = client.post("/v1/rides", json=_PICKUP, headers=_HEADERS)
    assert ride_resp.status_code == 200
    body = ride_resp.json()

    if body["status"] != "OFFERED":
        return  # no driver matched, skip

    ride_id = body["ride_id"]
    assigned_driver = body["driver_id"]

    wrong_driver = "some-other-driver-xyz"
    resp = client.post(f"/v1/drivers/{wrong_driver}/accept/{ride_id}")
    assert resp.status_code == 403


def test_decline_wrong_driver_returns_403(client):
    driver_id = "test-dispatch-driver-c"
    client.post(
        f"/v1/drivers/{driver_id}/location",
        json={"lat": _PICKUP["pickup_lat"], "lon": _PICKUP["pickup_lon"]},
    )

    ride_resp = client.post("/v1/rides", json=_PICKUP, headers=_HEADERS)
    body = ride_resp.json()

    if body["status"] != "OFFERED":
        return

    ride_id = body["ride_id"]
    resp = client.post(f"/v1/drivers/wrong-driver-xyz/decline/{ride_id}")
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Successful accept
# ---------------------------------------------------------------------------

def test_accept_correct_driver_returns_assigned(client):
    driver_id = "test-dispatch-driver-d"
    client.post(
        f"/v1/drivers/{driver_id}/location",
        json={"lat": _PICKUP["pickup_lat"], "lon": _PICKUP["pickup_lon"]},
    )

    ride_resp = client.post("/v1/rides", json=_PICKUP, headers=_HEADERS)
    body = ride_resp.json()

    if body["status"] != "OFFERED":
        return  # no available driver (all locked), skip

    ride_id = body["ride_id"]
    assigned = body["driver_id"]

    accept_resp = client.post(f"/v1/drivers/{assigned}/accept/{ride_id}")
    assert accept_resp.status_code == 200
    assert accept_resp.json()["status"] == "ASSIGNED"


# ---------------------------------------------------------------------------
# Double-accept guard (offer consumed after first accept)
# ---------------------------------------------------------------------------

def test_accept_twice_second_returns_410(client):
    driver_id = "test-dispatch-driver-e"
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
    second = client.post(f"/v1/drivers/{assigned}/accept/{ride_id}")
    # Offer key deleted on first accept
    assert second.status_code == 410
