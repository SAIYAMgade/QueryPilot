"""Investigation Case Management and Lifecycle API Endpoints."""

from typing import List
from fastapi import APIRouter, HTTPException

from app.schemas.investigation import (
    InvestigationResponse, InvestigationCreate, InvestigationUpdate
)
from app.investigations.repository import (
    get_all_investigations, get_investigation_by_id, create_investigation
)
from app.investigations.service import update_investigation_with_validation

router = APIRouter()


@router.get("", response_model=List[InvestigationResponse])
def list_investigations():
    """List all query investigations."""
    return get_all_investigations()


@router.post("", response_model=InvestigationResponse)
def new_investigation(data: InvestigationCreate):
    """Open a new query investigation case."""
    return create_investigation(data)


@router.get("/{investigation_id}", response_model=InvestigationResponse)
def get_investigation(investigation_id: str):
    """Retrieve full investigation details including timeline and findings."""
    inv = get_investigation_by_id(investigation_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return inv


@router.patch("/{investigation_id}", response_model=InvestigationResponse)
def patch_investigation(investigation_id: str, data: InvestigationUpdate):
    """Update investigation and validate resolution criteria if transitioning to RESOLVED."""
    try:
        return update_investigation_with_validation(investigation_id, data)
    except KeyError:
        raise HTTPException(status_code=404, detail="Investigation not found")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
