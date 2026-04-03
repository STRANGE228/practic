from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.repositories.invitation_repository import InvitationRepository
from app.repositories.board_repository import BoardRepository
from app.repositories.user_repository import UserRepository
from app.repositories.board_member_repository import BoardMemberRepository
from app.services.board_service import BoardService
from app.models.user import User
from app.models.board_member import MemberRole

router = APIRouter(prefix="/invitations", tags=["invitations"])
templates = Jinja2Templates(directory="app/templates")


@router.post("/create")
async def create_invitation(
        request: Request,
        board_id: int = Form(...),
        role: str = Form("viewer"),
        email: str = Form(None),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    board_repo = BoardRepository(db)
    board = board_repo.get(board_id)

    if not board or board.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Только владелец доски может создавать приглашения")

    inv_repo = InvitationRepository(db)
    invitation = inv_repo.create_invitation(
        board_id=board_id,
        invited_by=current_user.id,
        role=role,
        email=email
    )

    invite_link = f"{request.base_url}invitations/join/{invitation.token}"

    return JSONResponse({
        "success": True,
        "invite_link": invite_link,
        "token": invitation.token
    })


@router.get("/join/{token}")
async def join_board(
        request: Request,
        token: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    inv_repo = InvitationRepository(db)
    invitation = inv_repo.get_by_token(token)

    if not invitation:
        raise HTTPException(status_code=404, detail="Приглашение не найдено")

    from datetime import datetime
    if invitation.expires_at and invitation.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Приглашение истекло")

    if invitation.used:
        raise HTTPException(status_code=400, detail="Приглашение уже использовано")

    member_repo = BoardMemberRepository(db)
    existing_member = member_repo.db.query(member_repo.model).filter(
        member_repo.model.board_id == invitation.board_id,
        member_repo.model.user_id == current_user.id
    ).first()

    if existing_member:
        return RedirectResponse(url=f"/boards/{invitation.board_id}", status_code=303)

    member_repo.add_member(
        board_id=invitation.board_id,
        user_id=current_user.id,
        role=MemberRole.EDITOR if invitation.role == "editor" else MemberRole.VIEWER,
        invited_by=invitation.invited_by
    )

    inv_repo.use_invitation(token)

    return RedirectResponse(url=f"/boards/{invitation.board_id}", status_code=303)


@router.post("/{member_id}/remove")
async def remove_member(
        member_id: int,
        request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    member_repo = BoardMemberRepository(db)
    member = member_repo.get(member_id)

    if not member:
        raise HTTPException(status_code=404, detail="Участник не найден")

    board_repo = BoardRepository(db)
    board = board_repo.get(member.board_id)

    if not board or board.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Только владелец доски может удалять участников")

    member_repo.delete(member)

    return RedirectResponse(url=f"/boards/{board.id}", status_code=303)


@router.post("/{member_id}/update-role")
async def update_member_role(
        member_id: int,
        role: str = Form(...),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    member_repo = BoardMemberRepository(db)
    member = member_repo.get(member_id)

    if not member:
        raise HTTPException(status_code=404, detail="Участник не найден")

    board_repo = BoardRepository(db)
    board = board_repo.get(member.board_id)

    if not board or board.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Только владелец доски может изменять роли")

    role_enum = MemberRole.EDITOR if role == "editor" else MemberRole.VIEWER
    member_repo.update_role(member.board_id, member.user_id, role_enum)

    return RedirectResponse(url=f"/boards/{board.id}", status_code=303)