# app/services/finding_service.py

import uuid
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from app.models.presentation_model import PresentationFinding
from app.utils.findings.calculator import calculate_scores

class FindingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    from fastapi.encoders import jsonable_encoder

    async def create_finding(self, presentation_id: uuid.UUID, findings: dict, is_active: bool = False) -> PresentationFinding:
        scores = calculate_scores(findings)

        if is_active:
            await self.db.execute(
                update(PresentationFinding)
                .where(PresentationFinding.presentation_id == presentation_id)
                .values(is_active=False)
            )

        findings_json = jsonable_encoder(findings)

        new_finding = PresentationFinding(
            presentation_id=presentation_id,
            findings=findings_json,
            total_score=scores["total_score"],
            cockpit_score=scores["cockpit_score"],
            flight_path_score=scores["flight_path_score"],
            altitude_score=scores["altitude_score"],
            preflight_check_score=scores["preflight_check_score"],
            is_active=is_active
        )

        self.db.add(new_finding)
        await self.db.commit()
        await self.db.refresh(new_finding)
        return new_finding
