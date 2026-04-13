import re

# Canonical region set used across all sources and the UI
CANONICAL_REGIONS = [
    "National",
    "NCR",
    "Ontario",
    "Quebec",
    "British Columbia",
    "Alberta",
    "Saskatchewan",
    "Manitoba",
    "New Brunswick",
    "Nova Scotia",
    "Prince Edward Island",
    "Newfoundland",
    "Northwest Territories",
    "Nunavut",
    "Yukon",
    "International",
    "Unknown",
]

# ── MERX ──────────────────────────────────────────────────────────────────────

# Province code → canonical region
_MERX_PROVINCE_CODE = {
    "ON": "Ontario",
    "QC": "Quebec",
    "BC": "British Columbia",
    "AB": "Alberta",
    "SK": "Saskatchewan",
    "MB": "Manitoba",
    "NB": "New Brunswick",
    "NS": "Nova Scotia",
    "PE": "Prince Edward Island",
    "NL": "Newfoundland",
    "NT": "Northwest Territories",
    "NU": "Nunavut",
    "YT": "Yukon",
    "CA": "National",   # "All of Canada, CA, CAN"
}

# Region strings that begin with "Ottawa" map to NCR
_MERX_NCR_PREFIX = ("Ottawa",)

# Whole-string overrides (lowercased) for entries without a province code
_MERX_WHOLE = {
    "canada": "National",
    "all of canada": "National",
    "ontario": "Ontario",
    "ontario, can": "Ontario",
    "southern ontario": "Ontario",
    "quebec": "Quebec",
    "quebec, can": "Quebec",
    "british columbia": "British Columbia",
    "british columbia, can": "British Columbia",
    "alberta": "Alberta",
    "alberta, can": "Alberta",
    "saskatchewan": "Saskatchewan",
    "saskatchewan, can": "Saskatchewan",
    "manitoba": "Manitoba",
    "manitoba, can": "Manitoba",
    "new brunswick": "New Brunswick",
    "new brunswick, can": "New Brunswick",
    "nova scotia": "Nova Scotia",
    "nova scotia, can": "Nova Scotia",
    "prince edward island": "Prince Edward Island",
    "prince edward island, can": "Prince Edward Island",
    "newfoundland and labrador": "Newfoundland",
    "newfoundland and labrador, can": "Newfoundland",
    "northwest territories": "Northwest Territories",
    "nunavut": "Nunavut",
    "yukon": "Yukon",
}


def normalize_merx_region(region_str: str) -> str:
    if not region_str:
        return "Unknown"

    s = region_str.strip()

    # Ottawa entries → NCR
    if s.startswith(_MERX_NCR_PREFIX):
        return "NCR"

    # Try to extract province code: ", XX, " or ", XX," at end
    match = re.search(r",\s*([A-Z]{2})\s*,", s)
    if match:
        code = match.group(1)
        if code in _MERX_PROVINCE_CODE:
            canonical = _MERX_PROVINCE_CODE[code]
            # Ottawa is ON but belongs to NCR — already caught above,
            # but guard here too just in case
            return canonical

    # Fall back to whole-string lookup
    return _MERX_WHOLE.get(s.lower().rstrip(",").strip(), "Unknown")


# ── CanadaBuys ────────────────────────────────────────────────────────────────

_CB_MAP = {
    # National
    "*canada":                              "National",

    # NCR
    "*national capital region (ncr)":       "NCR",
    "*ottawa":                              "NCR",

    # Ontario
    "*ontario (except ncr)":               "Ontario",
    "*barrie":                              "Ontario",
    "*gravenhurst":                         "Ontario",
    "*kingston":                            "Ontario",

    # Quebec
    "*quebec (except ncr)":                "Quebec",
    "*chambly":                             "Quebec",
    "*montréal":                            "Quebec",
    "*montreal":                            "Quebec",

    # British Columbia
    "*british columbia":                    "British Columbia",
    "*vancouver":                           "British Columbia",

    # Alberta
    "*alberta":                             "Alberta",
    "*banff":                               "Alberta",
    "*calgary":                             "Alberta",

    # Saskatchewan
    "*saskatchewan":                        "Saskatchewan",

    # Manitoba
    "*manitoba":                            "Manitoba",
    "*thompson":                            "Manitoba",

    # New Brunswick
    "*new brunswick":                       "New Brunswick",

    # Nova Scotia
    "*nova scotia":                         "Nova Scotia",
    "*halifax":                             "Nova Scotia",

    # Prince Edward Island
    "*prince edward island":               "Prince Edward Island",

    # Newfoundland
    "*newfoundland and labrador":           "Newfoundland",
    "*st. john's":                          "Newfoundland",
    "*st. johns":                           "Newfoundland",

    # Territories
    "*northwest territories":              "Northwest Territories",
    "*nunavut territory":                   "Nunavut",
    "*nunavut":                             "Nunavut",
    "*yukon":                               "Yukon",

    # International
    "*foreign":                             "International",
    "*world":                               "International",
    "*japan":                               "International",
    "*maryland":                            "International",

    # Unknown
    "*remote offsite":                      "Unknown",
    "*unspecified":                         "Unknown",
}


def normalize_canadabuys_region(region_str: str) -> str:
    if not region_str:
        return "Unknown"
    return _CB_MAP.get(region_str.strip().lower(), "Unknown")
