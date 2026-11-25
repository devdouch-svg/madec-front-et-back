from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictException, NotFoundException
from app.core.security import generate_password, hash_password
from app.models.order import Order
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


def get_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if not user:
        raise NotFoundException(f"User {user_id} not found")
    return user


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    normalized = email.strip().lower()
    return db.query(User).filter(func.lower(User.email) == normalized).first()


def get_user_by_matricule(db: Session, matricule: str) -> Optional[User]:
    return db.query(User).filter(User.matricule == matricule.strip()).first()


def get_user_by_login(db: Session, login: str) -> Optional[User]:
    """Resolve Assabil USER_LOGIN / matricule / email for authentication."""
    key = login.strip()
    if not key:
        return None
    user = db.query(User).filter(func.lower(User.user_login) == key.lower()).first()
    if user:
        return user
    user = get_user_by_matricule(db, key)
    if user:
        return user
    if "@" in key:
        return get_user_by_email(db, key)
    return None


def list_users(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    societe: Optional[str] = None,
    agence: Optional[str] = None,
) -> tuple[List[User], int]:
    q = db.query(User)
    if role:
        q = q.filter(User.role == role)
    if is_active is not None:
        q = q.filter(User.is_active == is_active)
    if societe:
        q = q.filter(User.societe == societe)
    if agence:
        q = q.filter(User.agence == agence)
    if search:
        from app.core.strings import ilike_pattern
        like = ilike_pattern(search)
        q = q.filter(
            (User.email.ilike(like))
            | (User.first_name.ilike(like))
            | (User.last_name.ilike(like))
        )
    total = q.count()
    items = (
        q.order_by(User.last_name, User.first_name, User.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total


def create_user(db: Session, data: UserCreate) -> tuple[User, str]:
    """Returns (user, plain_password). Plain password is emailed to the user."""
    if get_user_by_email(db, data.email):
        raise ConflictException(f"Email {data.email!r} already registered")

    from app.services import app_settings

    plafond = data.plafond_mensuel
    if plafond is None and data.role == "acheteur":
        plafond = app_settings.get_default_plafond(db)

    plain_pw = generate_password()
    user = User(
        email=data.email,
        hashed_password=hash_password(plain_pw),
        first_name=data.first_name,
        last_name=data.last_name,
        phone=data.phone,
        matricule=data.matricule,
        user_login=data.user_login or data.matricule,
        role=data.role,
        payment_mode=data.payment_mode,
        plafond_mensuel=plafond,
        productsalesgroup_code=data.productsalesgroup_code,
        societe=data.societe,
        agence=data.agence or "001",
        ville=data.ville,
        langue=data.langue or "fr",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, plain_pw


def update_user(db: Session, user_id: int, data: UserUpdate) -> User:
    user = get_user(db, user_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


def toggle_user(db: Session, user_id: int) -> User:
    user = get_user(db, user_id)
    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    return user


def reset_user_password(db: Session, user_id: int) -> tuple[User, str]:
    """Admin resets a user's password. Returns (user, new_plain_password)."""
    user = get_user(db, user_id)
    plain_pw = generate_password()
    user.hashed_password = hash_password(plain_pw)
    db.commit()
    return user, plain_pw


def set_user_password(db: Session, user_id: int, new_password: str) -> User:
    """Admin sets a specific password for a user (manual change)."""
    user = get_user(db, user_id)
    user.hashed_password = hash_password(new_password)
    db.commit()
    db.refresh(user)
    return user


def update_plafond(db: Session, user_id: int, plafond: Optional[float]) -> User:
    user = get_user(db, user_id)
    user.plafond_mensuel = plafond
    db.commit()
    db.refresh(user)
    return user


def bulk_set_plafond(db: Session, plafond: Optional[float], roles: Optional[list[str]] = None) -> int:
    """Set the same monthly plafond for many users at once (default: all acheteurs).

    Returns the number of users updated. `plafond=None` means unlimited.
    """
    q = db.query(User)
    if roles:
        q = q.filter(User.role.in_(roles))
    count = q.update({User.plafond_mensuel: plafond}, synchronize_session=False)
    db.commit()
    return count


def update_payment_mode(
    db: Session,
    user_id: int,
    mode: str | None = None,
    modes: list[str] | None = None,
) -> User:
    from app.core.exceptions import BadRequestException
    from app.core.payment_modes import normalize_payment_modes

    user = get_user(db, user_id)
    try:
        if modes is not None:
            user.payment_mode = normalize_payment_modes(modes)
        elif mode:
            # Accept legacy single value or already-normalized combo string
            if mode == "les_deux" or "," not in mode:
                from app.core.payment_modes import expand_payment_modes

                user.payment_mode = normalize_payment_modes(expand_payment_modes(mode))
            else:
                user.payment_mode = normalize_payment_modes(mode.split(","))
        else:
            raise BadRequestException("Indiquez payment_mode ou modes[]")
    except ValueError as exc:
        raise BadRequestException(str(exc)) from exc
    db.commit()
    db.refresh(user)
    return user


def update_role(db: Session, user_id: int, role: str) -> User:
    user = get_user(db, user_id)
    user.role = role
    db.commit()
    db.refresh(user)
    return user


def get_plafond_status(db: Session, user: User) -> dict:
    """Calculate how much of the monthly plafond the user has spent."""
    now = datetime.now(timezone.utc)
    spent = (
        db.query(func.sum(Order.dueamount))
        .filter(
            Order.user_id == user.id,
            Order.sorder_status.notin_(["cancelled"]),
            extract("year",  Order.created_at) == now.year,
            extract("month", Order.created_at) == now.month,
        )
        .scalar()
        or 0.0
    )
    remaining = None
    if user.plafond_mensuel is not None:
        remaining = max(0.0, float(user.plafond_mensuel) - float(spent))
    return {
        "plafond_mensuel": user.plafond_mensuel,
        "spent_this_month": float(spent),
        "remaining": remaining,
    }
