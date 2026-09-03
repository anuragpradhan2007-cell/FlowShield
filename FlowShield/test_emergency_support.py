import protection_logic


# Temporarily replace Member 3's risk response
protection_logic.get_worker_risk = lambda worker_id: {
    "worker_id": worker_id,
    "stability_score": 25,
    "risk_tier": "Critical"
}


result = protection_logic.check_emergency_support(
    "e5b59720-4365-45a2-878c-458b1b644f4a",
    100,
    70
)

print(result)