import uuid
import random
from sqlalchemy.orm import Session

from app.models.trip import Trip
from app.models.payment import Payment


def _mock_psp_charge(amount: float) -> tuple[str, str]:
    """
    Simulates an external PSP response.
    Returns (status, provider_reference).
    """

    # 90% success simulation
    success = random.random() < 0.9

    if success:
        return "SUCCESS", f"psp_{uuid.uuid4().hex[:10]}"
    else:
        return "FAILED", None


def create_payment_for_ride(db: Session, ride_id: str) -> Payment:
    """
    Creates payment after trip completion.
    """

    trip = db.query(Trip).filter(Trip.ride_id == ride_id).first()

    if not trip or trip.status != "COMPLETED":
        raise ValueError("Trip not completed")

    amount = trip.fare

    payment = Payment(
        tenant_id=trip.tenant_id,
        ride_id=trip.ride_id,
        amount=amount,
        status="PENDING",
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    # ---- Call mock PSP ----
    status, provider_ref = _mock_psp_charge(amount)

    payment.status = status
    payment.provider_ref = provider_ref

    db.commit()
    db.refresh(payment)

    return payment
