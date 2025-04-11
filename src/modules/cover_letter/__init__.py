from fastapi import APIRouter

router = APIRouter(prefix="/cover-letter", tags=["Cover Letter"])

from . import cover_letter 