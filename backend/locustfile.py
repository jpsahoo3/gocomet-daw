from locust import HttpUser, task, between


class RideUser(HttpUser):
    wait_time = between(1, 2)

    @task
    def full_ride_flow(self):
        # ---- create ride ----
        resp = self.client.post(
            "/v1/rides",
            json={
                "pickup_lat": 12.9,
                "pickup_lon": 77.5,
                "drop_lat": 13.0,
                "drop_lon": 77.6,
            },
            headers={"X-Tenant-ID": "t1", "X-Region": "in"},
        )

        if resp.status_code != 200:
            return

        data = resp.json()
        ride_id = data.get("ride_id")
        driver_id = data.get("driver_id")

        if not ride_id or not driver_id:
            return

        # ---- driver accepts ----
        self.client.post(
            f"/v1/drivers/{driver_id}/accept",
            json={"ride_id": ride_id},
            headers={"X-Tenant-ID": "t1", "X-Region": "in"},
        )

        # ---- start trip ----
        self.client.post(f"/v1/trips/{ride_id}/start")

        # ---- end trip ----
        self.client.post(f"/v1/trips/{ride_id}/end")

        # ---- payment ----
        self.client.post(
            "/v1/payments",
            json={"ride_id": ride_id, "method": "CARD"},
        )
