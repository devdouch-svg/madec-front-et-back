from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db, require_admin
from app.core.permissions import require_human_user
from app.models.banner import Banner
from app.schemas.banner import BannerResponse, BannerUpdate
from app.schemas.common import MessageResponse
from app.services.storage import delete_file, save_banner_image

router = APIRouter(prefix="/banners", tags=["banners"], dependencies=[Depends(require_human_user)])


@router.get("", response_model=List[BannerResponse])
def list_banners(
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = db.query(Banner)
    if not (include_inactive and current_user.role == "admin"):
        q = q.filter(Banner.is_active == True)
    return q.order_by(Banner.position).all()


@router.get("/{banner_id}", response_model=BannerResponse)
def get_banner(banner_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    from app.core.exceptions import NotFoundException
    b = db.get(Banner, banner_id)
    if not b:
        raise NotFoundException("Banner not found")
    return b


@router.put("/{banner_id}", response_model=BannerResponse)
def update_banner(banner_id: int, body: BannerUpdate, db: Session = Depends(get_db), _=Depends(require_admin)):
    from app.core.exceptions import NotFoundException
    b = db.get(Banner, banner_id)
    if not b:
        raise NotFoundException("Banner not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(b, field, value)
    db.commit()
    db.refresh(b)
    return b


@router.post("/{banner_id}/image", response_model=BannerResponse)
async def upload_banner_image(
    banner_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    from app.core.exceptions import NotFoundException
    b = db.get(Banner, banner_id)
    if not b:
        raise NotFoundException("Banner not found")
    if b.image_path:
        delete_file(b.image_path)
    path = await save_banner_image(file, banner_id)
    b.image_path = path
    db.commit()
    db.refresh(b)
    return b


@router.patch("/{banner_id}/toggle", response_model=BannerResponse)
def toggle_banner(banner_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    from app.core.exceptions import NotFoundException
    b = db.get(Banner, banner_id)
    if not b:
        raise NotFoundException("Banner not found")
    b.is_active = not b.is_active
    db.commit()
    db.refresh(b)
    return b
