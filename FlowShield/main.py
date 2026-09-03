from fastapi import FastAPI

from database import engine, Base, SessionLocal
from models import EmergencyPot, CreditAssessment, Notification


Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.get("/")
def home():
    return {
        "message": "FlowShield Financial Protection Engine is running"
    }
@app.post("/emergency-pot/contribute")
def contribute_to_emergency_pot(worker_id: str, earning: float):

    db = SessionLocal()

    contribution = earning * 0.10

    pot = db.query(EmergencyPot).filter(
        EmergencyPot.worker_id == worker_id
    ).first()

    if pot is None:
        pot = EmergencyPot(
            worker_id=worker_id,
            balance=0.0,
            total_contributed=0.0,
            total_used=0.0
        )

        db.add(pot)

    pot.balance += contribution
    pot.total_contributed += contribution

    db.commit()
    db.refresh(pot)

    db.close()

    return {
        "worker_id": worker_id,
        "earning": earning,
        "contribution": contribution,
        "emergency_pot_balance": pot.balance
    }
@app.get("/emergency-pot/{worker_id}")
def get_emergency_pot(worker_id: str):

    db = SessionLocal()

    pot = db.query(EmergencyPot).filter(
        EmergencyPot.worker_id == worker_id
    ).first()

    db.close()

    if pot is None:
        return {
            "worker_id": worker_id,
            "balance": 0.0,
            "total_contributed": 0.0,
            "total_used": 0.0
        }

    return {
        "worker_id": worker_id,
        "balance": pot.balance,
        "total_contributed": pot.total_contributed,
        "total_used": pot.total_used
    }
@app.get("/credit/{worker_id}/eligibility")
def get_credit_eligibility(worker_id: str):

    from protection_logic import check_credit_eligibility

    result = check_credit_eligibility(worker_id)

    if result is None:
        return {
            "message": "Worker risk data not found"
        }

    db = SessionLocal()

    assessment = CreditAssessment(
        worker_id=result["worker_id"],
        stability_score=result["stability_score"],
        risk_level=result["risk_tier"],
        eligible=result["eligible"],
        credit_limit=result["credit_limit"],
        reason=result["reason"]
    )

    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    db.close()

    return result
@app.get("/emergency-support/{worker_id}")
def get_emergency_support(
    worker_id: str,
    requested_amount: float
):

    from protection_logic import check_emergency_support

    db = SessionLocal()

    pot = db.query(EmergencyPot).filter(
        EmergencyPot.worker_id == worker_id
    ).first()

    if pot is None:
        emergency_balance = 0.0
    else:
        emergency_balance = pot.balance

    result = check_emergency_support(
        worker_id,
        emergency_balance,
        requested_amount
    )

    db.close()

    if result is None:
        return {
            "message": "Worker risk data not found"
        }

    return result
@app.post("/emergency-pot/{worker_id}/release")
def release_emergency_funds(
    worker_id: str,
    requested_amount: float
):

    from protection_logic import check_emergency_support

    db = SessionLocal()

    pot = db.query(EmergencyPot).filter(
        EmergencyPot.worker_id == worker_id
    ).first()

    if pot is None:
        db.close()
        return {
            "message": "Emergency Pot not found"
        }

    result = check_emergency_support(
        worker_id,
        pot.balance,
        requested_amount
    )

    if result is None:
        db.close()
        return {
            "message": "Worker risk data not found"
        }

    if not result["emergency_support"]:
        db.close()
        return result

    release_amount = result["release_amount"]

    pot.balance -= release_amount
    pot.total_used += release_amount

    notification = Notification(
        worker_id=worker_id,
        type="EMERGENCY_SUPPORT",
        message=f"Emergency support of ₹{release_amount} has been approved."
    )

    db.add(notification)

    db.commit()
    db.refresh(pot)

    result["remaining_balance"] = pot.balance
    result["total_used"] = pot.total_used

    db.close()

    return result
@app.get("/notifications/{worker_id}")
def get_notifications(worker_id: str):

    db = SessionLocal()

    notifications = db.query(Notification).filter(
        Notification.worker_id == worker_id
    ).all()

    result = []

    for notification in notifications:
        result.append({
            "id": notification.id,
            "type": notification.type,
            "message": notification.message
        })

    db.close()

    return {
        "worker_id": worker_id,
        "notifications": result
    }
@app.post("/emergency-pot/{worker_id}/auto-contribute")
def auto_contribute(worker_id: str):

    from protection_logic import calculate_worker_contribution

    contribution = calculate_worker_contribution(worker_id)

    if contribution is None:
        return {
            "message": "Worker earnings not found"
        }

    db = SessionLocal()

    pot = db.query(EmergencyPot).filter(
        EmergencyPot.worker_id == worker_id
    ).first()

    if pot is None:
        pot = EmergencyPot(
            worker_id=worker_id,
            balance=0.0,
            total_contributed=0.0,
            total_used=0.0
        )
        db.add(pot)

    total_target = round(contribution, 2)

    new_contribution = total_target - pot.total_contributed

    if new_contribution < 0:
        new_contribution = 0.0

    new_contribution = round(new_contribution, 2)

    pot.balance += new_contribution
    pot.total_contributed += new_contribution

    db.commit()
    db.refresh(pot)

    db.close()

    return {
        "worker_id": worker_id,
        "contribution": new_contribution,
        "emergency_pot_balance": pot.balance,
        "message": "Emergency Pot automatically updated from Member 2 earnings."
    }