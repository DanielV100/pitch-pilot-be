from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.presentation_model import Presentation

class PresentationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_presentation(self, user_id, data):
        presentation = Presentation(
            user_id=user_id,
            name=data["name"],
            description=data["description"],
            tags=data["tags"],
            file_url=data["file_url"],
        )
        self.db.add(presentation)
        await self.db.commit()
        await self.db.refresh(presentation)
        return presentation