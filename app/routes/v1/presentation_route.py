from typing import List
from fastapi import APIRouter, Depends, File, Form, HTTPException, status, UploadFile
from sqlalchemy import select, desc
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
from app.models.presentation_model import TrainingResult
from app.schemas.presentation_schema import LatestTrainingAnalyticsOut


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
    file_url = upload_file_to_minio(
        file_buffer=file_buffer,  
        filename=file.filename,
        content_type=file.content_type,
    )

    
    findings_result = process_presentation_file(file_buffer, descrption=description)  

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
    await db.commit()

    result = await db.execute(
        select(Presentation)
        .options(
            selectinload(Presentation.trainings),
            selectinload(Presentation.finding_entries),
        )
        .where(Presentation.id == presentation.id)
    )
    presentation_full = result.scalar_one()

    return presentation_full




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

@router.get("/{presentation_id}/get-file-url", response_model=dict)
async def get_presentation_file_url(
    presentation_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
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

    if not presentation.file_url:
        raise HTTPException(status_code=404, detail="No file URL stored for this presentation")

    return {"file_url": presentation.file_url}


@router.get(
    "/{presentation_id}/latest-training-analytics",
    response_model=LatestTrainingAnalyticsOut,
    summary="Get analytics data for the dashboard" # Name angepasst
)
async def get_latest_training_analytics(
    presentation_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Fetches analysis scores for the dashboard.
    - Content/Delivery scores come from the active presentation finding.
    - Engagement score comes from the most recent training result.
    """
    # 1. Zugriff prüfen (bleibt gleich)
    presentation = await db.get(Presentation, presentation_id)
    if not presentation or presentation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Presentation not found or access denied",
        )

    # 2. Hole die aktive Präsentations-Analyse (für Content und Delivery)
    finding_stmt = select(PresentationFinding).where(
        PresentationFinding.presentation_id == presentation_id,
        PresentationFinding.is_active.is_(True)
    )
    finding_result = await db.execute(finding_stmt)
    active_finding = finding_result.scalar_one_or_none()
    
    # 3. Hole das letzte Trainings-Ergebnis (für Engagement)
    result_stmt = (
        select(TrainingResult)
        .join(Training, Training.id == TrainingResult.training_id)
        .where(Training.presentation_id == presentation_id)
        .order_by(Training.date.desc())
        .limit(1)
    )
    latest_result = await db.scalar(result_stmt) # .scalar() ist hier kürzer

    # 4. Baue die Antwort zusammen
    
    # Berechne den Content-Score (z.B. als Durchschnitt der relevanten Finding-Scores)
    # Annahme: "Content" ist der Durchschnitt aus 'flight_path' und 'preflight_check'
    content_score = 0
    if active_finding and active_finding.flight_path_score is not None and active_finding.preflight_check_score is not None:
         content_score = (active_finding.flight_path_score + active_finding.preflight_check_score) / 2

    # Annahme: "Delivery" ist der 'cockpit_score'
    delivery_score = active_finding.cockpit_score if active_finding else 0

    engagement_score = 0
    if latest_result and latest_result.eye_tracking_total_score is not None:
        engagement_score = latest_result.eye_tracking_total_score * 100

    return LatestTrainingAnalyticsOut(
        content_score=content_score,
        delivery_score=delivery_score,
        engagement_score=engagement_score
    )