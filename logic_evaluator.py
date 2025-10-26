# logic_evaluator.py
from sqlalchemy import select
from models import GuidelineTemplate

def evaluate_action(db, *, airline_id, liquor_type, service_class,
                    fill_level, cleanliness_score, seal_status, bottle_condition):
    """
    Evaluate bottle inspection data against airline guidelines.
    Cleanliness: 1–10 scale
    Fill level: 0–100 scale
    """

    stmt = select(GuidelineTemplate).where(
        GuidelineTemplate.airline_id == airline_id,
        GuidelineTemplate.liquor_type == liquor_type,
        GuidelineTemplate.service_class == service_class,
        GuidelineTemplate.is_active == True
    )

    rules = db.execute(stmt).scalars().all()
    if not rules:
        return {"action": "UNKNOWN", "reason": "No guideline found."}

    # Normalize input
    try:
        fill_level = float(fill_level)
        cleanliness_score = int(cleanliness_score)
    except Exception:
        return {"action": "ERROR", "reason": "Invalid numeric values."}

    seal_status = (seal_status or "").lower()
    bottle_condition = (bottle_condition or "").lower()

    # Sort by stricter fill threshold first
    rules = sorted(rules, key=lambda g: g.min_fill_level_threshold, reverse=True)

    for g in rules:
        if (
            cleanliness_score >= g.min_cleanliness_score
            and seal_status in g.allowed_seal_status
            and bottle_condition in g.allowed_bottle_condition
            and fill_level >= g.min_fill_level_threshold
        ):
            return {
                "action": g.recommended_action,
                "guideline_id": g.guideline_id
            }

    return {"action": "DISCARD", "reason": "No matching rule; discard enforced."}
