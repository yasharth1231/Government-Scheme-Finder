"""Deterministic eligibility engine. No LLM, no API calls."""


def _num(v):
    try:
        return float(v) if v is not None and v != "" else None
    except (TypeError, ValueError):
        return None


def _list(v):
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def _open(values):
    vals = [str(x).lower() for x in values]
    return (not vals) or ("any" in vals) or ("all" in vals)


def evaluate(p, c):
    """p = citizen profile, c = scheme criteria. Returns (status, matched, failed, to_confirm)."""
    matched, failed = [], []

    mn, mx = _num(c.get("min_age")), _num(c.get("max_age"))
    if mn is not None or mx is not None:
        if (mn is not None and p["age"] < mn) or (mx is not None and p["age"] > mx):
            failed.append(f"Age {p['age']} is outside the allowed range "
                          f"({int(mn) if mn is not None else 'any'}-{int(mx) if mx is not None else 'any'})")
        else:
            matched.append(f"Age {p['age']} is within the allowed range")

    cap = _num(c.get("max_income"))
    if cap is not None:
        if p["income"] > cap:
            failed.append(f"Income ₹{p['income']:,} is above the limit of ₹{int(cap):,}")
        else:
            matched.append(f"Income ₹{p['income']:,} is within the limit of ₹{int(cap):,}")

    states = _list(c.get("states"))
    if not _open(states):
        if p["state"] in states:
            matched.append(f"Available in {p['state']}")
        else:
            failed.append(f"Not available in {p['state']} (applies to: {', '.join(states)})")

    occs = _list(c.get("occupations"))
    if not _open(occs):
        if p["occupation"] in occs:
            matched.append(f"Occupation '{p['occupation']}' is covered")
        else:
            failed.append(f"Occupation '{p['occupation']}' not covered (for: {', '.join(occs)})")

    gender = c.get("gender")
    if gender and str(gender).lower() != "any":
        if str(gender).lower() == p["gender"].lower():
            matched.append(f"Open to {p['gender']} applicants")
        else:
            failed.append(f"Only for {gender} applicants")

    cats = _list(c.get("categories"))
    if not _open(cats):
        if p["category"] in cats:
            matched.append(f"Category '{p['category']}' is covered")
        else:
            failed.append(f"Only for categories: {', '.join(cats)}")

    if c.get("requires_disability"):
        (matched if p["disability"] else failed).append("Disability requirement")
    if c.get("requires_bpl"):
        (matched if p["bpl"] else failed).append("BPL card requirement")

    to_confirm = [str(x) for x in _list(c.get("special_conditions"))]

    if failed:
        return "Not eligible", matched, failed, to_confirm
    if to_confirm:
        return "Possibly eligible", matched, failed, to_confirm
    return "Eligible", matched, failed, to_confirm
