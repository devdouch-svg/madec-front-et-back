from __future__ import annotations

import json
import logging
import os
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.notification import Notification

logger = logging.getLogger("mymadec.notification")

_firebase_app = None


def _get_firebase():
    global _firebase_app
    if _firebase_app is not None:
        return _firebase_app
    try:
        import firebase_admin
        from firebase_admin import credentials

        if settings.FIREBASE_CREDENTIALS_JSON:
            cred_dict = json.loads(settings.FIREBASE_CREDENTIALS_JSON)
            cred = credentials.Certificate(cred_dict)
        elif os.path.exists(settings.FIREBASE_CREDENTIALS_PATH):
            cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        else:
            logger.warning("Firebase credentials not found — push notifications disabled")
            return None
        _firebase_app = firebase_admin.initialize_app(cred)
        return _firebase_app
    except Exception as exc:
        logger.error("Firebase init failed: %s", exc)
        return None


def send_push(fcm_token: str, title: str, body: str, data: Optional[dict] = None) -> bool:
    """Send a push notification via FCM."""
    app = _get_firebase()
    if app is None:
        return False
    try:
        from firebase_admin import messaging

        msg = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data={k: str(v) for k, v in (data or {}).items()},
            token=fcm_token,
        )
        messaging.send(msg)
        return True
    except Exception as exc:
        logger.error("FCM send failed: %s", exc)
        return False


def notify_role_users(
    db: Session,
    roles: list[str],
    *,
    title: str,
    body: str,
    type: str = "general",
    data: Optional[dict] = None,
) -> list[Notification]:
    """Persist + push notifications for every active user with one of the given roles."""
    from app.models.user import User

    users = (
        db.query(User)
        .filter(User.role.in_(roles), User.is_active == True)  # noqa: E712
        .all()
    )
    created: list[Notification] = []
    for user in users:
        created.append(
            create_notification(
                db,
                user_id=user.id,
                title=title,
                body=body,
                type=type,
                data=data,
                fcm_token=user.fcm_token,
            )
        )
    return created


def create_notification(
    db: Session,
    *,
    user_id: int,
    title: str,
    body: str,
    type: str = "general",
    data: Optional[dict] = None,
    fcm_token: Optional[str] = None,
) -> Notification:
    """Persist notification in DB and optionally send push."""
    notif = Notification(
        user_id=user_id,
        title=title,
        body=body,
        type=type,
        data=json.dumps(data) if data else None,
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)

    if fcm_token:
        send_push(fcm_token, title, body, data)

    return notif
