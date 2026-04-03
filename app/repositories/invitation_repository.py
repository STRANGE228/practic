from sqlalchemy.orm import Session
from app.models.invitation import Invitation
from app.repositories.base import BaseRepository
from typing import Optional
from datetime import datetime, timedelta
import uuid


class InvitationRepository(BaseRepository[Invitation]):
    def __init__(self, db: Session):
        super().__init__(db, Invitation)

    def create_invitation(self, board_id, invited_by, role = "viewer", email = None,
                          expires_in_hours = 168):
        expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)

        return self.create(
            token=str(uuid.uuid4()),
            board_id=board_id,
            invited_by=invited_by,
            email=email,
            role=role,
            expires_at=expires_at
        )

    def get_by_token(self, token):
        return self.db.query(Invitation).filter(Invitation.token == token).first()

    def use_invitation(self, token):
        invitation = self.get_by_token(token)
        if invitation:
            invitation.used = True
            self.db.commit()
            self.db.refresh(invitation)
        return invitation