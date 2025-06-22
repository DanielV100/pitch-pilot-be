def calculate_eye_tracking(blendshapes: list[dict]) -> tuple[dict, float]:
    """
    Berechnet eine einfache Heatmap und einen Score aus Blendshapes.
    Annahme: Jeder Eintrag in blendshapes ist ein Dict mit Blickrichtungsschlüsseln.
    """
    # Beispiel: Wir nehmen an, es gibt keys wie "eyeLookUp", "eyeLookDown", "eyeLookLeft", "eyeLookRight"
    heatmap = {"up": 0, "down": 0, "left": 0, "right": 0, "center": 0}
    total = len(blendshapes)
    good_frames = 0

    for b in blendshapes:
        # Dummy-Logik: "center" wenn alle Richtungen < 0.2
        if all(b.get(k, 0) < 0.2 for k in ["eyeLookUp", "eyeLookDown", "eyeLookLeft", "eyeLookRight"]):
            heatmap["center"] += 1
            good_frames += 1
        else:
            if b.get("eyeLookUp", 0) > 0.2:
                heatmap["up"] += 1
            if b.get("eyeLookDown", 0) > 0.2:
                heatmap["down"] += 1
            if b.get("eyeLookLeft", 0) > 0.2:
                heatmap["left"] += 1
            if b.get("eyeLookRight", 0) > 0.2:
                heatmap["right"] += 1

    # Score: Anteil der Zeit, in der "center" gehalten wurde
    total_score = good_frames / total if total > 0 else 0.0

    return heatmap, total_score

def calculate_attention_score(blendshapes: list[dict]) -> float:
    """
    Berechnet einen Aufmerksamkeitsscore aus Blendshapes.
    Annahme: Jeder Eintrag in blendshapes ist ein Dict mit Blickrichtungsschlüsseln.
    Score = Anteil der Frames, in denen der Blick "zentriert" ist.
    """
    total = len(blendshapes)
    good_frames = 0
    for b in blendshapes:
        # "center" wenn alle Richtungen < 0.2
        if all(b.get(k, 0) < 0.2 for k in ["eyeLookUp", "eyeLookDown", "eyeLookLeft", "eyeLookRight"]):
            good_frames += 1
    return good_frames / total if total > 0 else 0.0