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
    "TARIFFS",
    "SANCTION",
    "SANCTIONS",
    "WAR",
    "MISSILE",
    "IRAN",
    "ISRAEL",
    "RUSSIA",
    "UKRAINE",
    "CHINA",
    "TAIWAN",
    "OPEC",
    "TRUMP",
]

RED = [
    "CPI",
    "PPI",
    "NFP",
    "FOMC",
    "RATE",
    "POWELL",
    "GDP",
    "PCE",
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
    "SNB",
    "RBA",
    "BOC",
]

def is_high_impact(headline: str):
    """
    Returns:
        (True, color)  -> if headline should be sent
        (False, None)  -> ignore
    """

    text = headline.upper()

    if not any(word in text for word in HIGH_IMPACT_KEYWORDS):
        return False, None

    if any(word in text for word in RED):
        return True, 0xE74C3C  # Red

    if any(word in text for word in ORANGE):
        return True, 0xF39C12  # Orange

    return True, 0xF1C40F      # Yellow
