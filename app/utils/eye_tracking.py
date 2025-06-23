import logging

def calculate_eye_tracking(blendshapes: list[dict], grid_size: int = 40) -> tuple[dict, float]:
    """
    Berechnet eine 2D-Heatmap und einen Attention-Score aus Blendshapes.
    Jeder Eintrag in blendshapes ist ein Dict mit Blickrichtungsschlüsseln.
    Die Heatmap ist ein Dict mit "x,y"-Keys (Grid).
    """
    logging.debug(f"Calculating eye tracking from {len(blendshapes)} blendshapes (2D-Heatmap)")
    heatmap = {}
    total = len(blendshapes)
    good_frames = 0

    for b in blendshapes:
        # Blickvektor berechnen
        x = (b.get("eyeLookRight", 0) - b.get("eyeLookLeft", 0))
        y = (b.get("eyeLookUp", 0) - b.get("eyeLookDown", 0))
        # Normierung auf 0..1 (optional, je nach Range der Werte)
        # Hier: Wertebereich -1..1 auf 0..1 mappen
        x_norm = (x + 1) / 2
        y_norm = (y + 1) / 2
        # Auf Grid mappen
        gx = min(grid_size - 1, max(0, int(x_norm * (grid_size - 1))))
        gy = min(grid_size - 1, max(0, int(y_norm * (grid_size - 1))))
        key = f"{gx},{gy}"
        heatmap[key] = heatmap.get(key, 0) + 1
        # Attention-Score: "center" wenn alle Richtungen < 0.2
        if all(b.get(k, 0) < 0.2 for k in ["eyeLookUp", "eyeLookDown", "eyeLookLeft", "eyeLookRight"]):
            good_frames += 1

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