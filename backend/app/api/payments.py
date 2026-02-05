from fastapi import APIRouter, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.services.payment_service import create_payment_for_ride
from app.websocket.ws import manager

router = APIRouter()


def get_db() -> Session:
    return SessionLocal()


@router.post("/v1/payments/{ride_id}")
def pay_for_ride(ride_id: str, background_tasks: BackgroundTasks):
    db = get_db()

    try:
        payment = create_payment_for_ride(db, ride_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    background_tasks.add_task(
        manager.broadcast,
        f"Payment {payment.status} for ride {ride_id}, amount={payment.amount}",
    )

    return {
        "payment_id": str(payment.id),
        "status": payment.status,
        "amount": payment.amount,
        "provider_ref": payment.provider_ref,
    }
