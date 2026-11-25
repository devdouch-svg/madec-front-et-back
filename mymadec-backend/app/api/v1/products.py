from __future__ import annotations

import math
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db, require_admin, require_admin_or_gest
from app.core.permissions import require_human_user
from app.models.product import Product
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.product import (
    ProductAssign,
    ProductBulkAssign,
    ProductBulkAssignResult,
    ProductCreate,
    ProductMobileResponse,
    ProductResponse,
    ProductUpdate,
)
from app.services import product as product_svc
from app.services.storage import delete_file, save_product_image

router = APIRouter(prefix="/products", tags=["products"], dependencies=[Depends(require_human_user)])


@router.get("", response_model=PaginatedResponse[ProductResponse])
def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=500),
    gamme: Optional[str] = None,
    famille: Optional[str] = None,
    sous_famille: Optional[str] = None,
    categorie: Optional[str] = None,
    sous_categorie: Optional[str] = None,
    type_produit: Optional[str] = None,
    missing_mobile_category: bool = Query(False),
    society_code: Optional[str] = None,
    is_active: Optional[bool] = None,
    price_min: Optional[float] = Query(None, ge=0),
    price_max: Optional[float] = Query(None, ge=0),
    has_discount: Optional[bool] = None,
    is_liquidation: Optional[bool] = None,
    include_liquidations: bool = Query(False),
    search: Optional[str] = Query(None, min_length=2),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if is_active is None and current_user.role not in ("admin", "gestionnaire"):
        is_active = True
    items, total = product_svc.list_products(
        db, page, page_size, gamme, famille, sous_famille,
        categorie, sous_categorie, missing_mobile_category, society_code, is_active,
        price_min=price_min, price_max=price_max, has_discount=has_discount,
        is_liquidation=is_liquidation,
        include_liquidations=include_liquidations,
        search=search,
        type_produit=type_produit,
    )
    return PaginatedResponse(
        items=items, total=total, page=page,
        page_size=page_size, pages=math.ceil(total / page_size) or 1,
    )


@router.get("/mobile", response_model=PaginatedResponse[ProductMobileResponse])
def list_mobile_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    categorie: Optional[str] = None,
    sous_categorie: Optional[str] = None,
    type_produit: Optional[str] = None,
    society_code: Optional[str] = None,
    search: Optional[str] = Query(None, min_length=2),
    price_min: Optional[float] = Query(None, ge=0),
    price_max: Optional[float] = Query(None, ge=0),
    has_discount: Optional[bool] = None,
    is_liquidation: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Mobile catalogue — no ERP gamme/famille fields in the response."""
    is_active = True if current_user.role not in ("admin", "gestionnaire") else None
    items, total = product_svc.list_products(
        db, page, page_size,
        categorie=categorie,
        sous_categorie=sous_categorie,
        type_produit=type_produit,
        society_code=society_code,
        is_active=is_active,
        search=search,
        price_min=price_min,
        price_max=price_max,
        has_discount=has_discount,
        is_liquidation=is_liquidation,
    )
    return PaginatedResponse(
        items=items, total=total, page=page,
        page_size=page_size, pages=math.ceil(total / page_size) or 1,
    )


@router.get("/search", response_model=PaginatedResponse[ProductResponse])
def search_products(
    q: str = Query(..., min_length=2),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    active_only = None if current_user.role in ("admin", "gestionnaire") else True
    items, total = product_svc.list_products(db, page, page_size, is_active=active_only, search=q)
    return PaginatedResponse(
        items=items, total=total, page=page,
        page_size=page_size, pages=math.ceil(total / page_size) or 1,
    )


@router.get("/gammes", response_model=List[str])
def list_gammes(db: Session = Depends(get_db)):
    return product_svc.distinct_values(db, Product.gamme)


@router.get("/familles", response_model=List[str])
def list_familles(db: Session = Depends(get_db)):
    return product_svc.distinct_values(db, Product.famille)


@router.get("/sous-familles", response_model=List[str])
def list_sous_familles(db: Session = Depends(get_db)):
    return product_svc.distinct_values(db, Product.sous_famille)


@router.get("/categories", response_model=List[str])
def list_product_categories(db: Session = Depends(get_db)):
    return product_svc.distinct_values(db, Product.categorie)


@router.get("/sous-categories", response_model=List[str])
def list_product_sous_categories(db: Session = Depends(get_db)):
    return product_svc.distinct_values(db, Product.sous_categorie)


@router.get("/societes", response_model=List[str])
def list_societes(db: Session = Depends(get_db)):
    return product_svc.distinct_values(db, Product.society_code)


@router.get("/export/uncategorized")
def export_uncategorized_products(
    db: Session = Depends(get_db),
    _=Depends(require_admin_or_gest),
):
    """CSV of products missing a mobile catégorie (for back-office assignment)."""
    content = product_svc.uncategorized_products_csv(db)
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="produits-sans-categorie-mobile.csv"'},
    )


@router.get("/mobile/by-code/{product_code}", response_model=ProductMobileResponse)
def get_mobile_product_by_code(product_code: str, db: Session = Depends(get_db)):
    from app.core.exceptions import NotFoundException

    product = db.query(Product).filter(
        Product.product_code == product_code,
        Product.is_active == True,
    ).first()
    if not product:
        raise NotFoundException(f"Product with code {product_code!r} not found")
    return product


@router.get("/by-code/{product_code}", response_model=ProductResponse)
def get_product_by_code(
    product_code: str,
    db: Session = Depends(get_db),
):
    """Mobile barcode scan: look up product by product_code."""
    from app.core.exceptions import NotFoundException
    product = db.query(Product).filter(
        Product.product_code == product_code,
        Product.is_active == True,
    ).first()
    if not product:
        raise NotFoundException(f"Product with code {product_code!r} not found")
    return product


@router.get("/mobile/{product_id}", response_model=ProductMobileResponse)
def get_mobile_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return product_svc.get_product(
        db, product_id, allow_inactive=current_user.role in ("admin", "gestionnaire")
    )


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return product_svc.get_product(
        db, product_id, allow_inactive=current_user.role in ("admin", "gestionnaire")
    )


@router.post("", response_model=ProductResponse, status_code=201)
def create_product(body: ProductCreate, db: Session = Depends(get_db), _=Depends(require_admin_or_gest)):
    return product_svc.create_product(db, body)


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, body: ProductUpdate, db: Session = Depends(get_db), _=Depends(require_admin_or_gest)):
    return product_svc.update_product(db, product_id, body, allow_inactive=True)


@router.patch("/{product_id}/toggle", response_model=ProductResponse)
def toggle_product(product_id: int, db: Session = Depends(get_db), _=Depends(require_admin_or_gest)):
    return product_svc.toggle_product(db, product_id, allow_inactive=True)


@router.post("/bulk-assign", response_model=ProductBulkAssignResult)
def bulk_assign_products(
    body: ProductBulkAssign,
    db: Session = Depends(get_db),
    _=Depends(require_admin_or_gest),
):
    updated = product_svc.bulk_assign_products(db, body, allow_inactive=True)
    return ProductBulkAssignResult(updated=updated)


@router.post("/{product_id}/assign", response_model=ProductResponse)
def assign_product(product_id: int, body: ProductAssign, db: Session = Depends(get_db), _=Depends(require_admin_or_gest)):
    return product_svc.assign_product(db, product_id, body, allow_inactive=True)


@router.post("/{product_id}/image", response_model=ProductResponse)
async def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _=Depends(require_admin_or_gest),
):
    product = product_svc.get_product(db, product_id, allow_inactive=True)
    if product.image_path:
        delete_file(product.image_path)
    path = await save_product_image(file, product.product_code)
    product.image_path = path
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}/image", response_model=MessageResponse)
def delete_product_image(product_id: int, db: Session = Depends(get_db), _=Depends(require_admin_or_gest)):
    product = product_svc.get_product(db, product_id, allow_inactive=True)
    delete_file(product.image_path)
    product.image_path = None
    db.commit()
    return {"message": "Image deleted"}
