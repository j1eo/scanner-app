# logic_evaluator.py
def evaluate_action(guideline, *, fill_level, seal_status, cleanliness_score, label_status, bottle_condition):
    # normalize
    seal = (seal_status or "").lower()
    cond = (bottle_condition or "").lower()
    label = (label_status or "").lower()

    min_fill = float(guideline.min_fill_level_threshold)
    min_clean = int(guideline.min_cleanliness_score)

    # allowed values
    def allow(value, allowed):
        allowed = (allowed or "any").lower()
        if allowed == "any":
            return True
        return value == allowed

    ok_fill = float(fill_level) >= min_fill
    ok_clean = int(cleanliness_score) >= min_clean
    ok_seal = allow(seal, guideline.allowed_seal_status)
    ok_cond = allow(cond, guideline.allowed_bottle_condition)
    label_intact_required = "intact" in (guideline.label_requirements or "").lower()
    label_ok = ("intact" in label) if label_intact_required else True

    # Decision logic (mutually exclusive, ordered)
    if ok_fill and ok_clean and ok_seal and ok_cond and label_ok:
        return "Keep"

    # Refill window: slightly below threshold & still hygienic
    if (min_fill - 20) <= float(fill_level) < min_fill and ok_clean and seal in ("sealed", "resealed"):
        return "Refill"

    # Replace: hygiene ok-ish but presentation bad
    if int(cleanliness_score) >= max(min_clean - 1, 0) and ("damaged" in label or "torn" in label or cond == "fair"):
        return "Replace"

    # Otherwise
    return "Discard"
