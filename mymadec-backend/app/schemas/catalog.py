from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


def _require_non_blank(v: str) -> str:
    stripped = v.strip()
    if not stripped:
        raise ValueError("Ce champ est requis")
    return stripped


class CatalogGammeCreate(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return _require_non_blank(v)


class CatalogGammeUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return _require_non_blank(v)


class CatalogGammeResponse(BaseModel):
    id: int
    name: str
    is_active: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CatalogFamilleCreate(BaseModel):
    gamme_id: int
    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return _require_non_blank(v)


class CatalogFamilleUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
    gamme_id: Optional[int] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return _require_non_blank(v)


class CatalogFamilleResponse(BaseModel):
    id: int
    gamme_id: int
    gamme_name: Optional[str] = None
    name: str
    is_active: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CatalogSousFamilleCreate(BaseModel):
    famille_id: int
    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return _require_non_blank(v)


class CatalogSousFamilleUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
    famille_id: Optional[int] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return _require_non_blank(v)


class CatalogSousFamilleResponse(BaseModel):
    id: int
    famille_id: int
    famille_name: Optional[str] = None
    gamme_name: Optional[str] = None
    name: str
    is_active: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CatalogCategorieCreate(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return _require_non_blank(v)


class CatalogCategorieUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return _require_non_blank(v)


class CatalogCategorieResponse(BaseModel):
    id: int
    name: str
    is_active: bool
    sort_order: int
    image_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CatalogSousCategorieCreate(BaseModel):
    categorie_id: int
    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return _require_non_blank(v)


class CatalogSousCategorieUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
    categorie_id: Optional[int] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return _require_non_blank(v)


class CatalogSousCategorieResponse(BaseModel):
    id: int
    categorie_id: int
    categorie_name: Optional[str] = None
    name: str
    is_active: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrgSocieteCreate(BaseModel):
    code: str
    label: str

    @field_validator("code", "label")
    @classmethod
    def validate_text(cls, v: str) -> str:
        return _require_non_blank(v)


class OrgSocieteUpdate(BaseModel):
    code: Optional[str] = None
    label: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None

    @field_validator("code", "label")
    @classmethod
    def validate_text(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return _require_non_blank(v)


class OrgSocieteResponse(BaseModel):
    id: int
    code: str
    label: str
    is_active: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrgAgenceCreate(BaseModel):
    societe_id: int
    code: str
    label: str

    @field_validator("code", "label")
    @classmethod
    def validate_text(cls, v: str) -> str:
        return _require_non_blank(v)


class OrgAgenceUpdate(BaseModel):
    societe_id: Optional[int] = None
    code: Optional[str] = None
    label: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None

    @field_validator("code", "label")
    @classmethod
    def validate_text(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return _require_non_blank(v)


class OrgAgenceResponse(BaseModel):
    id: int
    societe_id: int
    societe_code: Optional[str] = None
    societe_label: Optional[str] = None
    code: str
    label: str
    is_active: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrgVilleCreate(BaseModel):
    code: str
    label: str

    @field_validator("code", "label")
    @classmethod
    def validate_text(cls, v: str) -> str:
        return _require_non_blank(v)


class OrgVilleUpdate(BaseModel):
    code: Optional[str] = None
    label: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None

    @field_validator("code", "label")
    @classmethod
    def validate_text(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return _require_non_blank(v)


class OrgVilleResponse(BaseModel):
    id: int
    code: str
    label: str
    is_active: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CatalogImportResult(BaseModel):
    gammes: int
    familles: int
    sous_familles: int
    categories: int
    sous_categories: int
    societes: int
    agences: int
    villes: int
    types: int = 0


class CatalogTypeTreeNode(BaseModel):
    id: int
    name: str
    is_active: bool
    sort_order: int
    product_count: int = 0


class CatalogSousCategorieTreeNode(BaseModel):
    id: int
    name: str
    is_active: bool
    sort_order: int
    product_count: int = 0
    types: list[CatalogTypeTreeNode] = []


class CatalogCategorieTreeNode(BaseModel):
    id: int
    name: str
    is_active: bool
    sort_order: int
    image_path: Optional[str] = None
    updated_at: Optional[datetime] = None
    product_count: int = 0
    sous_categories: list[CatalogSousCategorieTreeNode]


class CatalogTypeCreate(BaseModel):
    sous_categorie_id: int
    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return _require_non_blank(v)


class CatalogTypeUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
    sous_categorie_id: Optional[int] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return _require_non_blank(v)


class CatalogTypeResponse(BaseModel):
    id: int
    sous_categorie_id: int
    sous_categorie_name: Optional[str] = None
    categorie_name: Optional[str] = None
    name: str
    is_active: bool
    sort_order: int
    product_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CatalogReorderRequest(BaseModel):
    ids: list[int]

    @field_validator("ids")
    @classmethod
    def validate_ids(cls, v: list[int]) -> list[int]:
        if len(v) < 2:
            raise ValueError("Au moins deux éléments sont requis pour le tri")
        if len(set(v)) != len(v):
            raise ValueError("Identifiants dupliqués dans l'ordre")
        return v


class CatalogReorderResponse(BaseModel):
    updated: int
