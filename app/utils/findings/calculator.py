# app/utils/finding_scoring.py
from app.core.config import settings

def filter_findings(findings: dict) -> dict:
    slides = findings.get("slides", [])
    new_slides = []

    for slide in slides:
        # Convert slide to a dict (non-destructive if already a dict)
        slide_dict = slide.model_dump() if hasattr(slide, "model_dump") else dict(slide)

        # Filter findings using attribute access
        filtered_findings = [
            f.model_dump() if hasattr(f, "model_dump") else f
            for f in slide.findings
            if f.importance + f.confidence >= 18
        ]

        if filtered_findings:
            slide_dict["findings"] = filtered_findings
            new_slides.append(slide_dict)

    return {"slides": new_slides}




def calculate_scores(findings: dict) -> dict:
    slides = findings.get("slides", [])
    print(f"Calculating scores for {len(slides)} slides")
    categories = {1: [], 2: [], 3: [], 4: []}

    for slide in slides:
        for f in slide.get("findings", []):
            categories[f["type"]].append(f)


    print(f"Categories: {categories}")

    def score_for(category):
        items = categories[category]
        if not items:
            return 100.0
        avg_severity = sum(f["severity"] for f in items) / len(items)
        return max(0.0, 100.0 - avg_severity)

    preflight_score = score_for(1)
    altitude_score = score_for(2)
    flight_path_score = score_for(3)
    cockpit_score = score_for(4)

    total = (
        preflight_score * settings.FINDING_WEIGHT_PREFLIGHT +
        altitude_score * settings.FINDING_WEIGHT_ALTITUDE +
        flight_path_score * settings.FINDING_WEIGHT_FLIGHT_PATH +
        cockpit_score * settings.FINDING_WEIGHT_COCKPIT
    )

    return {
        "total_score": round(total, 2),
        "preflight_check_score": round(preflight_score, 2),
        "altitude_score": round(altitude_score, 2),
        "flight_path_score": round(flight_path_score, 2),
        "cockpit_score": round(cockpit_score, 2),
    }
