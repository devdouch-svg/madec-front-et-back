"""Reference-data management — additive API; does not replace /products/gammes etc."""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_admin, require_admin_or_gest
from app.core.exceptions import NotFoundException
from app.core.permissions import require_human_user
from app.schemas.common import MessageResponse
from app.schemas.catalog import (
    CatalogCategorieCreate,
    CatalogCategorieResponse,
    CatalogCategorieTreeNode,
    CatalogCategorieUpdate,
    CatalogFamilleCreate,
    CatalogFamilleResponse,
    CatalogFamilleUpdate,
    CatalogGammeCreate,
    CatalogGammeResponse,
    CatalogGammeUpdate,
    CatalogImportResult,
    CatalogReorderRequest,
    CatalogReorderResponse,
    CatalogSousCategorieCreate,
    CatalogSousCategorieResponse,
    CatalogSousCategorieUpdate,
    CatalogSousFamilleCreate,
    CatalogSousFamilleResponse,
    CatalogSousFamilleUpdate,
    CatalogTypeCreate,
    CatalogTypeResponse,
    CatalogTypeUpdate,
    OrgAgenceCreate,
    OrgAgenceResponse,
    OrgAgenceUpdate,
    OrgSocieteCreate,
    OrgSocieteResponse,
    OrgSocieteUpdate,
    OrgVilleCreate,
    OrgVilleResponse,
    OrgVilleUpdate,
)
from app.services import catalog as catalog_svc
from app.services.storage import delete_file, save_categorie_image
from app.models.catalog import CatalogCategorie

router = APIRouter(prefix="/catalog", tags=["catalog"], dependencies=[Depends(require_human_user)])


def _famille_response(row) -> CatalogFamilleResponse:
    return CatalogFamilleResponse(
        id=row.id,
        gamme_id=row.gamme_id,
        gamme_name=row.gamme.name if row.gamme else None,
        name=row.name,
        is_active=row.is_active,
        sort_order=row.sort_order,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _sous_famille_response(row) -> CatalogSousFamilleResponse:
    famille = row.famille
    gamme = famille.gamme if famille else None
    return CatalogSousFamilleResponse(
        id=row.id,
        famille_id=row.famille_id,
        famille_name=famille.name if famille else None,
        gamme_name=gamme.name if gamme else None,
        name=row.name,
        is_active=row.is_active,
        sort_order=row.sort_order,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _sous_categorie_response(row) -> CatalogSousCategorieResponse:
    cat = row.categorie
    return CatalogSousCategorieResponse(
        id=row.id,
        categorie_id=row.categorie_id,
        categorie_name=cat.name if cat else None,
        name=row.name,
        is_active=row.is_active,
        sort_order=row.sort_order,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _agence_response(row) -> OrgAgenceResponse:
    soc = row.societe
    return OrgAgenceResponse(
        id=row.id,
        societe_id=row.societe_id,
        societe_code=soc.code if soc else None,
        societe_label=soc.label if soc else None,
        code=row.code,
        label=row.label,
        is_active=row.is_active,
        sort_order=row.sort_order,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


# ── Gammes ────────────────────────────────────────────────────────────────────

@router.get("/gammes", response_model=List[CatalogGammeResponse])
def list_gammes(
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
):
    return catalog_svc.list_gammes(db, include_inactive=include_inactive)


@router.post("/gammes", response_model=CatalogGammeResponse, status_code=201)
def create_gamme(body: CatalogGammeCreate, db: Session = Depends(get_db), _=Depends(require_admin_or_gest)):
    return catalog_svc.create_gamme(db, body)


@router.put("/gammes/{gamme_id}", response_model=CatalogGammeResponse)
def update_gamme(
    gamme_id: int, body: CatalogGammeUpdate, db: Session = Depends(get_db), _=Depends(require_admin_or_gest)
):
    return catalog_svc.update_gamme(db, gamme_id, body)


# ── Familles ──────────────────────────────────────────────────────────────────

@router.get("/familles", response_model=List[CatalogFamilleResponse])
def list_familles(
    gamme_id: Optional[int] = None,
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
):
    rows = catalog_svc.list_familles(db, gamme_id=gamme_id, include_inactive=include_inactive)
    return [_famille_response(r) for r in rows]


@router.post("/familles", response_model=CatalogFamilleResponse, status_code=201)
def create_famille(body: CatalogFamilleCreate, db: Session = Depends(get_db), _=Depends(require_admin_or_gest)):
    row = catalog_svc.create_famille(db, body)
    db.refresh(row, attribute_names=["gamme"])
    return _famille_response(row)


@router.put("/familles/{famille_id}", response_model=CatalogFamilleResponse)
def update_famille(
    famille_id: int, body: CatalogFamilleUpdate, db: Session = Depends(get_db), _=Depends(require_admin_or_gest)
):
    row = catalog_svc.update_famille(db, famille_id, body)
    db.refresh(row, attribute_names=["gamme"])
    return _famille_response(row)


# ── Sous-familles ─────────────────────────────────────────────────────────────

@router.get("/sous-familles", response_model=List[CatalogSousFamilleResponse])
def list_sous_familles(
    famille_id: Optional[int] = None,
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
):
    rows = catalog_svc.list_sous_familles(db, famille_id=famille_id, include_inactive=include_inactive)
    return [_sous_famille_response(r) for r in rows]


@router.post("/sous-familles", response_model=CatalogSousFamilleResponse, status_code=201)
def create_sous_famille(
    body: CatalogSousFamilleCreate, db: Session = Depends(get_db), _=Depends(require_admin_or_gest)
):
    row = catalog_svc.create_sous_famille(db, body)
    db.refresh(row, attribute_names=["famille"])
    return _sous_famille_response(row)


@router.put("/sous-familles/{sous_famille_id}", response_model=CatalogSousFamilleResponse)
def update_sous_famille(
    sous_famille_id: int,
    body: CatalogSousFamilleUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_admin_or_gest),
):
    row = catalog_svc.update_sous_famille(db, sous_famille_id, body)
    db.refresh(row, attribute_names=["famille"])
    return _sous_famille_response(row)


# ── Catégories (mobile app) ───────────────────────────────────────────────────

@router.get("/categories", response_model=List[CatalogCategorieResponse])
def list_categories(
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
):
    return catalog_svc.list_categories(db, include_inactive=include_inactive)


@router.get("/categories/tree", response_model=List[CatalogCategorieTreeNode])
def list_categories_tree(
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
):
    return catalog_svc.get_categories_tree(db, include_inactive=include_inactive)


@router.post("/categories", response_model=CatalogCategorieResponse, status_code=201)
def create_categorie(body: CatalogCategorieCreate, db: Session = Depends(get_db), _=Depends(require_admin_or_gest)):
    return catalog_svc.create_categorie(db, body)


@router.put("/categories/{categorie_id}", response_model=CatalogCategorieResponse)
def update_categorie(
    categorie_id: int, body: CatalogCategorieUpdate, db: Session = Depends(get_db), _=Depends(require_admin_or_gest)
):
    return catalog_svc.update_categorie(db, categorie_id, body)


@router.post("/categories/{categorie_id}/image", response_model=CatalogCategorieResponse)
async def upload_categorie_image(
    categorie_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _=Depends(require_admin_or_gest),
):
    row = db.get(CatalogCategorie, categorie_id)
    if not row:
        raise NotFoundException("Catégorie introuvable")
    if row.image_path:
        delete_file(row.image_path)
    row.image_path = await save_categorie_image(file, categorie_id)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/categories/{categorie_id}/image", response_model=MessageResponse)
def delete_categorie_image(
    categorie_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_admin_or_gest),
):
    row = db.get(CatalogCategorie, categorie_id)
    if not row:
        raise NotFoundException("Catégorie introuvable")
    delete_file(row.image_path)
    row.image_path = None
    db.commit()
    return {"message": "Image supprimée"}


@router.get("/sous-categories", response_model=List[CatalogSousCategorieResponse])
def list_sous_categories(
    categorie_id: Optional[int] = None,
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
):
    rows = catalog_svc.list_sous_categories(db, categorie_id=categorie_id, include_inactive=include_inactive)
    return [_sous_categorie_response(r) for r in rows]


@router.post("/sous-categories", response_model=CatalogSousCategorieResponse, status_code=201)
def create_sous_categorie(
    body: CatalogSousCategorieCreate, db: Session = Depends(get_db), _=Depends(require_admin_or_gest)
):
    row = catalog_svc.create_sous_categorie(db, body)
    db.refresh(row, attribute_names=["categorie"])
    return _sous_categorie_response(row)


@router.put("/sous-categories/{sous_categorie_id}", response_model=CatalogSousCategorieResponse)
def update_sous_categorie(
    sous_categorie_id: int,
    body: CatalogSousCategorieUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_admin_or_gest),
):
    row = catalog_svc.update_sous_categorie(db, sous_categorie_id, body)
    db.refresh(row, attribute_names=["categorie"])
    return _sous_categorie_response(row)


def _type_response(row, product_count: int = 0) -> CatalogTypeResponse:
    sc = row.sous_categorie
    cat = sc.categorie if sc else None
    return CatalogTypeResponse(
        id=row.id,
        sous_categorie_id=row.sous_categorie_id,
        sous_categorie_name=sc.name if sc else None,
        categorie_name=cat.name if cat else None,
        name=row.name,
        is_active=row.is_active,
        sort_order=row.sort_order,
        product_count=product_count,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.get("/types", response_model=List[CatalogTypeResponse])
def list_types(
    sous_categorie_id: Optional[int] = None,
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
):
    rows = catalog_svc.list_types(db, sous_categorie_id=sous_categorie_id, include_inactive=include_inactive)
    counts: dict[str, int] = {}
    if sous_categorie_id is not None and rows:
        sc = rows[0].sous_categorie
        cat = sc.categorie if sc else None
        if sc and cat:
            counts = catalog_svc.type_product_counts(db, categorie_name=cat.name, sous_categorie_name=sc.name)
    return [_type_response(r, counts.get(r.name, 0)) for r in rows]


@router.post("/types", response_model=CatalogTypeResponse, status_code=201)
def create_type(body: CatalogTypeCreate, db: Session = Depends(get_db), _=Depends(require_admin_or_gest)):
    row = catalog_svc.create_type(db, body)
    db.refresh(row, attribute_names=["sous_categorie"])
    return _type_response(row)


@router.put("/types/{type_id}", response_model=CatalogTypeResponse)
def update_type(
    type_id: int,
    body: CatalogTypeUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_admin_or_gest),
):
    row = catalog_svc.update_type(db, type_id, body)
    db.refresh(row, attribute_names=["sous_categorie"])
    return _type_response(row)


@router.put("/reorder/categories", response_model=CatalogReorderResponse)
def reorder_categories(
    body: CatalogReorderRequest, db: Session = Depends(get_db), _=Depends(require_admin_or_gest)
):
    updated = catalog_svc.reorder_categories(db, body.ids)
    return CatalogReorderResponse(updated=updated)


@router.put("/reorder/sous-categories", response_model=CatalogReorderResponse)
def reorder_sous_categories(
    body: CatalogReorderRequest,
    categorie_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
    _=Depends(require_admin_or_gest),
):
    updated = catalog_svc.reorder_sous_categories(db, body.ids, categorie_id=categorie_id)
    return CatalogReorderResponse(updated=updated)


@router.put("/reorder/types", response_model=CatalogReorderResponse)
def reorder_types(
    body: CatalogReorderRequest,
    sous_categorie_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
    _=Depends(require_admin_or_gest),
):
    updated = catalog_svc.reorder_types(db, body.ids, sous_categorie_id=sous_categorie_id)
    return CatalogReorderResponse(updated=updated)


@router.put("/reorder/products", response_model=CatalogReorderResponse)
def reorder_products(
    body: CatalogReorderRequest, db: Session = Depends(get_db), _=Depends(require_admin_or_gest)
):
    updated = catalog_svc.reorder_products(db, body.ids)
    return CatalogReorderResponse(updated=updated)


# ── Sociétés ──────────────────────────────────────────────────────────────────

@router.get("/societes", response_model=List[OrgSocieteResponse])
def list_societes(include_inactive: bool = Query(False), db: Session = Depends(get_db)):
    return catalog_svc.list_societes(db, include_inactive=include_inactive)


@router.post("/societes", response_model=OrgSocieteResponse, status_code=201)
def create_societe(body: OrgSocieteCreate, db: Session = Depends(get_db), _=Depends(require_admin_or_gest)):
    return catalog_svc.create_societe(db, body)


@router.put("/societes/{societe_id}", response_model=OrgSocieteResponse)
def update_societe(
    societe_id: int, body: OrgSocieteUpdate, db: Session = Depends(get_db), _=Depends(require_admin_or_gest)
):
    return catalog_svc.update_societe(db, societe_id, body)


# ── Agences ─────────────────────────────────────────────────────────────────

@router.get("/agences", response_model=List[OrgAgenceResponse])
def list_agences(
    societe_id: Optional[int] = None,
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
):
    rows = catalog_svc.list_agences(db, societe_id=societe_id, include_inactive=include_inactive)
    return [_agence_response(r) for r in rows]


@router.post("/agences", response_model=OrgAgenceResponse, status_code=201)
def create_agence(body: OrgAgenceCreate, db: Session = Depends(get_db), _=Depends(require_admin_or_gest)):
    row = catalog_svc.create_agence(db, body)
    db.refresh(row, attribute_names=["societe"])
    return _agence_response(row)


@router.put("/agences/{agence_id}", response_model=OrgAgenceResponse)
def update_agence(
    agence_id: int, body: OrgAgenceUpdate, db: Session = Depends(get_db), _=Depends(require_admin_or_gest)
):
    row = catalog_svc.update_agence(db, agence_id, body)
    db.refresh(row, attribute_names=["societe"])
    return _agence_response(row)


# ── Villes ────────────────────────────────────────────────────────────────────

@router.get("/villes", response_model=List[OrgVilleResponse])
def list_villes(include_inactive: bool = Query(False), db: Session = Depends(get_db)):
    return catalog_svc.list_villes(db, include_inactive=include_inactive)


@router.post("/villes", response_model=OrgVilleResponse, status_code=201)
def create_ville(body: OrgVilleCreate, db: Session = Depends(get_db), _=Depends(require_admin_or_gest)):
    return catalog_svc.create_ville(db, body)


@router.put("/villes/{ville_id}", response_model=OrgVilleResponse)
def update_ville(
    ville_id: int, body: OrgVilleUpdate, db: Session = Depends(get_db), _=Depends(require_admin_or_gest)
):
    return catalog_svc.update_ville(db, ville_id, body)


# ── Import helper ─────────────────────────────────────────────────────────────

@router.post("/import-from-data", response_model=CatalogImportResult)
def import_from_data(db: Session = Depends(get_db), _=Depends(require_admin)):
    """One-shot import of distinct values already present on products/users."""
    return catalog_svc.import_from_existing_data(db)
