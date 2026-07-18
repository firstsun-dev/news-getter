DEEP_ANALYSIS_THRESHOLD = 60


def clamp(v: float) -> int:
    return max(0, min(100, round(v)))


def score_story(tiers: list[int], seen_count: int, distinct_sources: int) -> dict:
    authority = 100 - (min(tiers) - 1) * 25       # tier1→100, tier2→75, tier3→50, tier4→25
    confidence = clamp(authority * 0.7 + min(distinct_sources, 4) * 7.5)
    heat = clamp(min(seen_count, 6) * 12 + min(distinct_sources, 4) * 10)
    return {"confidence": confidence, "heat": heat}


def qualifies_for_deep_analysis(scores: dict) -> bool:
    return scores["confidence"] >= DEEP_ANALYSIS_THRESHOLD or scores["heat"] >= DEEP_ANALYSIS_THRESHOLD
