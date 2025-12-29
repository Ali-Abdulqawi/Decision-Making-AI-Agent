# app/config.py

# Decision thresholds
ACCEPT_THRESHOLD = 70
REJECT_THRESHOLD = 55

# ROI settings
ROI_GOOD = 1.5
ROI_OK = 1.0
ROI_CAP = 3.0

# Motivation (excitement) weighting
MOTIVATION_MAX_POINTS = 10

# Client risk weights
CLIENT_LEVEL_RISK = {
    "low": 0,
    "normal": 2,
    "high": 6,
    "sensitive": 10,
}

# Risk keywords → extra risk points
RISK_KEYWORDS = {
    "unclear": 4,
    "scope": 3,
    "creep": 4,
    "urgent": 2,
    "legal": 6,
    "refund": 4,
}

# Output confidence defaults
CONF_ACCEPT = 85
CONF_NEEDS_INFO = 50
CONF_REJECT = 75

