import base64
import json
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict

import pymupdf  
from fastapi import UploadFile
from app.utils.openai.openai_caller import get_findings_from_llm

from app.core.config import settings

PRESENTATION_BATCH_SIZE = settings.PRESENTATION_BATCH_SIZE
PRESENTATION_MAX_WORKERS = settings.PRESENTATION_MAX_WORKERS

def build_chunk(pdf, start: int, end: int):
    chunk = pymupdf.open()
    for page_num in range(start, end):
        chunk.insert_pdf(pdf, from_page=page_num, to_page=page_num)
    return chunk

def encode_chunk_to_base64(chunk_pdf) -> str:
    buffer = BytesIO()
    chunk_pdf.save(buffer, garbage=4, clean=True)
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("utf-8")


def process_presentation_file(file_like: BytesIO, descrption: str) -> dict:
    """Split PDF, send chunks to LLM, merge all slide findings into one result."""
    file_like.seek(0)
    pdf = pymupdf.open(stream=file_like.read(), filetype="pdf")
    results: List[tuple[int, List[Dict]]] = []

    def process_chunk(start_page: int) -> tuple[int, List[Dict]]:
        chunk_pdf = build_chunk(pdf, start_page, min(start_page + PRESENTATION_BATCH_SIZE, pdf.page_count))
        encoded = encode_chunk_to_base64(chunk_pdf)
        filename = f"slides_{start_page + 1}_to_{start_page + PRESENTATION_BATCH_SIZE}.pdf"
        response = get_findings_from_llm(encoded, filename, descrption)
        return start_page, response.slides

    with ThreadPoolExecutor(max_workers=PRESENTATION_MAX_WORKERS) as executor:
        futures = {
            executor.submit(process_chunk, i): i
            for i in range(0, pdf.page_count, PRESENTATION_BATCH_SIZE)
        }
        for future in as_completed(futures):
            start_index, findings = future.result()
            results.append((start_index, findings))

    results.sort(key=lambda x: x[0])

    merged_slides = []
    for chunk_index, slides in results:
        for i, slide in enumerate(slides):
            slide.page = chunk_index + i
            merged_slides.append(slide)


    return {"slides": merged_slides}
