import json
import math

def blendshape_array_to_dict(blendshape_arr):
    """
    Wandelt ein Array von Blendshape-Objekten in ein Dict mit Blickrichtungsschlüsseln um.
    """
    def get_score(name):
        for b in blendshape_arr:
            if b.get("categoryName") == name:
                return b.get("score", 0.0)
        return 0.0

    result = {
        "eyeLookUpLeft": get_score("eyeLookUpLeft"),
        "eyeLookUpRight": get_score("eyeLookUpRight"),
        "eyeLookDownLeft": get_score("eyeLookDownLeft"),
        "eyeLookDownRight": get_score("eyeLookDownRight"),
        "eyeLookInLeft": get_score("eyeLookInLeft"),
        "eyeLookInRight": get_score("eyeLookInRight"),
        "eyeLookOutLeft": get_score("eyeLookOutLeft"),
        "eyeLookOutRight": get_score("eyeLookOutRight"),
        "eyeSquintLeft": get_score("eyeSquintLeft"),
        "eyeSquintRight": get_score("eyeSquintRight"),
        "mouthSmileLeft": get_score("mouthSmileLeft"),
        "mouthSmileRight": get_score("mouthSmileRight"),
        "browInnerUp": get_score("browInnerUp"),
        "mouthFrownLeft": get_score("mouthFrownLeft"),
        "mouthFrownRight": get_score("mouthFrownRight"),
        "browDownLeft": get_score("browDownLeft"),
        "browDownRight": get_score("browDownRight"),
        "jawOpen": get_score("jawOpen"),
    }
    result["eyeLookUp"] = (result["eyeLookUpLeft"] + result["eyeLookUpRight"]) / 2
    result["eyeLookDown"] = (result["eyeLookDownLeft"] + result["eyeLookDownRight"]) / 2
    result["eyeLookLeft"] = (result["eyeLookOutLeft"] + result["eyeLookInRight"]) / 2
    result["eyeLookRight"] = (result["eyeLookInLeft"] + result["eyeLookOutRight"]) / 2
    return result

def parse_blendshape_entry(entry):
    """
    Wandelt einen Frame (`scores`-Liste) in ein verarbeitbares Dictionary um.
    """
    if isinstance(entry, list):
        return blendshape_array_to_dict(entry)    
    elif isinstance(entry, str):
        try:
            return blendshape_array_to_dict(json.loads(entry))
        except Exception:
            return {}
    elif isinstance(entry, dict):
        return entry
    return {}


def calculate_eye_tracking(blendshapes: list, grid_size: int = 40) -> tuple[dict, float]:
    """
    Berechnet EINE 2D-Heatmap der Blickrichtung.
    Gibt nur noch die Heatmap und einen Dummy-Score von 0.0 zurück, 
    da der echte Score jetzt von calculate_attention_score berechnet wird.
    """
    processed_frames = []
    for frame in blendshapes:
        scores_list = frame.get("scores")
        if not scores_list:
            continue
        d = parse_blendshape_entry(scores_list)
        if d:
            processed_frames.append(d)

    if not processed_frames:
        return {}, 0.0

    heatmap = {}
    for b in processed_frames:
        x_gaze = b.get("eyeLookRight", 0) - b.get("eyeLookLeft", 0)
        y_gaze = b.get("eyeLookUp", 0) - b.get("eyeLookDown", 0)

        x_norm = (x_gaze + 1) / 2
        y_norm = (y_gaze + 1) / 2

        gx = min(grid_size - 1, max(0, int(x_norm * (grid_size - 1))))
        gy = min(grid_size - 1, max(0, int(y_norm * (grid_size - 1))))

        key = f"{gx},{gy}"
        heatmap[key] = heatmap.get(key, 0) + 1
    return heatmap, 0.0



def calculate_attention_score(blendshapes: list) -> float:
    """
    Berechnet einen fortgeschrittenen, mehrdimensionalen Aufmerksamkeitsscore.
    Der Score kombiniert drei Faktoren für jeden Frame:
    1. Gaze Focus: Blickrichtung (zentriert ist besser).
    2. Positive Engagement: Anzeichen für Interesse (Lächeln, Konzentration).
    3. Negative Engagement: Anzeichen für Ablenkung (Stirnrunzeln, Verwirrung).
    
    Der finale Score ist der Durchschnitt über alle Frames.
    """
    processed_frames = []
    for frame in blendshapes:
        scores_list = frame.get("scores")
        if not scores_list:
            continue
        parsed_data = parse_blendshape_entry(scores_list)
        if parsed_data:
            processed_frames.append(parsed_data)

    if not processed_frames:
        return 0.0

    frame_scores = []
    for b in processed_frames:
        x_gaze = b.get("eyeLookRight", 0) - b.get("eyeLookLeft", 0)
        y_gaze = b.get("eyeLookUp", 0) - b.get("eyeLookDown", 0)
        magnitude = math.sqrt(x_gaze**2 + y_gaze**2)
        normalized_magnitude = min(1.0, magnitude / 1.414)
        gaze_focus_score = 1.0 - normalized_magnitude
        smile = (b.get("mouthSmileLeft", 0) + b.get("mouthSmileRight", 0)) / 2
        brow_up = b.get("browInnerUp", 0)
        eye_squint = (b.get("eyeSquintLeft", 0) + b.get("eyeSquintRight", 0)) / 2
        positive_score = (0.5 * smile) + (0.25 * brow_up) + (0.25 * eye_squint)
        positive_score = min(1.0, positive_score)
        frown = (b.get("mouthFrownLeft", 0) + b.get("mouthFrownRight", 0)) / 2
        brow_down = (b.get("browDownLeft", 0) + b.get("browDownRight", 0)) / 2
        jaw_open = b.get("jawOpen", 0)
        negative_score = (0.5 * frown) + (0.3 * brow_down) + (0.2 * jaw_open)
        negative_score = min(1.0, negative_score)
        final_score = (0.6 * gaze_focus_score + 0.4 * positive_score) * (1.0 - negative_score)
        frame_scores.append(final_score)
    total_attention_score = sum(frame_scores) / len(frame_scores) if frame_scores else 0.0
    return total_attention_score