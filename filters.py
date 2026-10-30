"""
USD-only high-impact filter.

A headline is sent only if ALL of these are true:
  1. It is NOT noise (T-bill auctions, earnings, FJElite blurbs, ...)
  2. It is NOT about a non-US country / central bank (Italian CPI, ECB, ...)
  3. It matches a HIGH-IMPACT USD pattern (US data release, Fed, FOMC,
     Fed chair/speakers, Treasury Sec., Trump on tariffs/Fed/rates, ...)

Returns (True, color) or (False, None) -- same contract as before.
"""

import re

RED_COLOR = 0xE74C3C
ORANGE_COLOR = 0xF39C12
YELLOW_COLOR = 0xF1C40F


def _rx(words):
    return re.compile(r"\b(?:" + "|".join(words) + r")\b", re.I)


# ---- 1. noise: never send -------------------------------------------------
NOISE = _rx([
    r"FJElite", r"Earnings", r"Q[1-4] 20\d\d", r"bids? for", r"bills?",
    r"auction", r"Treasury to sell", r"settles?", r"Effective Fed Funds",
    r"options? expiries", r"Fear (?:&|and) Greed", r"implied volatility",
    r"Currency Strength", r"WATCH LIVE", r"concludes", r"ends? (?:press|remarks)",
    r"press conference has ended", r"reverse repos?", r"repo operation",
])

# ---- 2. non-US subjects: never send (unless a USD marker is also present
#         AND the headline is about the Fed/US itself -- see below) ----------
FOREIGN = _rx([
    r"ECB", r"Lagarde", r"Eurozone", r"Euro ?area", r"EU", r"German\w*",
    r"France", r"French", r"Ital\w+", r"Spanish", r"Spain", r"Dutch",
    r"UK", r"Britain", r"British", r"BoE", r"BOE", r"Bailey",
    r"Japan\w*", r"BoJ", r"BOJ", r"Ueda", r"Swiss", r"SNB",
    r"Australia\w*", r"RBA", r"New Zealand", r"NZ", r"RBNZ", r"NBNZ",
    r"Canad\w+", r"BoC", r"BOC", r"China", r"Chinese", r"PBOC", r"Taiwan",
    r"South Korea\w*", r"S\.Korea\w*", r"Korean", r"India\w*", r"Russia\w*",
    r"Swed\w+", r"Norw\w+", r"Saxony", r"Bavaria", r"North[- ]Rhine",
    r"Turkey", r"Turkish", r"Brazil\w*", r"Mexic\w+", r"Tokyo", r"Madrid",
    r"London", r"Paris", r"Berlin", r"Seoul", r"Sydney", r"Hong Kong", r"Singapore",
])

# ---- 3. US markers --------------------------------------------------------
US_MARKER = _rx([
    r"US", r"U\.S\.", r"USD", r"America\w*", r"Fed", r"Fed's", r"FOMC",
    r"Powell", r"Warsh", r"Bessent", r"Treasury Secretary", r"Trump",
    r"White House", r"WH", r"Hassett", r"Vance", r"Bowman", r"Waller",
    r"Jefferson", r"Williams", r"Musalem", r"Goolsbee", r"Kashkari",
    r"Logan", r"Hammack", r"Schmid", r"Daly", r"Bostic", r"Barr", r"Cook",
    r"Miran", r"Collins", r"Harker", r"Barkin", r"Paulson", r"Lutnick",
    r"Greer",
])

# ---- 4. HIGH-IMPACT USD patterns (tier, color) ----------------------------
# Data releases: FJ posts US data without a country prefix, with "Actual".
US_DATA = _rx([
    r"CPI", r"Core CPI", r"PPI", r"Core PPI", r"PCE", r"Core PCE",
    r"Non-?Farm Payrolls?", r"NFP", r"ADP", r"Unemployment Rate",
    r"Initial Jobless Claims", r"Continuing Jobless Claims", r"JOLTS",
    r"GDP", r"GDP Price Index", r"ISM [\w\- ]*PMI", r"ISM [\w\- ]*Index",
    r"S&P Global [\w\- ]*PMI", r"Retail Sales", r"Durable Goods",
    r"Michigan[\w\- ]*(?:Sentiment|Inflation)", r"Consumer Confidence",
    r"Average Hourly Earnings", r"Employment Cost Index", r"Trade Balance",
    r"Housing Starts", r"Existing Home Sales", r"New Home Sales",
    r"Industrial Production", r"Philadelphia Fed", r"Empire State",
    r"Core Retail Sales", r"Personal (?:Income|Spending)",
    r"Fed Funds Rate", r"Fed Interest Rate Decision",
])
HAS_ACTUAL = re.compile(r"\bActual\b", re.I)

FED_RED = _rx([
    r"FOMC", r"Fed rate decision", r"Fed holds", r"Fed cuts", r"Fed hikes",
    r"rate (?:cut|hike|decision)", r"Powell", r"Warsh", r"Fed Chair",
    r"Federal Reserve", r"Fed funds",
])
FED_SPEAKER = _rx([r"Fed's", r"Fed (?:Governor|Gov\.?|Vice Chair|President)",
                   r"Fed officials?", r"Fed minutes", r"Beige Book",
                   r"Fed [A-Z][a-z]+:"])
US_POLICY = _rx([
    r"tariffs?", r"sanctions?", r"debt ceiling", r"government shutdown",
    r"shutdown", r"executive order", r"Section 232", r"Section 301",
])
TRUMP = _rx([r"Trump"])
TRUMP_TOPIC = _rx([r"tariffs?", r"Fed", r"Powell", r"Warsh", r"rates?",
                   r"inflation", r"trade deal", r"dollar", r"tax(?:es)?"])
OFFICIAL = _rx([r"Bessent", r"Treasury Secretary", r"Hassett", r"Lutnick", r"Greer"])
OFFICIAL_TOPIC = _rx([r"Fed", r"rates?", r"inflation", r"tariffs?", r"GDP",
                      r"yields?", r"dollar", r"jobs?", r"deficit", r"debt",
                      r"sanctions?", r"trade"])


# ---- XAUUSD (gold) --------------------------------------------------------
GOLD = _rx([r"gold", r"XAU\w*", r"bullion", r"precious metals?",
            r"safe[- ]haven"])
YIELDS = _rx([r"10-?(?:yr|year)", r"Treasury yields?", r"US yields?",
              r"real yields?", r"DXY", r"dollar index"])

# ---- MNQ (Nasdaq futures) -------------------------------------------------
NASDAQ = _rx([r"Nasdaq", r"MNQ", r"NQ", r"S&P 500 futures", r"S&P futures",
              r"US stock futures", r"Dow futures", r"tech stocks?"])
MEGACAP = _rx([r"Nvidia", r"NVDA", r"Microsoft", r"MSFT", r"Apple", r"AAPL",
               r"Alphabet", r"Google", r"GOOGL", r"Amazon", r"AMZN", r"Meta",
               r"Tesla", r"TSLA", r"Broadcom", r"AVGO", r"AMD", r"TSMC",
               r"OpenAI", r"Anthropic"])
MEGA_EVENT = _rx([r"shares? (?:fall|drop|jump|surge|plunge|rise|slide|tumble)s?",
                  r"guidance", r"export (?:controls?|curbs?|ban)",
                  r"downgrades?", r"upgrades?", r"beats?", r"misses?",
                  r"plunges?", r"soars?", r"tumbles?", r"slumps?"])

# ---- geopolitics that moves gold / risk (toggle) --------------------------
GEOPOLITICS = True
GEO = _rx([r"Iran", r"Hormuz", r"Israel", r"Taiwan"])
GEO_EVENT = _rx([r"cease-?fire", r"peace deal", r"deal", r"strikes?",
                 r"attacks? on", r"missiles?", r"escalat\w+", r"blockade",
                 r"retaliat\w+"])


def classify(headline: str):
    """Return (level, tag) or (None, None).
    level: 'red' | 'orange' | 'yellow'"""
    h = headline.strip()

    if NOISE.search(h):
        return None, None

    # ---- gold: any gold headline counts (even from non-US sources) ----
    if GOLD.search(h):
        return "orange", "GOLD"

    # ---- Nasdaq / MNQ ----
    if NASDAQ.search(h):
        return "orange", "NASDAQ"
    if MEGACAP.search(h) and MEGA_EVENT.search(h):
        return "yellow", "NASDAQ"

    # ---- geopolitics (gold / risk-off driver) ----
    if GEOPOLITICS and GEO.search(h) and GEO_EVENT.search(h):
        return "yellow", "GEOPOLITICS"

    us = bool(US_MARKER.search(h))
    foreign = bool(FOREIGN.search(h))

    # Non-US subject with no US marker -> not USD news.
    if foreign and not us:
        return None, None

    # US economic data release
    if US_DATA.search(h) and HAS_ACTUAL.search(h) and not foreign:
        return "red", "USD DATA"

    # FOMC / Fed chair / policy decisions
    if FED_RED.search(h) and not foreign:
        return "red", "FED"

    # Fed speakers / minutes
    if FED_SPEAKER.search(h):
        return "orange", "FED SPEAKER"

    # US yields / dollar index
    if YIELDS.search(h) and not foreign:
        return "orange", "YIELDS"

    # US officials (Bessent, Hassett, ...) only when talking markets/policy
    if OFFICIAL.search(h) and OFFICIAL_TOPIC.search(h) and not foreign:
        return "orange", "US POLICY"

    # tariffs / sanctions / shutdown
    if US_POLICY.search(h) and (us or not foreign):
        return "orange", "US POLICY"

    # Trump, only when it touches markets
    if TRUMP.search(h) and TRUMP_TOPIC.search(h):
        return "yellow", "TRUMP"

    return None, None


_COLORS = {"red": RED_COLOR, "orange": ORANGE_COLOR, "yellow": YELLOW_COLOR}


def is_high_impact(headline: str):
    """
    Returns:
        (True, color)  -> USD high-impact headline, send it
        (False, None)  -> ignore
    """
    level, _tag = classify(headline)
    if level is None:
        return False, None
    return True, _COLORS[level]


def get_tag(headline: str):
    """Category label for the headline (GOLD, NASDAQ, USD DATA, FED, ...)."""
    return classify(headline)[1]
