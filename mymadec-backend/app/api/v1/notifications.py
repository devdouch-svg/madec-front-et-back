from __future__ import annotations

import math
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db, require_admin
from app.core.permissions import require_human_user
from app.models.notification import Notification
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.notification import NotificationResponse, NotificationSend
from app.services.notification import create_notification

router = APIRouter(prefix="/notifications", tags=["notifications"], dependencies=[Depends(require_human_user)])


@router.get("", response_model=PaginatedResponse[NotificationResponse])
def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
    )
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResponse(
        items=items, total=total, page=page,
        page_size=page_size, pages=math.ceil(total / page_size) or 1,
    )


@router.patch("/{notif_id}/read", response_model=NotificationResponse)
def mark_read(notif_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    from app.core.exceptions import NotFoundException
    n = db.query(Notification).filter(
        Notification.id == notif_id, Notification.user_id == current_user.id
    ).first()
    if not n:
        raise NotFoundException("Notification not found")
    n.is_read = True
    db.commit()
    db.refresh(n)
    return n


@router.get("/unread-count")
def unread_count(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Mobile badge count: number of unread notifications."""
    count = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id, Notification.is_read == False)
        .count()
    )
    return {"unread_count": count}


@router.patch("/read-all", response_model=MessageResponse)
def mark_all_read(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    db.query(Notification).filter(
        Notification.user_id == current_user.id, Notification.is_read == False
    ).update({"is_read": True})
    db.commit()
    return {"message": "All notifications marked as read"}


@router.post("/send", response_model=NotificationResponse, status_code=201)
def send_notification(body: NotificationSend, db: Session = Depends(get_db), _=Depends(require_admin)):
    from app.core.exceptions import NotFoundException
    from app.models.user import User
    user = db.get(User, body.user_id)
    if not user:
        raise NotFoundException(f"User {body.user_id} not found")
    return create_notification(
        db,
        user_id=body.user_id,
        title=body.title,
        body=body.body,
        type=body.type,
        data=body.data,
        fcm_token=user.fcm_token if user else None,
    )


@router.delete("/{notif_id}", response_model=MessageResponse)
def delete_notification(notif_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    from app.core.exceptions import NotFoundException
    n = db.query(Notification).filter(
        Notification.id == notif_id, Notification.user_id == current_user.id
    ).first()
    if not n:
        raise NotFoundException("Notification not found")
    db.delete(n)
    db.commit()
    return {"message": "Notification deleted"}
