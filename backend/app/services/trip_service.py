from datetime import datetime
from sqlalchemy.orm import Session

from app.models.ride import Ride
from app.models.trip import Trip
from app.services.matching_service import get_redis
from app.services.fare_service import calculate_fare
from app.services.surge_service import update_surge


CELL = "default"  # simplified geo bucket


def _inc_active_rides(r):
    r.incr(f"area:{CELL}:active_rides")
    update_surge(CELL)


def _dec_active_rides(r):
    r.decr(f"area:{CELL}:active_rides")
    update_surge(CELL)


def _inc_available_drivers(r):
    r.incr(f"area:{CELL}:available_drivers")
    update_surge(CELL)


def _dec_available_drivers(r):
    r.decr(f"area:{CELL}:available_drivers")
    update_surge(CELL)


# ---------- Start Trip ----------
def start_trip(db: Session, ride_id: str) -> Trip:
    ride = db.query(Ride).filter(Ride.id == ride_id).first()

    if not ride:
        raise ValueError("Ride not found")

    if ride.status != "ASSIGNED":
        raise ValueError("Trip can start only when ASSIGNED")

    ride.status = "ONGOING"

    trip = Trip(ride_id=ride.id, status="ONGOING")

    db.add(trip)
    db.commit()
    db.refresh(trip)

    # ---- Update demand metrics ----
    r = get_redis()
    _inc_active_rides(r)
    _dec_available_drivers(r)

    return trip


# ---------- Pause ----------
def pause_trip(db: Session, ride_id: str) -> Trip:
    trip = db.query(Trip).filter(Trip.ride_id == ride_id, Trip.status == "ONGOING").first()

    if not trip:
        raise ValueError("Active trip not found")

    trip.status = "PAUSED"
    db.commit()
    db.refresh(trip)

    return trip


# ---------- Resume ----------
def resume_trip(db: Session, ride_id: str) -> Trip:
    trip = db.query(Trip).filter(Trip.ride_id == ride_id, Trip.status == "PAUSED").first()

    if not trip:
        raise ValueError("Paused trip not found")

    trip.status = "ONGOING"
    db.commit()
    db.refresh(trip)

    return trip


# ---------- End Trip ----------
def end_trip(db: Session, ride_id: str):
    ride = db.query(Ride).filter(Ride.id == ride_id).first()

    if not ride:
        raise ValueError("Ride not found")

    if ride.status != "ONGOING":
        raise ValueError("Trip can end only when ONGOING")

    trip = db.query(Trip).filter(Trip.ride_id == ride_id).first()

    # ---- Mock distance ----
    distance_km = 5.0

    end_time = datetime.utcnow()

    # ---- Real fare engine ----
    fare = calculate_fare(
        distance_km=distance_km,
        start_time=trip.start_time,
        end_time=end_time,
        cell=CELL,
    )

    trip.status = "COMPLETED"
    trip.end_time = end_time
    trip.distance_km = distance_km
    trip.fare = fare

    ride.status = "COMPLETED"

    r = get_redis()

    # ---- Release driver ----
    if ride.driver_id:
        r.delete(f"driver:lock:{ride.driver_id}")
        _inc_available_drivers(r)

    _dec_active_rides(r)

    db.commit()

    return trip
