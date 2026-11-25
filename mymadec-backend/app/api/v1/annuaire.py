from __future__ import annotations

import math
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_admin
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.user import AnnuaireEntry

# CDC §6.3: Annuaire is Admin-only
router = APIRouter(prefix="/annuaire", tags=["annuaire"], dependencies=[Depends(require_admin)])


@router.get("", response_model=PaginatedResponse[AnnuaireEntry])
def list_annuaire(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(User).filter(User.is_active == True)
    if search:
        from app.core.strings import ilike_pattern
        like = ilike_pattern(search)
        q = q.filter(
            (User.first_name.ilike(like))
            | (User.last_name.ilike(like))
            | (User.email.ilike(like))
        )
    total = q.count()
    items = (
        q.order_by(User.last_name, User.first_name, User.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return PaginatedResponse(
        items=items, total=total, page=page,
        page_size=page_size, pages=math.ceil(total / page_size) or 1,
    )


@router.get("/{user_id}", response_model=AnnuaireEntry)
def get_annuaire_entry(user_id: int, db: Session = Depends(get_db)):
    from app.core.exceptions import NotFoundException
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise NotFoundException("User not found in annuaire")
    return user
