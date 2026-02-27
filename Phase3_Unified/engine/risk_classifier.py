def classify_risk(score: float) -> str:
    if score < 0.30:
        return "LOW"
    elif score < 0.50:
        return "MEDIUM"
    else:
        return "HIGH"
