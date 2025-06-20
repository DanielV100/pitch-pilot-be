import json
import os
import pathlib
import math
import numpy as np
import soundfile as sf
from typing import TypedDict
from faster_whisper import WhisperModel
from app.core.config import settings
from ctranslate2 import get_cuda_device_count
import ffmpeg
from app.utils.openai.openai_caller import get_audio_feedback_from_llm
from app.utils.audio.audio_score_calculator import (
    read_env_score_config,
    speaking_pace_score,
    volume_score,
    filler_ratio_score,
    total_score,
)
from concurrent.futures import ThreadPoolExecutor

_whisper_model = None

def get_whisper_model() -> WhisperModel:
    global _whisper_model
    if _whisper_model is None:
        use_cuda = get_cuda_device_count() > 0
        _whisper_model = WhisperModel(
            settings.WHISPER_MODEL_NAME or "distil-large-v3",
            device="cuda" if use_cuda else "cpu",
            compute_type="float16" if use_cuda else "int8",
        )
    return _whisper_model

class Analysis(TypedDict):
    transcript: dict
    wpm: float
    avg_volume_dbfs: float
    duration: float
    volume_timeline: list[dict]
    fillers: list[dict]
    questions: list[str]
    formulation_aids: list[dict]
    clarity_score: float
    engagement_rating: float
    filler_ratio: float
    filler_score: float
    speaking_score: float
    volume_score: float
    total_score: float

def extract_transcript_and_words(path: str | pathlib.Path):
    model = get_whisper_model()
    segments, info = model.transcribe(
        str(path), beam_size=1, vad_filter=True, word_timestamps=True
    )
    transcript_words = []
    transcript_full_text = []
    words_total = 0
    for seg in segments:
        transcript_full_text.append(seg.text.strip())
        for word in seg.words:
            w = word.word.strip(".,?!")
            words_total += 1
            transcript_words.append({
                "start": word.start,
                "end": word.end,
                "word": w,
            })
    duration = info.duration
    wpm = words_total / (duration / 60) if duration else 0
    transcript_text = " ".join(transcript_full_text)
    return transcript_text, transcript_words, duration, wpm

def extract_audio_volume(path: str | pathlib.Path):
    pcm_path = pathlib.Path(path).with_suffix(".wav")
    try:
        (
            ffmpeg.input(str(path))
            .output(str(pcm_path), ac=1, ar=16000, format="wav")
            .overwrite_output()
            .run(quiet=True)
        )
        audio, sr = sf.read(pcm_path)
        rms = float(np.sqrt(np.mean(audio ** 2)))
        avg_dbfs = 20 * math.log10(rms) if rms > 0 else float("-inf")

        chunk_duration = 0.1
        samples_per_chunk = int(sr * chunk_duration)
        volume_timeline = []
        for i in range(0, len(audio), samples_per_chunk):
            chunk = audio[i:i + samples_per_chunk]
            chunk_rms = np.sqrt(np.mean(chunk ** 2)) if len(chunk) else 0
            chunk_dbfs = 20 * math.log10(chunk_rms) if chunk_rms > 0 else -100
            volume_timeline.append({
                "t": round(i / sr, 2),
                "rms": round(float(chunk_rms), 6),
                "dbfs": round(chunk_dbfs, 1),
            })
        os.remove(pcm_path)
        return avg_dbfs, volume_timeline
    except Exception as e:
        print(f"Error processing audio file {path}: {type(e)} - {e}")
        import traceback
        traceback.print_exc()
        return -99.0, []

def analyse_local_file(path: str | pathlib.Path) -> Analysis:
    with ThreadPoolExecutor() as executor:
        futures = {
            "transcript": executor.submit(extract_transcript_and_words, path),
            "volume": executor.submit(extract_audio_volume, path),
        }
        results = {key: future.result() for key, future in futures.items()}

    transcript_text, transcript_words, duration, wpm = results["transcript"]
    avg_dbfs, volume_timeline = results["volume"]
    feedback = get_audio_feedback_from_llm(transcript_text)

    clarity = feedback.get("clarity_score", 0)
    engagement = feedback.get("engagement_rating", 0)

    cfg = read_env_score_config()
    speaking = speaking_pace_score(wpm, cfg)
    volume = volume_score(avg_dbfs, cfg)
    filler_count = sum(f["count"] for f in feedback["fillers"])
    filler_ratio_val = filler_count / len(transcript_words) if transcript_words else 0
    filler_score_val = filler_ratio_score(filler_ratio_val, cfg)

    total = total_score(clarity, engagement, speaking, volume, filler_score_val, cfg)

    return {
        "transcript": {
            "full_text": transcript_text,
            "words": transcript_words
        },
        "wpm": round(wpm, 1),
        "avg_volume_dbfs": round(avg_dbfs, 1),
        "duration": round(duration, 2),
        "volume_timeline": volume_timeline,
        "fillers": feedback["fillers"],
        "questions": feedback["questions"],
        "formulation_aids": feedback["formulation_aids"],
        "clarity_score": clarity,
        "engagement_rating": engagement,
        "filler_ratio": round(filler_ratio_val, 3),
        "filler_score": round(filler_score_val, 1),
        "speaking_score": round(speaking, 1),
        "volume_score": round(volume, 1),
        "total_score": total, 
        "total_words": len(transcript_words)
    }
