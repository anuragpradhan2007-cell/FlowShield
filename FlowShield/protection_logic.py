from member2_service import get_worker_earnings


def calculate_emergency_contribution(earning):
    contribution = earning * 0.10
    return contribution


def calculate_worker_contribution(worker_id):
    data = get_worker_earnings(worker_id)

    if data is None:
        return None

    total_earnings = data["total_earnings_7_days"]

    contribution = calculate_emergency_contribution(total_earnings)

    return contribution
from member3_service import get_worker_risk


def check_credit_eligibility(worker_id):
    risk_data = get_worker_risk(worker_id)

    if risk_data is None:
        return None

    stability_score = risk_data["stability_score"]
    risk_tier = risk_data["risk_tier"]

    if stability_score >= 70:
        eligible = True
        credit_limit = 5000
        reason = "Worker has a stable financial profile."

    elif stability_score >= 40:
        eligible = True
        credit_limit = 2500
        reason = "Worker is at risk but may qualify for limited credit."

    else:
        eligible = False
        credit_limit = 0
        reason = "Worker has critical financial risk."

    return {
        "worker_id": worker_id,
        "stability_score": stability_score,
        "risk_tier": risk_tier,
        "eligible": eligible,
        "credit_limit": credit_limit,
        "reason": reason
    }
def check_emergency_support(worker_id, emergency_balance, requested_amount):

    risk_data = get_worker_risk(worker_id)

    if risk_data is None:
        return None

    risk_tier = risk_data["risk_tier"]
    stability_score = risk_data["stability_score"]

    if risk_tier == "Critical":
        release_amount = min(emergency_balance, requested_amount)

        if release_amount > 0:
            return {
                "worker_id": worker_id,
                "stability_score": stability_score,
                "risk_tier": risk_tier,
                "emergency_support": True,
                "release_amount": release_amount,
                "reason": "Critical financial risk detected. Emergency funds can be released."
            }

        return {
            "worker_id": worker_id,
            "stability_score": stability_score,
            "risk_tier": risk_tier,
            "emergency_support": False,
            "release_amount": 0,
            "reason": "Critical risk detected, but Emergency Pot has insufficient funds."
        }

    return {
        "worker_id": worker_id,
        "stability_score": stability_score,
        "risk_tier": risk_tier,
        "emergency_support": False,
        "release_amount": 0,
        "reason": "Worker is not in Critical risk."
    }
def calculate_release_amount(emergency_balance, requested_amount):
    if emergency_balance <= 0:
        return 0.0

    if requested_amount <= 0:
        return 0.0

    return min(emergency_balance, requested_amount)