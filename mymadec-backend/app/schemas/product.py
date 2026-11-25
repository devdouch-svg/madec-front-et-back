from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


def _blank_to_none(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    stripped = v.strip()
    return stripped if stripped else None


class ProductCreate(BaseModel):
    product_code: str
    name: str
    description: Optional[str] = None
    unit: Optional[str] = None
    type_produit: Optional[str] = None
    gamme: Optional[str] = None
    famille: Optional[str] = None
    sous_famille: Optional[str] = None
    categorie: Optional[str] = None
    sous_categorie: Optional[str] = None
    productsalesgroup_code: Optional[str] = None
    society_code: Optional[str] = None
    base_price: Optional[float] = None
    discount_rate: float = 0
    is_liquidation: bool = False

    model_config = {"str_strip_whitespace": True}

    @field_validator("product_code", "name")
    @classmethod
    def validate_required_text(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Ce champ est requis")
        return v.strip()

    @field_validator(
        "description", "unit", "type_produit", "gamme", "famille", "sous_famille",
        "categorie", "sous_categorie",
        "productsalesgroup_code", "society_code",
        mode="before",
    )
    @classmethod
    def normalize_optional_text(cls, v):
        if v is None or isinstance(v, str):
            return _blank_to_none(v)
        return v


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    unit: Optional[str] = None
    type_produit: Optional[str] = None
    gamme: Optional[str] = None
    famille: Optional[str] = None
    sous_famille: Optional[str] = None
    categorie: Optional[str] = None
    sous_categorie: Optional[str] = None
    productsalesgroup_code: Optional[str] = None
    society_code: Optional[str] = None
    base_price: Optional[float] = None
    discount_rate: Optional[float] = None
    is_liquidation: Optional[bool] = None
    sort_order: Optional[int] = None

    model_config = {"str_strip_whitespace": True}

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if not v.strip():
            raise ValueError("Le nom est requis")
        return v.strip()

    @field_validator(
        "description", "unit", "type_produit", "gamme", "famille", "sous_famille",
        "categorie", "sous_categorie",
        "productsalesgroup_code", "society_code",
        mode="before",
    )
    @classmethod
    def normalize_optional_text(cls, v):
        if v is None or isinstance(v, str):
            return _blank_to_none(v)
        return v


class ProductAssign(BaseModel):
    gamme: Optional[str] = None
    famille: Optional[str] = None
    sous_famille: Optional[str] = None
    categorie: Optional[str] = None
    sous_categorie: Optional[str] = None

    @field_validator(
        "gamme", "famille", "sous_famille", "categorie", "sous_categorie",
        mode="before",
    )
    @classmethod
    def normalize_optional_text(cls, v):
        if v is None or isinstance(v, str):
            return _blank_to_none(v)
        return v


class ProductBulkAssign(BaseModel):
    product_ids: List[int] = Field(..., min_length=1, max_length=500)
    gamme: Optional[str] = None
    famille: Optional[str] = None
    sous_famille: Optional[str] = None
    categorie: Optional[str] = None
    sous_categorie: Optional[str] = None

    @field_validator("product_ids")
    @classmethod
    def validate_ids(cls, v: List[int]) -> List[int]:
        if not v:
            raise ValueError("Au moins un produit requis")
        return v

    @field_validator(
        "gamme", "famille", "sous_famille", "categorie", "sous_categorie",
        mode="before",
    )
    @classmethod
    def normalize_optional_text(cls, v):
        if v is None or isinstance(v, str):
            return _blank_to_none(v)
        return v


class ProductBulkAssignResult(BaseModel):
    updated: int


class ProductMobileResponse(BaseModel):
    """Mobile-app product view — excludes ERP sync taxonomy."""

    id: int
    product_code: str
    name: str
    description: Optional[str]
    unit: Optional[str]
    type_produit: Optional[str]
    # Doubles as brand ("IDEAL", "STAR") for Figma-imported products —
    # exposed to mobile for that reason, despite the ERP-taxonomy exclusion
    # documented above.
    gamme: Optional[str]
    categorie: Optional[str]
    sous_categorie: Optional[str]
    productsalesgroup_code: Optional[str]
    society_code: Optional[str]
    base_price: Optional[float]
    discount_rate: float
    is_liquidation: bool
    sort_order: int = 0
    final_price: Optional[float]
    image_path: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProductResponse(BaseModel):
    id: int
    product_code: str
    name: str
    description: Optional[str]
    unit: Optional[str]
    type_produit: Optional[str]
    gamme: Optional[str]
    famille: Optional[str]
    sous_famille: Optional[str]
    categorie: Optional[str]
    sous_categorie: Optional[str]
    productsalesgroup_code: Optional[str]
    society_code: Optional[str]
    base_price: Optional[float]
    discount_rate: float
    is_liquidation: bool
    sort_order: int = 0
    final_price: Optional[float]
    image_path: Optional[str]
    is_active: bool
    synced_from_intermediate: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProductSyncItem(BaseModel):
    product_code: str
    name: str
    description: Optional[str] = None
    unit: Optional[str] = None
    gamme: Optional[str] = None
    famille: Optional[str] = None
    sous_famille: Optional[str] = None
    productsalesgroup_code: Optional[str] = None
    society_code: Optional[str] = None
    base_price: Optional[float] = None
    discount_rate: float = 0
    is_active: bool = True
    synced_from_intermediate: bool = True   # always True when coming from the ETL


class ProductSyncBulkRequest(BaseModel):
    items: List[ProductSyncItem] = Field(..., min_length=1, max_length=1000)
