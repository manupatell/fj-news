HIGH_IMPACT_KEYWORDS = [
    "CPI",
    "CORE CPI",
    "PPI",
    "CORE PPI",
    "NFP",
    "NONFARM",
    "PAYROLL",
    "GDP",
    "PCE",
    "CORE PCE",
    "PMI",
    "ISM",
    "JOLTS",
    "JOBLESS",
    "UNEMPLOYMENT",
    "RETAIL SALES",
    "RATE DECISION",
    "INTEREST RATE",
    "FOMC",
    "FED",
    "POWELL",
    "ECB",
    "BOE",
    "BOJ",
    "SNB",
    "RBA",
    "RBNZ",
    "BOC",
    "LAGARDE",
    "BAILEY",
    "UEDA",
    "BREAKING",
    "TARIFF",
    "SANCTION",
    "WAR",
    "MISSILE",
    "IRAN",
    "ISRAEL",
    "RUSSIA",
    "UKRAINE",
    "CHINA",
    "TAIWAN",
    "OPEC",
    "TRUMP"
]

RED = [
    "CPI",
    "NFP",
    "RATE",
    "FOMC",
    "POWELL",
    "PPI",
    "GDP",
    "PCE"
]

ORANGE = [
    "PMI",
    "ISM",
    "JOLTS",
    "JOBLESS",
    "RETAIL",
    "ECB",
    "BOE",
    "BOJ",
]

def is_high_impact(text: str):
    t = text.upper()

    if not any(k in t for k in HIGH_IMPACT_KEYWORDS):
        return False, None

    if any(k in t for k in RED):
        return True, 0xFF0000

    if any(k in t for k in ORANGE):
        return True, 0xFFA500

    return True, 0xFFD700
