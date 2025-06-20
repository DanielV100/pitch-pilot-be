from app.core.config import settings

def read_env_score_config():
    return {
        "ideal_wpm": settings.SCORE_IDEAL_WPM,
        "max_wpm_deviation": settings.SCORE_WPM_DEVIATION,
        "ideal_dbfs": settings.SCORE_IDEAL_DBFS,
        "dbfs_margin": settings.SCORE_DBFS_MARGIN,
        "filler_threshold": settings.SCORE_FILLER_RATIO_THRESHOLD,
        "weights": {
            "speaking": settings.SCORE_WEIGHT_SPEAKING,
            "volume": settings.SCORE_WEIGHT_VOLUME,
            "filler": settings.SCORE_WEIGHT_FILLER,
            "clarity": settings.SCORE_WEIGHT_CLARITY,
            "engagement": settings.SCORE_WEIGHT_ENGAGEMENT,
        }
    }

def speaking_pace_score(wpm: float, config: dict) -> int:
    ideal = config["ideal_wpm"]
    deviation = config["max_wpm_deviation"]
    diff = abs(wpm - ideal)
    if diff >= deviation:
        return 0
    return round((1 - (diff / deviation)) * 100)

def volume_score(avg_dbfs: float, config: dict) -> int:
    ideal = config["ideal_dbfs"]
    margin = config["dbfs_margin"]
    diff = abs(avg_dbfs - ideal)
    if diff >= margin:
        return 0
    return round((1 - (diff / margin)) * 100)

def filler_ratio_score(ratio: float, config: dict) -> int:
    threshold = config["filler_threshold"]
    if ratio >= threshold:
        return 0
    return round((1 - (ratio / threshold)) * 100)

def total_score(
    speaking_score: int,
    volume_score_: int,
    filler_score: int,
    clarity_score: int,
    engagement_rating: int,
    config: dict
) -> int:
    w = config["weights"]
    weighted_sum = (
        speaking_score * w["speaking"] +
        volume_score_ * w["volume"] +
        filler_score * w["filler"] +
        clarity_score * w["clarity"] +
        engagement_rating * w["engagement"]
    )
    return round(weighted_sum)
