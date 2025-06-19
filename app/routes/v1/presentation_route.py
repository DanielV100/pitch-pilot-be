from typing import List
from fastapi import APIRouter, Depends, File, Form, HTTPException, status, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_session
from app.services.presentation.presentation_service import PresentationService
from app.schemas.presentation_schema import PresentationCreate, PresentationOut
from app.models.user_model import User
from app.dependencies.auth_dep import get_current_user
from app.models.presentation_model import Presentation, PresentationFinding, Training
from sqlalchemy.orm import selectinload
from app.utils.minio_helper import upload_file_to_minio
from uuid import UUID
from app.utils.findings.findings_generator import process_presentation_file
from app.services.findings.findings_service import FindingService
from app.utils.findings.calculator import filter_findings

router = APIRouter()

from io import BytesIO

@router.post("/add-presentation", response_model=PresentationOut, status_code=status.HTTP_201_CREATED)
async def create_presentation(
    name: str = Form(...),
    description: str = Form(...),
    tags: List[str] = Form(...),
    file: UploadFile = File(...), 
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    file_bytes = await file.read()  
    file_buffer = BytesIO(file_bytes)
    file_url = upload_file_to_minio(file=file) 
    print(f"File uploaded to MinIO: {file_url}")

    
    findings_result = process_presentation_file(BytesIO(file_bytes), descrption=description)  

    presentation_service = PresentationService(db)
    presentation = await presentation_service.create_presentation(
        user_id=current_user.id,
        data={
            "name": name,
            "description": description,
            "tags": tags,
            "file_url": file_url
        }
    )

    filtered_findings = filter_findings(findings_result)
    finding_service = FindingService(db)
    await finding_service.create_finding(
        presentation_id=presentation.id,
        findings=filtered_findings,
        is_active=True
    )

    return presentation




@router.get("/get-presentations", response_model=list[PresentationOut])
async def get_presentations_for_current_user(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Presentation)
        .where(Presentation.user_id == current_user.id)
        .options(selectinload(Presentation.trainings)) 
    )
    return result.scalars().all()


@router.get("/{presentation_id}/get-presentation", response_model=PresentationOut)
async def get_presentation_by_id(
    presentation_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Presentation).where(
            Presentation.id == presentation_id,
            Presentation.user_id == current_user.id
        )
    )
    presentation = result.scalar_one_or_none()

    if not presentation:
        raise HTTPException(status_code=404, detail="Presentation not found or not yours")

    await db.refresh(presentation, ["trainings"])
    return presentation

@router.get("/{presentation_id}/get-active-finding")
async def get_active_finding(
    presentation_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(PresentationFinding)
        .where(
            PresentationFinding.presentation_id == presentation_id,
            PresentationFinding.is_active.is_(True)
        )
    )
    finding = result.scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=404, detail="No active finding found for this presentation")

    return finding

@router.get("/{presentation_id}/get-finding-bars")
async def get_finding_bars(
    presentation_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(PresentationFinding)
        .where(
            PresentationFinding.presentation_id == presentation_id,
            PresentationFinding.is_active.is_(True)
        )
    )
    finding = result.scalar_one_or_none()

    if not finding:
        raise HTTPException(status_code=404, detail="No active finding found for this presentation")

    if hasattr(finding.findings, "model_dump"):
        findings_dict = finding.findings.model_dump()
    else:
        findings_dict = finding.findings

    slides = findings_dict.get("slides", [])
    type_map = {1: "Pre flight", 2: "Altitude", 3: "Flight path", 4: "Cockpit"}
    buckets = []

    for slide in slides:
        for f in slide.get("findings", []):
            buckets.append({
                "type": type_map.get(f["type"], "Unknown"),
                "importance": f["importance"],
                "confidence": f["confidence"],
                "severity": f["severity"],
            })

    return buckets
