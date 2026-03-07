import logging
import uuid
import random
from sqlalchemy.orm import Session

from app.models.trip import Trip
from app.models.payment import Payment

logger = logging.getLogger(__name__)


def _mock_psp_charge(amount: float) -> tuple[str, str]:
    """Simulates an external PSP — 90 % success rate."""
    success = random.random() < 0.9
    if success:
        ref = f"psp_{uuid.uuid4().hex[:10]}"
        logger.debug("PSP charge succeeded | amount=%.2f ref=%s", amount, ref)
        return "SUCCESS", ref
    logger.warning("PSP charge failed (simulated) | amount=%.2f", amount)
    return "FAILED", None


def create_payment_for_ride(db: Session, ride_id: str) -> Payment:
    trip = db.query(Trip).filter(Trip.ride_id == ride_id).first()

    if not trip or trip.status != "COMPLETED":
        logger.error("Payment attempted on non-completed trip | ride_id=%s trip_status=%s",
                     ride_id, trip.status if trip else "NOT_FOUND")
        raise ValueError("Trip not completed")

    amount = trip.fare
    logger.info("Initiating payment | ride_id=%s amount=%.2f", ride_id, amount)

    payment = Payment(
        tenant_id=trip.tenant_id,
        ride_id=trip.ride_id,
        amount=amount,
        status="PENDING",
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    status, provider_ref = _mock_psp_charge(amount)

    payment.status = status
    payment.provider_ref = provider_ref
    db.commit()
    db.refresh(payment)

    logger.info(
        "Payment finalised | ride_id=%s payment_id=%s status=%s amount=%.2f ref=%s",
        ride_id, payment.id, status, amount, provider_ref,
    )
    return payment
